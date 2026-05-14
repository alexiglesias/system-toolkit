#!/usr/bin/env python3
"""
log_parser.py — parse Nginx/Apache combined-format access logs and report key stats.

Outputs the top IPs, the top URLs, and the count of each HTTP status code.
Designed for sysadmin / DevOps use: troubleshooting traffic spikes, finding
bad clients, spotting error patterns.

Usage:
    python3 log_parser.py --log /var/log/nginx/access.log
    python3 log_parser.py --log access.log --top 20 --format json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("log_parser")

# Combined log format:
# 1.2.3.4 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1234 "-" "Mozilla/..."
LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ '
    r'\[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<url>\S+) (?P<proto>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
)


@dataclass
class LogStats:
    total_lines: int = 0
    parsed_lines: int = 0
    top_ips: list[tuple[str, int]] = None
    top_urls: list[tuple[str, int]] = None
    status_counts: dict[str, int] = None


def parse_log(path: Path, top_n: int = 10) -> LogStats:
    ip_counter: Counter[str] = Counter()
    url_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    total = 0
    parsed = 0

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            total += 1
            match = LOG_PATTERN.match(line)
            if not match:
                continue
            parsed += 1
            ip_counter[match.group("ip")] += 1
            url_counter[match.group("url")] += 1
            status_counter[match.group("status")] += 1

    return LogStats(
        total_lines=total,
        parsed_lines=parsed,
        top_ips=ip_counter.most_common(top_n),
        top_urls=url_counter.most_common(top_n),
        status_counts=dict(sorted(status_counter.items())),
    )


def format_text(stats: LogStats) -> str:
    lines = []
    lines.append(f"Lines processed: {stats.parsed_lines}/{stats.total_lines}")
    lines.append("")
    lines.append("Top IPs:")
    for ip, count in stats.top_ips:
        lines.append(f"  {count:>8}  {ip}")
    lines.append("")
    lines.append("Top URLs:")
    for url, count in stats.top_urls:
        lines.append(f"  {count:>8}  {url}")
    lines.append("")
    lines.append("Status codes:")
    for code, count in stats.status_counts.items():
        lines.append(f"  {code}: {count}")
    return "\n".join(lines)


def format_json(stats: LogStats) -> str:
    return json.dumps({
        "total_lines": stats.total_lines,
        "parsed_lines": stats.parsed_lines,
        "top_ips": [{"ip": ip, "count": c} for ip, c in stats.top_ips],
        "top_urls": [{"url": u, "count": c} for u, c in stats.top_urls],
        "status_counts": stats.status_counts,
    }, indent=2)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Nginx/Apache access logs and report key statistics."
    )
    parser.add_argument("--log", type=Path, required=True, help="log file path")
    parser.add_argument("--top", type=int, default=10, help="top N entries (default: 10)")
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="output format (default: text)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    args = parse_args(argv)

    if not args.log.is_file():
        logger.error("log file not found: %s", args.log)
        return 1

    stats = parse_log(args.log, top_n=args.top)
    output = format_json(stats) if args.format == "json" else format_text(stats)
    print(output)

    if stats.parsed_lines == 0:
        logger.warning("no lines matched the combined log format")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
