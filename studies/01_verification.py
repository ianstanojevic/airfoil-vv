"""Study 1 -- Verification: how large is my own discretisation error?

Verification asks whether the equations are solved right. It says nothing about
whether they are the right equations; that is study 2.

The benchmark is a Joukowski section, because its inviscid lift is known in
closed form:

    Gamma = 4 pi V R sin(alpha + beta),   Cl = 2 Gamma / (V c)

so the error is *measured*, not estimated from a Richardson extrapolation of an
unknown. The geometry is generated analytically at every resolution, which keeps
discretisation error separate from geometry-representation error.

NACA 4-digit sections are deliberately not used here. Their camber line is two
parabolas joined at x = p that match in value and slope but not curvature, so the
surface is C1 but not C2 and the observed order is limited by the kink rather
than by the method. That is a property of the shape, not of the solver.

Outputs
    - the observed order of convergence p
    - the panel count below which the trailing-edge-clustered distribution
      becomes degenerate and the solution is unusable
    - the discretisation uncertainty carried by the panel count used in study 2

Without the last number, a few per cent of disagreement with XFOIL in study 2
would be uninterpretable: it could be entirely my own grid error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _style import BLUE, GREEN, RUST, save, use_style  # noqa: E402

from panelbl import Section, evaluate, joukowski, naca4, solve_panels  # noqa: E402

REPORT = Path(__file__).resolve().parents[1] / "report"
PANEL_COUNTS = [32, 64, 128, 256, 512, 1024, 2048]
ALPHAS = [0.0, 3.0, 5.0, 8.0]
PRODUCTION_PANELS = 320       # what studies 2 and 3 use
USABLE_FROM = 256             # established below


def convergence() -> dict:
    """Relative error against the exact Joukowski solution."""
    out = {}
    for alpha in ALPHAS:
        errors, values = [], []
        exact = joukowski(n=1024).exact_cl(alpha)
        for n in PANEL_COUNTS:
            section = joukowski(n=n)
            cl = evaluate(solve_panels(section.nodes), alpha).cl
            values.append(cl)
            errors.append(abs(cl - exact) / abs(exact))
        out[alpha] = {"exact": exact, "panels": PANEL_COUNTS,
                      "cl": values, "error": errors}
    return out


def observed_order(data: dict) -> dict:
    """Fit p to error ~ C h^p over the range where the discretisation is sane."""
    fits = {}
    for alpha, d in data.items():
        n = np.asarray(d["panels"], dtype=float)
        e = np.asarray(d["error"])
        keep = n >= USABLE_FROM
        p, log_c = np.polyfit(np.log(1.0 / n[keep]), np.log(e[keep]), 1)
        fits[alpha] = {"p": float(p), "c": float(np.exp(log_c)),
                       "points": int(keep.sum())}
    return fits


def production_uncertainty(data: dict) -> dict:
    """Discretisation error at the panel count studies 2 and 3 actually use."""
    out = {}
    for alpha, d in data.items():
        section = joukowski(n=PRODUCTION_PANELS)
        cl = evaluate(solve_panels(section.nodes), alpha).cl
        exact = d["exact"]
        out[alpha] = {"cl": cl, "exact": exact,
                      "relative_error": abs(cl - exact) / abs(exact)}
    return out


def repanelling_bias() -> dict:
    """Bias introduced by the production pipeline's chordwise re-panelling.

    ``Section`` re-samples any input geometry onto cosine-spaced chordwise
    stations. On a cusped trailing edge the upper and lower panels there end up
    closer together than their own length, and the resulting near-degenerate pair
    biases the lift by an amount that does *not* vanish with refinement. It is a
    modelling bias of the pipeline, so it belongs in the uncertainty budget
    rather than in the convergence fit.
    """
    out = {}
    for alpha in ALPHAS:
        js = joukowski(n=2048)
        direct = evaluate(solve_panels(js.nodes), alpha).cl
        piped = evaluate(Section(js.airfoil, n_panels=PRODUCTION_PANELS).solution, alpha).cl
        out[alpha] = {"direct": direct, "pipeline": piped,
                      "relative_bias": abs(piped - direct) / abs(direct)}
    return out


def figure(data: dict, fits: dict) -> None:
    import matplotlib.pyplot as plt
    use_style()
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.6))

    colours = {0.0: BLUE, 3.0: RUST, 5.0: GREEN, 8.0: "#8659A5"}
    for alpha, d in data.items():
        n = np.asarray(d["panels"], dtype=float)
        e = np.asarray(d["error"])
        ax.loglog(1 / n, e, "o-", ms=4, color=colours[alpha],
                  label=fr"$\alpha={alpha:g}^\circ$")
    ax.axvspan(1 / USABLE_FROM, 1 / PANEL_COUNTS[0], color="#ececec", zorder=0)
    ax.text(1 / 75, 8e-5, "degenerate\npanels", fontsize=8, color="#6a6a6a", ha="center")

    h = np.array([1 / 2048, 1 / USABLE_FROM])
    ax.loglog(h, 1.0 * h, "--", color="#9a9a9a", lw=1.0, zorder=0)
    ax.text(1 / 1500, 0.45 / 1500, "slope 1", color="#7a7a7a", fontsize=8)
    ax.set_xlabel("panel size $h = 1/N$")
    ax.set_ylabel(r"$|C_l - C_{l,\mathrm{exact}}| / C_{l,\mathrm{exact}}$")
    ax.set_title("Convergence against the exact Joukowski solution")
    ax.grid(True, which="both", alpha=0.5)
    ax.legend(loc="upper left", ncol=2)

    alphas = list(fits)
    ps = [fits[a]["p"] for a in alphas]
    ax2.bar([f"{a:g}" for a in alphas], ps, color=[colours[a] for a in alphas], width=0.55)
    ax2.axhline(1.0, color="#6a6a6a", ls="--", lw=1.0)
    ax2.text(0.99, 1.03, "first order", transform=ax2.get_yaxis_transform(),
             fontsize=8, color="#6a6a6a", ha="right")
    for i, p in enumerate(ps):
        ax2.text(i, p + 0.06, f"{p:.2f}", ha="center", fontsize=8.5)
    ax2.set_ylim(0, 1.35)
    ax2.set_xlabel(r"angle of attack [$^\circ$]")
    ax2.set_ylabel("observed order $p$")
    ax2.set_title("Observed order of convergence")
    ax2.grid(True, axis="y", alpha=0.5)

    save(fig, "fig1_verification.png")


def main() -> None:
    print("Study 1 -- verification against an exact solution\n")
    data = convergence()
    fits = observed_order(data)
    prod = production_uncertainty(data)
    bias = repanelling_bias()

    print(f"{'alpha':>7}{'Cl exact':>12}{'p':>8}{'err @ N=' + str(PRODUCTION_PANELS):>14}"
          f"{'pipeline bias':>16}")
    print("-" * 57)
    for alpha in ALPHAS:
        print(f"{alpha:>7.0f}{data[alpha]['exact']:>12.6f}{fits[alpha]['p']:>8.2f}"
              f"{100 * prod[alpha]['relative_error']:>13.3f}%"
              f"{100 * bias[alpha]['relative_bias']:>15.2f}%")

    worst_disc = max(p["relative_error"] for p in prod.values())
    worst_bias = max(b["relative_bias"] for b in bias.values())
    combined = float(np.hypot(worst_disc, worst_bias))
    print(f"\n  observed order          p = {np.mean([f['p'] for f in fits.values()]):.2f}")
    print(f"  usable panel count      N >= {USABLE_FROM}")
    print(f"  discretisation error    {100 * worst_disc:.2f} %  at N = {PRODUCTION_PANELS}")
    print(f"  re-panelling bias       {100 * worst_bias:.2f} %")
    print(f"  combined numerical      {100 * combined:.2f} %  <- carried into study 2")

    figure(data, fits)
    REPORT.mkdir(exist_ok=True)
    (REPORT / "verification.json").write_text(json.dumps({
        "panel_counts": PANEL_COUNTS,
        "production_panels": PRODUCTION_PANELS,
        "usable_from": USABLE_FROM,
        "convergence": {str(k): v for k, v in data.items()},
        "observed_order": {str(k): v for k, v in fits.items()},
        "production_uncertainty": {str(k): v for k, v in prod.items()},
        "repanelling_bias": {str(k): v for k, v in bias.items()},
        "numerical_uncertainty": combined,
    }, indent=1))
    print("  wrote report/verification.json")


if __name__ == "__main__":
    main()
