"""Pruebas de deteccion y de compatibilidad CUDA sin necesidad de GPU ni red."""
import unittest
from pathlib import Path

from scripts.audit_codex_reviews import (
    is_codex, is_review_receipt, thread_findings,
    valid_ack, commit_comment_findings,
)

from scripts.sync_codex_review_issues import synchronize, marker
from scripts.check_codex_review_result import check as check_codex_result

ROOT = Path(__file__).resolve().parents[1]


class CodexReviewPolicyTests(unittest.TestCase):
    def test_recognizes_bot_alias(self):
        self.assertTrue(is_codex("chatgpt-codex-connector"))
        self.assertTrue(is_codex("chatgpt-codex-connector[bot]"))
        self.assertFalse(is_codex("other-bot"))

    def test_does_not_confuse_receipts_with_actionable_review(self):
        self.assertTrue(is_review_receipt(
            "<!-- codex-review-receipt:v1 -->\nCodex Review"))
        self.assertTrue(is_review_receipt(
            "<!-- codex-pull-request-review-summary -->\nReview completed"))
        self.assertFalse(is_review_receipt("Preserve executable GPU code"))

    def test_finds_p1_in_commented_review_even_when_pr_merged(self):
        threads = [{
            "id": "PRRT_old",
            "isResolved": False,
            "isOutdated": True,
            "comments": {"nodes": [{
                "author": {"login": "chatgpt-codex-connector"},
                "url": "https://github.com/skyirim/prueba-cuda/pull/3",
                "body": "P1: falta PTX para A10G",
            }]},
        }]
        self.assertEqual(len(thread_findings(threads)), 1)
        threads[0]["isResolved"] = True
        self.assertEqual(thread_findings(threads), [])

    def test_non_codex_thread_does_not_block(self):
        threads = [{"id": "other", "isResolved": False,
                    "comments": {"nodes": [
                        {"author": {"login": "human"}, "body": "review"}]}}]
        self.assertEqual(thread_findings(threads), [])

    def test_commit_comment_is_pending_until_evidenced(self):
        comment = {"id": 123, "user": {"login": "chatgpt-codex-connector[bot]"},
                   "body": "Arreglar el error", "html_url": "https://github.com/x"}
        self.assertEqual(len(commit_comment_findings([comment], {})), 1)
        resolutions = {"commit_comments": {
            "123": {"fix_commit_sha": "a" * 40,
                    "evidence_url": "https://github.com/skyirim/prueba-cuda/commit/a"}}}
        self.assertEqual(commit_comment_findings([comment], resolutions), [])
        self.assertFalse(valid_ack({"fix_commit_sha": "foo", "evidence_url": "https://github.com/"}))

    def test_makefile_preserves_native_ucam_and_forward_ptx(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        line = next(line for line in makefile.splitlines()
                    if line.startswith("CUDA_GENCODE ?="))
        self.assertIn("arch=compute_75,code=sm_75", line)
        self.assertIn("arch=compute_75,code=compute_75", line)
        self.assertNotIn("code=sm_89", line)
        self.assertIn("$(CUDA_GENCODE)", makefile)

    def test_sync_same_finding_twice_does_not_duplicate_or_close(self):
        class FakeClient:
            def __init__(self):
                self.issues = []
                self.calls = []
            def list_issues(self, repo):
                return self.issues
            def request(self, method, path, payload):
                self.calls.append((method, path, payload))
                if method == 'POST':
                    issue = {'number': len(self.issues) + 1,
                             'html_url': 'https://github.com/skyirim/prueba-cuda/issues/100',
                             'title': payload['title'], 'body': payload['body'], 'state': 'open'}
                    self.issues.append(issue)
                    return issue
                if method == 'PATCH':
                    self.issues[0].update(payload)
                    return self.issues[0]
                raise AssertionError('Unexpected request')
        client = FakeClient()
        finding = {'key': 'pr-3', 'title': 'PR #3',
                   'url': 'https://github.com/skyirim/prueba-cuda/pull/3',
                   'items': [{'kind': 'pr-thread', 'id': 'thread3',
                              'url': 'https://github.com/skyirim/prueba-cuda/pull/3',
                              'body': 'P1: falta PTX'}]}
        payload = {'repo': 'skyirim/prueba-cuda', 'findings': [finding]}
        first = synchronize(client, payload)
        second = synchronize(client, payload)
        self.assertEqual(len(first['created']), 1)
        self.assertEqual(second['created'], [])
        self.assertEqual(second['closed'], [])
        self.assertEqual(len(client.issues), 1)
        self.assertEqual(client.issues[0]['state'], 'open')
        self.assertTrue(client.issues[0]['body'].startswith(marker('pr-3')))
        self.assertEqual([call[0] for call in client.calls], ['POST'])

    def test_code_review_gate_reports_pending_findings(self):
        self.assertEqual(check_codex_result({'findings': []}), [])
        pending = check_codex_result({'findings': [
            {'title': 'PR #4', 'items': [{'url': 'https://github.com/pull/4'}]}]})
        self.assertEqual(len(pending), 1)
        self.assertIn('PR #4', pending[0])

    def test_review_events_are_read_only_and_issue_sync_is_privileged(self):
        readonly = (ROOT / '.github/workflows/codex-review-sentinel.yml').read_text(encoding='utf-8')
        privileged = (ROOT / '.github/workflows/codex-review-issue-sync.yml').read_text(encoding='utf-8')
        self.assertIn('issues: read', readonly)
        self.assertNotIn('issues: write', readonly)
        self.assertNotIn('sync_codex_review_issues.py', readonly)
        self.assertIn('check_codex_review_result.py', readonly)
        self.assertIn('workflow_run:', privileged)
        self.assertIn('issues: write', privileged)
        self.assertIn('sync_codex_review_issues.py', privileged)
        self.assertIn('ref: ${{ github.event.repository.default_branch }}', privileged)


if __name__ == "__main__":
    unittest.main()
