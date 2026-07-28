"""Integral boundary layer marched on the inviscid surface velocity.

Potential flow gives exactly zero drag (d'Alembert). The drag here comes from a
boundary layer solved *on top of* the inviscid solution:

    laminar     Thwaites, closed form
    transition  Michel's criterion, or forced at laminar separation
    turbulent   Head's entrainment method, Ludwieg-Tillmann skin friction
    drag        Squire-Young applied to the momentum thickness

The coupling is ONE-WAY: displacement thickness is never fed back into the
panel solution. XFOIL iterates that coupling, and the difference is the whole
subject of the validation study in ``studies/``. Once the flow separates, the
premise of every formula above is gone -- ``BLResult.separated`` flags it and
the reported drag should be treated as invalid, not merely uncertain.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["SurfaceBL", "BLResult", "boundary_layer", "NU_AIR_15C"]

NU_AIR_15C = 1.46e-5  # kinematic viscosity of air at 15 C, m^2/s

# Squire-Young is evaluated here rather than at the trailing edge. With a sharp
# TE the potential-flow edge velocity goes to zero over the last few panels,
# which would drive the formula to Cd -> 0. The relation is meant to be
# insensitive to station choice inside attached flow, so any station clear of
# the TE singularity works; 0.95c is the convention used throughout.
_SQUIRE_YOUNG_STATION = 0.95

# Separation right at the trailing edge is normal and harmless. Only once it has
# moved forward past this station is the section genuinely heading for stall.
_STALL_WARNING_STATION = 0.85


@dataclass(frozen=True)
class SurfaceBL:
    """Boundary layer state along one surface, from stagnation to trailing edge."""

    x: np.ndarray              # chordwise station of each march point
    s: np.ndarray              # arc length from the stagnation point
    ue: np.ndarray             # edge velocity / V_inf
    theta: np.ndarray          # momentum thickness / chord
    shape: np.ndarray          # shape factor H
    cd: float                  # Squire-Young profile drag from this surface
    x_transition: float | None
    x_separation: float | None
    i_transition: int          # index into the parent panel arrays, -1 if none
    i_separation: int


@dataclass(frozen=True)
class BLResult:
    cd: float
    upper: SurfaceBL
    lower: SurfaceBL
    separated: bool
    x_stagnation: float

    @property
    def x_separation_min(self) -> float:
        """Most forward separation point over both surfaces; 1.0 if attached."""
        xs = [s.x_separation for s in (self.upper, self.lower) if s.x_separation is not None]
        return min(xs) if xs else 1.0


def _thwaites_shape(lam: np.ndarray | float):
    lam = np.clip(lam, -0.0999, 0.25)
    return np.where(lam > 0,
                    2.61 - 3.75 * lam + 5.24 * lam**2,
                    2.088 + 0.0731 / (lam + 0.14))


def _h1_from_h(h: float) -> float:
    if h <= 1.6:
        return 3.3 + 0.8234 * max(h - 1.1, 0.01) ** -1.287
    return 3.3 + 1.5501 * max(h - 0.6778, 0.01) ** -3.064


# Head's entrainment shape factor is H1 = 3.3 + (positive term), so the
# correlation is only defined for H1 > 3.3. Clamping below that -- 3.05 is the
# value that appears in several published listings -- raises a negative base to a
# fractional power and silently yields NaN, which then propagates into theta and
# out into the drag. H1 -> 3.3+ means H -> infinity anyway, and the H > 2.4
# separation test fires long before, so the floor belongs just above 3.3.
_H1_FLOOR = 3.32


def _h_from_h1(h1: float) -> float:
    h1 = max(h1, _H1_FLOOR)
    if h1 >= 5.3:
        return 1.1 + 0.86 * (h1 - 3.3) ** -0.777
    return 0.6778 + 1.1536 * (h1 - 3.3) ** -0.326


def _michel_margin(re, u, theta, s):
    """Positive once Michel's transition criterion has been crossed."""
    re_x = re * u * s
    if re_x <= 1e4:
        return -1.0
    return re * u * theta - 1.174 * (1 + 22400 / re_x) * re_x**0.46


