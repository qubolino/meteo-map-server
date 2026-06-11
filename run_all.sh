#!/usr/bin/env bash
# Run the full forecast pipeline.
# Rain, wind, and cloudbase generation run in parallel; index and cleanup follow.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

cd "$SCRIPT_DIR"

log "Starting meteo_france pipeline"

log "Generating maps (rain + wind + cloudbase in parallel)..."
$PYTHON meteo_rain.py      &
$PYTHON meteo_wind.py      &
$PYTHON meteo_cloudbase.py &
wait

log "Writing index.json..."
$PYTHON generate_index.py

log "Cleaning up expired maps..."
$PYTHON cleanup_maps.py --execute

log "Pipeline complete."
