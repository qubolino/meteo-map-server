"""Shared path configuration for meteo_france scripts."""

from pathlib import Path

BASE_DIR = Path(__file__).parent
GRIBS_DIR = BASE_DIR / "gribs"
MAPS_DIR = BASE_DIR / "generated_maps"
