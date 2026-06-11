#!/usr/bin/env python3
"""Rain map rendering from an SP1 xarray Dataset."""

import time
from multiprocessing import Pool
import xarray
from pathlib import Path

import pandas as pd

import generate_maps
import config


def _render_one(args):
    layer, maps_dir = args
    t0 = time.perf_counter()
    generate_maps.plot_rain_layer_to_png(layer=layer, output_dir=maps_dir)
    print(f"    rain {layer['time'].values}: {time.perf_counter()-t0:.1f}s", flush=True)


def render(ds: xarray.Dataset, maps_dir: Path, prev_tp=None, workers: int = config.RENDER_WORKERS):
    """
    Render rain maps for all timesteps in *ds*.

    *prev_tp* is the last total-precipitation layer from the previous window,
    needed to compute the accumulation diff across the window boundary.
    Returns the last tp layer so the caller can pass it to the next window.
    """
    da_full = ds["tp"]
    da = config.next_hours(da_full)

    # If no baseline from a prior window, find the last step before now-1h in this GRIB
    if prev_tp is None:
        start = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(hours=1)
        times = pd.DatetimeIndex(da_full.coords["time"].values)
        before = times[times < start]
        if len(before) > 0:
            prev_tp = da_full.isel(time=len(before) - 1)

    # Accumulation diff is sequential; compute all layers first
    layers = []
    for i in range(len(da.coords["time"])):
        current = da.isel(time=i)
        if prev_tp is not None:
            layers.append((current - prev_tp).assign_coords(time=current["time"].values))
        prev_tp = current

    tasks = [(layer, maps_dir) for layer in layers]
    if workers > 1:
        with Pool(workers) as pool:
            pool.map(_render_one, tasks)
    else:
        for task in tasks:
            _render_one(task)

    return prev_tp
