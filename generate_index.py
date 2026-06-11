#!/usr/bin/env python3
"""Write index.json into generated_maps/ so enroute knows what files are available."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
import config

FILENAME_RE = re.compile(
    r"^(rain|cloudbase|wind)_map_[\d.hPa_T:-]+\.png$"
)


def generate_index(maps_dir: Path = config.MAPS_DIR):
    maps_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        p.name for p in maps_dir.glob("*.png")
        if FILENAME_RE.match(p.name)
    )
    index = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "files": files,
    }
    index_path = maps_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2))
    print(f"index.json written: {len(files)} files")


if __name__ == "__main__":
    generate_index()
