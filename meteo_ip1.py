#!/usr/bin/env python3
"""Generate wind and cloudbase maps from the latest IP1 forecast (single GRIB read)."""

import argparse
from pathlib import Path

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

import generate_maps
import get_meteo_dataset
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


def cloudbase_height(t_kelvin, rel_humidity):
    """Hennig formula: cloud base in metres from temperature (K) and relative humidity (%)."""
    t_celsius = t_kelvin - 273.15
    dewpoint = (np.power(rel_humidity / 100, 1 / 8) * (112 + 0.9 * t_celsius) + 0.1 * t_celsius) - 112
    return 400 * (t_celsius - dewpoint)


def run(gribs_dir: Path, maps_dir: Path, pressure_levels: list = PRESSURE_LEVELS):
    # Two sequential reads to keep peak memory low on constrained hardware.
    # u,v are released before t,r are loaded.

    wind = get_meteo_dataset.get_latest_forecast("IP1", gribs_dir, fields=["u", "v"])
    da_u = config.next_hours(wind["u"])
    da_v = config.next_hours(wind["v"])
    n_times = len(da_u.coords["time"])

    for p in pressure_levels:
        for i in range(n_times):
            generate_maps.plot_wind_barbs_to_png(
                da_u.isel(time=i).sel(isobaricInhPa=p),
                da_v.isel(time=i).sel(isobaricInhPa=p),
                output_dir=maps_dir,
                subsample=20,
                barb_color="red",
                barb_length=4.0,
            )

    del da_u, da_v, wind

    cloud = get_meteo_dataset.get_latest_forecast("IP1", gribs_dir, fields=["t", "r"])
    da_t = config.next_hours(cloud["t"])
    da_r = config.next_hours(cloud["r"])

    for i in range(len(da_t.coords["time"])):
        layer = cloudbase_height(
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
