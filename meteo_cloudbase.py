#!/usr/bin/env python3
"""Generate cloud base height maps from the latest IP1 forecast."""

import argparse
from pathlib import Path
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import generate_maps
import get_meteo_dataset
import config

CLOUDBASE_CMAP = LinearSegmentedColormap.from_list(
    "cloudbase",
    [
        (0.25, 0.25, 0.25, 0.75),  # dark gray  → low cloud base
        (0.50, 0.50, 0.50, 0.75),  # mid gray
        (0.75, 0.75, 0.75, 0.75),  # light gray
        (1.00, 1.00, 1.00, 0.00),  # transparent → high / clear
    ],
    N=10,
)


def cloudbase_height(t_kelvin, rel_humidity):
    """Hennig formula: cloud base in metres from temperature (K) and relative humidity (%)."""
    t_celsius = t_kelvin - 273.15
    dewpoint = (np.power(rel_humidity / 100, 1 / 8) * (112 + 0.9 * t_celsius) + 0.1 * t_celsius) - 112
    return 400 * (t_celsius - dewpoint)


def run(gribs_dir: Path, maps_dir: Path):
    datasets = get_meteo_dataset.get_latest_forecast("IP1", gribs_dir, fields=["t", "r"])
    da_t = datasets["t"]
    da_r = datasets["r"]

    for i in range(len(da_t.coords["time"])):
        layer_t = da_t.isel(time=i).sel(isobaricInhPa=1000)
        layer_r = da_r.isel(time=i).sel(isobaricInhPa=1000)
        layer = cloudbase_height(layer_t, layer_r)

        generate_maps.plot_layer_to_png(
            layer,
            output_path=maps_dir / f"cloudbase_map_{np.datetime_as_string(layer['time'].values, unit='s')}.png",
            vmin=0,
            vmax=4000,
            levels=5,
            cmap=CLOUDBASE_CMAP,
        )


def main():
    parser = argparse.ArgumentParser(description="Generate cloud base maps from latest AROME IP1 forecast.")
    parser.add_argument("--gribs-dir", type=Path, default=config.GRIBS_DIR)
    parser.add_argument("--maps-dir", type=Path, default=config.MAPS_DIR)
    args = parser.parse_args()
    run(args.gribs_dir, args.maps_dir)


if __name__ == "__main__":
    main()
