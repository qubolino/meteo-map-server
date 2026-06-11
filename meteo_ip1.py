#!/usr/bin/env python3
"""Generate wind and cloudbase maps from the latest IP1 forecast (single GRIB read)."""

import argparse
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

import generate_maps
import get_meteo_dataset
import config

PRESSURE_LEVELS = [1000, 900, 800, 700]
POOL_WORKERS = 2

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


def cloudbase_height(t_kelvin, rel_humidity):
    """Hennig formula: cloud base in metres from temperature (K) and relative humidity (%)."""
    t_celsius = t_kelvin - 273.15
    dewpoint = (np.power(rel_humidity / 100, 1 / 8) * (112 + 0.9 * t_celsius) + 0.1 * t_celsius) - 112
    return 400 * (t_celsius - dewpoint)


def _render_wind(args):
    layer_u, layer_v, maps_dir = args
    generate_maps.plot_wind_barbs_to_png(
        layer_u, layer_v,
        output_dir=maps_dir,
        subsample=20,
        barb_color="red",
        barb_length=4.0,
    )


def _render_cloudbase(args):
    layer, maps_dir = args
    generate_maps.plot_layer_to_png(
        layer,
        output_path=maps_dir / f"cloudbase_map_{np.datetime_as_string(layer['time'].values, unit='s')}.png",
        vmin=0,
        vmax=4000,
        levels=5,
        cmap=CLOUDBASE_CMAP,
    )


def run(gribs_dir: Path, maps_dir: Path, pressure_levels: list = PRESSURE_LEVELS):
    datasets = get_meteo_dataset.get_latest_forecast(
        "IP1", gribs_dir, fields=["u", "v", "t", "r"]
    )

    da_u = config.next_hours(datasets["u"])
    da_v = config.next_hours(datasets["v"])
    da_t = config.next_hours(datasets["t"])
    da_r = config.next_hours(datasets["r"])

    n_times = len(da_u.coords["time"])

    wind_tasks = [
        (da_u.isel(time=i).sel(isobaricInhPa=p),
         da_v.isel(time=i).sel(isobaricInhPa=p),
         maps_dir)
        for p in pressure_levels
        for i in range(n_times)
    ]

    cloudbase_tasks = [
        (cloudbase_height(da_t.isel(time=i).sel(isobaricInhPa=1000),
                          da_r.isel(time=i).sel(isobaricInhPa=1000)),
         maps_dir)
        for i in range(n_times)
    ]

    with Pool(POOL_WORKERS) as pool:
        pool.map(_render_wind, wind_tasks)
        pool.map(_render_cloudbase, cloudbase_tasks)


def main():
    parser = argparse.ArgumentParser(
        description="Generate wind and cloudbase maps from latest AROME IP1 forecast."
    )
    parser.add_argument("--gribs-dir", type=Path, default=config.GRIBS_DIR)
    parser.add_argument("--maps-dir", type=Path, default=config.MAPS_DIR)
    parser.add_argument(
        "--levels", type=int, nargs="+", default=PRESSURE_LEVELS,
        metavar="HPA", help="Pressure levels in hPa. Default: 1000 900 800 700."
    )
    args = parser.parse_args()
    run(args.gribs_dir, args.maps_dir, args.levels)


if __name__ == "__main__":
    main()
