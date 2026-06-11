#!/usr/bin/env python3
"""
Main pipeline entry point.

For each 6h GRIB window within the forecast horizon:
  1. Download SP1 (if not cached) → render rain
  2. Download IP1 (if not cached) → render wind → render cloudbase
  3. Update index.json
"""

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

    for group, sp1_date, ip1_date in get_meteo_dataset.iter_windows():
        log(f"Window {group}")

        log("  Rain...")
        sp1_file = get_meteo_dataset.download_window_file("SP1", group, sp1_date)
        ds = get_meteo_dataset.read_file(sp1_file, fields=["tp"])
        prev_tp = meteo_rain.render(ds, config.MAPS_DIR, prev_tp)
        del ds

        ip1_file = get_meteo_dataset.download_window_file("IP1", group, ip1_date)

        log("  Wind...")
        ds = get_meteo_dataset.read_file(ip1_file, fields=["u", "v"])
        meteo_ip1.render_wind(ds, config.MAPS_DIR)
        del ds

        log("  Cloudbase...")
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
