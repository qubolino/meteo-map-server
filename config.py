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
        # Qt color format: #AARRGGBB
        "colors": ["#9900B2E6", "#990000CC", "#9900CC00", "#9900CCCC"],
    },
    "cloudbase": {
        "units": "m",
        "vmin": 0,
        "vmax": 4000,
        # Qt color format: #AARRGGBB
        "colors": ["#40404040", "#40808080", "#40BFBFBF", "#00FFFFFF"],
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
