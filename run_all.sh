#!/usr/bin/env bash
# Run the full forecast pipeline: rain, wind, cloudbase, index, cleanup.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

cd "$SCRIPT_DIR"

log "Starting meteo_france pipeline"

log "Generating rain maps..."
$PYTHON meteo_rain.py

log "Generating wind maps..."
$PYTHON meteo_wind.py

log "Generating cloudbase maps..."
$PYTHON meteo_cloudbase.py

log "Writing index.json..."
$PYTHON generate_index.py

log "Cleaning up expired maps..."
$PYTHON cleanup_maps.py --execute

log "Pipeline complete."
