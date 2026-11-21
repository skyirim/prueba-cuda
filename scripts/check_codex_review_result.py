#!/usr/bin/env python3
"""Check de solo lectura: bloquea si hay revisiones de Codex sin resolver."""
import json
from pathlib import Path
import sys


def check(data: dict) -> list[str]:
    findings = data.get("findings")
    if not isinstance(findings, list):
        return ["La auditoria no contiene una lista valida de findings."]
    return [
        f"{group.get('title', group.get('key', 'sin referencia'))}: "
        + ", ".join(str(item.get("url") or item.get("id")) for item in group.get("items", []))
        for group in findings
    ]


def main() -> int:
    try:
        data = json.loads(Path("codex-review-audit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("ERROR: no se puede validar el resultado Codex:", exc, file=sys.stderr)
        return 2
    pending = check(data)
    for msg in pending:
        print("CODEX PENDIENTE:", msg, file=sys.stderr)
    if pending:
        print(f"Fallo cerrado: {len(pending)} grupos pendientes.", file=sys.stderr)
        return 1
    print("Sin hallazgos Codex pendientes en la auditoria consultada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