def _crossing_fraction(prev: float, curr: float) -> float:
    """Where between two stations a monotone quantity crosses zero, in [0, 1]."""
    if curr == prev:
        return 1.0
    return float(np.clip(-prev / (curr - prev), 0.0, 1.0))


def _march(x, s, ue, re):
    """March one surface.

    Transition and separation are located *between* stations by linear
    interpolation of the criterion, not snapped to the nearest station. Snapping
    quantises both to the panel spacing, which makes Cd change in steps as the
    panel count is refined and destroys monotone grid convergence -- see
    ``studies/01_verification.py``.

    Returns (theta, H, s_transition, s_separation), where the two locations are
    arc lengths, or None if they do not occur.
    """
    n = len(s)
    theta = np.zeros(n)
    shape = np.zeros(n)
    s_tr = s_sep = None

    dueds = np.gradient(ue, s)

    # Laminar: Thwaites in closed form, theta^2 = 0.45/(Re Ue^6) * int Ue^5 ds.
    # The integral starts at the stagnation point (s = 0, Ue = 0), which lies
    # s[0] ahead of the first control point.
    integral = 0.5 * ue[0] ** 5 * s[0]
    theta[0] = np.sqrt(0.45 * integral / (re * max(ue[0], 1e-6) ** 6))
    shape[0] = 2.24
    lam_prev = 0.0
    michel_prev = _michel_margin(re, max(ue[0], 1e-6), theta[0], s[0])

    k_tr = -1
    frac = 1.0
    for k in range(1, n):
        integral += 0.5 * (ue[k] ** 5 + ue[k - 1] ** 5) * (s[k] - s[k - 1])
        u = max(ue[k], 1e-6)
        theta[k] = np.sqrt(0.45 * integral / (re * u**6))
        lam = re * theta[k] ** 2 * dueds[k]
        shape[k] = float(_thwaites_shape(lam))
        michel = _michel_margin(re, u, theta[k], s[k])

        if lam < -0.09:                                  # laminar separation
            k_tr = k
            frac = _crossing_fraction(lam_prev + 0.09, lam + 0.09)
            break
        if michel > 0:                                   # Michel
            k_tr = k
            frac = _crossing_fraction(michel_prev, michel)
            break
        lam_prev, michel_prev = lam, michel

    # Turbulent: Head's entrainment method, started from the interpolated
    # transition point rather than from the station that tripped the criterion.
    if 0 <= k_tr < n:
        s_tr = float(s[k_tr - 1] + frac * (s[k_tr] - s[k_tr - 1]))
        t = float(theta[k_tr - 1] + frac * (theta[k_tr] - theta[k_tr - 1]))
        u_tr = float(ue[k_tr - 1] + frac * (ue[k_tr] - ue[k_tr - 1]))
        h = min(2.0, max(1.35, float(shape[k_tr - 1] + frac * (shape[k_tr] - shape[k_tr - 1]))))
        h1 = _h1_from_h(h)

        s_from, u_from = s_tr, u_tr
        for k in range(k_tr, n):
            ds = s[k] - s_from
            if ds > 0:
                sub = 4
                h_prev = h
                for m in range(sub):
                    u = max(u_from + (ue[k] - u_from) * (m + 0.5) / sub, 1e-6)
                    re_theta = max(200.0, re * u * t)
                    cf = 0.246 * 10 ** (-0.678 * h) * re_theta**-0.268
                    dt = cf / 2 - (h + 2) * t * dueds[k] / u
                    dh1 = (0.0306 * max(h1 - 3, 0.02) ** -0.6169 - h1 * dt) / max(t, 1e-9)
                    t = max(t + dt * ds / sub, 1e-9)
                    h1 = max(h1 + dh1 * ds / sub, _H1_FLOOR)
                    h = _h_from_h1(h1)
            else:
                h_prev = h
            theta[k], shape[k] = t, h
            if h > 2.4:                                  # turbulent separation
                f = _crossing_fraction(h_prev - 2.4, h - 2.4)
                s_sep = float(s_from + f * (s[k] - s_from))
                break
            s_from, u_from = s[k], ue[k]

    return theta, shape, s_tr, s_sep


