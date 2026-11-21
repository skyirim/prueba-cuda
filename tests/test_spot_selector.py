"""Pruebas aisladas de selección live Spot: nunca realizan llamadas AWS reales."""
import copy
from datetime import datetime, timedelta, timezone
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.select_gpu_spot import (
    SelectionError, assert_fresh, gpu_qualified,
    hardware_qualified, select, latest_quotes,
)

NOW = datetime(2026, 11, 21, 15, 0, tzinfo=timezone.utc)


class FakePaginator:
    def __init__(self, quotes):
        self.quotes = quotes
        self.calls = 0

    def paginate(self, **kwargs):
        self.calls += 1
        yield {"SpotPriceHistory": self.quotes}


class FakeEC2:
    def __init__(self, specs, quotes):
        self.specs = specs
        self.pager = FakePaginator(quotes)
        self.described = 0

    def describe_instance_types(self, InstanceTypes):
        self.described += 1
        return {"InstanceTypes": [self.specs[t] for t in InstanceTypes if t in self.specs]}

    def get_paginator(self, operation):
        assert operation == "describe_spot_price_history"
        return self.pager


class FakeQuotas:
    def __init__(self, value=126):
        self.value = value
        self.calls = 0

    def get_service_quota(self, **kwargs):
        self.calls += 1
        return {"Quota": {"Value": self.value}}


class FakeSession:
    def __init__(self, ec2, quotas):
        self.ec2 = ec2
        self.quotas = quotas

    def client(self, name, region_name):
        assert region_name == "us-west-2"
        return self.ec2 if name == "ec2" else self.quotas


def instance(name, *, cpu=16, vcpu=32, ram_mib=131072, gpu="L4", count=1,
             fraction=1, vram=22888):
    return {"InstanceType": name,
            "VCpuInfo": {"DefaultCores": cpu, "DefaultVCpus": vcpu},
            "MemoryInfo": {"SizeInMiB": ram_mib},
            "ProcessorInfo": {"SupportedArchitectures": ["x86_64"]},
            "GpuInfo": {"Gpus": [{
                "Manufacturer": "NVIDIA", "Name": gpu, "Count": count,
                "GpuPartitionSize": fraction, "MemoryInfo": {"SizeInMiB": vram}
            }]}}


def baseline():
    return {"status": "VERIFIED",
            "cpu": {"physical_cores_min": 12, "logical_processors_min": 12,
                    "ram_gib_min": 31},
            "gpu": {"devices_min": 1, "cuda_cores_fp32_min": 4352,
                    "vram_mib_min": 11264}}


def pool(name, zone="us-west-2c", overhead=0.02):
    return {"region": "us-west-2", "zone": zone,
            "instance_type": name, "ami_id": "ami-test", "subnet_id": "subnet-test",
            "approved": True, "linux_cuda_runtime_passed": True,
            "cuda_sm75_build_passed": True, "reference_execution_passed": True,
            "estimated_additional_usd_h": overhead}


def quote(name, zone, price, when=NOW):
    return {"InstanceType": name, "AvailabilityZone": zone,
            "SpotPrice": str(price), "Timestamp": when}


class PricingTests(unittest.TestCase):
    def test_2080ti_minimums_exclude_small_cpu(self):
        self.assertFalse(hardware_qualified(instance("g6.4xlarge", cpu=8), baseline()))
        self.assertTrue(hardware_qualified(instance("gr6.8xlarge", cpu=16), baseline()))

    def test_reject_fractional_gpu(self):
        self.assertFalse(gpu_qualified(instance("g6f.large", count=0, fraction=.125),
                                       baseline()))
        self.assertFalse(hardware_qualified(instance("g5g.8xlarge", gpu="T4g"),
                                            baseline()))

    def test_58_sm_is_not_a_requirement(self):
        self.assertTrue(hardware_qualified(instance("gr6.8xlarge"), baseline()))

    def test_latest_price_not_historical_minimum(self):
        ec2 = FakeEC2({}, [
            quote("gr6.8xlarge", "us-west-2c", .10, NOW - timedelta(hours=2)),
            quote("gr6.8xlarge", "us-west-2c", .49, NOW - timedelta(minutes=1)),
        ])
        value = latest_quotes(ec2, ["gr6.8xlarge"], NOW)
        self.assertEqual(value[("gr6.8xlarge", "us-west-2c")]["price"], .49)

    def test_chooses_current_cheapest_eligible(self):
        ec2 = FakeEC2(
            {"gr6.8xlarge": instance("gr6.8xlarge"),
             "g7.4xlarge": instance("g7.4xlarge", cpu=16, vcpu=16, ram_mib=65536,
                                   gpu="RTX PRO 4500", vram=32768)},
            [quote("gr6.8xlarge", "us-west-2c", .4929),
             quote("g7.4xlarge", "us-west-2a", .7658)])
        session = FakeSession(ec2, FakeQuotas())
        plan = select(baseline(), [pool("gr6.8xlarge"), pool("g7.4xlarge", "us-west-2a")],
                      session=session, now=NOW)
        self.assertEqual(plan["best"]["type"], "gr6.8xlarge")
        self.assertEqual(session.ec2.pager.calls, 1)
        self.assertEqual(session.quotas.calls, 1)
        assert_fresh(plan, NOW + timedelta(seconds=59))
        with self.assertRaises(SelectionError):
            assert_fresh(plan, NOW + timedelta(seconds=60))

    def test_detects_cpu_and_vram_constraints(self):
        x = instance("wrong", cpu=6)
        self.assertFalse(hardware_qualified(x, baseline()))
        x = instance("wrong", vram=4000)
        self.assertFalse(hardware_qualified(x, baseline()))

    def test_quota_zero_fails_closed(self):
        ec2 = FakeEC2({"gr6.8xlarge": instance("gr6.8xlarge")},
                      [quote("gr6.8xlarge", "us-west-2c", .49)])
        with self.assertRaises(SelectionError):
            select(baseline(), [pool("gr6.8xlarge")],
                   session=FakeSession(ec2, FakeQuotas(0)), now=NOW)

    def test_uncertified_images_fail_closed(self):
        x = pool("gr6.8xlarge")
        x["cuda_sm75_build_passed"] = False
        with self.assertRaises(SelectionError):
            select(baseline(), [x], session=None, now=NOW)

    def test_draft_baseline_fails_closed(self):
        b = baseline()
        b["status"] = "DRAFT"
        with self.assertRaises(SelectionError):
            select(b, [pool("gr6.8xlarge")], session=None, now=NOW)

    def test_fresh_query_per_call(self):
        ec2 = FakeEC2({"gr6.8xlarge": instance("gr6.8xlarge")},
                      [quote("gr6.8xlarge", "us-west-2c", .49)])
        session = FakeSession(ec2, FakeQuotas())
        select(baseline(), [pool("gr6.8xlarge")], session=session, now=NOW)
        select(baseline(), [pool("gr6.8xlarge")], session=session, now=NOW)
        self.assertEqual(ec2.pager.calls, 2)
        self.assertEqual(session.quotas.calls, 2)


if __name__ == "__main__":
    unittest.main()
