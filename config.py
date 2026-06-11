"""Shared configuration for meteo_france scripts."""

from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).parent
GRIBS_DIR = BASE_DIR / "gribs"
MAPS_DIR = BASE_DIR / "generated_maps"

FORECAST_HORIZON_HOURS = 10
RENDER_WORKERS = 4  # set > 1 to render maps in parallel (uses multiprocessing)


def next_hours(da, hours: int = FORECAST_HORIZON_HOURS):
    """Return timesteps from 1 hour ago through the next *hours* from now."""
    now = pd.Timestamp.utcnow().tz_localize(None)
    start = now - pd.Timedelta(hours=1)
    cutoff = now + pd.Timedelta(hours=hours)
    times = pd.DatetimeIndex(da.coords["time"].values)
    mask = (times >= start) & (times <= cutoff)
    return da.isel(time=mask)
