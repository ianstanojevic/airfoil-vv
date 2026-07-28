"""Shared figure style for the report.

The categorical palette is validated for colour-vision deficiency against a light
surface (worst adjacent pair dE 8.2 deutan, 14.7 tritan, 21.5 normal). Series are
also direct-labelled, so identity never rests on colour alone.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

FIGDIR = Path(__file__).resolve().parents[1] / "report" / "figures"

BLUE, RUST, GREEN, PURPLE = "#1F6FB8", "#B0472A", "#2E8B6B", "#8659A5"
SERIES = (BLUE, RUST, GREEN, PURPLE)
INK, MUTED, GRID = "#1a1a1a", "#5c5c5c", "#d8d8d8"


def use_style() -> None:
    mpl.rcParams.update({
        "figure.dpi": 130,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": MUTED,
        "axes.linewidth": 0.8,
        "axes.labelcolor": INK,
        "axes.titlesize": 11,
        "axes.titleweight": "medium",
        "axes.labelsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": mpl.cycler(color=list(SERIES)),
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "lines.linewidth": 1.6,
        "font.size": 9.5,
    })


def save(fig, name: str) -> Path:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    path = FIGDIR / name
    fig.savefig(path)
    plt.close(fig)
    print(f"  wrote {path.relative_to(FIGDIR.parents[1])}")
    return path
