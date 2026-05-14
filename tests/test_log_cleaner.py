"""Tests for log_cleaner.py."""

from __future__ import annotations

import gzip
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from log_cleaner import find_old_files, archive_file, main


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    """Create a directory with three log files: one new, two old."""
    d = tmp_path / "logs"
    d.mkdir()

    new_log = d / "new.log"
    new_log.write_text("new content")

    old_log = d / "old.log"
    old_log.write_text("old content")
    old_time = time.time() - 60 * 60 * 24 * 60  # 60 days ago
    os.utime(old_log, (old_time, old_time))

    older_log = d / "older.log"
    older_log.write_text("older content")
    older_time = time.time() - 60 * 60 * 24 * 100  # 100 days ago
    os.utime(older_log, (older_time, older_time))

    return d


def test_find_old_files_returns_only_files_older_than_cutoff(log_dir: Path) -> None:
    cutoff = datetime.now() - timedelta(days=30)
    old = find_old_files(log_dir, cutoff)
    names = sorted(p.name for p in old)
    assert names == ["old.log", "older.log"]


def test_find_old_files_ignores_subdirectories(log_dir: Path, tmp_path: Path) -> None:
    sub = log_dir / "subdir"
    sub.mkdir()
    sub_time = time.time() - 60 * 60 * 24 * 100
    os.utime(sub, (sub_time, sub_time))

    cutoff = datetime.now() - timedelta(days=30)
    old = find_old_files(log_dir, cutoff)
    assert all(p.is_file() for p in old)
    assert "subdir" not in [p.name for p in old]


def test_archive_file_creates_gzip_and_removes_source(tmp_path: Path) -> None:
    source = tmp_path / "test.log"
    source.write_text("log content here")
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()

    result = archive_file(source, archive_dir)

    assert result == archive_dir / "test.log.gz"
    assert result.exists()
    assert not source.exists()
    with gzip.open(result, "rt") as f:
        assert f.read() == "log content here"


def test_archive_file_dry_run_does_not_move_anything(tmp_path: Path) -> None:
    source = tmp_path / "test.log"
    source.write_text("log content")
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()

    archive_file(source, archive_dir, dry_run=True)

    assert source.exists()
    assert not (archive_dir / "test.log.gz").exists()


def test_main_returns_zero_when_nothing_to_archive(tmp_path: Path) -> None:
    source = tmp_path / "logs"
    source.mkdir()
    (source / "new.log").write_text("fresh")
    archive = tmp_path / "archive"

    rc = main(["--source", str(source), "--archive", str(archive), "--days", "30"])
    assert rc == 0


def test_main_returns_one_for_missing_source(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    rc = main(["--source", "/does/not/exist", "--archive", str(archive)])
    assert rc == 1


def test_main_returns_one_for_invalid_days(tmp_path: Path) -> None:
    source = tmp_path / "logs"
    source.mkdir()
    archive = tmp_path / "archive"
    rc = main(["--source", str(source), "--archive", str(archive), "--days", "0"])
    assert rc == 1


def test_main_archives_old_files_end_to_end(log_dir: Path, tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    rc = main([
        "--source", str(log_dir),
        "--archive", str(archive),
        "--days", "30",
    ])
    assert rc == 0
    assert (archive / "old.log.gz").exists()
    assert (archive / "older.log.gz").exists()
    assert (log_dir / "new.log").exists()
    assert not (log_dir / "old.log").exists()
