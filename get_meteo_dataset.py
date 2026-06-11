#!/usr/bin/env python3
"""
Download the latest Arome0025 forecast files from meteofetch,
avoiding duplicate downloads by tracking the latest reference time.
"""

import argparse
import json
from pathlib import Path
import pandas as pd
from meteofetch import Arome0025
import xarray

import config

xarray.set_options(use_new_combine_kwarg_defaults=True)


def get_latest_reference_time(paquet: str) -> pd.Timestamp:
    return Arome0025.get_latest_forecast_time(paquet=paquet)


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


def download_latest_forecast(paquet: str, path: Path) -> list:
    """
    Download the latest Arome0025 forecast for the given paquet if not already cached.
    Returns a list of local file paths.
    """
    path.mkdir(parents=True, exist_ok=True)
    cache = load_cache(path, paquet)

    latest_ref_time = get_latest_reference_time(paquet)
    if latest_ref_time is None:
        raise ValueError(f"No forecasts available for paquet '{paquet}'.")

    if cache["latest_reference_time"] == latest_ref_time.isoformat():
        print(f"Already up-to-date (ref: {latest_ref_time}): {cache['file_paths']}")
        return cache["file_paths"]

    print(f"Downloading {paquet} (ref: {latest_ref_time})...")
    file_paths = Arome0025.get_latest_forecast(paquet=paquet, path=str(path), return_data=False)
    file_paths = [str(fp) for fp in file_paths]

    save_cache(path, paquet, latest_ref_time.isoformat(), file_paths)
    print(f"Downloaded: {file_paths}")

    # Delete previously cached files
    if cache["file_paths"]:
        for old_path in cache["file_paths"]:
            try:
                Path(old_path).unlink()
                print(f"Deleted stale file: {old_path}")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Could not delete {old_path}: {e}")

    return file_paths


def _horizon_start(file_path: str) -> int:
    """Parse the start hour from a filename like arome__0025__IP1__07H12H__....grib2."""
    import re
    m = re.search(r"__(\d+)H\d+H__", file_path)
    return int(m.group(1)) if m else 0


def iter_forecast(paquet: str, path: Path = None, fields=None, hours: int = None):
    """
    Yield one xarray.Dataset per GRIB file, in forecast-time order.

    Files whose horizon range starts beyond *hours* are skipped entirely,
    so we never load data we won't use. Each dataset is read, yielded, and
    then discarded by the caller — keeping peak memory to one file at a time.
    """
    if path is None:
        path = config.GRIBS_DIR
    if hours is None:
        hours = config.FORECAST_HORIZON_HOURS

    file_paths = download_latest_forecast(paquet=paquet, path=path)
    relevant = [fp for fp in sorted(file_paths) if _horizon_start(fp) < hours]

    print(f"Reading {len(relevant)}/{len(file_paths)} files (horizon ≤ {hours}h)")
    for fp in relevant:
        yield Arome0025._read_multiple_gribs([Path(fp)], fields, 1)


def get_latest_forecast(paquet: str, path: Path = None, fields=None) -> xarray.Dataset:
    if path is None:
        path = config.GRIBS_DIR
    file_paths = download_latest_forecast(paquet=paquet, path=path)
    return Arome0025._read_multiple_gribs([Path(fp) for fp in file_paths], fields, 4)


def main():
    parser = argparse.ArgumentParser(
        description="Download the latest Arome0025 forecast files from meteofetch."
    )
    parser.add_argument("--paquet", default="SP1", help="Forecast paquet (e.g. SP1, IP1). Default: SP1.")
    parser.add_argument("--path", type=Path, default=config.GRIBS_DIR, help="Directory to save GRIB files.")
    args = parser.parse_args()
    download_latest_forecast(args.paquet, args.path)


if __name__ == "__main__":
    main()
