"""Airfoil coordinates and reference XFOIL polars from airfoiltools.com.

The site serves HTTP only and sets no CORS headers, so everything is fetched
here and cached on disk. Cached files are never re-requested, which keeps the
study reproducible and keeps load off a free community resource.
"""

from __future__ import annotations

import io
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .geometry import Airfoil, parse_dat

__all__ = ["REYNOLDS_AVAILABLE", "cache_dir", "airfoil_index", "load_airfoil",
           "load_xfoil_polar", "PolarKey"]

BASE = "http://airfoiltools.com"
_UA = "airfoil-vv/1.0 (engineering study; contact via github.com/ianstanojevic)"
_DELAY = 0.5

# The Reynolds numbers airfoiltools publishes XFOIL polars for.
REYNOLDS_AVAILABLE = (50_000, 100_000, 200_000, 500_000, 1_000_000)

_CACHE = Path(__file__).resolve().parents[2] / "data_cache"


def cache_dir() -> Path:
    _CACHE.mkdir(exist_ok=True)
    return _CACHE


@dataclass(frozen=True)
class PolarKey:
    airfoil_id: str
    reynolds: int
    ncrit: int = 9

    @property
    def key(self) -> str:
        return f"xf-{self.airfoil_id}-{self.reynolds}"


def _fetch(url: str, cache_name: str) -> str | None:
    path = cache_dir() / cache_name
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    path.write_text(text, encoding="utf-8")
    time.sleep(_DELAY)
    return text


def airfoil_index() -> list[str]:
    """Every airfoil id in the database, in the site's own order."""
    html = _fetch(f"{BASE}/search/airfoils", "_index.html")
    if html is None:
        raise RuntimeError("could not reach airfoiltools.com")
    seen, ids = set(), []
    for m in re.finditer(r"airfoil=([a-z0-9][a-z0-9\-.]*)", html):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            ids.append(m.group(1))
    return ids


def load_airfoil(airfoil_id: str) -> Airfoil:
    """Coordinates for one airfoil, normalised to Selig order."""
    text = _fetch(f"{BASE}/airfoil/seligdatfile?airfoil={airfoil_id}",
                  f"{airfoil_id}.dat")
    if text is None:
        raise RuntimeError(f"could not fetch coordinates for {airfoil_id}")
    return parse_dat(text)


def load_xfoil_polar(airfoil_id: str, reynolds: int) -> pd.DataFrame | None:
    """Reference XFOIL polar (Ncrit 9, M 0), or None if the site has none.

    Columns: alpha, cl, cd, cdp, cm, xtr_top, xtr_bot.
    """
    key = PolarKey(airfoil_id, reynolds).key
    text = _fetch(f"{BASE}/polar/csv?polar={key}", f"{key}.csv")
    if text is None:
        return None

    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("Alpha,")), None)
    if start is None:
        return None
    df = pd.read_csv(io.StringIO("\n".join(lines[start:])))
    df.columns = ["alpha", "cl", "cd", "cdp", "cm", "xtr_top", "xtr_bot"]
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    if df.empty:
        return None
    df["airfoil_id"] = airfoil_id
    df["reynolds"] = reynolds
    return df.sort_values("alpha").reset_index(drop=True)
