#!/usr/bin/env python3
"""Vigilancia no facturable: detecta baseline incompleto y cotizaciones caducadas."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def audit(today: date | None = None):
    today = today or date.today()
    baseline = json.loads((ROOT / "config/hardware-base.json").read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / "config/research-snapshot.json").read_text(encoding="utf-8"))
    captured = date.fromisoformat(snapshot["captured_utc"])
    max_age = int(snapshot["maximum_age_days"])
    age = (today - captured).days
    findings = []
    if baseline["status"] != "VERIFIED":
        findings.append("Equipo base documentado pero equivalencia CUDA y resultados UCAM/AWS pendientes de certificar.")
    if age > max_age:
        findings.append(f"Consulta de precios/cuotas AWS antigua: {age} dias (limite {max_age}).")
    return findings, age, snapshot["captured_utc"]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    findings, age, captured = audit()
    if args.markdown:
        print("# Auditoria mensual CUDA / AWS")
        print("")
        print(f"Fuente de precios/cuotas consultada: {captured} (hace {age} dias).")
        if findings:
            for finding in findings:
                print("ALERTA:", finding)
        else:
            print("Sin avisos documentales pendientes. Esto no sustituye tests CUDA reales.")
        print("")
        print("Documentacion: README.md, AGENTS.md y docs/implementacion.md")
    else:
        for finding in findings:
            print("ALERTA:", finding)
        if not findings:
            print("Documentacion temporal vigente; revisar ejecucion CUDA por separado.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
