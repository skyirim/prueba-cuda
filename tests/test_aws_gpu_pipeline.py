"""Offline regression tests for AWS GPU CI (no EC2, S3 or SSM calls)."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.aws_gpu_job import (
    ALLOWED_REGION, JOB_STEPS, candidate_pools, collect_ssm_output,
    env_required, script_for_step, volume_size,
)
from infrastructure.select_gpu_spot import select, SelectionError


ROOT = Path(__file__).resolve().parents[1]


class FakeEC2:
    def describe_security_groups(self, GroupIds):
        return {"SecurityGroups": [{"GroupId": GroupIds[0], "VpcId": "vpc-example"}]}

    def describe_images(self, Owners=None, Filters=None, ImageIds=None):
        if ImageIds:
            return {"Images": [{
                "Architecture": "x86_64", "RootDeviceName": "/dev/sda1",
                "BlockDeviceMappings": [{
                    "DeviceName": "/dev/sda1", "Ebs": {"VolumeSize": 120}}]}]}
        return {"Images": [{
            "ImageId": "ami-official", "CreationDate": "2026-11-13",
            "Architecture": "x86_64", "Name": "Official NVIDIA AMI"}]}

    def describe_subnets(self, Filters):
        return {"Subnets": [{
            "SubnetId": "subnet-example", "AvailabilityZone": "us-west-2c",
            "MapPublicIpOnLaunch": True, "VpcId": "vpc-example"}]}


class FakeSession:
    def client(self, service, region_name):
        assert service == "ec2"
        assert region_name == ALLOWED_REGION
        return FakeEC2()


class FakeS3:
    def get_paginator(self, operation):
        assert operation == "list_objects_v2"
        class Paginator:
            def paginate(self, **kwargs):
                yield {"Contents": [{"Key": kwargs["Prefix"] + "stdout"},
                                    {"Key": kwargs["Prefix"] + "stderr"}]}
        return Paginator()

    def get_object(self, Bucket, Key):
        from io import BytesIO
        return {"Body": BytesIO(b"stdout completo\n" if Key.endswith("stdout")
                                else b"stderr completo\n")}


class AwsJobTests(unittest.TestCase):
    def test_probe_discovers_official_ami_and_restrictions(self):
        p = {
            "region": "us-west-2",
            "official_ami_name": "Official NVIDIA AMI",
            "allowed_zones": ["us-west-2c"],
            "instance_types": ["gr6.8xlarge"],
        }
        pools = candidate_pools(FakeSession(), p, "sg-example", "vpc-example")
        self.assertEqual(len(pools), 1)
        self.assertEqual(pools[0]["ami_id"], "ami-official")
        self.assertEqual(pools[0]["subnet_id"], "subnet-example")
        self.assertTrue(pools[0]["probe_allowed"])
        self.assertFalse(pools[0]["approved"])

    def test_probe_disallows_other_regions(self):
        with self.assertRaises(SelectionError):
            candidate_pools(FakeSession(), {"region": "eu-west-1"}, "sg", "vpc")

    def test_gpu_ami_volume_never_shrinks_snapshot(self):
        root, size = volume_size(FakeEC2(), "ami-official")
        self.assertEqual(root, "/dev/sda1")
        self.assertEqual(size, 120)

    def test_stages_and_archive_restore_all_results(self):
        self.assertEqual(JOB_STEPS, ("prepare", "inventory", "compile", "execute"))
        for name in JOB_STEPS:
            text = script_for_step(name, "bucket-test", "runs/1/1", "us-west-2")
            self.assertIn("set -euo pipefail", text)
            self.assertIn("scripts/ci/", text)
        archive = script_for_step("archive", "bucket-test", "runs/1/1", "us-west-2")
        self.assertIn("results.tar.gz", archive)
        self.assertIn("aws s3 cp", archive)

    def test_complete_stdout_stderr_archived(self):
        with tempfile.TemporaryDirectory() as tmp:
            collect_ssm_output(FakeS3(), "bucket", "runs/id/ssm/compile/",
                               Path(tmp))
            files = [p for p in Path(tmp).iterdir() if p.is_file()]
            self.assertEqual(len(files), 2)
            texts = [p.read_text() for p in files]
            self.assertTrue(any("stdout completo" in v for v in texts))
            self.assertTrue(any("stderr completo" in v for v in texts))

    def test_missing_variables_fail_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                env_required("AWS_GPU_S3_BUCKET")

    def test_ci_is_disabled_without_certification(self):
        base = json.loads((ROOT / "config/hardware-base.json").read_text())
        with self.assertRaises(SelectionError):
            select(base, [], session=None)

    def test_cloudformation_has_controls(self):
        template = json.loads((ROOT / "infrastructure/cloudformation/gpu-ci-base.json").read_text())
        resources = template["Resources"]
        for name in ("GithubRole", "InstanceRole", "InstanceProfile",
                     "GithubOidc", "GpuSg", "Bucket", "SsmLogs",
                     "Watchdog", "WatchdogRule", "WatchdogRole"):
            self.assertIn(name, resources)
        sg = resources["GpuSg"]["Properties"]
        self.assertNotIn("SecurityGroupIngress", sg)
        bucket = resources["Bucket"]["Properties"]
        self.assertTrue(bucket["PublicAccessBlockConfiguration"]["BlockPublicPolicy"])
        self.assertEqual(bucket["BucketEncryption"]["ServerSideEncryptionConfiguration"][0]
                         ["ServerSideEncryptionByDefault"]["SSEAlgorithm"], "AES256")
        trust = resources["GithubRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]
        self.assertIn("token.actions.githubusercontent.com:sub", trust["Condition"]["StringEquals"])
        watcher = resources["WatchdogRule"]["Properties"]["ScheduleExpression"]
        self.assertEqual(watcher, "rate(5 minutes)")
        self.assertEqual(sg["SecurityGroupEgress"][0]["IpProtocol"], "tcp")
        self.assertEqual(sg["SecurityGroupEgress"][0]["FromPort"], 443)
        self.assertEqual(sg["SecurityGroupEgress"][0]["ToPort"], 443)
        instance_permissions = resources["InstanceRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
        names = {s.get("Sid") for s in instance_permissions}
        self.assertTrue({"CWDiscoverGroups", "CWDiscoverStreams", "CWWriteStreams"} <= names)
        controller = resources["GithubRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
        tagged = next(s for s in controller if s.get("Sid") == "SendSsmOnlyTaggedCIInstances")
        self.assertEqual(tagged["Condition"]["StringEquals"]["ssm:resourceTag/Project"], "prueba-cuda")
        self.assertEqual(tagged["Condition"]["StringEquals"]["ssm:resourceTag/Mode"], "ci")

    def test_action_push_gated_and_publishes_always(self):
        workflow = (ROOT / ".github/workflows/aws-gpu-ci.yml").read_text()
        self.assertIn("branches: [main]", workflow)
        self.assertIn("vars.AWS_CUDA_ENABLED == 'true'", workflow)
        self.assertIn("aws-actions/configure-aws-credentials@", workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("retention-days: 90", workflow)
        self.assertIn("--mode qualify", workflow)
        self.assertIn("--mode ci", workflow)

    def test_compilers_cover_standalone_sources(self):
        compile_src = (ROOT / "scripts/ci/compile.sh").read_text()
        run_src = (ROOT / "scripts/ci/execute.sh").read_text()
        self.assertIn("programs/cuda", compile_src)
        self.assertIn("programs/c", compile_src)
        self.assertIn("code=compute_75", compile_src)
        self.assertIn("timeout", run_src)
        self.assertIn("make --no-print-directory test", run_src)


if __name__ == "__main__":
    unittest.main()
