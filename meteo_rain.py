#!/usr/bin/env python3
"""Generate rain accumulation maps from the latest SP1 forecast."""

import argparse
from multiprocessing import Pool
from pathlib import Path

import generate_maps
import get_meteo_dataset
import config

POOL_WORKERS = 2


def _render(args):
    layer, maps_dir = args
    generate_maps.plot_rain_layer_to_png(layer=layer, output_dir=maps_dir)


def run(gribs_dir: Path, maps_dir: Path):
    datasets = get_meteo_dataset.get_latest_forecast("SP1", gribs_dir, fields=["tp"])
    da = config.next_hours(datasets["tp"])

    # Accumulation diff is sequential, so pre-compute all layers before parallelising render
    layers = []
    for i in range(len(da.coords["time"])):
        if i == 0:
            layers.append(da.isel(time=i))
        else:
            layers.append(
                (da.isel(time=i) - da.isel(time=i - 1)).assign_coords(
                    time=da.isel(time=i)["time"].values
                )
            )

    with Pool(POOL_WORKERS) as pool:
        pool.map(_render, [(layer, maps_dir) for layer in layers])


def main():
    parser = argparse.ArgumentParser(description="Generate rain maps from latest AROME SP1 forecast.")
    parser.add_argument("--gribs-dir", type=Path, default=config.GRIBS_DIR)
    parser.add_argument("--maps-dir", type=Path, default=config.MAPS_DIR)
    args = parser.parse_args()
    run(args.gribs_dir, args.maps_dir)


if __name__ == "__main__":
    main()
