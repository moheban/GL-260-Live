from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

try:  # Optional dependency; the solver works without it.
    import numpy as np
except ImportError:
    np = None

from .base import SOL_KA1, SOL_KA2, SOL_KW, SOL_ION_CHARGES


@dataclass(frozen=True)
class ClosedCarbonateInputs:
    """
    Inputs for an Aqion-style closed carbonate system.

    total_inorganic_carbon_m is the dissolved inorganic carbon (CT) in mol/L.
    Equilibrium constants default to the thermodynamic values at 25 C taken
    from the existing solubility model constants.
    """

    total_inorganic_carbon_m: float
    temperature_c: float = 25.0
    ka1: float = SOL_KA1
    ka2: float = SOL_KA2
    kw: float = SOL_KW


@dataclass(frozen=True)
class ClosedCarbonateSpeciation:
    """Speciation results for the closed carbonate system."""

    ph: float
    h_conc: float
    oh_conc: float
    species_m: Dict[str, float]
    alpha: Dict[str, float]
    ionic_strength: float
    charge_balance_residual: float
    solver: str
    quartic_ph: float | None = None


def _alpha_fractions_from_h(h_conc: float, ka1: float, ka2: float) -> Dict[str, float]:
    """Ionization fractions a0/a1/a2 from Eq. (6) on the Aqion page."""

    denom = (h_conc**2) + (ka1 * h_conc) + (ka1 * ka2)
    if denom <= 0:
        denom = 1e-30
    a0 = (h_conc**2) / denom
    a1 = (ka1 * h_conc) / denom
    a2 = (ka1 * ka2) / denom
    return {"a0": a0, "a1": a1, "a2": a2}


def _ionic_strength(species: Dict[str, float]) -> float:
    """
    Ionic strength for the closed system species.

    H2CO3 is neutral and omitted; the remaining charges follow SOL_ION_CHARGES.
    """

    labels_to_ions = {
        "H+": "H",
        "HCO3-": "HCO3",
        "CO3^2-": "CO3",
        "OH-": "OH",
    }
    ionic = 0.0
    for label, conc in species.items():
        ion = labels_to_ions.get(label)
        if ion is None:
            continue
        z = SOL_ION_CHARGES.get(ion, 0)
        ionic += conc * (z**2)
    return 0.5 * ionic


def _species_from_ph(
    ct: float, ph: float, ka1: float, ka2: float, kw: float
) -> Tuple[Dict[str, float], Dict[str, float], float, float]:
    h = 10.0 ** (-ph)
    alpha = _alpha_fractions_from_h(h, ka1, ka2)
    h2co3 = ct * alpha["a0"]
    hco3 = ct * alpha["a1"]
    co3 = ct * alpha["a2"]
    oh = kw / max(h, 1e-30)
    species = {
        "H+": h,
        "H2CO3": h2co3,
        "HCO3-": hco3,
        "CO3^2-": co3,
        "OH-": oh,
    }
    return species, alpha, h, oh


def _charge_balance_residual(ct: float, h: float, ka1: float, ka2: float, kw: float) -> float:
    """Charge balance from Eq. (4e): [H+] - [HCO3-] - 2[CO3^2-] - [OH-]."""

    if h <= 0:
        return math.inf
    alpha = _alpha_fractions_from_h(h, ka1, ka2)
    hco3 = ct * alpha["a1"]
    co3 = ct * alpha["a2"]
    oh = kw / h
    return h - hco3 - 2.0 * co3 - oh


def _quartic_coefficients(ct: float, ka1: float, ka2: float, kw: float) -> List[float]:
    """
    Coefficients of Eq. (5) from the Aqion page.

    x^4 + K1*x^3 + (K1*K2 - Kw - CT*K1)*x^2 - K1*(Kw + 2*CT*K2)*x - Kw*K1*K2 = 0
    """

    return [
        1.0,
        ka1,
        (ka1 * ka2) - kw - (ct * ka1),
        -ka1 * (kw + 2.0 * ct * ka2),
        -kw * ka1 * ka2,
    ]


def _solve_quartic_root(
    ct: float, ka1: float, ka2: float, kw: float, *, tol: float = 1e-14
) -> float | None:
    if np is None:
        return None
    coeffs = _quartic_coefficients(ct, ka1, ka2, kw)
    roots = np.roots(coeffs)
    real_roots = [
        r.real for r in roots if abs(r.imag) < tol and 1e-16 < r.real < 1.0
    ]
    if not real_roots:
        return None

    def balance(h: float) -> float:
        return abs(_charge_balance_residual(ct, h, ka1, ka2, kw))

    return min(real_roots, key=balance)


