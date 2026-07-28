"""Study 2 -- Benchmark against XFOIL over a population of sections.

This is a code-to-code comparison, not validation in the ASME V&V 20 sense: the
reference is another code, so agreement bounds *consistency with an accepted
method*, not agreement with reality. The distinction matters and is kept
throughout. The handful of true experimental comparisons live in
``tests/test_physics.py::TestAgainstMeasuredData``.

XFOIL is the right reference anyway. It solves the same physics -- panel method
plus integral boundary layer -- with one crucial difference: its coupling is
two-way. Displacement thickness is fed back into the inviscid problem and the two
are iterated to convergence. Everything measured here is therefore an estimate of
what the one-way approximation costs.

Reference data: XFOIL polars published by airfoiltools.com at Ncrit 9, M 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from panelbl import Section  # noqa: E402
from panelbl.data import load_airfoil, load_xfoil_polar  # noqa: E402

REPORT = Path(__file__).resolve().parents[1] / "report"
PANELS = 320                       # justified in study 1
REYNOLDS = (100_000, 200_000, 500_000, 1_000_000)
ALPHA_RANGE = (-6.0, 16.0)
ALPHA_STEP = 0.5

# A deliberately mixed population: symmetric to strongly cambered, thin to thick,
# conventional to laminar-flow to high-lift. A benchmark on NACA 4-digit sections
# alone would flatter the method.
AIRFOILS = [
    "naca0006-il", "n0009sm-il", "n0012-il", "naca0015-il", "naca0018-il",
    "naca1408-il", "naca1412-il", "naca2408-il", "naca2412-il", "naca2415-il",
    "naca4412-il", "naca4415-il", "n6409-il", "naca23012-il",
    "naca63206-il", "n63412-il", "n64108-il", "naca65209-il",
    "clarky-il", "e387-il", "e423-il", "s1223-il", "sd7037-il", "rg15-il",
    "mh32-il", "ag35-il", "fx63137-il", "goe398-il",
]


def compare_one(airfoil_id: str, reynolds: int) -> pd.DataFrame | None:
    reference = load_xfoil_polar(airfoil_id, reynolds)
    if reference is None or len(reference) < 10:
        return None

    try:
        section = Section(load_airfoil(airfoil_id), n_panels=PANELS)
    except Exception as exc:                      # geometry we cannot re-panel
        print(f"    ! {airfoil_id}: {exc}")
        return None

    lo = max(ALPHA_RANGE[0], reference.alpha.min())
    hi = min(ALPHA_RANGE[1], reference.alpha.max())
    alphas = np.arange(lo, hi + 1e-9, ALPHA_STEP)
    if len(alphas) < 5:
        return None

    rows = []
    for alpha in alphas:
        point = section.at(float(alpha), float(reynolds))
        rows.append({
            "airfoil_id": airfoil_id, "reynolds": reynolds, "alpha": float(alpha),
            "cl": point.cl, "cd": point.cd, "cm": point.cm,
            "xtr_top": point.x_transition_upper, "xtr_bot": point.x_transition_lower,
            "x_sep_top": point.x_separation_upper, "x_sep_bot": point.x_separation_lower,
            "separated": point.separated,
        })
    mine = pd.DataFrame(rows)

    for column in ("cl", "cd", "cm", "xtr_top", "xtr_bot"):
        mine[f"{column}_ref"] = np.interp(mine.alpha, reference.alpha, reference[column])

    mine["thickness"] = 100 * section.decomposition.max_thickness
    mine["camber"] = 100 * section.decomposition.max_camber
    # x_sep is None while attached; 1.0 keeps it usable as a continuous predictor
    mine["x_sep"] = mine[["x_sep_top", "x_sep_bot"]].min(axis=1).fillna(1.0)

    mine["d_cl"] = mine.cl - mine.cl_ref
    mine["d_cd"] = mine.cd - mine.cd_ref
    mine["rel_cd"] = mine.d_cd / mine.cd_ref
    mine["d_xtr_top"] = mine.xtr_top - mine.xtr_top_ref
    return mine


def main() -> None:
    print("Study 2 -- benchmark against XFOIL\n")
    print(f"  {len(AIRFOILS)} sections x {len(REYNOLDS)} Reynolds numbers, "
          f"N = {PANELS} panels")

    frames = []
    for i, airfoil_id in enumerate(AIRFOILS, 1):
        got = 0
        for reynolds in REYNOLDS:
            frame = compare_one(airfoil_id, reynolds)
            if frame is not None:
                frames.append(frame)
                got += 1
        print(f"  [{i:>2}/{len(AIRFOILS)}] {airfoil_id:<16} {got}/{len(REYNOLDS)} polars")

    if not frames:
        raise SystemExit("no reference polars retrieved")

    data = pd.concat(frames, ignore_index=True)
    REPORT.mkdir(exist_ok=True)
    out = REPORT / "benchmark.csv"
    data.to_csv(out, index=False)

    print(f"\n  {len(data):,} comparison points from "
          f"{data.airfoil_id.nunique()} sections")
    print(f"  wrote {out.relative_to(REPORT.parent)}")

    attached = data[data.x_sep >= 0.95]
    print("\n  attached flow only (separation aft of 0.95c):")
    print(f"    points                {len(attached):,}")
    print(f"    median |dCl|          {attached.d_cl.abs().median():.4f}")
    print(f"    median |dCd|/Cd       {100 * attached.rel_cd.abs().median():.1f} %")
    print(f"    90th pct |dCd|/Cd     {100 * attached.rel_cd.abs().quantile(0.9):.1f} %")
    print("\n  all points:")
    print(f"    median |dCl|          {data.d_cl.abs().median():.4f}")
    print(f"    median |dCd|/Cd       {100 * data.rel_cd.abs().median():.1f} %")


if __name__ == "__main__":
    main()
