"""Pruebas de deteccion y de compatibilidad CUDA sin necesidad de GPU ni red."""
import unittest
from pathlib import Path

from scripts.audit_codex_reviews import (
    is_codex, is_review_receipt, thread_findings,
    valid_ack, commit_comment_findings,
)

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


if __name__ == "__main__":
    unittest.main()
