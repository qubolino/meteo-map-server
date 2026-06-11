#!/usr/bin/env python3
"""Write index.json into generated_maps/ so enroute knows what files are available."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
import config

FILENAME_RE = re.compile(
    r"^(rain|cloudbase|wind)_map_[\d.hPa_T:Z-]+\.png$"
)


def generate_index(maps_dir: Path = config.MAPS_DIR,
                   reference_time: str | None = None,
                   file_reference_times: dict[str, str] | None = None):
    """
    Write index.json.

    Args:
        reference_time: ISO-8601 UTC string for the model run that produced
                        the current batch (e.g. "2026-06-11T12:00:00Z").
        file_reference_times: mapping of filename → reference_time for files
                              whose origin differs from the batch default.
    """
    maps_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        p.name for p in maps_dir.glob("*.png")
        if FILENAME_RE.match(p.name)
    )

    file_meta = {}
    for fname in files:
        rt = (file_reference_times or {}).get(fname) or reference_time
        if rt:
            file_meta[fname] = {"reference_time": rt}

    index = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "layers": config.LAYER_META,
        "files": files,
    }
    if file_meta:
        index["file_meta"] = file_meta
    if reference_time:
        index["reference_time"] = reference_time

    index_path = maps_dir / "index.json"
    tmp = index_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(index, indent=2))
    tmp.rename(index_path)
    print(f"index.json written: {len(files)} files", flush=True)


if __name__ == "__main__":
    generate_index()
