from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Protocol

# Thermodynamic / physical constants used across speciation models.
SOL_KA1 = 4.45e-7
SOL_KA2 = 4.69e-11
SOL_KW = 1.0e-14
SOL_KSP_NAHCO3 = 2.5e-8
SOL_KSP_NA2CO3 = 1.0e-3
SOL_SATURATION_TOL = 1e-3
SOL_DAVIES_LIMIT = 0.5
SOL_DAVIES_COEFF = 0.3
SOL_ACTIVITY_EXTRAPOLATION_LIMIT = 2.5
SOL_MW_NAHCO3 = 84.0066
SOL_MW_NA2CO3 = 105.9888
SOL_MW_NAOH = 39.997
SOL_MW_CO2 = 44.0095
SOL_A_DEBYE = 0.509
SOL_B_DEBYE = 0.328
SOL_WATER_DENSITY_25C_G_PER_ML = 0.9970474
SOL_HEADSPACE_DEFAULT_PCO2_ATM = 0.0004
SOL_DEFAULT_SENSITIVITY_PCT = 5.0
SOL_PH_SWEEP_DEFAULT = (6.0, 10.5, 7)
SOL_PKA1_COEFFS = (-1.333e-5, -0.008867, 6.58)
SOL_PKA2_COEFFS = (-3.5238e-5, -0.010719, 10.62)
CYCLE_TRACKER_NOTE_PREFIX = "[Cycle]"
DIAG_WATER_ASSUMPTION_FACTOR = 5.0
DIAG_MIN_WATER_MASS_G = 200.0
REPROCESSING_SLURRY_VOLUME_L = 2.5

SOL_SPECIES_MOLAR_MASSES: Dict[str, float] = {
    "Na+": 22.989769,
    "H+": 1.00784,
    "HCO3-": 61.01684,
    "CO3^2-": 60.0089,
    "H2CO3": 62.02484,
    "OH-": 17.007,
}

SOL_GLOSSARY_ENTRIES: "OrderedDict[str, str]" = OrderedDict(
    [
        (
            "Ionic strength",
            "A weighted sum of ion concentrations (0.5 Σ ci·zi²) that captures how crowded the "
            "electrolyte is and directly impacts activity coefficients.",
        ),
        (
            "Activity coefficient",
            "Correction factor that adjusts molar concentration to an effective 'activity' to account "
            "for ionic interactions (Debye–Hückel in this module).",
        ),
        (
            "Saturation index",
            "Ratio of the ionic product to the solubility product (Ksp). Values above 1 indicate supersaturation.",
        ),
        (
            "Alkalinity",
            "Charge-balance measure of the solution's ability to neutralize acid, approximated as "
            "[HCO3-] + 2[CO3^2-] + [OH-] - [H+].",
        ),
    ]
)

SOLUBILITY_PRESETS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict(
    [
        (
            "1 L Lab Titration",
            {
                "description": "Bench-scale dissolution aimed at near-neutral pH.",
                "values": {
                    "mass_na_hco3_g": 10.0,
                    "water_mass_g": 1000.0,
                    "solution_volume_l": None,
                    "temperature_c": 25.0,
                    "initial_ph_guess": 8.35,
                    "forced_ph_target": 8.30,
                },
            },
        ),
        (
            "CO2 Scrubber Startup",
            {
                "description": "Pre-charge for a gas scrubbing loop with gentle CO2 bleed.",
                "values": {
                    "mass_na_hco3_g": 25.0,
                    "water_mass_g": 1500.0,
                    "solution_volume_l": None,
                    "temperature_c": 30.0,
                    "initial_ph_guess": 8.6,
                    "forced_ph_target": 8.10,
                    "headspace_pco2_atm": SOL_HEADSPACE_DEFAULT_PCO2_ATM,
                    "headspace_kh_m_per_atm": 0.033,
                    "use_temperature_adjusted_constants": True,
                },
            },
        ),
        (
            "High Strength Slurry",
            {
                "description": "Concentrated charge for crystallizer stress-testing.",
                "values": {
                    "mass_na_hco3_g": 100.0,
                    "water_mass_g": None,
                    "solution_volume_l": 0.85,
                    "temperature_c": 35.0,
                    "initial_ph_guess": 9.1,
                    "forced_ph_target": 8.9,
                    "ionic_strength_cap": 0.5,
                },
            },
        ),
    ]
)

