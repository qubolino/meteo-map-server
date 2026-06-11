#!/usr/bin/env bash
# Run the full forecast pipeline.
# Rain (SP1) and IP1 (wind + cloudbase) run in parallel, each using 2 worker
# processes — 4 workers total, matching the Pi 4's quad-core layout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

cd "$SCRIPT_DIR"

log "Starting meteo_france pipeline"

log "Generating maps (SP1 rain + IP1 wind/cloudbase in parallel)..."
$PYTHON meteo_rain.py &
$PYTHON meteo_ip1.py  &
wait

log "Writing index.json..."
$PYTHON generate_index.py

log "Cleaning up expired maps..."
$PYTHON cleanup_maps.py --execute

log "Pipeline complete."
