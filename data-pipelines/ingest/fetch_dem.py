"""Fetch a DEM tile for the pilot AOI.

Primary source: Copernicus DEM GLO-30 on AWS Open Data (no key) — see ADR-0006. Many
dev/CI environments are offline, so `--fallback-fixture` (auto on any fetch failure)
copies the committed clipped fixture instead, keeping the pipeline and tests runnable.

Usage:
    python -m ingest.fetch_dem --lat 28 --lon 83 --out /tmp/dem.tif
    python -m ingest.fetch_dem --fallback-fixture --out /tmp/dem.tif
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# Copernicus DEM public tile layout on AWS Open Data. GLO-30 (~30 m) for the focused
# pilot; GLO-90 (~90 m, ~9x smaller) for national coverage where 30 m would be ~2 GB.
COP_DEM_BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
COP_DEM_BASE_90 = "https://copernicus-dem-90m.s3.amazonaws.com"

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "tests"
    / "fixtures"
    / "dem"
    / "nepal_aoi_clip_glo30.tif"
)


def tile_url(lat: int, lon: int, resolution: int = 30) -> str:
    ns = f"N{abs(lat):02d}" if lat >= 0 else f"S{abs(lat):02d}"
    ew = f"E{abs(lon):03d}" if lon >= 0 else f"W{abs(lon):03d}"
    # The COG name encodes the grid spacing: "10" for GLO-30, "30" for GLO-90.
    code = "30" if resolution == 90 else "10"
    base = COP_DEM_BASE_90 if resolution == 90 else COP_DEM_BASE
    name = f"Copernicus_DSM_COG_{code}_{ns}_00_{ew}_00_DEM"
    return f"{base}/{name}/{name}.tif"


def try_fetch_tile(lat: int, lon: int, out: Path, resolution: int = 90) -> Path | None:
    """Download one tile; return None on any failure (NO fixture fallback).

    Used by the national seed, where a missing tile must be skipped, not replaced by the
    small pilot fixture (which would corrupt the mosaic).
    """
    try:
        import requests

        url = tile_url(lat, lon, resolution)
        resp = requests.get(url, timeout=60, stream=True)
        if resp.status_code != 200:
            print(f"fetch_dem: skip {url} (HTTP {resp.status_code})")
            return None
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as handle:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                handle.write(chunk)
        return out
    except Exception as exc:  # offline, DNS, timeout, etc.
        print(f"fetch_dem: skip N{lat} E{lon} ({type(exc).__name__})")
        return None


def _use_fixture(out: Path, reason: str) -> Path:
    print(f"fetch_dem: falling back to committed fixture ({reason}).")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE, out)
    return out


def fetch(
    lat: int, lon: int, out: Path, fallback_fixture: bool = False, resolution: int = 30
) -> Path:
    if fallback_fixture:
        return _use_fixture(out, "requested")
    try:
        import requests

        url = tile_url(lat, lon, resolution)
        print(f"fetch_dem: GET {url}")
        resp = requests.get(url, timeout=30, stream=True)
        if resp.status_code != 200:
            return _use_fixture(out, f"HTTP {resp.status_code}")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as handle:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                handle.write(chunk)
        print(f"fetch_dem: wrote {out}")
        return out
    except Exception as exc:  # offline, DNS, timeout, etc.
        return _use_fixture(out, f"{type(exc).__name__}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a Copernicus GLO-30 DEM tile")
    parser.add_argument("--lat", type=int, default=28, help="tile SW latitude")
    parser.add_argument("--lon", type=int, default=83, help="tile SW longitude")
    parser.add_argument("--out", default="/tmp/terrabean_dem.tif")
    parser.add_argument("--fallback-fixture", action="store_true")
    args = parser.parse_args()
    fetch(args.lat, args.lon, Path(args.out), fallback_fixture=args.fallback_fixture)


if __name__ == "__main__":
    main()
