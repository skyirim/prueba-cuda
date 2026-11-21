#!/usr/bin/env python3
"""Revisa integridad documental sin activar recursos de AWS."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "README.md", "AGENTS.md", "opencode.json",
    "docs/hardware-base.md", "docs/compatibilidad.md",
    "docs/aws-investigacion.md", "docs/arquitectura.md",
    "docs/implementacion.md", "docs/operacion.md",
    "docs/seguridad.md", "docs/decisiones/0001-criterios-de-equivalencia.md",
    "config/hardware-base.json", "config/hardware-base.schema.json",
    "config/inventory-template.json", "scripts/check_baseline.py",
    "src/hello_c.c", "src/cuda_smoke.cu", "Makefile",
    ".github/workflows/docs-check.yml", ".github/workflows/maintenance.yml",
    "templates/cuda-gpu-workflow.yml", "scripts/audit_maintenance.py",
    "config/research-snapshot.json", "docs/plan-pruebas.md", "docs/registro.md",
    "infrastructure/README.md",
    ".opencode/skills/cuda-equivalencia/SKILL.md",
    ".opencode/skills/aws-spot-gpu/SKILL.md",
    ".opencode/skills/runner-efimero/SKILL.md",
]

def main() -> int:
    errors = []
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            errors.append("Falta archivo requerido: " + rel)
    for rel in ["config/hardware-base.json",
                "config/hardware-base.schema.json",
                "config/inventory-template.json", "opencode.json"]:
        if (ROOT / rel).exists():
            try:
                json.loads((ROOT / rel).read_text(encoding="utf-8"))
            except (ValueError, UnicodeError) as exc:
                errors.append("JSON invalido " + rel + ": " + str(exc))

    md = ROOT / "README.md"
    if md.exists():
        text = md.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            target = unquote(link.split("#")[0].strip())
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            if not (ROOT / target).exists():
                errors.append("README enlaza ruta inexistente: " + target)

    config_file = ROOT / "config/hardware-base.json"
    if config_file.exists():
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
            status = data.get("status")
            if status not in {"PENDING_SOURCE", "DRAFT", "VERIFIED"}:
                errors.append("Estado baseline no reconocido")
            elif status != "VERIFIED":
                print("BLOQUEO DOCUMENTADO: equipo base sin certificacion completa.")
        except (ValueError, UnicodeError):
            pass

    for error in errors:
        print("ERROR:", error, file=sys.stderr)
    if errors:
        print("Verificacion documental FALLIDA.", file=sys.stderr)
        return 1
    print("Documentos, JSON y enlaces internos presentes. No implica compatibilidad CUDA ni despliegue AWS.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
