#!/usr/bin/env python3
"""Comprueba que 3 arranques EC2 distintos ejecutaron SAXPY y se eliminaron.

No simula resultados, nunca sustituye los registros reales SSM.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys


def verify(root: Path, repetitions: int = 3) -> list[dict]:
    results = []
    seen_ids = set()
    for number in range(1, repetitions + 1):
        folder = root / f"run-{number}"
        state_path = folder / "state.json"
        if not state_path.is_file():
            raise RuntimeError(f"Prueba {number}: no existe state.json")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        instance_id = state.get("instance_id")
        if not instance_id or instance_id in seen_ids:
            raise RuntimeError(f"Prueba {number}: EC2 ausente o reutilizada")
        seen_ids.add(instance_id)
        if state.get("terminated") is not True:
            raise RuntimeError(f"Prueba {number}: EC2 sin terminación confirmada")
        if state.get("failed_step"):
            raise RuntimeError(f"Prueba {number}: falló {state['failed_step']}")
        steps = {x["name"]: x for x in state.get("steps", [])}
        for name in ("prepare", "inventory", "compile", "execute"):
            step = steps.get(name)
            if not step or step.get("status") != "Success" or step.get("response_code") != 0:
                raise RuntimeError(f"Prueba {number}: {name} sin éxito confirmado")
        execute = folder / "ssm" / "execute"
        logs = [p for p in execute.rglob("*")
                if p.is_file() and p.name != "result.json"]
        if not logs or not any("SAXPY_NVIDIA_PASS" in p.read_text(
                encoding="utf-8", errors="replace") for p in logs):
            raise RuntimeError(f"Prueba {number}: sin SAXPY_NVIDIA_PASS en logs SSM")
        if not (folder / "results.tar.gz").is_file():
            raise RuntimeError(f"Prueba {number}: sin binarios/resultados archivados")
        results.append({
            "repetition": number, "instance_id": instance_id,
            "instance_type": state.get("offer", {}).get("type"),
            "availability_zone": state.get("offer", {}).get("zone"),
            "spot_usd_h": state.get("offer", {}).get("price_usd_h"),
            "duration_s": state.get("duration_seconds"),
            "compute_estimate_usd": state.get("estimated_compute_usd"),
            "terminated": True, "saxpy": "PASS",
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts/aws-gpu"))
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    try:
        results = verify(args.root, args.count)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        summary = Path("artifacts/aws-gpu/three-runs-summary.json")
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"SAXPY_THREE_RUNS_PASS: {len(results)} EC2 distintas, 3 pruebas CUDA y 3 terminaciones")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"SAXPY_THREE_RUNS_FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
