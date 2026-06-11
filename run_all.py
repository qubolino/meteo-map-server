#!/usr/bin/env python3
"""
Main pipeline entry point.

For each 6h GRIB window within the forecast horizon:
  1. Download SP1 (if not cached) → render rain
  2. Download IP1 (if not cached) → render wind → render cloudbase
  3. Update index.json
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import time

import get_meteo_dataset
import generate_index
import cleanup_maps
import meteo_rain
import meteo_ip1
import config


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


@contextmanager
def timed(label: str):
    t0 = time.perf_counter()
    yield
    elapsed = time.perf_counter() - t0
    log(f"  {label}: {elapsed:.1f}s")


def main():
    log("Starting pipeline")
    total_t0 = time.perf_counter()

    prev_tp = None

    for group, sp1_date, ip1_date in get_meteo_dataset.iter_windows():
        log(f"── Window {group} ──")

        with timed("download SP1"):
            sp1_file = get_meteo_dataset.download_window_file("SP1", group, sp1_date)
        with timed("read SP1"):
            ds = get_meteo_dataset.read_file(sp1_file, fields=["tp"])
        with timed("render rain"):
            prev_tp = meteo_rain.render(ds, config.MAPS_DIR, prev_tp)
        del ds

        with timed("download IP1"):
            ip1_file = get_meteo_dataset.download_window_file("IP1", group, ip1_date)

        with timed("read IP1 (u,v)"):
            ds = get_meteo_dataset.read_file(ip1_file, fields=["u", "v"])
        with timed("render wind"):
            meteo_ip1.render_wind(ds, config.MAPS_DIR)
        del ds

        with timed("read IP1 (t,r)"):
            ds = get_meteo_dataset.read_file(ip1_file, fields=["t", "r"])
        with timed("render cloudbase"):
            meteo_ip1.render_cloudbase(ds, config.MAPS_DIR)
        del ds

        with timed("update index"):
            generate_index.generate_index()

    with timed("cleanup maps"):
        cleanup_maps.cleanup_files(config.MAPS_DIR, dry_run=False)

    total = time.perf_counter() - total_t0
    log(f"Pipeline complete in {total:.1f}s")


if __name__ == "__main__":
    main()
