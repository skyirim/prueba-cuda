#!/usr/bin/env python3
"""Auditoria de hallazgos Codex en PRs y comentarios de commits.

Solo lectura. Requiere GITHUB_TOKEN y GITHUB_REPOSITORY para consulta real.
Los hilos solo se consideran cerrados si GitHub indica isResolved=true.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BOT_NAME = "chatgpt-codex-connector"
API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
MAX_PAGES = 20


def is_codex(login: str | None) -> bool:
    return str(login or "").lower().removesuffix("[bot]") == BOT_NAME


def is_review_receipt(body: str | None) -> bool:
    text = (body or "").lstrip()
    return text.startswith("<!-- codex-review-receipt:") or text.startswith(
        "<!-- codex-pull-request-review-summary -->"
    )


def thread_findings(nodes: list[dict]) -> list[dict]:
    """Devuelve solo hilos no resueltos que incluyen comentarios de Codex."""
    findings = []
    for thread in nodes:
        if thread.get("isResolved"):
            continue
        comments = thread.get("comments", {}).get("nodes", [])
        for comment in comments:
            if is_codex((comment.get("author") or {}).get("login")):
                findings.append({
                    "id": thread["id"],
                    "kind": "pr-thread",
                    "url": comment.get("url"),
                    "body": comment.get("body", ""),
                    "outdated": bool(thread.get("isOutdated")),
                })
                break
    return findings


def valid_ack(entry: dict | None) -> bool:
    """Comentarios sin hilo necesitan solucion referenciada de modo auditable."""
    if not isinstance(entry, dict):
        return False
    sha = entry.get("fix_commit_sha")
    url = entry.get("evidence_url")
    return bool(
        isinstance(sha, str) and re.fullmatch("[0-9a-fA-F]{40}", sha)
        and isinstance(url, str) and url.startswith("https://github.com/")
    )


def commit_comment_findings(comments: list[dict], resolutions: dict) -> list[dict]:
    findings = []
    for comment in comments:
        if not is_codex((comment.get("user") or {}).get("login")):
            continue
        body = comment.get("body") or ""
        if is_review_receipt(body) or not body.strip():
            continue
        comment_id = str(comment["id"])
        if valid_ack(resolutions.get("commit_comments", {}).get(comment_id)):
            continue
        findings.append({
            "id": comment_id, "kind": "commit-comment",
            "url": comment.get("html_url"),
            "body": body, "commit_id": comment.get("commit_id"),
        })
    return findings


class GitHubClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("Se requiere GITHUB_TOKEN (sin permisos de escritura para auditar).")
        self.token = token

    def request(self, path: str, payload: dict | None = None):
        url = GRAPHQL if path == "/graphql" else API + path
        raw = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=raw, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "prueba-cuda-codex-review-sentinel",
            "Content-Type": "application/json",
        }, method="POST" if raw is not None else "GET")
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
        if path == "/graphql" and data.get("errors"):
            raise RuntimeError("GitHub GraphQL: " + json.dumps(data["errors"]))
        return data

    def paged(self, path: str):
        results = []
        for page in range(1, MAX_PAGES + 1):
            sep = "&" if "?" in path else "?"
            part = self.request(f"{path}{sep}per_page=100&page={page}")
            if not isinstance(part, list):
                raise ValueError("La API de GitHub no devolvio una lista paginada.")
            results.extend(part)
            if len(part) < 100:
                return results
        raise RuntimeError("GitHub: pagina limite alcanzada; no se puede afirmar auditoria completa.")

    def review_threads(self, owner: str, name: str, number: int):
        query = """
        query($owner:String!, $name:String!, $number:Int!, $cursor:String) {
          repository(owner:$owner,name:$name) {
            pullRequest(number:$number) {
              reviewThreads(first:100,after:$cursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id isResolved isOutdated
                  comments(first:100) {
                    pageInfo { hasNextPage }
                    nodes { author { login } url body }
                  }
                }
              }
            }
          }
        }
        """
        all_nodes = []
        cursor = None
        for _ in range(MAX_PAGES):
            out = self.request("/graphql", {
                "query": query, "variables": {
                    "owner": owner, "name": name, "number": number, "cursor": cursor
                }
            })
            pr = ((out["data"].get("repository") or {}).get("pullRequest") or {})
            conn = pr.get("reviewThreads")
            if conn is None:
                raise RuntimeError(f"No se pudo leer reviewThreads de PR #{number}.")
            for node in conn["nodes"]:
                if node["comments"]["pageInfo"]["hasNextPage"]:
                    raise RuntimeError("Hilo de Codex con mas de 100 comentarios: revisar manualmente.")
            all_nodes.extend(conn["nodes"])
            if not conn["pageInfo"]["hasNextPage"]:
                return all_nodes
            cursor = conn["pageInfo"]["endCursor"]
        raise RuntimeError("Revisiones paginadas incompletas; auditoria bloqueada.")


def audit(client: GitHubClient, repo: str, resolutions: dict) -> dict:
    owner, name = repo.split("/", 1)
    findings = []
    prs = client.paged(f"/repos/{repo}/pulls?state=all")
    for pr in prs:
        number = pr["number"]
        pending = thread_findings(client.review_threads(owner, name, number))
        # Reviews con texto tecnico sin hilos o REQUEST_CHANGES tambien se atienden.
        reviews = client.paged(f"/repos/{repo}/pulls/{number}/reviews")
        for review in reviews:
            if not is_codex((review.get("user") or {}).get("login")):
                continue
            body = review.get("body") or ""
            if (review.get("state") == "CHANGES_REQUESTED"
                    or (body.strip() and not is_review_receipt(body))):
                if not valid_ack(resolutions.get("review_comments", {}).get(str(review["id"]))):
                    pending.append({
                        "id": str(review["id"]), "kind": "general-review",
                        "url": review.get("html_url"), "body": body,
                    })
        comments = client.paged(f"/repos/{repo}/issues/{number}/comments")
        for comment in comments:
            body = comment.get("body") or ""
            if (is_codex((comment.get("user") or {}).get("login"))
                    and body.strip() and not is_review_receipt(body)
                    and not valid_ack(resolutions.get("issue_comments", {}).get(str(comment["id"])))):
                pending.append({
                    "id": str(comment["id"]), "kind": "pr-conversation-comment",
                    "url": comment.get("html_url"), "body": body,
                })
        if pending:
            findings.append({
                "key": f"pr-{number}", "title": f"PR #{number}",
                "url": pr.get("html_url"), "items": pending,
            })
    commit_comments = client.paged(f"/repos/{repo}/comments")
    for comment in commit_comment_findings(commit_comments, resolutions):
        findings.append({
            "key": "commit-" + comment["id"],
            "title": "Comentario Codex en commit " + str(comment.get("commit_id", ""))[:12],
            "url": comment.get("url"), "items": [comment],
        })
    return {
        "repo": repo,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "prs_scanned": len(prs),
        "commit_comments_scanned": len(commit_comments),
        "findings": findings,
    }


def main() -> int:
    try:
        repo = os.environ.get("GITHUB_REPOSITORY", "skyirim/prueba-cuda")
        outpath = Path(os.environ.get("CODEX_AUDIT_OUTPUT", "codex-review-audit.json"))
        resolutions = json.loads(Path("docs/codex-review-resolutions.json").read_text(encoding="utf-8"))
        data = audit(GitHubClient(os.environ.get("GITHUB_TOKEN", "")), repo, resolutions)
        outpath.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"GitHub auditado: {data['prs_scanned']} PR; {data['commit_comments_scanned']} comentarios de commit.")
        for group in data["findings"]:
            print(f"PENDIENTE: {group['title']} ({group['url']})")
            for item in group["items"]:
                print(f"  - {item['kind']}: {item['url']}")
        print(f"Hallazgos sin resolver: {len(data['findings'])} grupos.")
        return 0  # El paso de check fallara DESPUES de sincronizar incidencias.
    except (OSError, KeyError, ValueError, RuntimeError, HTTPError, URLError) as exc:
        print(f"ERROR DE AUDITORIA CODEX: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
