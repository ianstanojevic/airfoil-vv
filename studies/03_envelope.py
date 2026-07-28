"""Study 3 -- Where can the method be trusted, and does it know it?

Study 2 measured the disagreement with XFOIL. A single median error over a mixed
population is close to useless in practice: the question an engineer actually
asks is "for the case in front of me right now, can I use the cheap method?"

So the question here is whether the disagreement is *predictable from quantities
the solver already computes* -- its own separation location and Reynolds number --
without knowing the reference answer. If it is, the method can carry its own
error bar and refuse the cases it cannot handle.

The rule is fitted on one set of sections and tested on sections it has never
seen (leave-one-section-out), so the reported skill is out-of-sample. Fitting and
scoring on the same data would only measure how flexible the fit is.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _style import BLUE, GREEN, PURPLE, RUST, save, use_style  # noqa: E402

REPORT = Path(__file__).resolve().parents[1] / "report"
NUMERICAL_UNCERTAINTY = 0.026     # from study 1; see report/verification.json

SEP_BINS = [0.0, 0.70, 0.85, 0.95, 0.99, 1.001]
SEP_LABELS = ["<0.70", "0.70-0.85", "0.85-0.95", "0.95-0.99", "attached"]


def load() -> pd.DataFrame:
    path = REPORT / "benchmark.csv"
    if not path.exists():
        raise SystemExit("run studies/02_benchmark.py first")
    data = pd.read_csv(path)
    data["abs_rel_cd"] = data.rel_cd.abs()
    data["abs_d_cl"] = data.d_cl.abs()
    data["sep_bin"] = pd.cut(data.x_sep, SEP_BINS, labels=SEP_LABELS, right=False)
    return data


def by_separation(data: pd.DataFrame) -> pd.DataFrame:
    g = data.groupby("sep_bin", observed=True)
    return pd.DataFrame({
        "points": g.size(),
        "median_rel_cd": 100 * g.abs_rel_cd.median(),
        "p90_rel_cd": 100 * g.abs_rel_cd.quantile(0.9),
        "median_d_cl": g.abs_d_cl.median(),
    }).reset_index()


def by_reynolds(data: pd.DataFrame) -> pd.DataFrame:
    attached = data[data.x_sep >= 0.95]
    g = attached.groupby("reynolds", observed=True)
    return pd.DataFrame({
        "points": g.size(),
        "median_rel_cd": 100 * g.abs_rel_cd.median(),
        "p90_rel_cd": 100 * g.abs_rel_cd.quantile(0.9),
        "median_d_cl": g.abs_d_cl.median(),
    }).reset_index()


def self_certification(data: pd.DataFrame) -> dict:
    """Leave-one-section-out test of a rule using only self-computed quantities.

    Rule: accept a point when the predicted separation is aft of 0.95c and
    Re >= 200 000. The claim under test is that accepted points stay inside a
    stated drag band. Both the band and the acceptance are fitted on the training
    sections only and scored on the held-out one.
    """
    sections = sorted(data.airfoil_id.unique())
    rows = []
    for held_out in sections:
        train = data[data.airfoil_id != held_out]
        test = data[data.airfoil_id == held_out]

        accept_train = (train.x_sep >= 0.95) & (train.reynolds >= 200_000)
        if accept_train.sum() < 30:
            continue
        band = float(train.loc[accept_train, "abs_rel_cd"].quantile(0.9))

        accept_test = (test.x_sep >= 0.95) & (test.reynolds >= 200_000)
        n_acc = int(accept_test.sum())
        if n_acc == 0:
            continue
        inside = float((test.loc[accept_test, "abs_rel_cd"] <= band).mean())
        rows.append({
            "held_out": held_out, "band": band, "accepted": n_acc,
            "coverage": inside,
            "median_accepted": float(test.loc[accept_test, "abs_rel_cd"].median()),
            "median_rejected": float(test.loc[~accept_test, "abs_rel_cd"].median())
            if (~accept_test).any() else np.nan,
        })

    frame = pd.DataFrame(rows)
    return {
        "per_section": frame,
        "mean_band": float(frame.band.mean()),
        "mean_coverage": float(frame.coverage.mean()),
        "sections": len(frame),
        "median_accepted": float(frame.median_accepted.median()),
        "median_rejected": float(frame.median_rejected.median()),
    }


def figures(data: pd.DataFrame, sep: pd.DataFrame, re_tab: pd.DataFrame,
            cert: dict) -> None:
    import matplotlib.pyplot as plt
    use_style()

    fig, axes = plt.subplots(1, 3, figsize=(12.4, 3.6))

    ax = axes[0]
    order = [lab for lab in SEP_LABELS if lab in set(sep.sep_bin)]
    sub = sep.set_index("sep_bin").loc[order]
    ax.bar(range(len(sub)), sub.median_rel_cd, color=BLUE, width=0.6, label="median")
    ax.plot(range(len(sub)), sub.p90_rel_cd, "o", color=RUST, ms=5, label="90th pct")
    ax.set_xticks(range(len(sub)))
    ax.set_xticklabels(sub.index, rotation=20, ha="right")
    ax.set_xlabel("predicted separation point $x_{sep}/c$")
    ax.set_ylabel(r"$|\Delta C_d| / C_d$  [%]")
    ax.set_title("Drag error against own separation prediction")
    ax.grid(True, axis="y", alpha=0.5)
    ax.legend()

    ax = axes[1]
    ax.plot(re_tab.reynolds, re_tab.median_rel_cd, "o-", color=BLUE, ms=5, label="median")
    ax.plot(re_tab.reynolds, re_tab.p90_rel_cd, "s--", color=RUST, ms=4.5, label="90th pct")
    ax.axhline(100 * NUMERICAL_UNCERTAINTY, color=GREEN, ls=":", lw=1.4)
    ax.text(re_tab.reynolds.iloc[0], 100 * NUMERICAL_UNCERTAINTY * 1.08,
            "own numerical uncertainty", fontsize=8, color=GREEN)
    ax.set_xscale("log")
    ax.set_xlabel("Reynolds number")
    ax.set_ylabel(r"$|\Delta C_d| / C_d$  [%]")
    ax.set_title("Attached flow only, by Reynolds number")
    ax.grid(True, which="both", alpha=0.5)
    ax.legend()

    ax = axes[2]
    accepted = data[(data.x_sep >= 0.95) & (data.reynolds >= 200_000)]
    rejected = data.drop(accepted.index)
    bins = np.linspace(0, 1.0, 41)
    ax.hist(rejected.abs_rel_cd.clip(0, 1), bins=bins, color="#c9c9c9",
            label=f"rejected (n={len(rejected):,})")
    ax.hist(accepted.abs_rel_cd.clip(0, 1), bins=bins, color=BLUE,
            label=f"accepted (n={len(accepted):,})")
    ax.axvline(cert["mean_band"], color=PURPLE, ls="--", lw=1.4)
    ax.text(cert["mean_band"] * 1.05, ax.get_ylim()[1] * 0.82,
            f"held-out band\n{100*cert['mean_band']:.0f} %", fontsize=8, color=PURPLE)
    ax.set_xlabel(r"$|\Delta C_d| / C_d$")
    ax.set_ylabel("comparison points")
    ax.set_title("Self-certification splits the population")
    ax.grid(True, axis="y", alpha=0.5)
    ax.legend()

    save(fig, "fig2_envelope.png")


def main() -> None:
    print("Study 3 -- validity envelope and self-certification\n")
    data = load()
    sep = by_separation(data)
    re_tab = by_reynolds(data)
    cert = self_certification(data)

    print("Drag error against the method's own separation prediction")
    print(sep.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print("\nAttached flow only, by Reynolds number")
    print(re_tab.to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    print(f"\nSelf-certification, leave-one-section-out over {cert['sections']} sections")
    print(f"  accept when x_sep >= 0.95c and Re >= 2e5")
    print(f"  drag band (90th pct on training sections)  {100*cert['mean_band']:.1f} %")
    print(f"  held-out coverage inside that band         {100*cert['mean_coverage']:.1f} %")
    print(f"  median error, accepted points              {100*cert['median_accepted']:.1f} %")
    print(f"  median error, rejected points              {100*cert['median_rejected']:.1f} %")

    figures(data, sep, re_tab, cert)
    summary = {
        "by_separation": sep.to_dict("records"),
        "by_reynolds": re_tab.to_dict("records"),
        "self_certification": {k: v for k, v in cert.items() if k != "per_section"},
        "numerical_uncertainty": NUMERICAL_UNCERTAINTY,
        "total_points": int(len(data)),
        "sections": int(data.airfoil_id.nunique()),
    }
    (REPORT / "envelope.json").write_text(json.dumps(summary, indent=1, default=float))
    print("  wrote report/envelope.json")


if __name__ == "__main__":
    main()
