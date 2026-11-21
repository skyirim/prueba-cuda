#!/usr/bin/env python3
"""Selector de tarifas Spot EN TIEMPO REAL, solo lectura. No inicia EC2.

ATENCION: el orquestador que ejecute RunInstances DEBE invocar select() de
nuevo inmediatamente antes de CADA lanzamiento y assert_fresh() antes de
consumirlo (TTL=60s). Ante insuficiencia Spot, reconsultar.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

# GPU CUDA cores FP32 acreditados por NVIDIA/AWS; solo GPU completas.
# Ampliar mediante PR con referencias verificables y pruebas reales.
GPU_CUDA_CORES = {
    "L4": 7424,
    "A10G": 9216,
    "L40S": 18176,
    "RTX PRO 4500": 10496,
    "RTX PRO Server 6000": 24064,
}

SPOT_GVT_QUOTA_CODE = "L-3819A6DF"
PLAN_TTL_SECONDS = 60


class SelectionError(RuntimeError):
    pass


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def gpu_qualified(info: dict, baseline: dict) -> bool:
    """No agregar GPU distintas ni utilizar fracciones sin garantía real."""
    ref = baseline["gpu"]
    for gpu in info.get("GpuInfo", {}).get("Gpus", []):
        name = gpu.get("Name")
        gpu_count = gpu.get("Count", 0)
        fraction = gpu.get("GpuPartitionSize", 1)
        vram = gpu.get("MemoryInfo", {}).get("SizeInMiB", 0)
        if (gpu.get("Manufacturer", "").lower() == "nvidia"
                and gpu_count >= ref["devices_min"]
                and fraction == 1
                and GPU_CUDA_CORES.get(name, 0) >= ref["cuda_cores_fp32_min"]
                and vram >= ref["vram_mib_min"]):
            return True
    return False


def hardware_qualified(info: dict, baseline: dict) -> bool:
    cpu = baseline["cpu"]
    return (info.get("VCpuInfo", {}).get("DefaultCores", 0) >= cpu["physical_cores_min"]
            and info.get("VCpuInfo", {}).get("DefaultVCpus", 0) >= cpu["logical_processors_min"]
            and info.get("MemoryInfo", {}).get("SizeInMiB", 0) >= cpu["ram_gib_min"] * 1024
            and "x86_64" in info.get("ProcessorInfo", {}).get("SupportedArchitectures", [])
            and gpu_qualified(info, baseline))


def pool_certified(pool: dict) -> bool:
    """Rechazar pools de muestra, imágenes sin validar y destinos incompletos."""
    required = ("region", "zone", "instance_type", "ami_id", "subnet_id")
    return (all(pool.get(k) for k in required)
            and str(pool["ami_id"]).startswith("ami-")
            and str(pool["subnet_id"]).startswith("subnet-")
            and pool.get("approved") is True
            and pool.get("linux_cuda_runtime_passed") is True
            and pool.get("cuda_sm75_build_passed") is True
            and pool.get("reference_execution_passed") is True)


def latest_quotes(ec2, types: list[str], now: datetime) -> dict[tuple[str, str], dict]:
    """Consultar API AHORA, tomar última cotización tipo/AZ (no mínimo histórico)."""
    data = {}
    pages = ec2.get_paginator("describe_spot_price_history").paginate(
        InstanceTypes=sorted(set(types)),
        ProductDescriptions=["Linux/UNIX"],
        StartTime=now - timedelta(days=7),
        EndTime=now,
    )
    for page in pages:
        for quote in page.get("SpotPriceHistory", []):
            key = quote["InstanceType"], quote["AvailabilityZone"]
            ts = quote["Timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            price = float(quote["SpotPrice"])
            if price <= 0:
                continue
            if key not in data or ts > data[key]["time"]:
                data[key] = {"time": ts, "price": price}
    return data


def select(baseline: dict, pools: list[dict], *,
           session, now: datetime | None = None) -> dict:
    """No consume instantáneas históricas; consulta precio/cuota/CPU ACTUAL."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise SelectionError("Hora UTC con zona horaria obligatoria.")
    if baseline.get("status") != "VERIFIED":
        raise SelectionError("Fuente hardware UCAM no certificada con pruebas reales.")
    if baseline["cpu"]["physical_cores_min"] < 12 or baseline["gpu"]["cuda_cores_fp32_min"] < 4352:
        raise SelectionError("Perfil debilita los mínimos UCAM; selección bloqueada.")
    vetted = [p for p in pools if pool_certified(p)]
    if not vetted:
        raise SelectionError("No hay pools/AMIs con pruebas CUDA y UCAM aprobadas.")
    regions = sorted({p["region"] for p in vetted})
    offers = []
    audited = []
    for region in regions:
        ec2 = session.client("ec2", region_name=region)
        quotas = session.client("service-quotas", region_name=region)
        quota = float(quotas.get_service_quota(
            ServiceCode="ec2", QuotaCode=SPOT_GVT_QUOTA_CODE)["Quota"]["Value"])
        region_pools = [p for p in vetted if p["region"] == region]
        types = sorted({p["instance_type"] for p in region_pools})
        info_rows = ec2.describe_instance_types(InstanceTypes=types)["InstanceTypes"]
        infos = {x["InstanceType"]: x for x in info_rows}
        # Precio interrogado durante ESTA selección; nunca cargar de JSON.
        quotes = latest_quotes(ec2, types, now)
        for pool in region_pools:
            kind = pool["instance_type"]
            spec = infos.get(kind)
            if not spec or not hardware_qualified(spec, baseline):
                audited.append({"region": region, "type": kind, "reason": "hardware"})
                continue
            vcpu = spec["VCpuInfo"]["DefaultVCpus"]
            if quota < vcpu:
                audited.append({"region": region, "type": kind, "reason": "quota"})
                continue
            spot = quotes.get((kind, pool["zone"]))
            if not spot:
                audited.append({"region": region, "type": kind, "reason": "no-spot-quote"})
                continue
            overhead = float(pool.get("estimated_additional_usd_h", 0))
            if overhead < 0:
                raise SelectionError("Overhead negativo prohibido.")
            offers.append({
                "region": region, "zone": pool["zone"], "type": kind,
                "ami_id": pool["ami_id"], "subnet_id": pool["subnet_id"],
                "price_usd_h": spot["price"],
                "quoted_timestamp": spot["time"].isoformat(),
                "estimated_additional_usd_h": overhead,
                "estimated_total_usd_h": round(spot["price"] + overhead, 8),
                "cpu_cores": spec["VCpuInfo"]["DefaultCores"],
                "gpu": spec["GpuInfo"]["Gpus"][0]["Name"],
            })
    if not offers:
        raise SelectionError(f"No existe precio Spot actual de pools compatibles. Excluidos: {audited}")
    offers.sort(key=lambda x: (x["estimated_total_usd_h"], x["price_usd_h"],
                               x["region"], x["zone"], x["type"]))
    return {
        "checked_at_utc": now.isoformat(),
        "expires_at_utc": (now + timedelta(seconds=PLAN_TTL_SECONDS)).isoformat(),
        "ttl_seconds": PLAN_TTL_SECONDS,
        "best": offers[0],
        "alternatives": offers[1:],
        "excluded": audited,
        "spot_capacity_guaranteed": False,
        "mode": "read-only-plan-NOT-launched",
    }


def assert_fresh(plan: dict, now: datetime | None = None) -> None:
    """Invocar JUSTO ANTES de RunInstances; si caduca, recalcular de cero."""
    now = now or datetime.now(timezone.utc)
    expires = datetime.fromisoformat(plan["expires_at_utc"])
    checked = datetime.fromisoformat(plan["checked_at_utc"])
    if (now.tzinfo is None or now < checked
            or now >= expires
            or (expires - checked).total_seconds() > PLAN_TTL_SECONDS):
        raise SelectionError("Plan de precio caducado o no confiable: reconsultar AWS.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="config/hardware-base.json")
    parser.add_argument("--pools", default="config/approved-gpu-pools.json")
    args = parser.parse_args()
    try:
        baseline = load_json(args.baseline)
        pools = load_json(args.pools)["pools"]
        import boto3
        plan = select(baseline, pools, session=boto3.Session())
        assert_fresh(plan)
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, SelectionError) as exc:
        print(f"BLOQUEADO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
