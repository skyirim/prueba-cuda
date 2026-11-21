#!/usr/bin/env python3
"""Orquestador GitHub-hosted -> EC2 Spot -> SSM -> S3 -> GitHub Actions.

AWS roles are obtained through GitHub OIDC. No self-hosted runner or SSH port
is needed. Every SSM step is printed to the GitHub Actions job, with full
stdout/stderr saved to artifacts/aws-gpu/. No EC2 instance is left running on
normal exit; the independent AWS watchdog protects abnormal termination.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shlex
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from infrastructure.select_gpu_spot import (  # noqa: E402
    SelectionError, assert_fresh, load_json, select,
)

ALLOWED_REGION = "us-west-2"
JOB_STEPS = ("prepare", "inventory", "compile", "execute")
WAIT_SSM_SECONDS = 480
CMD_TIMEOUT_SECONDS = 900


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    print(f"[{stamp()}] {message}", flush=True)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta variable {name}. Ejecutar infraestructura y configurar repo.")
    return value


def read_ami(ec2, name: str):
    data = ec2.describe_images(
        Owners=["amazon"], Filters=[
            {"Name": "name", "Values": [name]},
            {"Name": "state", "Values": ["available"]},
            {"Name": "architecture", "Values": ["x86_64"]},
        ])["Images"]
    if not data:
        raise SelectionError("No existe una AMI oficial NVIDIA/Ubuntu con el nombre configurado.")
    return max(data, key=lambda x: x["CreationDate"])


def candidate_pools(session, config: dict, sg_id: str, vpc_id: str) -> list[dict]:
    """Manual qualification only; these pools are NEVER approved automatically."""
    region = config["region"]
    if region != ALLOWED_REGION:
        raise SelectionError("Región de calificación no autorizada.")
    ec2 = session.client("ec2", region_name=region)
    sg = ec2.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]
    if sg["VpcId"] != vpc_id:
        raise SelectionError("SG y VPC no coinciden.")
    image = read_ami(ec2, config["official_ami_name"])
    subnets = ec2.describe_subnets(Filters=[
        {"Name": "vpc-id", "Values": [vpc_id]},
        {"Name": "state", "Values": ["available"]},
    ])["Subnets"]
    pools = []
    for subnet in subnets:
        if subnet.get("AvailabilityZone") not in config.get("allowed_zones", []):
            continue
        for kind in config["instance_types"]:
            pools.append({
                "region": region,
                "zone": subnet["AvailabilityZone"],
                "instance_type": kind,
                "ami_id": image["ImageId"],
                "subnet_id": subnet["SubnetId"],
                "estimated_additional_usd_h": float(config.get("estimated_additional_usd_h", 0.02)),
                "probe_allowed": True,
                "approved": False,
            })
    if not pools:
        raise SelectionError("Ninguna subred autorizada disponible para calificación.")
    return pools


def get_pools(session, args, baseline: dict, sg_id: str, vpc_id: str):
    if args.mode == "qualify":
        if os.environ.get("AWS_CUDA_PROBE_ENABLED") != "true":
            raise SelectionError("Calificación AWS no habilitada explícitamente.")
        cfg = load_json("config/probe-gpu-pools.json")
        return candidate_pools(session, cfg, sg_id, vpc_id)
    if baseline["status"] != "VERIFIED":
        raise SelectionError("Baseline DRAFT: el modo push no arranca EC2.")
    pools = load_json("config/approved-gpu-pools.json")["pools"]
    if not pools:
        raise SelectionError("No existen pools CUDA aprobados con pruebas reales.")
    return pools


def volume_size(ec2, ami_id: str) -> tuple[str, int]:
    image = ec2.describe_images(ImageIds=[ami_id])["Images"][0]
    if image.get("Architecture") != "x86_64":
        raise SelectionError("La imagen debe ser x86-64 como la referencia UCAM.")
    root = image.get("RootDeviceName", "/dev/sda1")
    mappings = image.get("BlockDeviceMappings", [])
    size = max([int(m["Ebs"]["VolumeSize"]) for m in mappings
                if m.get("DeviceName") == root and "Ebs" in m] or [80])
    return root, max(80, size)


def launch(session, plan: dict, args, profile: str, sg: str, run_id: str, deadline: int):
    spot_ceiling = float(args.spot_ceiling)
    all_offers = [plan["best"]] + plan["alternatives"]
    if args.mode == "qualify" and not os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        raise SelectionError("Calificación GPU solo por workflow_dispatch.")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise SelectionError("El lanzamiento de instancias requiere refs/heads/main.")
    # Every attempted launch re-reads AWS price/quotas in this function caller.
    for offer in all_offers:
        if offer["price_usd_h"] > spot_ceiling:
            log(f"Oferta rechazada por techo de precio: {offer['type']} {offer['price_usd_h']}")
            continue
        if offer["region"] != ALLOWED_REGION:
            continue
        ec2 = session.client("ec2", region_name=offer["region"])
        root, size = volume_size(ec2, offer["ami_id"])
        now = datetime.now(timezone.utc)
        assert_fresh(plan, now)
        max_price = min(spot_ceiling, round(offer["price_usd_h"] * 1.15, 6))
        if max_price < offer["price_usd_h"]:
            continue
        tags = [
            {"Key": "Project", "Value": "prueba-cuda"},
            {"Key": "Mode", "Value": "ci"},
            {"Key": "GitHubRun", "Value": run_id},
            {"Key": "ExpireAtEpoch", "Value": str(deadline)},
            {"Key": "Purpose", "Value": args.mode},
        ]
        log(f"RunInstances {offer['type']} {offer['zone']}; Spot verificado "
            f"{offer['price_usd_h']:.5f} USD/h, cap {max_price:.5f} USD/h; "
            f"expires {deadline}.")
        resp = ec2.run_instances(
            ImageId=offer["ami_id"], InstanceType=offer["type"],
            MinCount=1, MaxCount=1,
            IamInstanceProfile={"Name": profile},
            NetworkInterfaces=[{"DeviceIndex": 0, "SubnetId": offer["subnet_id"],
                                "Groups": [sg], "AssociatePublicIpAddress": True,
                                "DeleteOnTermination": True}],
            BlockDeviceMappings=[{"DeviceName": root, "Ebs": {
                "VolumeSize": size, "VolumeType": "gp3",
                "Encrypted": True, "DeleteOnTermination": True}}],
            MetadataOptions={"HttpTokens": "required"},
            InstanceMarketOptions={"MarketType": "spot",
                                   "SpotOptions": {"SpotInstanceType": "one-time",
                                                   "InstanceInterruptionBehavior": "terminate",
                                                   "MaxPrice": f"{max_price:.6f}"}},
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[
                {"ResourceType": "instance", "Tags": tags},
                {"ResourceType": "volume", "Tags": tags},
            ],
            UserData="#!/bin/bash\nset -eu\nsystemctl start amazon-ssm-agent || "
                     "systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service || true\n",
        )
        return offer, resp["Instances"][0]["InstanceId"], size
    raise SelectionError("Ninguna oferta respetó el presupuesto y las restricciones.")


def wait_for_ssm(session, instance_id: str, region: str):
    ec2 = session.client("ec2", region_name=region)
    ssm = session.client("ssm", region_name=region)
    ec2.get_waiter("instance_running").wait(
        InstanceIds=[instance_id], WaiterConfig={"Delay": 10, "MaxAttempts": 36})
    until = time.monotonic() + WAIT_SSM_SECONDS
    while time.monotonic() < until:
        data = ssm.describe_instance_information(
            Filters=[{"Key": "InstanceIds", "Values": [instance_id]}])
        if any(x.get("PingStatus") == "Online" for x in data["InstanceInformationList"]):
            log("SSM Agent online, host EC2 listo.")
            return
        log("Esperando registro del agente SSM...")
        time.sleep(12)
    raise TimeoutError("La EC2 no se registró en Systems Manager en el plazo máximo.")


def collect_ssm_output(s3, bucket: str, prefix: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(obj["Key"] for obj in page.get("Contents", []))
    for index, key in enumerate(sorted(keys)):
        if key.endswith("/"):
            continue
        name = f"{index:02d}-{key.rsplit('/', 1)[-1]}"
        contents = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        (dest / name).write_bytes(contents)
        print(f"::group::SSM salida {key}", flush=True)
        print(contents.decode("utf-8", errors="replace"), flush=True)
        print("::endgroup::", flush=True)
    if not keys:
        log("SSM todavia no ha publicado logs S3; conservar CloudWatch y diagnóstico.")


def ssm_step(session, instance_id, region, bucket, prefix, group, name, script, dest: Path):
    ssm = session.client("ssm", region_name=region)
    s3 = session.client("s3", region_name=region)
    log(f"SSM etapa {name} -> EC2 {instance_id}")
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["bash -lc " + shlex.quote(script)]},
        TimeoutSeconds=180,
        OutputS3BucketName=bucket,
        OutputS3KeyPrefix=f"{prefix}/ssm/{name}",
        CloudWatchOutputConfig={"CloudWatchOutputEnabled": True,
                                "CloudWatchLogGroupName": group},
        Comment=f"prueba-cuda: {name}",
    )
    command_id = response["Command"]["CommandId"]
    end = time.monotonic() + CMD_TIMEOUT_SECONDS
    status = "Pending"
    inv = None
    while time.monotonic() < end:
        time.sleep(5)
        try:
            inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        except ssm.exceptions.InvocationDoesNotExist:
            continue
        status = inv["Status"]
        if status in ("Success", "Failed", "Cancelled", "TimedOut", "Cancelling"):
            break
    else:
        status = "HostPollTimeout"
    collect_ssm_output(s3, bucket, f"{prefix}/ssm/{name}/", dest)
    outcome = {
        "name": name, "status": status, "command_id": command_id,
        "response_code": inv.get("ResponseCode") if inv else None,
        "stdout_url": inv.get("StandardOutputUrl") if inv else None,
        "stderr_url": inv.get("StandardErrorUrl") if inv else None,
    }
    write_json(dest / "result.json", outcome)
    if status != "Success":
        raise RuntimeError(f"Etapa {name} falló: {status} (SSM {command_id})")
    return outcome


def script_for_step(name: str, bucket: str, prefix: str, region: str) -> str:
    head = "set -euo pipefail\nexport AWS_DEFAULT_REGION=" + shlex.quote(region) + "\n"
    work = "cd /opt/prueba-cuda\n"
    if name == "prepare":
        return (head
                + "command -v aws >/dev/null || "
                + "(apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y awscli)\n"
                + "mkdir -p /opt/prueba-cuda\n"
                + f"aws s3 cp {shlex.quote(f's3://{bucket}/{prefix}/source.tar.gz')} /tmp/prueba-cuda-source.tar.gz\n"
                + "tar -xzf /tmp/prueba-cuda-source.tar.gz -C /opt/prueba-cuda\n"
                + work + "bash scripts/ci/prepare.sh\n")
    if name in ("inventory", "compile", "execute"):
        return head + work + f"bash scripts/ci/{name}.sh\n"
    if name == "archive":
        return (head + work
                + "mkdir -p artifacts\n"
                + "tar -czf /tmp/prueba-cuda-results.tar.gz "
                + "--warning=no-file-changed build artifacts 2>/dev/null || "
                + "tar -czf /tmp/prueba-cuda-results.tar.gz artifacts\n"
                + f"aws s3 cp /tmp/prueba-cuda-results.tar.gz {shlex.quote(f's3://{bucket}/{prefix}/results.tar.gz')}\n")
    raise ValueError("Etapa desconocida.")


def terminate(session, instance_id: str, region: str):
    ec2 = session.client("ec2", region_name=region)
    log(f"Terminando EC2 {instance_id}...")
    ec2.terminate_instances(InstanceIds=[instance_id])
    ec2.get_waiter("instance_terminated").wait(
        InstanceIds=[instance_id], WaiterConfig={"Delay": 10, "MaxAttempts": 40})
    log(f"EC2 terminada {instance_id}")


def cleanup(session, path: Path):
    if not path.exists():
        log("No hay estado local de EC2 para limpieza de emergencia.")
        return
    state = json.loads(path.read_text(encoding="utf-8"))
    iid = state.get("instance_id")
    if iid and state.get("terminated") is not True:
        terminate(session, iid, state["region"])
        state["terminated"] = True
        write_json(path, state)


def run(args, session) -> int:
    if os.environ.get("GITHUB_REPOSITORY") != "skyirim/prueba-cuda":
        raise SelectionError("Este controlador solo se puede ejecutar desde skyirim/prueba-cuda.")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise SelectionError("Solo main puede lanzar EC2 mediante OIDC.")
    if args.mode == "ci" and os.environ.get("AWS_CUDA_ENABLED") != "true":
        raise SelectionError("Activación de push CUDA no autorizada.")
    if args.mode == "qualify" and os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise SelectionError("La calificación solo puede iniciarse manualmente.")
    if not (0 < args.spot_ceiling <= 4.0):
        raise ValueError("Techo Spot debe estar en (0,4] USD/h.")
    if not (15 <= args.ttl_minutes <= 90):
        raise ValueError("TTL entre 15 y 90 minutos.")
    bucket = env_required("AWS_GPU_S3_BUCKET")
    profile = env_required("AWS_GPU_INSTANCE_PROFILE")
    sg_id = env_required("AWS_GPU_SECURITY_GROUP")
    vpc_id = env_required("AWS_GPU_VPC_ID")
    log_group = env_required("AWS_GPU_LOG_GROUP")
    region = env_required("AWS_REGION")
    if region != ALLOWED_REGION:
        raise SelectionError("Solo Oregón habilitado en esta implantación.")
    baseline = load_json("config/hardware-base.json")
    pools = get_pools(session, args, baseline, sg_id, vpc_id)
    run_id = env_required("GITHUB_RUN_ID") + "/" + env_required("GITHUB_RUN_ATTEMPT")
    prefix = "runs/" + run_id
    outdir = Path("artifacts/aws-gpu")
    outdir.mkdir(parents=True, exist_ok=True)
    state_path = outdir / "state.json"
    state = {"mode": args.mode, "region": region, "started_at": stamp(),
             "run_id": run_id, "terminated": False, "steps": []}
    write_json(state_path, state)
    s3 = session.client("s3", region_name=region)
    local = Path(args.archive)
    if not local.is_file():
        raise FileNotFoundError(local)
    log("Subiendo código de main a S3 cifrado...")
    s3.upload_file(str(local), bucket, prefix + "/source.tar.gz")
    deadline = int(time.time() + args.ttl_minutes * 60)
    failed = None
    instance_id = None
    offer = None
    start = time.monotonic()
    try:
        tried = set()
        # Cada reintento consulta las tarifas y cuotas de AWS de nuevo.
        for _ in range(4):
            plan = select(baseline, pools, session=session, qualification=args.mode == "qualify")
            choices = [plan["best"]] + plan["alternatives"]
            remaining = [p for p in choices if (p["region"], p["zone"], p["type"]) not in tried]
            if not remaining:
                raise SelectionError("No hay más ofertas Spot válidas tras reconsultar precios.")
            plan["best"] = remaining[0]
            plan["alternatives"] = remaining[1:]
            try:
                offer, instance_id, size = launch(
                    session, plan, args, profile, sg_id, run_id.replace("/", "-"), deadline)
                break
            except Exception as exc:
                # Solo capacidad/precio, nunca errores IAM, configuración ni cuotas.
                code = getattr(getattr(exc, "response", None), "get", lambda *_: {})("Error", {}).get("Code", "")
                if code not in ("InsufficientInstanceCapacity", "SpotMaxPriceTooLow",
                                "UnfulfillableCapacity", "InsufficientFreeAddressesInSubnet"):
                    raise
                tried.add((plan["best"]["region"], plan["best"]["zone"], plan["best"]["type"]))
                log(f"Spot {plan['best']['type']} no disponible: {code}. Reconsultando.")
        if not instance_id:
            raise SelectionError("No se ha podido iniciar Spot en cuatro intentos.")
        state.update({"instance_id": instance_id, "offer": offer,
                      "volume_gib": size, "region": offer["region"],
                      "price_checked_at": plan["checked_at_utc"], "deadline_epoch": deadline})
        write_json(state_path, state)
        wait_for_ssm(session, instance_id, region)
        for name in JOB_STEPS:
            try:
                outcome = ssm_step(session, instance_id, region, bucket, prefix, log_group,
                                   name, script_for_step(name, bucket, prefix, region),
                                   outdir / "ssm" / name)
                state["steps"].append(outcome)
                write_json(state_path, state)
            except Exception as exc:
                state["failed_step"] = name
                failed = exc
                write_json(state_path, state)
                break
        # Archivar SIEMPRE que el host SSM esté disponible, incluso tras un fallo.
        try:
            ssm_step(session, instance_id, region, bucket, prefix, log_group,
                     "archive", script_for_step("archive", bucket, prefix, region),
                     outdir / "ssm" / "archive")
        except Exception as exc:
            if failed is None:
                failed = exc
            log(f"No se pudo publicar el tar de resultados: {exc}")
        try:
            s3.download_file(bucket, prefix + "/results.tar.gz",
                             str(outdir / "results.tar.gz"))
        except Exception:
            log("No hay results.tar.gz; conservar las salidas SSM registradas.")
        if failed is not None:
            raise failed
        return 0
    except Exception as exc:
        (outdir / "error.txt").write_text(
            "".join(traceback.format_exception(exc)), encoding="utf-8")
        print(f"::error::{type(exc).__name__}: {exc}", flush=True)
        raise
    finally:
        state["duration_seconds"] = round(time.monotonic() - start)
        if offer:
            state["estimated_compute_usd"] = round(
                state["duration_seconds"] / 3600 * offer["price_usd_h"], 5)
            state["estimated_total_usd"] = round(
                state["duration_seconds"] / 3600 * offer["estimated_total_usd_h"], 5)
        if instance_id:
            try:
                terminate(session, instance_id, region)
                state["terminated"] = True
            except Exception as exc:
                log(f"ERROR DE LIMPIEZA: {exc}; watchdog ExpireAtEpoch sigue activo.")
                state["termination_error"] = str(exc)
        write_json(state_path, state)
        summary = Path(os.environ.get("GITHUB_STEP_SUMMARY", "/dev/null"))
        with summary.open("a", encoding="utf-8") as file:
            file.write(f"\n## AWS GPU {args.mode}\n\n")
            file.write(f"- EC2: {instance_id or 'no iniciada'}\n")
            file.write(f"- Tipo/AZ: {offer['type'] if offer else '-'} / "
                       f"{offer['zone'] if offer else '-'}\n")
            file.write(f"- Precio Spot (consultado al lanzar): "
                       f"{offer['price_usd_h'] if offer else '-'} USD/h\n")
            file.write(f"- Tiempo: {state['duration_seconds']} s\n")
            file.write(f"- Coste EC2 estimado: {state.get('estimated_compute_usd', '-')} USD\n")
            file.write(f"- Terminada: {state['terminated']}\n")
            file.write(f"- Etapa fallida: {state.get('failed_step', 'ninguna')}\n")
            file.write(f"- Logs: adjuntos en artefacto aws-gpu-{run_id.replace('/', '-')}\n")
        log("El precio estimado no constituye facturación real (EBS/IP/logs adicionales).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["qualify", "ci"], required=False, default="ci")
    parser.add_argument("--archive", default="source.tar.gz")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--spot-ceiling", type=float, default=1.5)
    parser.add_argument("--ttl-minutes", type=int, default=70)
    args = parser.parse_args()
    try:
        import boto3
        session = boto3.Session(region_name=os.environ.get("AWS_REGION", ALLOWED_REGION))
        if args.cleanup:
            cleanup(session, Path("artifacts/aws-gpu/state.json"))
            return 0
        return run(args, session)
    except Exception as exc:
        log(f"ERROR {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
