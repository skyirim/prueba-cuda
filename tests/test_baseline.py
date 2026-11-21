"""Pruebas del validador; los valores simulados NO describen el equipo base real."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_baseline import validate

class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "status": "VERIFIED",
            "source_document": {"name": "FICTICIO", "sha256": "a" * 64},
            "cpu": {"architecture": "x86_64", "physical_cores_min": 4,
                    "logical_processors_min": 4, "ram_gib_min": 8},
            "gpu": {"devices_min": 1, "cuda_cores_fp32_min": 1000,
                    "sm_min": 10, "vram_mib_min": 2048,
                    "compute_capability_min": "7.5", "full_gpu_required": True},
            "portability": {"same_cpu_binary_required": True, "reference_tests": ["vector-add"]},
        }
        self.inv = {
            "cpu": {"architecture": "x86_64", "physical_cores_visible": 4,
                    "physical_cores_verified": True, "logical_processors": 4, "ram_gib": 16},
            "gpu": {"devices": 1, "cuda_cores_fp32_verified": 2000, "gpu_cores_verified": True,
                    "sm_visible": 20, "vram_mib": 4096,
                    "compute_capability": "8.9", "is_fractional": False},
            "tests": {"c_smoke_pass": True, "cuda_smoke_pass": True,
                      "reference_comparison_pass": True},
            "evidence": {"cpu_physical_cores": "evidence/cpu.txt",
                         "gpu_cuda_cores": "evidence/gpu.txt",
                         "reference_results": "evidence/tests.txt",
                         "timestamp_utc": "2026-11-21T14:00:00Z"},
        }
    def test_accepts_only_complete_mock(self):
        self.assertEqual(validate(self.base, self.inv), [])
    def test_rejects_unknown_source(self):
        x = copy.deepcopy(self.base)
        x["status"] = "PENDING_SOURCE"
        self.assertTrue(validate(x, self.inv))
    def test_rejects_less_cpu(self):
        x = copy.deepcopy(self.inv)
        x["cpu"]["physical_cores_visible"] = 2
        self.assertTrue(any("physical_cores_visible" in e for e in validate(self.base, x)))
    def test_rejects_fractional_gpu(self):
        x = copy.deepcopy(self.inv)
        x["gpu"]["is_fractional"] = True
        self.assertTrue(any("fraccionado" in e for e in validate(self.base, x)))
    def test_rejects_missing_evidence(self):
        x = copy.deepcopy(self.inv)
        x["evidence"]["gpu_cuda_cores"] = None
        self.assertTrue(any("evidencia" in e for e in validate(self.base, x)))
    def test_rejects_missing_runtime_test(self):
        x = copy.deepcopy(self.inv)
        x["tests"]["cuda_smoke_pass"] = False
        self.assertTrue(any("cuda_smoke_pass" in e for e in validate(self.base, x)))

if __name__ == "__main__":
    unittest.main()
