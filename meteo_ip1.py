#!/usr/bin/env python3
"""Wind and cloudbase map rendering from an IP1 xarray Dataset."""

import xarray
from pathlib import Path

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

import generate_maps
import config

PRESSURE_LEVELS = [1000, 900, 800, 700]

CLOUDBASE_CMAP = LinearSegmentedColormap.from_list(
    "cloudbase",
    [
        (0.25, 0.25, 0.25, 0.75),
        (0.50, 0.50, 0.50, 0.75),
        (0.75, 0.75, 0.75, 0.75),
        (1.00, 1.00, 1.00, 0.00),
    ],
    N=10,
)


def _cloudbase_height(t_kelvin, rel_humidity):
    """Hennig formula: cloud base in metres from temperature (K) and relative humidity (%)."""
    t_celsius = t_kelvin - 273.15
    dewpoint = (np.power(rel_humidity / 100, 1 / 8) * (112 + 0.9 * t_celsius) + 0.1 * t_celsius) - 112
    return 400 * (t_celsius - dewpoint)


def render_wind(ds: xarray.Dataset, maps_dir: Path, pressure_levels: list = PRESSURE_LEVELS):
    da_u = config.next_hours(ds["u"])
    da_v = config.next_hours(ds["v"])
    for i in range(len(da_u.coords["time"])):
        for p in pressure_levels:
            generate_maps.plot_wind_barbs_to_png(
                da_u.isel(time=i).sel(isobaricInhPa=p),
                da_v.isel(time=i).sel(isobaricInhPa=p),
                output_dir=maps_dir,
                subsample=20,
                barb_color="red",
                barb_length=4.0,
            )


def render_cloudbase(ds: xarray.Dataset, maps_dir: Path):
    da_t = config.next_hours(ds["t"])
    da_r = config.next_hours(ds["r"])
    for i in range(len(da_t.coords["time"])):
        layer = _cloudbase_height(
            da_t.isel(time=i).sel(isobaricInhPa=1000),
            da_r.isel(time=i).sel(isobaricInhPa=1000),
        )
        generate_maps.plot_layer_to_png(
            layer,
            output_path=maps_dir / f"cloudbase_map_{np.datetime_as_string(layer['time'].values, unit='s')}.png",
            vmin=0,
            vmax=4000,
            levels=5,
            cmap=CLOUDBASE_CMAP,
        )
