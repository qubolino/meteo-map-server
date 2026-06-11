#!/usr/bin/env python3
"""
Download the latest Arome0025 forecast files from meteofetch,
avoiding duplicate downloads by tracking the latest reference time.
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from meteofetch import Arome0025
import xarray

import config

xarray.set_options(use_new_combine_kwarg_defaults=True)

_WINDOW_RE = re.compile(r"__(\d+)H(\d+)H__")


def _window_label(file_path: str) -> str:
    """Extract the window label from a filename, e.g. '07H12H'."""
    m = _WINDOW_RE.search(file_path)
    return m.group(0).strip("_") if m else ""


def _window_start(file_path: str) -> int:
    """Extract the start hour from a filename, e.g. 7 from '07H12H'."""
    m = _WINDOW_RE.search(file_path)
    return int(m.group(1)) if m else 0


def load_cache(path: Path, paquet: str) -> dict:
    cache_file = path / f"{paquet}_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return {"latest_reference_time": None, "file_paths": None}


def save_cache(path: Path, paquet: str, reference_time: str, file_paths: list):
    cache_file = path / f"{paquet}_cache.json"
    with open(cache_file, "w") as f:
        json.dump({"latest_reference_time": reference_time, "file_paths": file_paths}, f)


def download_latest_forecast(paquet: str, path: Path) -> list[str]:
    """
    Download the latest Arome0025 forecast for the given paquet if not already cached.
    Returns a sorted list of local file paths.
    """
    path.mkdir(parents=True, exist_ok=True)
    cache = load_cache(path, paquet)

    latest_ref_time = Arome0025.get_latest_forecast_time(paquet=paquet)
    if latest_ref_time is None:
        raise ValueError(f"No forecasts available for paquet '{paquet}'.")

    if cache["latest_reference_time"] == latest_ref_time.isoformat():
        print(f"[{paquet}] Already up-to-date (ref: {latest_ref_time})")
        return sorted(cache["file_paths"])

    print(f"[{paquet}] Downloading (ref: {latest_ref_time})...")
    file_paths = Arome0025.get_latest_forecast(paquet=paquet, path=str(path), return_data=False)
    file_paths = sorted(str(fp) for fp in file_paths)

    save_cache(path, paquet, latest_ref_time.isoformat(), file_paths)
    print(f"[{paquet}] Downloaded: {file_paths}")

    if cache["file_paths"]:
        for old in cache["file_paths"]:
            try:
                Path(old).unlink()
                print(f"[{paquet}] Deleted stale: {old}")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[{paquet}] Could not delete {old}: {e}")

    return file_paths


def read_file(file_path: str, fields=None) -> xarray.Dataset:
    """Read a single GRIB file into an xarray Dataset."""
    return Arome0025._read_multiple_gribs([Path(file_path)], fields, 1)


def iter_windows(gribs_dir: Path = None, hours: int = None):
    """
    Yield (window_label, sp1_file, ip1_file) for each 6h window within the
    forecast horizon, in time order. Both paquets are downloaded upfront
    (fast, cached after first run), then paired by window label so the caller
    can load, render, and discard one window at a time.
    """
    if gribs_dir is None:
        gribs_dir = config.GRIBS_DIR
    if hours is None:
        hours = config.FORECAST_HORIZON_HOURS

    sp1_files = {_window_label(fp): fp for fp in download_latest_forecast("SP1", gribs_dir)}
    ip1_files = {_window_label(fp): fp for fp in download_latest_forecast("IP1", gribs_dir)}

    windows = sorted(sp1_files.keys() & ip1_files.keys())
    relevant = [w for w in windows if _window_start(sp1_files[w]) < hours]

    print(f"Processing {len(relevant)}/{len(windows)} windows (horizon ≤ {hours}h): {relevant}")
    for window in relevant:
        yield window, sp1_files[window], ip1_files[window]


def main():
    parser = argparse.ArgumentParser(
        description="Download the latest Arome0025 forecast files from meteofetch."
    )
    parser.add_argument("--paquet", default="SP1", help="Paquet to download (e.g. SP1, IP1).")
    parser.add_argument("--path", type=Path, default=config.GRIBS_DIR)
    args = parser.parse_args()
    download_latest_forecast(args.paquet, args.path)


if __name__ == "__main__":
    main()