SOL_ION_CHARGES: Dict[str, int] = {
    "Na": 1,
    "H": 1,
    "HCO3": -1,
    "CO3": -2,
    "OH": -1,
}

SOL_ION_SIZES_NM: Dict[str, float] = {
    "Na": 0.90,
    "H": 0.90,
    "HCO3": 0.43,
    "CO3": 0.40,
    "OH": 0.35,
}


@dataclass(frozen=True)
class SolubilityInputs:
    """User-supplied sodium bicarbonate dissolution inputs."""

    mass_na_hco3_g: float
    water_mass_g: Optional[float] = None
    solution_volume_l: Optional[float] = None
    temperature_c: float = 25.0
    initial_ph_guess: float = 8.35
    forced_ph_target: Optional[float] = None
    use_temperature_adjusted_constants: bool = False
    ionic_strength_cap: Optional[float] = None
    headspace_pco2_atm: Optional[float] = None
    headspace_kh_m_per_atm: Optional[float] = None
    degassed_fraction: float = 0.0
    total_inorganic_carbon_mol: Optional[float] = None
    headspace_volume_l: Optional[float] = None
    speciation_mode: str = "fixed_pCO2"

    def volume_l(self) -> float:
        if self.solution_volume_l is not None:
            return self.solution_volume_l
        if self.water_mass_g is None:
            raise ValueError("Provide either a solution volume or water mass.")
        return (self.water_mass_g / SOL_WATER_DENSITY_25C_G_PER_ML) / 1000.0

    def _retained_carbon_fraction(self) -> float:
        frac = 1.0 - (self.degassed_fraction or 0.0)
        return max(frac, 0.0)

    def total_moles(self) -> float:
        return self.mass_na_hco3_g / SOL_MW_NAHCO3

    def total_carbon_concentration(self) -> float:
        volume = self.volume_l()
        if volume <= 0:
            raise ValueError("Solution volume must be positive.")
        return (self.total_moles() / volume) * self._retained_carbon_fraction()

    def headspace_carbon_contribution(self) -> float:
        target = self.headspace_target_h2co3()
        return target if target is not None else 0.0

    def total_carbon_with_headspace(self) -> float:
        total = self.total_carbon_concentration()
        headspace = self.headspace_target_h2co3()
        if headspace is None:
            return total
        return total + headspace

    def carbon_inventory_concentration(self) -> float:
        volume = self.volume_l()
        if volume <= 0:
            raise ValueError("Solution volume must be positive.")
        if self.total_inorganic_carbon_mol is not None:
            return (
                max(self.total_inorganic_carbon_mol, 0.0)
                / volume
                * self._retained_carbon_fraction()
            )
        return self.total_carbon_with_headspace()

    def sodium_concentration(self) -> float:
        volume = self.volume_l()
        if volume <= 0:
            raise ValueError("Solution volume must be positive.")
        return self.total_moles() / volume

    def headspace_target_h2co3(self) -> Optional[float]:
        if (
            self.headspace_pco2_atm is None
            or self.headspace_kh_m_per_atm is None
            or self.headspace_pco2_atm <= 0
            or self.headspace_kh_m_per_atm <= 0
        ):
            return None
        return self.headspace_pco2_atm * self.headspace_kh_m_per_atm


@dataclass(frozen=True)
class SolubilitySpeciationResult:
    """Activity-based speciation outputs for the solubility module."""

    concentrations_m: Dict[str, float]
    moles: Dict[str, float]
    activity_coefficients: Dict[str, float]
    ionic_strength: float
    ph: float
    saturation_indices: Dict[str, float]
    fractional_carbon: Dict[str, float]
    mass_concentrations_g_per_l: Dict[str, float]
    alkalinity_meq_per_l: float
    total_carbon_m: float
    charge_balance_residual: float
    assumptions: List[str]
    warnings: List[str]
    carbonate_as_na2co3_wt_percent: Optional[float]
    ionic_strength_capped: bool = False
    dissolved_mass_na_hco3_g: Optional[float] = None
    undissolved_mass_na_hco3_g: Optional[float] = None
    dissolved_fraction: Optional[float] = None


