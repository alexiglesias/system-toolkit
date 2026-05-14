"""Tests for log_parser.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from log_parser import parse_log, format_text, format_json, main


SAMPLE_LOG = '''\
1.2.3.4 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
1.2.3.4 - - [10/Oct/2025:13:55:37 +0000] "GET /style.css HTTP/1.1" 200 567 "-" "Mozilla/5.0"
5.6.7.8 - - [10/Oct/2025:13:55:38 +0000] "GET /index.html HTTP/1.1" 200 1234 "-" "curl/7.0"
5.6.7.8 - - [10/Oct/2025:13:55:39 +0000] "GET /missing HTTP/1.1" 404 0 "-" "curl/7.0"
9.9.9.9 - - [10/Oct/2025:13:55:40 +0000] "POST /api/data HTTP/1.1" 500 100 "-" "Python"
this line is malformed and should be skipped
'''


@pytest.fixture
def sample_log(tmp_path: Path) -> Path:
    p = tmp_path / "access.log"
    p.write_text(SAMPLE_LOG)
    return p


def test_parse_log_counts_total_and_parsed(sample_log: Path) -> None:
    stats = parse_log(sample_log)
    assert stats.total_lines == 6
    assert stats.parsed_lines == 5


def test_parse_log_top_ips(sample_log: Path) -> None:
    stats = parse_log(sample_log)
    ips = dict(stats.top_ips)
    assert ips["1.2.3.4"] == 2
    assert ips["5.6.7.8"] == 2
    assert ips["9.9.9.9"] == 1


def test_parse_log_top_urls(sample_log: Path) -> None:
    stats = parse_log(sample_log)
    urls = dict(stats.top_urls)
    assert urls["/index.html"] == 2
    assert urls["/style.css"] == 1


def test_parse_log_status_counts(sample_log: Path) -> None:
    stats = parse_log(sample_log)
    assert stats.status_counts == {"200": 3, "404": 1, "500": 1}


def test_parse_log_top_n_limits_results(sample_log: Path) -> None:
    stats = parse_log(sample_log, top_n=1)
    assert len(stats.top_ips) == 1
    assert len(stats.top_urls) == 1


def test_format_json_is_valid_json(sample_log: Path) -> None:
    stats = parse_log(sample_log)
    text = format_json(stats)
    data = json.loads(text)
    assert "top_ips" in data
    assert "top_urls" in data
    assert "status_counts" in data


def test_format_text_contains_section_headers(sample_log: Path) -> None:
    stats = parse_log(sample_log)
    text = format_text(stats)
    assert "Top IPs:" in text
    assert "Top URLs:" in text
    assert "Status codes:" in text


def test_main_returns_one_for_missing_file(tmp_path: Path, capsys) -> None:
    rc = main(["--log", str(tmp_path / "missing.log")])
    assert rc == 1


def test_main_returns_two_for_no_matching_lines(tmp_path: Path, capsys) -> None:
    p = tmp_path / "junk.log"
    p.write_text("not a log file\njust garbage\n")
    rc = main(["--log", str(p)])
    assert rc == 2


def test_main_returns_zero_for_valid_log(sample_log: Path, capsys) -> None:
    rc = main(["--log", str(sample_log)])
    assert rc == 0
