#!/usr/bin/env python3
"""
Main pipeline entry point.

Each 6h GRIB window is processed in a dedicated child process (spawn) so that
all GRIB/xarray memory is returned to the OS before the next window starts.

For each window:
  1. Download SP1 (if not cached) → render rain
  2. Download IP1 (if not cached) → render wind → render cloudbase
  3. Update index.json

Safe to schedule every 15 minutes: an exclusive lockfile prevents overlapping
runs, and the pipeline exits early if the latest model run hasn't changed.
"""

import fcntl
import multiprocessing
import pickle
import sys
import tempfile
import warnings
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import time

warnings.filterwarnings("ignore", message="ecCodes", module="gribapi")

import get_meteo_dataset
import generate_index
import cleanup_maps
import config

LOCK_FILE = config.MAPS_DIR / "pipeline.lock"


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


@contextmanager
def timed(label: str):
    t0 = time.perf_counter()
    yield
    log(f"  {label}: {time.perf_counter() - t0:.1f}s")


# ---------------------------------------------------------------------------
# Per-window work — runs in a child process
# ---------------------------------------------------------------------------

def _process_window(group: str, sp1_date: str, ip1_date: str,
                    prev_tp_path: str | None, out_tp_path: str,
                    reference_time: str | None = None):
    """Download and render one 6h window; hand off prev_tp via pickle files."""
    import meteo_rain
    import meteo_ip1

    @contextmanager
    def timed(label):
        t0 = time.perf_counter()
        yield
        log(f"  {label}: {time.perf_counter() - t0:.1f}s")

    prev_tp = None
    if prev_tp_path and Path(prev_tp_path).exists():
        with open(prev_tp_path, "rb") as f:
            prev_tp = pickle.load(f)

    with timed("download SP1"):
        sp1_file = get_meteo_dataset.download_window_file("SP1", group, sp1_date)
    with timed("read SP1"):
        ds = get_meteo_dataset.read_file(sp1_file, fields=["tp"])
    with timed("render rain"):
        prev_tp = meteo_rain.render(ds, config.MAPS_DIR, prev_tp)
    del ds

    with open(out_tp_path, "wb") as f:
        pickle.dump(prev_tp, f)
    del prev_tp

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
        generate_index.generate_index(reference_time=reference_time)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def main():
    config.MAPS_DIR.mkdir(parents=True, exist_ok=True)
    lock_fh = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("Another pipeline run is in progress — exiting.")
        lock_fh.close()
        sys.exit(0)

    try:
        _run()
    finally:
        fcntl.flock(lock_fh, fcntl.LOCK_UN)
        lock_fh.close()


def _run():
    log("Starting pipeline")
    total_t0 = time.perf_counter()

    # Skip if the latest model run hasn't changed since last time
    sp1_cached = get_meteo_dataset._load_ref_cache(config.GRIBS_DIR, "SP1")
    ip1_cached = get_meteo_dataset._load_ref_cache(config.GRIBS_DIR, "IP1")

    sp1_ref = get_meteo_dataset.get_latest_reference_time("SP1")
    ip1_ref = get_meteo_dataset.get_latest_reference_time("IP1")

    sp1_date = f"{sp1_ref:%Y-%m-%dT%H}"
    ip1_date = f"{ip1_ref:%Y-%m-%dT%H}"

    if sp1_date == sp1_cached and ip1_date == ip1_cached:
        log(f"No new model run (SP1: {sp1_date}, IP1: {ip1_date}) — exiting.")
        return

    log(f"New run detected — SP1: {sp1_date}, IP1: {ip1_date}")

    groups = get_meteo_dataset._relevant_groups()
    log(f"Windows to process: {groups}")

    with tempfile.TemporaryDirectory() as tmpdir:
        prev_tp_path = None

        for i, group in enumerate(groups):
            log(f"── Window {group} ──")
            out_tp_path = str(Path(tmpdir) / f"prev_tp_{i}.pkl")

            ref_iso = f"{sp1_date}:00:00Z"

            p = multiprocessing.Process(
                target=_process_window,
                args=(group, sp1_date, ip1_date, prev_tp_path, out_tp_path, ref_iso),
            )
            p.start()
            p.join()

            if p.exitcode != 0:
                log(f"Window {group} failed (exit {p.exitcode}), aborting")
                break

            prev_tp_path = out_tp_path

    with timed("cleanup maps"):
        cleanup_maps.cleanup_files(config.MAPS_DIR, dry_run=False)

    log(f"Pipeline complete in {time.perf_counter() - total_t0:.1f}s")


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
