#!/usr/bin/env python3
"""
ec2_inventory.py — list EC2 instances across regions and output CSV or JSON.

Works against real AWS or against LocalStack (set AWS_ENDPOINT_URL).

Usage:
    python3 ec2_inventory.py                           # text output, default region
    python3 ec2_inventory.py --regions us-east-1 eu-west-1
    python3 ec2_inventory.py --format json --output instances.json

LocalStack:
    AWS_ENDPOINT_URL=http://localhost:4566 \\
        AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \\
        python3 ec2_inventory.py --regions us-east-1
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    print("error: boto3 not installed. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger("ec2_inventory")


@dataclass
class Instance:
    instance_id: str
    region: str
    state: str
    instance_type: str
    public_ip: str
    private_ip: str
    name: str
    launch_time: str


def get_ec2_client(region: str):
    """Build an EC2 client, honoring AWS_ENDPOINT_URL for LocalStack."""
    endpoint_url = os.environ.get("AWS_ENDPOINT_URL")
    kwargs = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
        logger.debug("using endpoint override: %s", endpoint_url)
    return boto3.client("ec2", **kwargs)


def list_instances_in_region(region: str) -> list[Instance]:
    client = get_ec2_client(region)
    instances: list[Instance] = []

    try:
        paginator = client.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    name = ""
                    for tag in inst.get("Tags", []):
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                            break
                    instances.append(Instance(
                        instance_id=inst["InstanceId"],
                        region=region,
                        state=inst["State"]["Name"],
                        instance_type=inst["InstanceType"],
                        public_ip=inst.get("PublicIpAddress", ""),
                        private_ip=inst.get("PrivateIpAddress", ""),
                        name=name,
                        launch_time=inst["LaunchTime"].isoformat() if "LaunchTime" in inst else "",
                    ))
    except (BotoCoreError, ClientError) as e:
        logger.error("failed to query region %s: %s", region, e)
        return []

    return instances


def write_csv(instances: list[Instance], output: Path | None) -> None:
    fieldnames = list(asdict(instances[0]).keys()) if instances else [
        "instance_id", "region", "state", "instance_type",
        "public_ip", "private_ip", "name", "launch_time",
    ]
    stream = output.open("w", newline="") if output else sys.stdout
    try:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for inst in instances:
            writer.writerow(asdict(inst))
    finally:
        if output:
            stream.close()


def write_json(instances: list[Instance], output: Path | None) -> None:
    data = [asdict(i) for i in instances]
    text = json.dumps(data, indent=2)
    if output:
        output.write_text(text)
    else:
        print(text)


def write_text(instances: list[Instance]) -> None:
    if not instances:
        print("no instances found")
        return
    print(f"{'INSTANCE ID':<22} {'REGION':<14} {'STATE':<10} {'TYPE':<14} {'NAME':<24} {'PUBLIC IP':<16} {'PRIVATE IP'}")
    for i in instances:
        print(f"{i.instance_id:<22} {i.region:<14} {i.state:<10} {i.instance_type:<14} {i.name:<24} {i.public_ip:<16} {i.private_ip}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List EC2 instances across regions (works with LocalStack or real AWS).",
    )
    parser.add_argument(
        "--regions", nargs="+",
        default=[os.environ.get("AWS_DEFAULT_REGION", "us-east-1")],
        help="AWS regions to query (default: $AWS_DEFAULT_REGION or us-east-1)",
    )
    parser.add_argument(
        "--format", choices=("text", "csv", "json"), default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--output", type=Path,
        help="write output to file (default: stdout)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    all_instances: list[Instance] = []
    for region in args.regions:
        logger.info("querying region: %s", region)
        all_instances.extend(list_instances_in_region(region))

    logger.info("found %d instance(s) across %d region(s)", len(all_instances), len(args.regions))

    if args.format == "csv":
        write_csv(all_instances, args.output)
    elif args.format == "json":
        write_json(all_instances, args.output)
    else:
        write_text(all_instances)

    return 0


if __name__ == "__main__":
    sys.exit(main())