def _stations(sol, vt, i0, direction, x_stag, y_stag):
    """Arc length, edge velocity and panel indices along one surface."""
    idx = (np.arange(i0, sol.n_panels) if direction > 0
           else np.arange(i0, -1, -1))
    px = np.concatenate([[x_stag], sol.xc[idx][:-1]])
    py = np.concatenate([[y_stag], sol.yc[idx][:-1]])
    step = np.hypot(sol.xc[idx] - px, sol.yc[idx] - py)
    return sol.xc[idx], np.cumsum(step), np.abs(vt[idx]), idx


def boundary_layer(sol, forces, reynolds: float) -> BLResult:
    """Solve the boundary layer on both surfaces at one operating point."""
    vt = forces.vt
    n = sol.n_panels

    # Stagnation point: the sign change in tangential velocity nearest the LE.
    crossings = np.flatnonzero(vt[:-1] * vt[1:] < 0) + 1
    if len(crossings):
        dist = np.hypot(sol.xc[crossings], sol.yc[crossings])
        i_stag = int(crossings[np.argmin(dist)])
    else:
        i_stag = n // 2
    i_stag = int(np.clip(i_stag, 1, n - 2))

    # It lies *between* control points i_stag-1 and i_stag, so interpolate it and
    # let the two marches start on opposite sides. Sharing a station puts one
    # march on the wrong side of stagnation, where dUe/ds has the wrong sign, and
    # the lower-surface march can collapse to zero drag.
    va, vb = abs(vt[i_stag - 1]), abs(vt[i_stag])
    f = va / (va + vb) if va + vb > 1e-12 else 0.5
    x_stag = sol.xc[i_stag - 1] + f * (sol.xc[i_stag] - sol.xc[i_stag - 1])
    y_stag = sol.yc[i_stag - 1] + f * (sol.yc[i_stag] - sol.yc[i_stag - 1])

    surfaces = {}
    total_cd = 0.0
    separated = False
    for name, direction, start in (("upper", +1, i_stag), ("lower", -1, i_stag - 1)):
        x, s, ue, idx = _stations(sol, vt, start, direction, x_stag, y_stag)
        theta, shape, s_tr, s_sep = _march(x, s, ue, reynolds)

        # The march returns arc lengths; map them to chordwise stations and to
        # the nearest panel index (the latter only for drawing markers).
        def to_x(s_value):
            return None if s_value is None else float(np.interp(s_value, s, x))

        def to_index(s_value):
            return -1 if s_value is None else int(idx[int(np.argmin(np.abs(s - s_value)))])

        x_tr, x_sep = to_x(s_tr), to_x(s_sep)

        k_end = len(s) - 1 if s_sep is None else int(np.searchsorted(s, s_sep))
        usable = np.flatnonzero((x[: k_end + 1] <= _SQUIRE_YOUNG_STATION)
                                & (theta[: k_end + 1] > 0))
        if len(usable):
            k = int(usable[-1])
            cd = float(2 * theta[k] * max(ue[k], 1e-6) ** ((shape[k] + 5) / 2))
        else:
            cd = 0.0

        if x_sep is not None and x_sep < _STALL_WARNING_STATION:
            separated = True
        total_cd += cd

        surfaces[name] = SurfaceBL(
            x=x, s=s, ue=ue, theta=theta, shape=shape, cd=cd,
            x_transition=x_tr, x_separation=x_sep,
            i_transition=to_index(s_tr), i_separation=to_index(s_sep),
        )

    return BLResult(cd=total_cd, separated=separated, x_stagnation=float(x_stag),
                    **surfaces)
