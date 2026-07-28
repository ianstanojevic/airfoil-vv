"""High-level analysis API: geometry in, polar out."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Sequence

import numpy as np

from .boundary_layer import BLResult, boundary_layer
from .geometry import Airfoil, decompose, rebuild
from .panel import PanelSolution, alpha_zero_lift, evaluate, solve_panels

__all__ = ["OperatingPoint", "Section", "analyse", "polar"]


@dataclass(frozen=True)
class OperatingPoint:
    alpha: float
    reynolds: float
    cl: float
    cd: float
    cm: float
    cd_pressure: float          # inviscid; d'Alembert says this should be ~0
    cp_min: float
    x_transition_upper: float | None
    x_transition_lower: float | None
    x_separation_upper: float | None
    x_separation_lower: float | None
    separated: bool

    @property
    def ld(self) -> float:
        return self.cl / self.cd if self.cd > 0 else float("nan")

    def as_dict(self) -> dict:
        d = asdict(self)
        d["ld"] = self.ld
        return d


class Section:
    """A re-panelled airfoil, solved once, then swept over alpha cheaply.

    The panel system is solved for two unit freestream directions at construction
    time; every subsequent angle of attack is a superposition, so a 100-point
    polar costs one factorisation, not one hundred.
    """

    def __init__(self, airfoil: Airfoil, n_panels: int = 200,
                 camber_scale: float = 1.0, thickness_scale: float = 1.0):
        if n_panels % 2:
            n_panels += 1
        self.airfoil = airfoil
        self.n_panels = n_panels
        self.decomposition = decompose(airfoil.xy, n_panels // 2)
        self.nodes = rebuild(self.decomposition, camber_scale, thickness_scale)
        self.solution: PanelSolution = solve_panels(self.nodes)

    @property
    def alpha_zero_lift(self) -> float:
        return alpha_zero_lift(self.solution)

    def at(self, alpha: float, reynolds: float) -> OperatingPoint:
        forces = evaluate(self.solution, alpha)
        bl: BLResult = boundary_layer(self.solution, forces, reynolds)
        return OperatingPoint(
            alpha=float(alpha), reynolds=float(reynolds),
            cl=forces.cl, cd=bl.cd, cm=forces.cm_quarter,
            cd_pressure=forces.cd_pressure, cp_min=forces.cp_min,
            x_transition_upper=bl.upper.x_transition,
            x_transition_lower=bl.lower.x_transition,
            x_separation_upper=bl.upper.x_separation,
            x_separation_lower=bl.lower.x_separation,
            separated=bl.separated,
        )

    def sweep(self, alphas: Iterable[float], reynolds: float) -> list[OperatingPoint]:
        return [self.at(a, reynolds) for a in alphas]


def analyse(airfoil: Airfoil, alpha: float, reynolds: float,
            n_panels: int = 200) -> OperatingPoint:
    """One-shot convenience wrapper. Use ``Section`` for sweeps."""
    return Section(airfoil, n_panels).at(alpha, reynolds)


def polar(airfoil: Airfoil, alphas: Sequence[float], reynolds: float,
          n_panels: int = 200) -> list[OperatingPoint]:
    return Section(airfoil, n_panels).sweep(alphas, reynolds)
