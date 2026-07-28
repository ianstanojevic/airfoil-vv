"""Airfoil geometry: file parsing, normalisation, re-panelling, decomposition.

The one non-obvious choice here is that surface splines are built in ξ = √x
rather than x. Near the leading edge an airfoil surface behaves as y ~ √x, which
a cubic spline in x fits poorly: on a 35-point coordinate file the error reaches
~0.006c right at the nose, which is exactly where the suction peak sits. In √x
the curve is nearly straight at the nose and the error halves. See
``tests/test_geometry.py::test_sqrt_spline_beats_linear_spline``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.interpolate import CubicSpline

__all__ = [
    "Airfoil",
    "Decomposition",
    "JoukowskiSection",
    "parse_dat",
    "normalise",
    "split_surfaces",
    "surface_spline",
    "decompose",
    "rebuild",
    "naca4",
    "joukowski",
]


@dataclass(frozen=True)
class Airfoil:
    """Coordinates in Selig order: TE -> upper -> LE -> lower -> TE."""

    name: str
    xy: np.ndarray  # (n, 2), normalised: LE at origin, chord 1, chord line on x

    @property
    def n_points(self) -> int:
        return len(self.xy)


@dataclass(frozen=True)
class Decomposition:
    """Camber line and thickness distribution on cosine-spaced stations.

    Vertical convention (thickness measured along y, as in XFOIL's GDES), which
    makes ``rebuild(dec, 1.0, 1.0)`` reproduce the input surfaces exactly.
    """

    x: np.ndarray
    camber: np.ndarray
    thickness: np.ndarray

    @property
    def max_thickness(self) -> float:
        return float(self.thickness.max())

    @property
    def max_camber(self) -> float:
        return float(np.abs(self.camber).max())


def parse_dat(text: str) -> Airfoil:
    """Read a Selig or Lednicer coordinate file.

    Lednicer files list the two surfaces separately from the leading edge, often
    behind a header line holding the two point counts. Selig files run in one
    sweep from the trailing edge. Both are normalised to Selig order here.
    """
    name = ""
    nums: list[tuple[float, float]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.replace(",", " ").split()
        if len(parts) >= 2:
            try:
                nums.append((float(parts[0]), float(parts[1])))
                continue
            except ValueError:
                pass
        if not name:
            name = line
    if len(nums) < 20:
        raise ValueError(f"only {len(nums)} coordinate pairs found")

    counts = None
    if abs(nums[0][0]) > 1.5 or abs(nums[0][1]) > 1.5:
        counts = (int(round(nums[0][0])), int(round(nums[0][1])))
        nums = nums[1:]

    if counts is not None or nums[0][0] < 0.5:  # Lednicer
        if counts is not None and counts[0] + counts[1] <= len(nums):
            split = counts[0]
        else:
            split = len(nums) // 2
            for i in range(1, len(nums)):
                if nums[i][0] < nums[i - 1][0] and nums[i][0] < 0.15:
                    split = i
                    break
        upper, lower = nums[:split], nums[split:]
        if not upper or not lower:
            raise ValueError("could not split Lednicer surfaces")
        pts = list(reversed(upper)) + lower
    else:
        pts = nums

    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
            clean.append(p)

    return Airfoil(name or "unnamed", normalise(np.asarray(clean, dtype=float)))


def normalise(xy: np.ndarray) -> np.ndarray:
    """Put the leading edge at the origin, the chord on the x axis, chord = 1.

    The leading edge is taken as the point furthest from the trailing-edge
    midpoint, which is robust for cambered and reflexed sections alike.
    """
    te = 0.5 * (xy[0] + xy[-1])
    le_idx = int(np.argmax(np.sum((xy - te) ** 2, axis=1)))
    le = xy[le_idx]
    d = te - le
    chord = float(np.hypot(*d))
    if chord < 1e-9:
        raise ValueError("degenerate chord")
    ca, sa = d[0] / chord, d[1] / chord
    u = xy - le
    out = np.empty_like(u)
    out[:, 0] = (u[:, 0] * ca + u[:, 1] * sa) / chord
    out[:, 1] = (-u[:, 0] * sa + u[:, 1] * ca) / chord
    return out


def split_surfaces(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split into (upper, lower), each with strictly increasing x.

    The leading edge is pinned to x = 0. Points that land numerically ahead of
    it -- which happens when thickness is applied normal to a camber line with a
    steep nose -- are dropped by the monotonicity filter.
    """
    le_idx = int(np.argmin(xy[:, 0]))

    def monotone(arr: np.ndarray) -> np.ndarray:
        out = [(0.0, float(arr[0, 1]))]
        for x, y in arr[1:]:
            if x > out[-1][0] + 1e-7:
                out.append((float(x), float(y)))
        return np.asarray(out)

    upper = monotone(xy[: le_idx + 1][::-1])
    lower = monotone(xy[le_idx:])
    return upper, lower


def surface_spline(surface: np.ndarray) -> CubicSpline:
    """Natural cubic spline of one surface, parameterised in √x.

    Returns a spline in ξ = √x; evaluate with ``spl(np.sqrt(x))``.
    """
    xi = np.sqrt(np.clip(surface[:, 0], 0.0, None))
    return CubicSpline(xi, surface[:, 1], bc_type="natural")


def decompose(xy: np.ndarray, n: int = 80) -> Decomposition:
    """Camber and thickness on ``n + 1`` cosine-spaced stations."""
    upper, lower = split_surfaces(xy)
    su, sl = surface_spline(upper), surface_spline(lower)

    x = 0.5 * (1.0 - np.cos(np.pi * np.arange(n + 1) / n))
    xi = np.sqrt(x)
    yu, yl = su(xi), sl(xi)
    yu[0] = yl[0] = 0.0  # the leading edge is pinned

    return Decomposition(x, 0.5 * (yu + yl), np.clip(yu - yl, 0.0, None))


def rebuild(dec: Decomposition, camber_scale: float = 1.0,
            thickness_scale: float = 1.0) -> np.ndarray:
    """Panel nodes in CLOCKWISE order: TE -> lower -> LE -> upper -> TE.

    Clockwise means "left of travel" is the outward normal, which is what the
    panel solver assumes. The trailing edge is closed to a sharp point; a blunt
    base panel makes the linear-vortex system ill-conditioned, and for the
    sections used here the gap is under 0.3 % of chord.

    Returns ``(2n + 1, 2)`` with ``nodes[0] == nodes[-1]``.
    """
    c = camber_scale * dec.camber
    t = thickness_scale * dec.thickness
    yu, yl = c + 0.5 * t, c - 0.5 * t
    y_te = 0.5 * (yu[-1] + yl[-1])
    yu[-1] = yl[-1] = y_te

    x = dec.x
    nodes = np.empty((2 * len(x) - 1, 2))
    nodes[: len(x), 0] = x[::-1]
    nodes[: len(x), 1] = yl[::-1]
    nodes[len(x):, 0] = x[1:]
    nodes[len(x):, 1] = yu[1:]
    return nodes


@dataclass(frozen=True)
class JoukowskiSection:
    """A Joukowski airfoil together with its closed-form inviscid lift.

    This is the verification benchmark. NACA 4-digit sections are unsuitable for
    measuring an observed order of convergence: their camber line is defined
    piecewise about x = p and the two parabolas match in value and slope but not
    in curvature, so the surface is C1 but not C2 and the convergence rate is
    limited by the kink rather than by the method. A Joukowski section is
    analytic everywhere and its lift is exact, so the error is known rather than
    estimated.

    Conformal map z = zeta + a^2 / zeta applied to a circle of radius R centred
    at ``centre`` and passing through zeta = a. The Kutta condition places a
    stagnation point at that image point, giving

        Gamma = 4 pi V R sin(alpha + beta),   beta = asin(y_c / R)
        Cl    = 2 Gamma / (V c)

    with alpha measured from the zeta-plane real axis. ``exact_cl`` takes the
    angle of attack in the *normalised* frame and applies the chord-line rotation
    internally.
    """

    airfoil: Airfoil
    radius: float
    centre: tuple[float, float]
    chord: float
    chord_angle: float          # rotation applied by normalise(), radians
    nodes: np.ndarray           # analytic panel nodes, clockwise, closed

    @property
    def beta(self) -> float:
        return math.asin(self.centre[1] / self.radius)

    def exact_cl(self, alpha_deg: float) -> float:
        alpha = math.radians(alpha_deg) + self.chord_angle
        gamma = 4.0 * math.pi * self.radius * math.sin(alpha + self.beta)
        return 2.0 * gamma / self.chord


def joukowski(x_centre: float = -0.09, y_centre: float = 0.06,
              a: float = 1.0, n: int = 400) -> JoukowskiSection:
    """Joukowski section with an exact lift solution.

    ``n`` is the panel count: the surface is generated analytically at exactly
    the requested resolution, so refining ``n`` refines the discretisation
    without introducing any interpolation error. ``nodes`` is ready to hand
    straight to :func:`panelbl.solve_panels`.

    Defaults give roughly 11 % thickness and 3 % camber, comparable to the NACA
    sections used elsewhere in the study.
    """
    centre = complex(x_centre, y_centre)
    radius = abs(complex(a, 0.0) - centre)
    te_angle = math.atan2(-y_centre, a - x_centre)

    def contour(m: int) -> np.ndarray:
        # Cosine-clustered about the trailing-edge image so the cusp is resolved.
        t = te_angle + np.pi * (1.0 - np.cos(np.pi * np.arange(m + 1) / m))
        z = (centre + radius * np.exp(1j * t))
        z = z + a**2 / z
        out = np.column_stack([z.real, z.imag])
        return out if out[1, 1] > out[-2, 1] else out[::-1]   # Selig: upper first

    # The chord and its inclination are properties of the section, not of the
    # sampling. Taking them from the requested resolution would make the
    # "exact" reference move with the discretisation being tested, which
    # quietly destroys the convergence measurement.
    fine = contour(200_000)
    te = 0.5 * (fine[0] + fine[-1])
    le = fine[int(np.argmax(np.sum((fine - te) ** 2, axis=1)))]
    d = te - le
    chord = float(np.hypot(*d))
    chord_angle = math.atan2(d[1], d[0])

    xy = contour(n)

    # Normalise about the *analytic* leading edge so every resolution lands in
    # the same frame; normalise() would pick its own LE from the samples.
    ca, sa = d[0] / chord, d[1] / chord
    u = xy - le
    normalised = np.column_stack([(u[:, 0] * ca + u[:, 1] * sa) / chord,
                                  (-u[:, 0] * sa + u[:, 1] * ca) / chord])
    nodes = normalised[::-1].copy()          # Selig -> clockwise
    nodes[-1] = nodes[0]                     # the cusp closes exactly

    return JoukowskiSection(
        airfoil=Airfoil("Joukowski", normalised),
        radius=radius, centre=(x_centre, y_centre),
        chord=chord, chord_angle=chord_angle, nodes=nodes,
    )


def naca4(digits: str, n: int = 200) -> Airfoil:
    """Analytic NACA 4-digit section, thickness applied normal to the camber line.

    Used as the exact reference in the geometry tests -- the coordinate files
    from the database are only ~35 points and cannot serve that role.
    """
    if len(digits) != 4 or not digits.isdigit():
        raise ValueError(f"expected 4 digits, got {digits!r}")
    m = int(digits[0]) / 100.0
    p = int(digits[1]) / 10.0
    t = int(digits[2:]) / 100.0

    x = 0.5 * (1.0 - np.cos(np.pi * np.arange(n + 1) / n))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2
                  + 0.2843 * x**3 - 0.1015 * x**4)

    yc = np.zeros_like(x)
    dyc = np.zeros_like(x)
    if m > 0 and p > 0:
        fore = x < p
        yc[fore] = m / p**2 * (2 * p * x[fore] - x[fore] ** 2)
        dyc[fore] = 2 * m / p**2 * (p - x[fore])
        aft = ~fore
        yc[aft] = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x[aft] - x[aft] ** 2)
        dyc[aft] = 2 * m / (1 - p) ** 2 * (p - x[aft])

    th = np.arctan(dyc)
    s, co = np.sin(th), np.cos(th)
    upper = np.column_stack([x - yt * s, yc + yt * co])
    lower = np.column_stack([x + yt * s, yc - yt * co])

    xy = np.vstack([upper[::-1], lower[1:]])
    return Airfoil(f"NACA {digits}", normalise(xy))
