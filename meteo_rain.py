#!/usr/bin/env python3
"""Rain map rendering from an SP1 xarray Dataset."""

import time
import xarray
from pathlib import Path

import generate_maps
import config


def render(ds: xarray.Dataset, maps_dir: Path, prev_tp=None):
    da = config.next_hours(ds["tp"])
    for i in range(len(da.coords["time"])):
        current = da.isel(time=i)
        layer = current if prev_tp is None else (current - prev_tp).assign_coords(
            time=current["time"].values
        )
        t0 = time.perf_counter()
        generate_maps.plot_rain_layer_to_png(layer=layer, output_dir=maps_dir)
        print(f"    rain {layer['time'].values}: {time.perf_counter()-t0:.1f}s", flush=True)
        prev_tp = current
    return prev_tp
