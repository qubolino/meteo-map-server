#!/usr/bin/env bash
# Run the full forecast pipeline sequentially.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

cd "$SCRIPT_DIR"

log "Starting meteo_france pipeline"

log "Generating rain maps (SP1)..."
$PYTHON meteo_rain.py

log "Generating wind and cloudbase maps (IP1)..."
$PYTHON meteo_ip1.py

log "Writing index.json..."
$PYTHON generate_index.py

log "Cleaning up expired maps..."
$PYTHON cleanup_maps.py --execute

log "Pipeline complete."
