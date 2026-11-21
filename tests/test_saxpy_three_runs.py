"""Pruebas offline: 3 ciclos GPU reales deben ser independientes y verificables."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.ci.verify_three_runs import verify

ROOT = Path(__file__).resolve().parents[1]
STEPS = ("prepare", "inventory", "compile", "execute")


def make_fake_run(root: Path, n: int, *, iid: str | None = None,
                  terminated: bool = True, cuda_pass: bool = True):
    p = root / f"run-{n}"
    (p / "ssm" / "execute").mkdir(parents=True, exist_ok=True)
    (p / "ssm" / "execute" / "00-stdout").write_text(
        "GPU=NVIDIA L4\nSAXPY_NVIDIA_PASS\n" if cuda_pass else "CUDA_ERROR\n",
        encoding="utf-8",
    )
    (p / "results.tar.gz").write_bytes(b"archive-demo")
    state = {
        "instance_id": iid or f"i-{n:016d}",
        "terminated": terminated,
        "offer": {"type": "gr6.8xlarge", "zone": "us-west-2c",
                  "price_usd_h": 0.4929},
        "duration_seconds": 180,
        "steps": [{"name": name, "status": "Success", "response_code": 0}
                  for name in STEPS],
    }
    (p / "state.json").write_text(json.dumps(state), encoding="utf-8")


class SaxpyThreeRunsTests(unittest.TestCase):
    def test_validates_three_distinct_finished_ec2_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for n in range(1, 4):
                make_fake_run(root, n)
            output = verify(root, 3)
            self.assertEqual(len(output), 3)
            self.assertEqual(len({x["instance_id"] for x in output}), 3)
            self.assertTrue(all(x["terminated"] and x["saxpy"] == "PASS"
                                for x in output))

    def test_detects_reused_instance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for n in range(1, 4):
                make_fake_run(root, n, iid="i-reused")
            with self.assertRaisesRegex(RuntimeError, "reutilizada"):
                verify(root, 3)

    def test_missing_cuda_output_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for n in range(1, 4):
                make_fake_run(root, n, cuda_pass=n != 2)
            with self.assertRaisesRegex(RuntimeError, "SAXPY_NVIDIA_PASS"):
                verify(root, 3)

    def test_instance_not_deleted_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for n in range(1, 4):
                make_fake_run(root, n, terminated=n != 3)
            with self.assertRaisesRegex(RuntimeError, "terminación"):
                verify(root, 3)

    def test_missing_cycle_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for n in (1, 2):
                make_fake_run(root, n)
            with self.assertRaisesRegex(RuntimeError, "state.json"):
                verify(root, 3)

    def test_sample_matches_nvidia_saxpy_logic(self):
        src = (ROOT / "programs/cuda/saxpy_nvidia.cu").read_text(encoding="utf-8")
        self.assertIn("saxpy_kernel<<<", src)
        self.assertIn("1 << 20", src)
        self.assertIn("cudaDeviceSynchronize", src)
        self.assertIn("SAXPY_NVIDIA_PASS", src)
        self.assertIn("cudaGetLastError", src)
        self.assertIn("cudaMemcpyDeviceToHost", src)

    def test_workflow_checks_three_real_runs_with_single_cost_guard(self):
        wf = (ROOT / ".github/workflows/aws-saxpy-three-runs.yml").read_text()
        self.assertIn("workflow_dispatch:", wf)
        self.assertIn("vars.AWS_CUDA_PROBE_ENABLED == 'true'", wf)
        self.assertIn("for n in 1 2 3", wf)
        self.assertIn("--spot-ceiling 0.60", wf)
        self.assertIn("--ttl-minutes 30", wf)
        self.assertIn("verify_three_runs.py", wf)
        self.assertIn("if: always()", wf)
        self.assertIn("retention-days: 90", wf)
        self.assertNotIn("continue-on-error: true", wf)


if __name__ == "__main__":
    unittest.main()
