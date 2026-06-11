#!/usr/bin/env python3
"""Generate rain accumulation maps from the latest SP1 forecast."""

import argparse
from pathlib import Path

import generate_maps
import get_meteo_dataset
import config


def run(gribs_dir: Path, maps_dir: Path):
    prev = None
    for ds in get_meteo_dataset.iter_forecast("SP1", gribs_dir, fields=["tp"]):
        da = config.next_hours(ds["tp"])
        for i in range(len(da.coords["time"])):
            current = da.isel(time=i)
            layer = current if prev is None else (current - prev).assign_coords(time=current["time"].values)
            generate_maps.plot_rain_layer_to_png(layer=layer, output_dir=maps_dir)
            prev = current


def main():
    parser = argparse.ArgumentParser(description="Generate rain maps from latest AROME SP1 forecast.")
    parser.add_argument("--gribs-dir", type=Path, default=config.GRIBS_DIR)
    parser.add_argument("--maps-dir", type=Path, default=config.MAPS_DIR)
    args = parser.parse_args()
    run(args.gribs_dir, args.maps_dir)


if __name__ == "__main__":
    main()