@dataclass(frozen=True)
class SolubilityMathStep:
    """Detailed sub-step for a math entry."""

    title: str
    expression: str = ""
    detail: str = ""
    latex: str = ""
    units: str = ""

    def as_text(self) -> str:
        parts = [self.title]
        if self.expression:
            parts.append(self.expression)
        if self.units:
            parts.append(f"[{self.units}]")
        if self.detail:
            parts.append(f"— {self.detail}")
        return " ".join(part for part in parts if part).strip()

    def as_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "expression": self.expression,
            "detail": self.detail,
            "latex": self.latex,
            "units": self.units,
        }


@dataclass(frozen=True)
class SolubilityMathEntry:
    """Single line of math context for the Advanced Solubility Module."""

    description: str
    expression: str
    result: str
    units: str = ""
    steps: Sequence[SolubilityMathStep] = field(default_factory=tuple)

    def as_text(self) -> str:
        pieces = [self.description]
        if self.expression:
            pieces.append(self.expression)
        if self.result:
            pieces.append(f"= {self.result}")
        if self.units:
            pieces.append(f"[{self.units}]")
        base_line = " ".join(piece for piece in pieces if piece)
        if self.steps:
            step_lines = "; ".join(step.as_text() for step in self.steps)
            return f"{base_line} → {step_lines}" if base_line else step_lines
        return base_line

    def as_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "expression": self.expression,
            "result": self.result,
            "units": self.units,
            "steps": [step.as_dict() for step in self.steps],
        }


