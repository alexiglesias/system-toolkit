#!/usr/bin/env python3
"""
log_cleaner.py — archive log files older than N days.

Walks a directory, finds files older than the cutoff, moves them to an archive
directory and gzip-compresses them. Supports a dry-run mode for safe testing.

Usage:
    python3 log_cleaner.py --source /var/log/app --archive /var/log/app/archive
    python3 log_cleaner.py --source /var/log/app --archive /tmp/archive --days 7
    python3 log_cleaner.py --source /var/log/app --archive /tmp/archive --dry-run
"""

from __future__ import annotations

import argparse
import gzip
import logging
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("log_cleaner")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def find_old_files(source: Path, cutoff: datetime) -> list[Path]:
    """Return all regular files in source that were modified before cutoff."""
    old_files: list[Path] = []
    for path in source.iterdir():
        if not path.is_file():
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if mtime < cutoff:
            old_files.append(path)
    return old_files


def archive_file(source_file: Path, archive_dir: Path, dry_run: bool = False) -> Path:
    """Move source_file into archive_dir, gzip-compressing it. Returns the archive path."""
    archive_path = archive_dir / f"{source_file.name}.gz"

    if dry_run:
        logger.info("[dry-run] would archive %s -> %s", source_file, archive_path)
        return archive_path

    with source_file.open("rb") as f_in, gzip.open(archive_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    source_file.unlink()
    logger.info("archived %s -> %s", source_file, archive_path)
    return archive_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive log files older than a given number of days."
    )
    parser.add_argument(
        "--source", type=Path, required=True,
        help="directory containing logs to scan",
    )
    parser.add_argument(
        "--archive", type=Path, required=True,
        help="directory to move archived logs into",
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="files older than this many days are archived (default: 30)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="show what would happen without moving any files",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="enable debug logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    if not args.source.is_dir():
        logger.error("source is not a directory: %s", args.source)
        return 1

    if args.days < 1:
        logger.error("--days must be >= 1, got: %s", args.days)
        return 1

    if not args.dry_run:
        args.archive.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.now() - timedelta(days=args.days)
    logger.info("scanning %s for files older than %s", args.source, cutoff.isoformat())

    old_files = find_old_files(args.source, cutoff)
    if not old_files:
        logger.info("no files older than %d days found", args.days)
        return 0

    logger.info("found %d file(s) to archive", len(old_files))
    for f in old_files:
        try:
            archive_file(f, args.archive, dry_run=args.dry_run)
        except OSError as e:
            logger.error("failed to archive %s: %s", f, e)
            return 2

    logger.info("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
