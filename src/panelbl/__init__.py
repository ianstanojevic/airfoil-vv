"""panelbl - a coupled panel / integral-boundary-layer airfoil solver.

The point of this package is not the solver, which is textbook. The point is the
verification and validation campaign in ``studies/``, which measures where the
method can be trusted and where it cannot.

    >>> from panelbl import naca4, Section
    >>> section = Section(naca4("2412"))
    >>> point = section.at(alpha=4.0, reynolds=1_000_000)
    >>> round(point.cl, 3), round(point.cd, 5)
    (0.723, 0.00674)
"""

from .boundary_layer import BLResult, NU_AIR_15C, SurfaceBL, boundary_layer
from .geometry import (Airfoil, Decomposition, JoukowskiSection, decompose,
                       joukowski, naca4, normalise, parse_dat, rebuild,
                       split_surfaces, surface_spline)
from .panel import (AeroForces, PanelSolution, alpha_zero_lift, evaluate,
                    solve_panels)
from .solve import OperatingPoint, Section, analyse, polar

__version__ = "1.0.0"

__all__ = [
    "Airfoil", "Decomposition", "JoukowskiSection", "parse_dat", "normalise",
    "split_surfaces", "surface_spline", "decompose", "rebuild", "naca4",
    "joukowski",
    "PanelSolution", "AeroForces", "solve_panels", "evaluate", "alpha_zero_lift",
    "SurfaceBL", "BLResult", "boundary_layer", "NU_AIR_15C",
    "OperatingPoint", "Section", "analyse", "polar",
]
