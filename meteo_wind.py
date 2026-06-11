#!/usr/bin/env python3
"""Generate wind barb maps from the latest IP1 forecast."""

import argparse
from pathlib import Path
import generate_maps
import get_meteo_dataset
import config

PRESSURE_LEVELS = [1000, 900, 800, 700]


def run(gribs_dir: Path, maps_dir: Path, pressure_levels: list = PRESSURE_LEVELS):
    datasets = get_meteo_dataset.get_latest_forecast("IP1", gribs_dir, fields=["u", "v"])
    da_u = datasets["u"]
    da_v = datasets["v"]

    for pressure in pressure_levels:
        for i in range(len(da_u.coords["time"])):
            layer_u = da_u.isel(time=i).sel(isobaricInhPa=pressure)
            layer_v = da_v.isel(time=i).sel(isobaricInhPa=pressure)
            generate_maps.plot_wind_barbs_to_png(
                layer_u,
                layer_v,
                output_dir=maps_dir,
                subsample=20,
                barb_color="red",
                barb_length=4.0,
            )


def main():
    parser = argparse.ArgumentParser(description="Generate wind maps from latest AROME IP1 forecast.")
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