def solve_closed_carbonate_system(
    inputs: ClosedCarbonateInputs,
    *,
    ph_bracket: Tuple[float, float] = (2.0, 12.5),
    validate_quartic: bool = True,
) -> ClosedCarbonateSpeciation:
    """
    Solve the closed carbonate system exactly as laid out on aqion.de/site/160.

    The pH is found via charge balance (Eq. 4e) with mole balance (4d);
    the quartic (Eq. 5) is evaluated as an optional cross-check.
    """

    ct = max(inputs.total_inorganic_carbon_m, 0.0)
    ka1 = inputs.ka1
    ka2 = inputs.ka2
    kw = inputs.kw

    low_ph, high_ph = ph_bracket

    def cb(ph_value: float) -> float:
        return _charge_balance_residual(ct, 10.0 ** (-ph_value), ka1, ka2, kw)

    f_low = cb(low_ph)
    f_high = cb(high_ph)
    if f_low == 0:
        ph_root = low_ph
        solver_used = "bracket-bound"
    elif f_high == 0:
        ph_root = high_ph
        solver_used = "bracket-bound"
    elif f_low * f_high > 0:
        # Fall back to quartic-only solve when the bracket fails (should be rare).
        quartic = _solve_quartic_root(ct, ka1, ka2, kw)
        if quartic is None:
            raise ValueError("Unable to bracket the closed-system pH root.")
        ph_root = -math.log10(quartic)
        solver_used = "quartic-fallback"
    else:
        lo, hi = low_ph, high_ph
        solver_used = "bisection-charge-balance"
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            f_mid = cb(mid)
            if abs(f_mid) < 1e-14 or abs(hi - lo) < 1e-6:
                ph_root = mid
                break
            if f_low * f_mid <= 0:
                hi = mid
                f_high = f_mid
            else:
                lo = mid
                f_low = f_mid
        else:
            ph_root = 0.5 * (lo + hi)

    quartic_ph: float | None = None
    if validate_quartic:
        quartic_root = _solve_quartic_root(ct, ka1, ka2, kw)
        if quartic_root is not None:
            quartic_ph = -math.log10(quartic_root)

    ph = ph_root
    species, alpha, h_val, oh_val = _species_from_ph(ct, ph, ka1, ka2, kw)
    ionic_strength = _ionic_strength(species)
    residual = _charge_balance_residual(ct, h_val, ka1, ka2, kw)
    return ClosedCarbonateSpeciation(
        ph=ph,
        h_conc=h_val,
        oh_conc=oh_val,
        species_m=species,
        alpha=alpha,
        ionic_strength=ionic_strength,
        charge_balance_residual=residual,
        solver=solver_used,
        quartic_ph=quartic_ph,
    )


def generate_closed_system_curve(
    inputs: ClosedCarbonateInputs,
    *,
    ph_range: Tuple[float, float] = (2.0, 12.5),
    steps: int = 200,
) -> List[Dict[str, float]]:
    """Return a pH sweep (alphas and concentrations) matching Aqion's diagrams."""

    low, high = ph_range
    if steps < 2:
        steps = 2
    values: List[Dict[str, float]] = []
    for idx in range(steps):
        ph = low + (high - low) * idx / (steps - 1)
        species, alpha, h, oh = _species_from_ph(
            inputs.total_inorganic_carbon_m, ph, inputs.ka1, inputs.ka2, inputs.kw
        )
        values.append(
            {
                "ph": ph,
                "H+": h,
                "H2CO3": species["H2CO3"],
                "HCO3-": species["HCO3-"],
                "CO3^2-": species["CO3^2-"],
                "OH-": oh,
                "alpha0": alpha["a0"],
                "alpha1": alpha["a1"],
                "alpha2": alpha["a2"],
            }
        )
    return values


def render_closed_system_plot(
    sweep: Sequence[Dict[str, float]], output_path: str, *, title: str | None = None
) -> None:
    """
    Generate a matplotlib plot similar to the Aqion closed-system speciation diagram.
    """

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ph = [row["ph"] for row in sweep]
    ax.plot(ph, [row["H2CO3"] for row in sweep], label="H2CO3*", color="#0d6efd")
    ax.plot(ph, [row["HCO3-"] for row in sweep], label="HCO3-", color="#198754")
    ax.plot(ph, [row["CO3^2-"] for row in sweep], label="CO3^2-", color="#d63384")
    ax.set_xlabel("pH")
    ax.set_ylabel("Concentration (mol/L)")
    ax.set_xlim(min(ph), max(ph))
    ax.set_ylim(bottom=0)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
