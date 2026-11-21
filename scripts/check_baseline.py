#!/usr/bin/env python3
"""Gate de requisitos. La comparacion numerica NO reemplaza ensayos CUDA reales."""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

def positive(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0

def cc_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+\.[0-9]+", value):
        raise ValueError("compute capability debe ser X.Y")
    return tuple(map(int, value.split(".")))

def validate(baseline: dict, inventory: dict | None) -> list[str]:
    errors = []
    if baseline.get("status") != "VERIFIED":
        return ["El perfil base no tiene estado VERIFIED: no se certifica equivalencia."]
    src = baseline.get("source_document", {})
    if not src.get("name") or not re.fullmatch(r"[0-9a-fA-F]{64}", str(src.get("sha256", ""))):
        errors.append("Fuente base sin nombre y SHA-256 valido.")
    cpu = baseline.get("cpu", {})
    gpu = baseline.get("gpu", {})
    if not cpu.get("architecture"):
        errors.append("Arquitectura CPU de base desconocida.")
    for key in ("physical_cores_min", "logical_processors_min", "ram_gib_min"):
        if not positive(cpu.get(key)):
            errors.append("CPU base: falta " + key)
    for key in ("devices_min", "cuda_cores_fp32_min", "sm_min", "vram_mib_min"):
        if not positive(gpu.get(key)):
            errors.append("GPU base: falta " + key)
    if gpu.get("full_gpu_required") is None:
        errors.append("GPU base: falta full_gpu_required.")
    try:
        cc_tuple(gpu.get("compute_capability_min"))
    except ValueError:
        errors.append("GPU base: falta compute_capability_min.")
    portability = baseline.get("portability", {})
    if portability.get("same_cpu_binary_required") is None:
        errors.append("No se ha definido compatibilidad de binario CPU.")
    if not portability.get("reference_tests"):
        errors.append("No se identifican pruebas ejecutables de la referencia.")
    if inventory is None:
        errors.append("Falta inventario de la instancia AWS y resultados reales.")
        return errors
    actual_cpu = inventory.get("cpu", {})
    actual_gpu = inventory.get("gpu", {})
    evidence = inventory.get("evidence", {})
    if not actual_cpu.get("physical_cores_verified") or not evidence.get("cpu_physical_cores"):
        errors.append("Cores fisicos CPU de destino sin evidencia verificable.")
    if not actual_gpu.get("gpu_cores_verified") or not evidence.get("gpu_cuda_cores"):
        errors.append("CUDA cores efectivos de destino sin evidencia verificable.")
    if actual_gpu.get("is_fractional") is None:
        errors.append("No se sabe si la GPU de destino es fraccionada.")
    elif gpu.get("full_gpu_required") and actual_gpu["is_fractional"]:
        errors.append("Se exige GPU completa: el destino es fraccionado.")
    for min_key, actual_key in [
        ("physical_cores_min", "physical_cores_visible"),
        ("logical_processors_min", "logical_processors"),
        ("ram_gib_min", "ram_gib"),
    ]:
        req, got = cpu.get(min_key), actual_cpu.get(actual_key)
        if positive(req) and (not positive(got) or got < req):
            errors.append(f"CPU {actual_key}={got} < minimo {req}.")
    for min_key, actual_key in [
        ("devices_min", "devices"),
        ("cuda_cores_fp32_min", "cuda_cores_fp32_verified"),
        ("sm_min", "sm_visible"),
        ("vram_mib_min", "vram_mib"),
    ]:
        req, got = gpu.get(min_key), actual_gpu.get(actual_key)
        if positive(req) and (not positive(got) or got < req):
            errors.append(f"GPU {actual_key}={got} < minimo {req}.")
    try:
        if cc_tuple(actual_gpu.get("compute_capability")) < cc_tuple(gpu.get("compute_capability_min")):
            errors.append("Compute capability del destino inferior a la base.")
    except ValueError:
        errors.append("Compute capability del destino no medido.")
    if portability.get("same_cpu_binary_required") is True:
        if cpu.get("architecture") != actual_cpu.get("architecture"):
            errors.append("ISA CPU distinta: mismo binario no ejecutable de modo nativo.")
    for key in ("c_smoke_pass", "cuda_smoke_pass", "reference_comparison_pass"):
        if inventory.get("tests", {}).get(key) is not True:
            errors.append("Falta prueba real satisfactoria: " + key)
    if not evidence.get("reference_results") or not evidence.get("timestamp_utc"):
        errors.append("Falta evidencia fechada de resultados contra referencia.")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="config/hardware-base.json")
    parser.add_argument("--inventory", help="JSON del entorno AWS y evidencia")
    args = parser.parse_args()
    try:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8")) if args.inventory else None
    except (OSError, ValueError) as exc:
        print("ERROR leyendo JSON:", exc, file=sys.stderr)
        return 2
    errors = validate(baseline, inventory)
    if errors:
        for err in errors:
            print("BLOQUEADO:", err, file=sys.stderr)
        return 1
    print("COMPARACION NUMERICA + FLAGS DE PRUEBAS: OK. Revisar evidencias manualmente; no es garantia universal.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
