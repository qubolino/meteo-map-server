#!/usr/bin/env python3
"""Rain map rendering from an SP1 xarray Dataset."""

import xarray
from pathlib import Path

import generate_maps
import config


def render(ds: xarray.Dataset, maps_dir: Path, prev_tp=None):
    """
    Render rain maps for all timesteps in *ds*.

    *prev_tp* is the last total-precipitation layer from the previous window,
    needed to compute the accumulation diff across the window boundary.
    Returns the last tp layer so the caller can pass it to the next window.
    """
    da = config.next_hours(ds["tp"])
    for i in range(len(da.coords["time"])):
        current = da.isel(time=i)
        layer = current if prev_tp is None else (current - prev_tp).assign_coords(
            time=current["time"].values
        )
        generate_maps.plot_rain_layer_to_png(layer=layer, output_dir=maps_dir)
        prev_tp = current
    return prev_tp
