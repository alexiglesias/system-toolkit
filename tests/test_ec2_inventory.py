"""Tests for ec2_inventory.py using moto to mock AWS."""

from __future__ import annotations

import json
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from ec2_inventory import list_instances_in_region, main


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mock AWS credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    # Make sure no real endpoint override leaks in
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


@mock_aws
def test_list_instances_returns_empty_when_no_instances(aws_credentials) -> None:
    result = list_instances_in_region("us-east-1")
    assert result == []


@mock_aws
def test_list_instances_returns_running_instance(aws_credentials) -> None:
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ec2.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "test-server"}],
        }],
    )

    result = list_instances_in_region("us-east-1")
    assert len(result) == 1
    assert result[0].instance_type == "t2.micro"
    assert result[0].name == "test-server"
    assert result[0].state == "running"
    assert result[0].region == "us-east-1"


@mock_aws
def test_list_instances_handles_instances_without_name_tag(aws_credentials) -> None:
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ec2.run_instances(ImageId="ami-12345678", InstanceType="t2.micro", MinCount=1, MaxCount=1)

    result = list_instances_in_region("us-east-1")
    assert len(result) == 1
    assert result[0].name == ""


@mock_aws
def test_list_instances_handles_multiple_instances(aws_credentials) -> None:
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ec2.run_instances(ImageId="ami-12345678", InstanceType="t2.micro", MinCount=3, MaxCount=3)

    result = list_instances_in_region("us-east-1")
    assert len(result) == 3


@mock_aws
def test_main_outputs_json_to_file(aws_credentials, tmp_path: Path, capsys) -> None:
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ec2.run_instances(ImageId="ami-12345678", InstanceType="t2.micro", MinCount=1, MaxCount=1)

    output = tmp_path / "instances.json"
    rc = main([
        "--regions", "us-east-1",
        "--format", "json",
        "--output", str(output),
    ])
    assert rc == 0
    assert output.exists()
    data = json.loads(output.read_text())
    assert len(data) == 1
    assert data[0]["instance_type"] == "t2.micro"


@mock_aws
def test_main_outputs_csv_with_header(aws_credentials, tmp_path: Path) -> None:
    output = tmp_path / "instances.csv"
    rc = main([
        "--regions", "us-east-1",
        "--format", "csv",
        "--output", str(output),
    ])
    assert rc == 0
    content = output.read_text()
    assert "instance_id" in content
    assert "region" in content
