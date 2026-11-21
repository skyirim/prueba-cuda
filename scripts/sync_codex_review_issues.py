#!/usr/bin/env python3
"""Mantiene issues de hallazgos Codex sin duplicados. No edita codigo."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API = "https://api.github.com"
MAX_PAGES = 20
MARKER = "<!-- codex-review-task:"


def marker(key: str) -> str:
    return MARKER + key + " -->"


def issue_body(group: dict) -> str:
    lines = [
        marker(group["key"]),
        "## Revisión de Codex pendiente",
        "",
        f"Origen: {group.get('url')}",
        "",
        "La directiva CODEX-REVIEW-12 exige reproducir cada defecto, implementar la",
        "solución, ejecutar pruebas, responder en el hilo original y volver a",
        "inspeccionar las revisiones antes de cerrar esta incidencia.",
        "",
    ]
    for item in group["items"]:
        lines += [
            f"### {item.get('kind')} — {item.get('url')}",
            "",
            (item.get("body") or "")[:2500],
            "",
        ]
    lines += [
        "### Requisitos de cierre",
        "",
        "- [ ] Solución aplicada (PR/commit enlazado) y pruebas pertinentes ejecutadas.",
        "- [ ] Comentarios originales respondidos con evidencias.",
        "- [ ] Hilos de Codex marcados realmente resueltos en GitHub.",
        "- [ ] Auditoría repetida sin hallazgos anteriores ni nuevos.",
        "",
        "Esta incidencia se mantiene automáticamente mientras la API siga",
        "mostrando una observación pendiente. La vigilancia no modifica código.",
        "",
    ]
    return "\n".join(lines)


class Client:
    def __init__(self, token: str):
        if not token:
            raise ValueError("Falta GITHUB_TOKEN.")
        self.token = token

    def request(self, method: str, path: str, payload=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(API + path, method=method, data=data, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "prueba-cuda-codex-review-sentinel",
            "Content-Type": "application/json",
        })
        with urlopen(req, timeout=30) as response:
            if response.status == 204:
                return None
            return json.load(response)

    def list_issues(self, repo: str):
        rows = []
        for page in range(1, MAX_PAGES + 1):
            part = self.request("GET",
                                f"/repos/{repo}/issues?state=all&per_page=100&page={page}")
            rows.extend(x for x in part if "pull_request" not in x)
            if len(part) < 100:
                return rows
        raise RuntimeError("Paginacion de issues incompleta: no sincronizar.")


def synchronize(client: Client, audit: dict) -> dict:
    repo = audit["repo"]
    current = {}
    for issue in client.list_issues(repo):
        body = issue.get("body") or ""
        if body.startswith(MARKER):
            key = body.split("-->", 1)[0][len(MARKER):]
            current[key] = issue

    found = {g["key"]: g for g in audit["findings"]}
    changed = {"created": [], "reopened": [], "closed": [], "updated": []}
    for key, group in found.items():
        title = "[codex-review] " + group["title"] + " — observaciones pendientes"
        body = issue_body(group)
        old = current.get(key)
        if old is None:
            obj = client.request("POST", f"/repos/{repo}/issues",
                                 {"title": title, "body": body})
            changed["created"].append(obj["html_url"])
        else:
            update = {}
            if old.get("state") != "open":
                update["state"] = "open"
                changed["reopened"].append(old["html_url"])
            if old.get("body") != body:
                update["body"] = body
            if old.get("title") != title:
                update["title"] = title
            if update:
                client.request("PATCH", f"/repos/{repo}/issues/{old['number']}", update)
                changed["updated"].append(old["html_url"])
    for key, old in current.items():
        if key not in found and old.get("state") == "open":
            client.request("PATCH", f"/repos/{repo}/issues/{old['number']}",
                           {"state": "closed", "state_reason": "completed"})
            changed["closed"].append(old["html_url"])
    return changed


def main() -> int:
    try:
        path = Path(os.environ.get("CODEX_AUDIT_OUTPUT", "codex-review-audit.json"))
        audit = json.loads(path.read_text(encoding="utf-8"))
        changed = synchronize(Client(os.environ.get("GITHUB_TOKEN", "")), audit)
        print(json.dumps(changed, indent=2, ensure_ascii=False))
        count = len(audit["findings"])
        if count:
            print(f"REVISIONES CODEX SIN RESOLVER: {count}. Check bloqueado.", file=sys.stderr)
        return 1 if count else 0
    except (OSError, KeyError, ValueError, RuntimeError, HTTPError, URLError) as exc:
        print(f"ERROR al sincronizar revisiones Codex: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
