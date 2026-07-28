"""Linear-strength vortex panel method with a trailing-edge Kutta condition.

Steady, incompressible, inviscid. Derivation for one panel running 0 -> L along
the local x axis, with counterclockwise-positive sheet strength gamma(xi) varying
linearly between the two nodes:

    u = -(1/2pi) * integral gamma(xi) * y / R^2 dxi
    v =  (1/2pi) * integral gamma(xi) * (x - xi) / R^2 dxi

Both integrals close in terms of

    A = theta2 - theta1 = atan2(y, x-L) - atan2(y, x)
    B = ln(r1 / r2)

At a panel's own control point the limit from outside is A = pi, B = 0, which
gives the classical Vt = -gamma/2 jump across a vortex sheet.

The system is solved once per geometry for freestream (1,0) and (0,1). Every
angle of attack then follows by superposition,

    gamma(alpha) = cos(alpha) * gamma_A + sin(alpha) * gamma_B

so sweeping alpha costs one dot product per station instead of a fresh solve.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["PanelSolution", "AeroForces", "solve_panels", "evaluate", "alpha_zero_lift"]

_TWO_PI = 2.0 * np.pi


@dataclass(frozen=True)
class PanelSolution:
    """Geometry-only solution; alpha enters afterwards by superposition."""

    nodes: np.ndarray      # (N+1, 2) clockwise, closed
    xc: np.ndarray         # (N,) control points
    yc: np.ndarray
    nx: np.ndarray         # (N,) outward unit normal
    ny: np.ndarray
    tx: np.ndarray         # (N,) unit tangent, direction of travel
    ty: np.ndarray
    length: np.ndarray     # (N,)
    vt_a: np.ndarray       # (N,) surface tangential velocity for freestream (1,0)
    vt_b: np.ndarray       # (N,) ... and for (0,1)
    gamma_a: np.ndarray    # (N+1,) nodal vortex strengths
    gamma_b: np.ndarray

    @property
    def n_panels(self) -> int:
        return len(self.xc)


@dataclass(frozen=True)
class AeroForces:
    alpha: float
    vt: np.ndarray
    cp: np.ndarray
    cl: float
    cm_quarter: float
    cd_pressure: float     # d'Alembert: must be ~0, so this is a solver health check
    cp_min: float
    v_max: float


def _influence(px, py, x1, y1, ct, st, L, self_panel):
    """Velocity at (px, py) per unit nodal gamma. Broadcasting-friendly.

    Returns (u1, v1, u2, v2) in GLOBAL coordinates, where subscript 1/2 is the
    contribution of the panel's first/second node.
    """
    dx, dy = px - x1, py - y1
    xp = dx * ct + dy * st
    yp = -dx * st + dy * ct

    r1 = np.maximum(np.hypot(xp, yp), 1e-12)
    r2 = np.maximum(np.hypot(xp - L, yp), 1e-12)
    A = np.arctan2(yp, xp - L) - np.arctan2(yp, xp)
    B = np.log(r1 / r2)
    # On its own control point yp is exactly zero and the sign of the limit is
    # ambiguous in floating point, so pin it to the outside branch.
    A = np.where(self_panel, np.pi, A)
    B = np.where(self_panel, 0.0, B)

    Pa = (xp * A - yp * B) / L
    Pb = (xp * B - L + yp * A) / L
    u1, u2 = -(A - Pa) / _TWO_PI, -Pa / _TWO_PI
    v1, v2 = (B - Pb) / _TWO_PI, Pb / _TWO_PI

    return (u1 * ct - v1 * st, u1 * st + v1 * ct,
            u2 * ct - v2 * st, u2 * st + v2 * ct)


def solve_panels(nodes: np.ndarray) -> PanelSolution:
    """Assemble and solve the panel system for both unit freestream directions."""
    nodes = np.asarray(nodes, dtype=float)
    n = len(nodes) - 1

    d = nodes[1:] - nodes[:-1]
    length = np.hypot(d[:, 0], d[:, 1])
    if np.any(length < 1e-12):
        raise ValueError("zero-length panel")
    tx, ty = d[:, 0] / length, d[:, 1] / length
    nx, ny = -ty, tx                       # left of travel; clockwise nodes => outward
    xc = 0.5 * (nodes[:-1, 0] + nodes[1:, 0])
    yc = 0.5 * (nodes[:-1, 1] + nodes[1:, 1])

    # (i, j): influence of panel j at control point i
    eye = np.eye(n, dtype=bool)
    u1, v1, u2, v2 = _influence(
        xc[:, None], yc[:, None],
        nodes[:-1, 0][None, :], nodes[:-1, 1][None, :],
        tx[None, :], ty[None, :], length[None, :], eye,
    )

    A = np.zeros((n + 1, n + 1))
    T = np.zeros((n, n + 1))
    normal_1 = u1 * nx[:, None] + v1 * ny[:, None]
    normal_2 = u2 * nx[:, None] + v2 * ny[:, None]
    tang_1 = u1 * tx[:, None] + v1 * ty[:, None]
    tang_2 = u2 * tx[:, None] + v2 * ty[:, None]
    idx = np.arange(n)
    np.add.at(A, (idx[:, None], idx[None, :]), normal_1)
    np.add.at(A, (idx[:, None], idx[None, :] + 1), normal_2)
    np.add.at(T, (idx[:, None], idx[None, :]), tang_1)
    np.add.at(T, (idx[:, None], idx[None, :] + 1), tang_2)

    A[n, 0] = 1.0
    A[n, n] = 1.0                          # Kutta: gamma_0 + gamma_N = 0

    rhs = np.zeros((n + 1, 2))
    rhs[:n, 0] = -nx
    rhs[:n, 1] = -ny
    gamma = np.linalg.solve(A, rhs)
    gamma_a, gamma_b = gamma[:, 0], gamma[:, 1]

    return PanelSolution(
        nodes=nodes, xc=xc, yc=yc, nx=nx, ny=ny, tx=tx, ty=ty, length=length,
        vt_a=tx + T @ gamma_a, vt_b=ty + T @ gamma_b,
        gamma_a=gamma_a, gamma_b=gamma_b,
    )


def evaluate(sol: PanelSolution, alpha_deg: float) -> AeroForces:
    """Surface pressures and integrated forces at one angle of attack."""
    a = np.radians(alpha_deg)
    ca, sa = np.cos(a), np.sin(a)

    vt = ca * sol.vt_a + sa * sol.vt_b
    cp = 1.0 - vt**2

    dfx = -cp * sol.nx * sol.length
    dfy = -cp * sol.ny * sol.length
    cx, cy = dfx.sum(), dfy.sum()
    mz = np.sum((sol.xc - 0.25) * dfy - sol.yc * dfx)

    return AeroForces(
        alpha=alpha_deg, vt=vt, cp=cp,
        cl=float(cy * ca - cx * sa),
        cm_quarter=float(-mz),             # nose-up positive
        cd_pressure=float(cx * ca + cy * sa),
        cp_min=float(cp.min()),
        v_max=float(np.abs(vt).max()),
    )


def alpha_zero_lift(sol: PanelSolution) -> float:
    """Zero-lift angle in degrees. Cl is linear in alpha here, so two points suffice."""
    c0 = evaluate(sol, 0.0).cl
    c5 = evaluate(sol, 5.0).cl
    return float(-c0 / ((c5 - c0) / 5.0))
