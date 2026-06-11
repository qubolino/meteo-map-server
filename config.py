"""Shared configuration for meteo_france scripts."""

from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).parent
GRIBS_DIR = BASE_DIR / "gribs"
MAPS_DIR = BASE_DIR / "generated_maps"

FORECAST_HORIZON_HOURS = 10
RENDER_WORKERS = 1  # set > 1 to render maps in parallel (uses multiprocessing)


def next_hours(da, hours: int = FORECAST_HORIZON_HOURS):
    """Return a DataArray filtered to timesteps within the next *hours* from now."""
    now = pd.Timestamp.utcnow().tz_localize(None)
    cutoff = now + pd.Timedelta(hours=hours)
    times = pd.DatetimeIndex(da.coords["time"].values)
    mask = (times >= now) & (times <= cutoff)
    return da.isel(time=mask)
