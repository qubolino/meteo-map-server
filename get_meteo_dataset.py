#!/usr/bin/env python3
"""
Forecast data access for AROME 0025.

Downloads individual 6h-window GRIB files on demand; each file is meant to be
processed and deleted before the next is fetched, keeping both disk usage and
peak memory to one window at a time.
"""

import argparse
import json
import re
from pathlib import Path

import requests
import pandas as pd
from meteofetch import Arome0025
import xarray

import config

xarray.set_options(use_new_combine_kwarg_defaults=True)

_WINDOW_RE = re.compile(r"(\d+)H(\d+)H")


def _window_start(group: str) -> int:
    """Return start hour from a group label, e.g. 7 from '07H12H'."""
    m = _WINDOW_RE.search(group)
    return int(m.group(1)) if m else 0


def _relevant_groups(hours: int = None) -> list[str]:
    if hours is None:
        hours = config.FORECAST_HORIZON_HOURS
    return [g for g in Arome0025.groups_ if _window_start(g) < hours]


# ---------------------------------------------------------------------------
# Reference-time cache (stores only the run timestamp, not file paths)
# ---------------------------------------------------------------------------

def _load_ref_cache(gribs_dir: Path, paquet: str) -> str | None:
    cache_file = gribs_dir / f"{paquet}_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f).get("latest_reference_time")
    return None


def _save_ref_cache(gribs_dir: Path, paquet: str, reference_time: str):
    gribs_dir.mkdir(parents=True, exist_ok=True)
    cache_file = gribs_dir / f"{paquet}_cache.json"
    with open(cache_file, "w") as f:
        json.dump({"latest_reference_time": reference_time}, f)


def get_latest_reference_time(paquet: str, gribs_dir: Path = None) -> pd.Timestamp:
    """Return the latest available reference time, caching the result."""
    if gribs_dir is None:
        gribs_dir = config.GRIBS_DIR

    ref_time = Arome0025.get_latest_forecast_time(paquet=paquet)
    if ref_time is None:
        raise ValueError(f"No forecasts available for paquet '{paquet}'.")

    _save_ref_cache(gribs_dir, paquet, f"{ref_time:%Y-%m-%dT%H}")
    return ref_time


# ---------------------------------------------------------------------------
# Single-file download
# ---------------------------------------------------------------------------

def _build_url(paquet: str, group: str, date_str: str) -> str:
    return (
        Arome0025.base_url_
        + "/"
        + Arome0025.url_.format(date=date_str, paquet=paquet, group=group)
    )


def download_window_file(paquet: str, group: str, date_str: str, gribs_dir: Path = None) -> Path:
    """
    Download a single 6h-window GRIB file and return its path.
    The file name follows the same convention as meteofetch (colons → dashes).
    """
    if gribs_dir is None:
        gribs_dir = config.GRIBS_DIR
    gribs_dir.mkdir(parents=True, exist_ok=True)

    url = _build_url(paquet, group, date_str)
    filename = url.split("/")[-1].replace(":", "-")
    dest = gribs_dir / filename

    if dest.exists():
        print(f"[{paquet}/{group}] Already cached: {dest}")
        return dest

    print(f"[{paquet}/{group}] Downloading...")
    with requests.get(url, stream=True, timeout=Arome0025.TIMEOUT) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024 * 16):
                f.write(chunk)

    print(f"[{paquet}/{group}] Saved to {dest}")

    # Remove stale files for the same paquet+group from a previous run
    for stale in gribs_dir.glob(f"arome__0025__{paquet}__{group}__*.grib2"):
        if stale != dest:
            stale.unlink()
            print(f"[{paquet}/{group}] Deleted stale: {stale.name}")

    return dest


# ---------------------------------------------------------------------------
# Single-file read
# ---------------------------------------------------------------------------

def read_file(file_path: str | Path, fields=None) -> xarray.Dataset:
    """Read a single GRIB file into an xarray Dataset."""
    return Arome0025._read_multiple_gribs([Path(file_path)], fields, 1)


# ---------------------------------------------------------------------------
# CLI (download only, for debugging)
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download AROME 0025 window files.")
    parser.add_argument("--paquet", default="SP1")
    parser.add_argument("--group", default="00H06H")
    parser.add_argument("--gribs-dir", type=Path, default=config.GRIBS_DIR)
    args = parser.parse_args()

    ref = get_latest_reference_time(args.paquet, args.gribs_dir)
    download_window_file(args.paquet, args.group, f"{ref:%Y-%m-%dT%H}", args.gribs_dir)


if __name__ == "__main__":
    main()
