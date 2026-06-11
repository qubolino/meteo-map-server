#!/usr/bin/env python3
"""
Main pipeline entry point.

For each 6h GRIB window within the forecast horizon:
  1. Load SP1 → render rain → free
  2. Load IP1 (u,v) → render wind → free
  3. Load IP1 (t,r) → render cloudbase → free
  4. Update index.json

This keeps peak memory to a single 6h dataset at a time.
"""

import sys
from datetime import datetime, timezone

import get_meteo_dataset
import generate_index
import cleanup_maps
import meteo_rain
import meteo_ip1
import config


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    log("Starting pipeline")

    prev_tp = None  # carry rain accumulation across window boundaries

    for window, sp1_file, ip1_file in get_meteo_dataset.iter_windows():
        log(f"Window {window}")

        log("  Rain (SP1)...")
        ds = get_meteo_dataset.read_file(sp1_file, fields=["tp"])
        prev_tp = meteo_rain.render(ds, config.MAPS_DIR, prev_tp)
        del ds

        log("  Wind (IP1 u,v)...")
        ds = get_meteo_dataset.read_file(ip1_file, fields=["u", "v"])
        meteo_ip1.render_wind(ds, config.MAPS_DIR)
        del ds

        log("  Cloudbase (IP1 t,r)...")
        ds = get_meteo_dataset.read_file(ip1_file, fields=["t", "r"])
        meteo_ip1.render_cloudbase(ds, config.MAPS_DIR)
        del ds

        log("  Updating index.json...")
        generate_index.generate_index()

    log("Cleaning up expired maps...")
    cleanup_maps.cleanup_files(config.MAPS_DIR, dry_run=False)

    log("Pipeline complete.")


if __name__ == "__main__":
    main()
