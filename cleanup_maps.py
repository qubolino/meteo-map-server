#!/usr/bin/env python3
"""Delete generated map PNGs whose forecast timestamp has passed."""

import argparse
import glob
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import config


def extract_timestamp(filepath: str) -> datetime | None:
    match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", filepath)
    if match:
        return datetime.fromisoformat(match.group(1)).replace(tzinfo=timezone.utc)
    return None


def cleanup_files(directory: Path, pattern: str = "*.png", dry_run: bool = True) -> int:
    """Delete files whose embedded timestamp is in the past. Returns count deleted."""
    now = datetime.now(timezone.utc)
    deleted = 0
    for filepath in glob.glob(str(directory / pattern)):
        ts = extract_timestamp(filepath)
        if ts is None:
            print(f"Skipping (no timestamp): {filepath}")
            continue
        if ts < now:
            if dry_run:
                print(f"[DRY RUN] Would delete: {filepath}  ({ts})")
            else:
                try:
                    os.remove(filepath)
                    print(f"Deleted: {filepath}  ({ts})")
                    deleted += 1
                except OSError as e:
                    print(f"Error deleting {filepath}: {e}")
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Delete map PNGs with expired forecast timestamps.")
    parser.add_argument("--directory", "-d", type=Path, default=config.MAPS_DIR)
    parser.add_argument("--pattern", "-p", default="*.png")
    parser.add_argument("--execute", action="store_true", help="Actually delete (default: dry run).")
    args = parser.parse_args()

    dry_run = not args.execute
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}  |  Directory: {args.directory}")
    count = cleanup_files(args.directory, args.pattern, dry_run)
    if not dry_run:
        print(f"Done. {count} file(s) deleted.")


if __name__ == "__main__":
    main()