class SolubilityMathLogger:
    """Collect and render math steps for optional user review."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = bool(enabled)
        self._sections: "OrderedDict[str, List[SolubilityMathEntry]]" = OrderedDict()

    def _section_entries(self, section: str) -> List[SolubilityMathEntry]:
        key = section or "General"
        if key not in self._sections:
            self._sections[key] = []
        return self._sections[key]

    def log(
        self,
        section: str,
        description: str,
        expression: str,
        result: str,
        units: str = "",
        steps: Sequence[SolubilityMathStep] = (),
    ) -> None:
        if not self.enabled:
            return
        entry = SolubilityMathEntry(
            description=description, expression=expression, result=result, units=units, steps=tuple(steps)
        )
        self._section_entries(section).append(entry)

    def extend_lines(self, section: str, lines: Sequence[str]) -> None:
        """Append plain-text lines to a section as lightweight math entries."""
        if not self.enabled:
            return
        entries = self._section_entries(section)
        for line in lines:
            if not line:
                continue
            entries.append(
                SolubilityMathEntry(
                    description=str(line),
                    expression="",
                    result="",
                    units="",
                    steps=tuple(),
                )
            )

    def export(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.enabled:
            return {}
        exported: Dict[str, List[Dict[str, Any]]] = {}
        for section, entries in self._sections.items():
            exported[section] = [entry.as_dict() for entry in entries]
        return exported

    def export_sections(self) -> List[Dict[str, Any]]:
        """Return math sections in UI-friendly structure."""
        if not self.enabled or not self._sections:
            return []
        sections: List[Dict[str, Any]] = []
        for name, entries in self._sections.items():
            sections.append({"name": name, "entries": [entry.as_dict() for entry in entries]})
        return sections

    def preview_lines(self, max_sections: int = 3, max_lines: int = 10) -> List[str]:
        if not self.enabled or not self._sections:
            return []
        preview: List[str] = []
        for section_index, (section, entries) in enumerate(self._sections.items()):
            if section_index >= max_sections:
                preview.append("... additional sections omitted ...")
                break
            preview.append(f"[{section}]")
            for entry in entries:
                preview.append(f"  {entry.as_text()}")
                if len(preview) >= max_lines:
                    preview.append("... more math captured ...")
                    return preview
        return preview


DEFAULT_SOLUBILITY_INPUTS = SolubilityInputs(
    mass_na_hco3_g=10.0,
    water_mass_g=1000.0,
    solution_volume_l=None,
    temperature_c=25.0,
    initial_ph_guess=8.35,
)


@dataclass(frozen=True)
class ModelMetadata:
    """Describes the envelope and provenance of a speciation model."""

    reference: str
    temperature_range_c: Tuple[float, float]
    ionic_strength_limit: Optional[float] = None
    notes: str = ""


@dataclass
class ModelOptions:
    """User/solver-configurable options passed into a model."""

    override_ionic_strength_cap: Optional[float] = None
    activity_model: str = "debye-huckel"
    extra: Dict[str, Any] = field(default_factory=dict)


class SpeciationModel(Protocol):
    """Protocol describing callable hooks every speciation model must expose."""

    key: str
    label: str
    description: str
    metadata: ModelMetadata

    def solve(
        self,
        params: SolubilityInputs,
        *,
        model_options: Optional[ModelOptions] = None,
        math_logger: Optional[SolubilityMathLogger] = None,
        math_section: str = "Speciation",
    ) -> SolubilitySpeciationResult:
        ...

    def solve_forced_ph(
        self,
        params: SolubilityInputs,
        forced_ph: float,
        *,
        model_options: Optional[ModelOptions] = None,
        math_logger: Optional[SolubilityMathLogger] = None,
        math_section: str = "Forced pH Speciation",
    ) -> SolubilitySpeciationResult:
        ...

    def generate_ph_sweep(
        self,
        params: SolubilityInputs,
        sweep_low: float,
        sweep_high: float,
        sweep_steps: int,
        *,
        model_options: Optional[ModelOptions] = None,
        math_logger: Optional[SolubilityMathLogger] = None,
    ) -> List[Dict[str, float]]:
        ...

    def generate_sensitivity_rows(
        self,
        params: SolubilityInputs,
        enabled_axes: Dict[str, bool],
        *,
        model_options: Optional[ModelOptions] = None,
        math_logger: Optional[SolubilityMathLogger] = None,
    ) -> List[Dict[str, str]]:
        ...


_SPEC_MODEL_REGISTRY: "OrderedDict[str, SpeciationModel]" = OrderedDict()
DEFAULT_SPEC_MODEL_KEY = "debye_huckel_full"


def register_speciation_model(model: SpeciationModel) -> None:
    """Register a model implementation so the UI and solver can look it up by key."""
    _SPEC_MODEL_REGISTRY[model.key] = model


def get_speciation_model(key: Optional[str]) -> SpeciationModel:
    if key and key in _SPEC_MODEL_REGISTRY:
        return _SPEC_MODEL_REGISTRY[key]
    if DEFAULT_SPEC_MODEL_KEY not in _SPEC_MODEL_REGISTRY:
        raise KeyError(
            "No speciation models have been registered; unable to resolve default."
        )
    return _SPEC_MODEL_REGISTRY[DEFAULT_SPEC_MODEL_KEY]


def list_speciation_models() -> List[SpeciationModel]:
    return list(_SPEC_MODEL_REGISTRY.values())


__all__ = [
    "SOL_KA1",
    "SOL_KA2",
    "SOL_KW",
    "SOL_KSP_NAHCO3",
    "SOL_KSP_NA2CO3",
    "SOL_SATURATION_TOL",
    "SOL_DAVIES_LIMIT",
    "SOL_DAVIES_COEFF",
    "SOL_ACTIVITY_EXTRAPOLATION_LIMIT",
    "SOL_MW_NAHCO3",
    "SOL_MW_NA2CO3",
    "SOL_MW_NAOH",
    "SOL_MW_CO2",
    "SOL_A_DEBYE",
    "SOL_B_DEBYE",
    "SOL_WATER_DENSITY_25C_G_PER_ML",
    "SOL_HEADSPACE_DEFAULT_PCO2_ATM",
    "SOL_DEFAULT_SENSITIVITY_PCT",
    "SOL_PH_SWEEP_DEFAULT",
    "SOL_PKA1_COEFFS",
    "SOL_PKA2_COEFFS",
    "CYCLE_TRACKER_NOTE_PREFIX",
    "SOL_SPECIES_MOLAR_MASSES",
    "SOL_GLOSSARY_ENTRIES",
    "SOLUBILITY_PRESETS",
    "SOL_ION_CHARGES",
    "SOL_ION_SIZES_NM",
    "DIAG_WATER_ASSUMPTION_FACTOR",
    "DIAG_MIN_WATER_MASS_G",
    "REPROCESSING_SLURRY_VOLUME_L",
    "SolubilityInputs",
    "SolubilitySpeciationResult",
    "SolubilityMathStep",
    "SolubilityMathEntry",
    "SolubilityMathLogger",
    "DEFAULT_SOLUBILITY_INPUTS",
    "ModelMetadata",
    "ModelOptions",
    "SpeciationModel",
    "register_speciation_model",
    "get_speciation_model",
    "list_speciation_models",
    "DEFAULT_SPEC_MODEL_KEY",
]
