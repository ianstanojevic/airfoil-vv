"""Physics tests: does the solver obey the laws it claims to?

These are invariants and closed-form limits, not regression snapshots. Every
tolerance here is justified in the comment above it; none of them was widened to
make a failing test pass.
"""

from __future__ import annotations

import numpy as np
import pytest

from panelbl import (Section, alpha_zero_lift, boundary_layer, evaluate, naca4,
                     solve_panels, decompose, rebuild)


def section(digits: str, n_panels: int = 200) -> Section:
    return Section(naca4(digits, 400), n_panels=n_panels)


# Glauert's thickness correction. A thick section has a steeper lift curve than
# thin airfoil theory's 2*pi; comparing straight to 2*pi is the wrong reference
# and would make a correct solver look broken.
def thickness_factor(t_over_c: float) -> float:
    return 1.0 + 0.77 * t_over_c


class TestInviscid:
    def test_symmetric_section_has_no_lift_at_zero_alpha(self):
        assert evaluate(section("0012").solution, 0.0).cl == pytest.approx(0.0, abs=5e-3)

    def test_lift_curve_slope_matches_glauert(self):
        sol = section("0012").solution
        slope = (evaluate(sol, 5.0).cl - evaluate(sol, 0.0).cl) / np.radians(5.0)
        assert slope == pytest.approx(2 * np.pi * thickness_factor(0.12), abs=0.15)

    def test_symmetric_section_has_no_pitching_moment(self):
        assert evaluate(section("0012").solution, 5.0).cm_quarter == pytest.approx(0.0, abs=0.02)

    @pytest.mark.parametrize("digits", ["0012", "2412", "4412"])
    def test_dalembert_paradox(self, digits):
        """Inviscid pressure drag must vanish. This is the sharpest single check
        on the panel influence coefficients: a sign error anywhere breaks it."""
        assert evaluate(section(digits).solution, 5.0).cd_pressure == pytest.approx(0.0, abs=5e-3)

    def test_zero_lift_angle_matches_thin_airfoil_theory(self):
        """Thin airfoil theory: alpha_L0 = -(1/pi) * int (dyc/dx)(cos t - 1) dt.
        Computed independently from the camber line, not from the panel solve."""
        foil = naca4("2412", 400)
        dec = decompose(foil.xy, 120)
        t = (np.arange(400) + 0.5) * np.pi / 400
        x = 0.5 * (1 - np.cos(t))
        dyc = np.gradient(np.interp(x, dec.x, dec.camber), x)
        expected = np.degrees(-np.trapezoid(dyc * (np.cos(t) - 1), t) / np.pi)
        assert alpha_zero_lift(section("2412").solution) == pytest.approx(expected, abs=0.35)


class TestBoundaryLayer:
    def test_drag_is_positive_and_finite(self):
        """Guards the H1 correlation floor: H1 <= 3.3 raises a negative base to a
        fractional power and yields a silent NaN that propagates into the drag."""
        s = section("2412")
        for alpha in np.arange(-8.0, 16.1, 0.5):
            cd = s.at(alpha, 1e6).cd
            assert np.isfinite(cd), f"non-finite Cd at alpha={alpha}"
            assert cd > 0, f"non-positive Cd at alpha={alpha}"

    def test_both_surfaces_contribute_drag_when_attached(self):
        """A shared starting station between the two boundary layer marches puts
        one of them on the wrong side of stagnation and collapses its drag to
        zero. It only shows up at particular alpha/panel-count combinations, so
        this sweeps a grid of both."""
        for n_panels in (120, 160, 240, 320):
            s = section("2412", n_panels)
            for alpha in (0.0, 1.0, 2.0, 3.0, 4.0):
                bl = boundary_layer(s.solution, evaluate(s.solution, alpha), 3e6)
                assert bl.lower.cd > 1e-4, f"lower surface drag lost at n={n_panels}, a={alpha}"
                assert bl.upper.cd > 1e-4, f"upper surface drag lost at n={n_panels}, a={alpha}"

    def test_drag_falls_monotonically_with_reynolds(self):
        s = section("0012")
        cds = [s.at(0.0, re).cd for re in (1e6, 3e6, 6e6, 9e6)]
        assert all(b < a for a, b in zip(cds, cds[1:])), cds

    def test_transition_moves_forward_with_reynolds(self):
        s = section("0012")
        xtr = [s.at(0.0, re).x_transition_upper for re in (1e6, 3e6, 9e6)]
        assert all(b < a for a, b in zip(xtr, xtr[1:])), xtr

    def test_thicker_section_has_more_drag(self):
        thin = Section(naca4("0009", 400)).at(0.0, 1e6).cd
        thick = Section(naca4("0018", 400)).at(0.0, 1e6).cd
        assert thick > thin

    def test_separation_moves_forward_with_alpha(self):
        s = section("2412")
        xs = [s.at(a, 1e6).x_separation_upper or 1.0 for a in (6.0, 10.0, 14.0)]
        assert all(b <= a for a, b in zip(xs, xs[1:])), xs


