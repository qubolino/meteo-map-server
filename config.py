"""Shared configuration for meteo_france scripts."""

from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).parent
GRIBS_DIR = BASE_DIR / "gribs"
MAPS_DIR = BASE_DIR / "generated_maps"

FORECAST_HORIZON_HOURS = 10
RENDER_WORKERS = 4  # set > 1 to render maps in parallel (uses multiprocessing)

# ---------------------------------------------------------------------------
# Layer metadata — single source of truth for rendering AND index.json
# ---------------------------------------------------------------------------

LAYER_META = {
    "rain": {
        "units": "mm/h",
        "vmin": 0.1,
        "vmax": 10.0,
        "colors": ["#00B2E699", "#0000CC99", "#00CC0099", "#00CCCC99"],
    },
    "cloudbase": {
        "units": "m",
        "vmin": 0,
        "vmax": 4000,
        "colors": ["#40404040", "#80808040", "#BFBFBF40", "#FFFFFF00"],
    },
    "wind": {
        "units": "kt",
    },
}


def next_hours(da, hours: int = FORECAST_HORIZON_HOURS):
    """Return timesteps from 1 hour ago through the next *hours* from now."""
    now = pd.Timestamp.utcnow().tz_localize(None)
    start = now - pd.Timedelta(hours=1)
    cutoff = now + pd.Timedelta(hours=hours)
    times = pd.DatetimeIndex(da.coords["time"].values)
    mask = (times >= start) & (times <= cutoff)
    return da.isel(time=mask)
