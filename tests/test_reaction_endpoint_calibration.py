"""Focused checks for model-owned completion, calibration and carbonate forecasts."""

import importlib.util
import sys
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture(scope="module")
def app():
    """Load the real application once for integration checks without opening Tk.

    Takes no input and returns its module; imports dependencies and registers the
    module in sys.modules. Import failures propagate to expose environment issues.
    """
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location(
        "gl260_endpoint_tests", root / "GL-260 Data Analysis and Plotter.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def carbonate(app):
    """Return a two-to-one carbonate template and 25 mol NaOH inventory.

    Uses the imported app's dataclasses; creates only local objects. Construction
    errors propagate so tests cannot silently use a different reaction definition.
    """
    base = next(iter(app._builtin_reaction_templates().values()))
    template = replace(
        base,
        template_id="carbonate_test",
        name="Sodium carbonate",
        gas_species_id="gas",
        species=(
            app.ReactionSpecies("feed", "NaOH", "NaOH", "solution", "reactant", 39.997),
            app.ReactionSpecies("gas", "CO2", "CO2", "gas", "reactant_gas", 44.0095),
            app.ReactionSpecies(
                "product", "Na2CO3", "Na2CO3", "solution", "product", 105.99
            ),
        ),
        steps=(
            app.ReactionStep(
                "main", "Carbonation", {"feed": -2, "gas": -1, "product": 1}
            ),
        ),
        input_fields=(),
        yield_basis=app.ReactionYieldBasis("product", "feed"),
    )
    rows = [asdict(item) for item in template.species]
    rows[0]["initial_moles"] = 25.0
    return template, rows


@pytest.mark.parametrize(
    "uptake,expected", [(0.0, 0.0), (6.25, 50.0), (12.5, 100.0), (15.0, 100.0)]
)
def test_nonunit_stoichiometry(app, carbonate, uptake, expected):
    """Check Python and routed native/fallback completion for CO2 uptake in mol.

    Fixture inputs are unchanged; returns None and raises on coefficient errors.
    Backend health routing may be exercised by the production wrapper.
    """
    template, rows = carbonate
    for core in (app._python_reaction_dashboard_core, app._run_reaction_dashboard_core):
        result = core(
            rows,
            [asdict(step) for step in template.steps],
            gas_uptake_mol=uptake,
            gas_species_id="gas",
            yield_species_id="product",
            target_reactant_species_id="feed",
            actual_yield_mass_g=None,
        )
        assert result["completion_pct"] == pytest.approx(expected)
        assert result["completion_basis_product_mol"] == pytest.approx(12.5)


def test_recharge_intervals_preserve_consumption(app):
    """Check four known charge decays, partial progress and native compatibility.

    Uses synthetic absolute psi/Celsius arrays; mutates no source data. Returns
    None and raises if recharge resets progress or Python/native routing differs.
    """
    pressure = np.tile(np.linspace(794.6959, 14.6959, 5), 4)
    intervals = [(index, index + 4) for index in range(0, 20, 5)]
    kwargs = dict(
        x_label="Elapsed Time (minutes)",
        expected_gas_mol=2.0,
        endpoint_position=19,
        displacement_l=None,
        cycle_intervals=intervals,
    )
    python = app._python_reaction_endpoint_calibration_core(
        np.arange(20), pressure, np.full(20, 25.0), **kwargs
    )
    routed = app._run_reaction_endpoint_calibration_core(
        np.arange(20), pressure, np.full(20, 25.0), **kwargs
    )
    assert np.asarray(python["conversion_pct"])[[4, 9, 14, 19]] == pytest.approx(
        [25, 50, 75, 100]
    )
    assert python["conversion_pct"][5] == pytest.approx(25)
    assert routed["consumed_moles"] == pytest.approx(python["consumed_moles"])
    expected_volume = (
        2
        * app.REACTION_ENDPOINT_CALIBRATION_R_L_ATM_MOL_K
        / (4 * 780 / 14.6959 / 298.15)
    )
    assert python["effective_headspace_l"] == pytest.approx(expected_volume)
    kwargs["cycle_intervals"] = [(0, 5), (4, 9)]
    invalid = app._python_reaction_endpoint_calibration_core(
        np.arange(20), pressure, np.full(20, 25.0), **kwargs
    )
    assert invalid["effective_headspace_l"] is None


def test_resolve_refreshes_and_failure_clears(app, carbonate):
    """Verify calibrated uptake is refreshed and failed trace reads erase old state.

    Uses local UI stand-ins and current template inputs. Returns None; only harness
    state changes. Assertions expose reuse of stale chemistry or failed results.
    """
    template, rows = carbonate
    harness = SimpleNamespace(
        _reaction_source_mode_var=SimpleNamespace(
            get=lambda: "endpoint_calibrated_trace"
        ),
        _reaction_endpoint_calibration={
            "endpoint_global_index": 9,
            "expected_gas_mol": 99,
            "effective_headspace_l": 1,
        },
        _refresh_reaction_endpoint_calibration=lambda **kwargs: {
            "expected_gas_mol": 12.5,
            "effective_headspace_l": 1,
        },
    )
    assert (
        app.UnifiedApp._reaction_dashboard_resolve_gas_uptake(harness, template, rows)[
            0
        ]
        == 12.5
    )
    harness._reaction_endpoint_trace_inputs = lambda: None
    assert (
        app.UnifiedApp._refresh_reaction_endpoint_calibration(
            harness, endpoint_global_index=9, selection_method="manual"
        )
        == {}
    )
    assert harness._reaction_endpoint_calibration == {}


def test_carbonate_forecast_uses_batch_and_model(app, carbonate):
    """Exercise the real Pitzer forecast and verify cycle count scales with headspace.

    Inputs are the carbonate fixture and independent pressure/volume conditions.
    Returns None; solver backend routing is the only side effect. Raises if the
    observed four-to-five cycles are forced instead of calculated from the batch.
    """
    template, rows = carbonate
    kwargs = dict(
        ph_model=app.get_speciation_model("naoh_co2_pitzer_hmw"),
        liquid_volume_l=3.0,
        headspace_l=0.785412,
        temperature_c=25.0,
        low_psig=0,
        high_psig=780,
        ph_low=10.5,
        ph_high=12.4,
        target_ph=11.4,
    )
    first = app._reaction_carbonate_endpoint_guidance(template, rows, **kwargs)
    assert first.get("target_gas_mol", 0) > 0, first
    target_ph, _composition = kwargs["ph_model"].predict_planning_ph(
        planning_context={
            "naoh_mass_g": 25 * app.REACTION_NAOH_MOLAR_MASS_G_MOL,
            "solution_volume_l": 3.0,
            "temperature_c": 25.0,
        },
        cumulative_co2_moles=first["target_gas_mol"],
        cycle_index=0,
    )
    assert target_ph == pytest.approx(11.4, abs=0.002)
    kwargs["headspace_l"] *= 2
    second = app._reaction_carbonate_endpoint_guidance(template, rows, **kwargs)
    assert second["estimated_cycles"] == pytest.approx(first["estimated_cycles"] / 2)
    assert second["target_gas_mol"] == pytest.approx(first["target_gas_mol"])
    kwargs["headspace_l"] = 0.785412 * first["estimated_cycles"] / 4.5
    matched = app._reaction_carbonate_endpoint_guidance(template, rows, **kwargs)
    assert matched["estimated_cycles"] == pytest.approx(4.5)
    assert matched["observation_agrees"]
    kwargs["liquid_volume_l"] = None
    assert (
        "unavailable"
        in app._reaction_carbonate_endpoint_guidance(template, rows, **kwargs)[
            "message"
        ]
    )
    print("Independent batch forecast:", first["message"])


def test_existing_endpoint_regressions(app):
    """Retain existing endpoint and source-isolation checks using their real harnesses.

    Takes the app fixture, returns None, and raises on existing regression failures.
    Only local regression harnesses and backend health routing are mutated.
    """
    app._regression_test_reaction_endpoint_calibration_core()
    app._regression_test_reaction_endpoint_gas_demand_and_cycle_clone()


def test_live_calibration_invalidates_charge_and_trace_cache(app, carbonate):
    """Run the owning refresh path against live markers, charge and trace edits.

    Fixture rows are copied; local harness state and backend routing may change.
    Returns None and raises if equal-sum trace edits or new charge reuse old math.
    """
    template, fixture_rows = carbonate
    rows = [dict(row) for row in fixture_rows]
    pressure = np.tile(np.linspace(794.6959, 14.6959, 5), 4)
    trace = dict(
        x=np.arange(20.0),
        pressure=pressure,
        temperature=np.full(20, 25.0),
        sample_indices=np.arange(20),
        x_label="Elapsed Time (minutes)",
    )
    statuses = []
    harness = SimpleNamespace(
        _reaction_endpoint_calibration={},
        _reaction_start_global_index=0,
        _reaction_endpoint_trace_inputs=lambda: trace,
        _reaction_active_template=lambda: template,
        _reaction_dashboard_species_rows_with_inputs=lambda template: (rows, {}),
        _reaction_dashboard_steps_from_editor=lambda: [
            asdict(step) for step in template.steps
        ],
        _reaction_dashboard_step_rows_for_available_inputs=lambda template, steps: (
            steps,
            [],
        ),
        _reaction_dashboard_endpoint_guidance=lambda template, rows: {},
        _reaction_calibration_start_index=lambda indices, endpoint: 0,
        _reaction_dashboard_input_float=lambda key: None,
        _reaction_endpoint_status_var=SimpleNamespace(
            set=statuses.append, get=lambda: statuses[-1]
        ),
        _get_xy=lambda: (trace["x"], pressure, trace["temperature"]),
        _effective_peaks=lambda: {0, 5, 10, 15},
        _effective_troughs=lambda: {4, 9, 14, 19},
        _form_cycles=lambda *args: app.UnifiedApp._form_cycles(None, *args),
    )
    refresh = app.UnifiedApp._refresh_reaction_endpoint_calibration
    first = refresh(harness, endpoint_global_index=19, selection_method="manual")
    assert first["expected_gas_mol"] == pytest.approx(12.5)
    assert first["conversion_pct"][9] == pytest.approx(50)
    rows[0]["initial_moles"] = 50
    second = refresh(harness, endpoint_global_index=19, selection_method="manual")
    assert second["effective_headspace_l"] == pytest.approx(
        2 * first["effective_headspace_l"]
    )
    pressure[1], pressure[2] = pressure[2], pressure[1]
    third = refresh(harness, endpoint_global_index=19, selection_method="manual")
    assert third["cache_signature"] != second["cache_signature"]
    assert third["conversion_pct"][1] != second["conversion_pct"][1]


def test_model_selection_clears_result_and_calibration(app, carbonate, monkeypatch):
    """Verify model selection cannot export or consume the preceding model's result.

    Uses a local UI harness and temporary settings mapping. Returns None, mutates
    only the harness, and raises if either result cache survives the model change.
    """
    template, _rows = carbonate
    monkeypatch.setattr(app, "settings", {})
    messages = []
    harness = SimpleNamespace(
        _reaction_active_template=lambda: template,
        _refresh_reaction_template_selector=lambda: None,
        _load_reaction_template_into_ui=lambda template: None,
        _reaction_endpoint_calibration={"expected_gas_mol": 99},
        _reaction_dashboard_last_result={"template_id": "old_model"},
        _reaction_endpoint_status_var=SimpleNamespace(set=messages.append),
    )
    app.UnifiedApp._on_reaction_template_selected(harness)
    assert not harness._reaction_endpoint_calibration
    assert harness._reaction_dashboard_last_result is None
    assert template.name in messages[-1]