class TestAgainstMeasuredData:
    """Abbott & von Doenhoff, *Theory of Wing Sections* (NACA Report 824),
    smooth-surface section drag. These are the only true validation points in the
    suite -- everything else is verification against theory or invariants."""

    @pytest.mark.parametrize("digits,reynolds,measured", [
        ("0012", 3e6, 0.0060),
        ("0012", 6e6, 0.0057),
        ("2412", 3e6, 0.0062),
    ])
    def test_minimum_drag(self, digits, reynolds, measured):
        cd = section(digits).at(0.0, reynolds).cd
        assert cd == pytest.approx(measured, abs=8e-4)


class TestGeometry:
    def test_rebuild_round_trips_the_input_surfaces(self):
        """decompose -> rebuild at unit scale must return the same section; the
        vertical thickness convention exists precisely to make this exact."""
        foil = naca4("2412", 400)
        dec = decompose(foil.xy, 120)
        nodes = rebuild(dec, 1.0, 1.0)
        from panelbl.geometry import split_surfaces, surface_spline
        upper, lower = split_surfaces(foil.xy)
        su, sl = surface_spline(upper), surface_spline(lower)
        interior = (nodes[:, 0] > 1e-6) & (nodes[:, 0] < 0.999)
        x, y = nodes[interior, 0], nodes[interior, 1]
        dev = np.minimum(np.abs(y - su(np.sqrt(x))), np.abs(y - sl(np.sqrt(x))))
        assert dev.max() < 5e-4

    def test_zero_camber_scale_makes_any_section_symmetric(self):
        s = Section(naca4("4412", 400), camber_scale=0.0)
        assert evaluate(s.solution, 0.0).cl == pytest.approx(0.0, abs=1e-6)
        assert evaluate(s.solution, 0.0).cm_quarter == pytest.approx(0.0, abs=1e-6)

    def test_sqrt_spline_beats_linear_spline_at_the_nose(self):
        """The reason surface splines are parameterised in sqrt(x): near the
        leading edge y ~ sqrt(x), which a cubic spline in x cannot follow on a
        coarse coordinate file. This reproduces that comparison on a 35-station
        sampling of an exact NACA 2412."""
        from scipy.interpolate import CubicSpline
        from panelbl.geometry import split_surfaces, surface_spline

        exact = naca4("2412", 400)
        upper_exact, _ = split_surfaces(exact.xy)
        ref = surface_spline(upper_exact)

        stations = np.array([0, .0125, .025, .05, .075, .1, .15, .2, .25, .3, .4,
                             .5, .6, .7, .8, .9, .95, 1.0])
        coarse = np.column_stack([stations, ref(np.sqrt(stations))])
        in_x = CubicSpline(coarse[:, 0], coarse[:, 1], bc_type="natural")
        in_sqrt = surface_spline(coarse)

        probe = np.linspace(1e-5, 0.2, 400)
        err_x = np.abs(in_x(probe) - ref(np.sqrt(probe))).max()
        err_sqrt = np.abs(in_sqrt(np.sqrt(probe)) - ref(np.sqrt(probe))).max()
        assert err_sqrt < err_x / 1.8, f"sqrt {err_sqrt:.2e} vs x {err_x:.2e}"
