"""Verify carbonate endpoint doses flow through real Planning timeline chemistry."""

import math
from types import SimpleNamespace

import pytest

pytest_plugins = ("test_reaction_endpoint_calibration",)


def setup_plan(app, **overrides):
    """Return fresh form, params and harness for a representative carbonate run.

    Takes the imported app and optional form overrides. Returns local objects;
    no persistent settings change. Constructor errors propagate.
    """
    key = "naoh_co2_pitzer_hmw"
    harness = app._PlanningPayloadHarness(key, key, True)
    harness.settings = {}
    form = dict(
        workflow_key="Planning",
        mass_naoh_g=1100.0,
        water_mass_g=2510.0,
        reaction_naoh_mass=1100.0,
        reaction_solution_volume=2.51,
        planning_total_vessel_volume_l=4.0,
        planning_headspace_pressure_high_psi=730.0,
        planning_cycle_delta_p_psi=730.0,
        planning_stop_ph=8.25,
        planning_stop_co2_added_g=3000.0,
        carbonate_mode_enabled=True,
        carbonate_target_ph=11.4,
        carbonate_guard_margin_ph=0.25,
        planning_ph_model_key=key,
        planning_spec_model_key=key,
        planning_use_same_model=True,
    )
    form.update(overrides)
    params = app.SolubilityInputs(
        mass_na_hco3_g=0.0,
        water_mass_g=2510.0,
        solution_volume_l=2.51,
        temperature_c=28.4,
        headspace_volume_l=1.49,
        use_temperature_adjusted_constants=False,
    )
    return harness, form, params


def test_partial_pressure_reaches_real_timeline_endpoint(app, monkeypatch):
    """Verify reduced pressure inventory, recomputed pH and Python fallback agree.

    Uses the real Planning model, generator and timeline consumer. Returns None;
    backend disabling is temporary and no UI/settings are written. Assertions
    expose dose, total, pH or report divergence between the shared pipeline stages.
    """
    harness, form, params = setup_plan(app)
    payload = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    rows = payload["cycle_transfer"]
    final = rows[-1]
    forecast = payload["carbonate_forecast"]
    plan = forecast["operator_dosing_plan"]
    assert final["is_partial_charge"]
    assert final["selected_moles"] < rows[0]["selected_moles"]
    assert final["peak_pressure_psi"] < 730
    assert final["peak_pressure_psi"] == pytest.approx(
        plan["final_partial_charge_pressure_psig"]
    )
    pressure_dose = app._python_carbonate_pressure_drop_inventory_core(
        high_psig=final["peak_pressure_psi"],
        delta_psig=final["delta_pressure_psi"],
        headspace_volume_l=1.49,
        temperature_c=28.4,
    )
    assert final["selected_mass_g"] == pytest.approx(pressure_dose["dose_g"])
    assert final["ph_after"] == pytest.approx(11.4, abs=1e-5)
    assert payload["total_moles_vdw"] == pytest.approx(
        sum(r["selected_moles"] for r in rows)
    )
    assert plan["full_cycles_before_guard"] == len(rows) - 1
    assert plan["max_final_partial_co2_g"] == pytest.approx(final["selected_mass_g"])
    assert forecast["estimated_total_co2_g"] == pytest.approx(
        final["cumulative_co2_mass_g"]
    )
    model = app.get_speciation_model("naoh_co2_pitzer_hmw")
    result = app.solubility_simulate_cycle_timeline(
        params,
        rows,
        model=model,
        ph_model=model,
        reaction_context={
            **form,
            "naoh_mass_g": 1100.0,
            "solution_volume_l": 2.51,
            "temperature_c": 28.4,
            "target_ph": 11.4,
        },
    )
    final_timeline = result["timeline"][-1]
    assert final_timeline["co2_added_mass_g"] == pytest.approx(final["selected_mass_g"])
    assert final_timeline["ph"] == pytest.approx(11.4, abs=1e-5)
    assert final_timeline["delta_pressure_psi"] == pytest.approx(
        final["delta_pressure_psi"]
    )
    report = app._build_planning_pdf_report(
        {
            "workflow_key": "Planning",
            "inputs": form,
            "cycle_payload": payload,
            "timeline": result["timeline"],
        },
        sections=["timeline", "plot"],
    )
    assert report["endpoint_dose_applied"]
    assert report["target_cycles"] == len(rows)
    assert "Charge-Cycle" in report["models"][-1]["title"]
    monkeypatch.setattr(app, "_load_rust_backend", lambda: None)
    fallback = harness._generate_planning_cycle_payload(
        dict(form), SimpleNamespace(params=params)
    )
    fallback_final = fallback["cycle_transfer"][-1]
    assert fallback_final["selected_moles"] == pytest.approx(
        final["selected_moles"], rel=1e-6
    )
    assert fallback_final["ph_after"] == pytest.approx(final["ph_after"], abs=1e-5)
    print(
        "Endpoint:",
        len(rows),
        final["peak_pressure_psi"],
        final["selected_mass_g"],
        final_timeline["ph"],
    )


@pytest.mark.parametrize("target_cycle", [0.6, 3.0, 3.65])
def test_endpoint_first_whole_and_partial_cycles(app, monkeypatch, target_cycle):
    """Exercise first-charge, exact whole-charge and later partial-dose boundaries.

    Takes pytest inputs; installs a nonlinear pH model temporarily to make the
    expected dose independent of interpolation. Runs real ledger accounting,
    returns None and raises if cycle mass or stop count disagrees with that model.
    """
    harness, form, params = setup_plan(app, planning_cycle_co2_g=200.0)
    full_mol = 200.0 / app.SOL_MW_CO2

    def prediction(model, *, cumulative_co2_moles, **kwargs):
        """Return known nonlinear pH for cumulative moles, without side effects.

        Ignores model/context; returns the standard predictor tuple. No errors.
        """
        x = cumulative_co2_moles / full_mol
        return 11.4 + 0.1 * (target_cycle**2 - x**2), None, "planning_model", None

    monkeypatch.setattr(app, "_predict_planning_ph_for_model", prediction)
    payload = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    rows = payload["cycle_transfer"]
    assert len(rows) == math.ceil(target_cycle)
    assert sum(row["selected_mass_g"] for row in rows) == pytest.approx(
        target_cycle * 200, abs=0.002
    )
    assert rows[-1]["ph_after"] == pytest.approx(11.4, abs=1e-6)
    assert all(row["selected_mass_g"] == pytest.approx(200) for row in rows[:-1])
    if target_cycle == 3:
        assert not rows[-1]["is_partial_charge"]
    form["carbonate_mode_enabled"] = False
    form["planning_stop_ph"] = 11.4
    ordinary = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    assert all(
        row["selected_mass_g"] == pytest.approx(200)
        for row in ordinary["cycle_transfer"]
    )


def test_declining_pressure_schedule_and_exhaustion(app):
    """Use 15-PSIg cylinder declines and retain exact per-cycle report instructions.

    Takes the app fixture; runs local Planning objects with real chemistry.
    Returns None and raises on a fabricated pressure, an extra unsupplied cycle,
    incorrect endpoint mass, or a report that repeats a fixed full pressure.
    """
    pressures = [730, 715, 700, 685, 670, 655]
    harness, form, params = setup_plan(
        app, planning_charge_pressures_psig=", ".join(map(str, pressures))
    )
    payload = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    rows = payload["cycle_transfer"]
    assert len(rows) <= len(pressures)
    assert rows[-1]["ph_after"] == pytest.approx(11.4, abs=1e-5)
    for index, row in enumerate(rows):
        assert row["available_charge_pressure_psig"] == pressures[index]
        assert row["peak_pressure_psi"] <= pressures[index] + 1e-6
        inventory = app._python_carbonate_pressure_drop_inventory_core(
            high_psig=row["peak_pressure_psi"],
            delta_psig=row["delta_pressure_psi"],
            headspace_volume_l=1.49,
            temperature_c=28.4,
        )
        assert row["selected_moles"] == pytest.approx(inventory["dose_mol"])
        if index < len(rows) - 1:
            assert row["peak_pressure_psi"] == pressures[index]
    assert rows[1]["selected_mass_g"] < rows[0]["selected_mass_g"]
    forecast = payload["carbonate_forecast"]
    plan = forecast["operator_dosing_plan"]
    assert plan["full_cycles_before_guard"] == len(rows) - 1
    assert plan["max_final_partial_co2_g"] == pytest.approx(rows[-1]["selected_mass_g"])
    assert forecast["estimated_cycles"] == pytest.approx(
        len(rows) - 1 + rows[-1]["cycle_charge_fraction"]
    )
    report = app._build_planning_pdf_report(
        {
            "workflow_key": "Planning",
            "inputs": form,
            "cycle_payload": payload,
            "timeline": rows,
        },
        sections=(),
    )
    summary = str(report["models"][0])
    assert "Per-cycle schedule" in summary
    assert "equivalent full cycles" not in summary
    for row in plan["full_cycle_schedule"]:
        assert f"{row['charge_pressure_psig']:.1f} PSIg" in summary
    form["planning_charge_pressures_psig"] = "730, 715"
    exhausted = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    assert len(exhausted["cycle_transfer"]) == 2
    assert "exhausted" in exhausted["projection_warning"]
    assert not exhausted["carbonate_forecast"].get("operator_dosing_plan")


def test_pressure_list_validation(app):
    """Reject incomplete pressure lists and incompatible manual dosing inputs.

    Takes the app fixture; returns None with local-only form mutation. Invalid
    lists must raise ValueError rather than skipping a cycle or inventing values.
    """
    assert app._parse_planning_charge_pressures("730, 715;700\n685") == [
        730,
        715,
        700,
        685,
    ]
    for text in ("730,,700", "730, nan", "730, -1", "730,", "730, bad"):
        with pytest.raises(ValueError):
            app._parse_planning_charge_pressures(text)
    harness, form, params = setup_plan(
        app, planning_cycle_co2_g=200, planning_charge_pressures_psig="730,715"
    )
    with pytest.raises(ValueError, match="clear the manual"):
        harness._generate_planning_cycle_payload(form, SimpleNamespace(params=params))
    form["planning_cycle_co2_g"] = None
    form["planning_cycle_delta_p_psi"] = 100
    form["planning_charge_pressures_psig"] = "730, 620"
    with pytest.raises(ValueError, match="trough"):
        harness._generate_planning_cycle_payload(form, SimpleNamespace(params=params))


def test_incompatible_native_inventory_falls_back(app, monkeypatch):
    """Reject an older extension's inconsistent gas constant at both boundaries.

    Uses temporary backend doubles; no persistent settings are changed. Returns
    None and asserts that native inconsistency yields the Python inventory and
    inverse pressure instead of inconsistent final-cycle chemistry.
    """
    kwargs = dict(
        high_psig=550.0, delta_psig=550.0, headspace_volume_l=1.49, temperature_c=28.4
    )
    expected = app._python_carbonate_pressure_drop_inventory_core(**kwargs)
    bad_inventory = {**expected, "dose_mol": expected["dose_mol"] * 1.001}
    inverse_args = dict(
        target_dose_mol=expected["dose_mol"],
        trough_psig=0.0,
        maximum_charge_psig=730.0,
        headspace_volume_l=1.49,
        temperature_c=28.4,
    )
    monkeypatch.setattr(app, "_load_rust_backend", lambda: None)
    expected_charge = app._python_carbonate_charge_pressure_setpoint_core(
        **inverse_args
    )
    backend = SimpleNamespace(
        carbonate_pressure_drop_inventory_core=lambda **kwargs: bad_inventory,
        carbonate_charge_pressure_setpoint_core=lambda **kwargs: {
            **expected_charge,
            "charge_pressure_psig": 560.0,
        },
    )
    monkeypatch.setattr(app, "_load_rust_backend", lambda: backend)
    monkeypatch.setattr(app, "_run_rust_kernel_with_timeout", lambda name, run: run())
    assert app._carbonate_pressure_drop_inventory_core(**kwargs) == expected
    assert (
        app._python_carbonate_charge_pressure_setpoint_core(**inverse_args)
        == expected_charge
    )


def test_requested_final_pressure_is_reflected_in_fourth_row(app):
    """Reproduce three declining full charges followed by a 550-to-0 PSIg dose.

    Uses a real-model target obtained independently from the specified pressure
    inventories. Returns None; local-only objects are created. Raises if the
    fourth row repeats a full dose or does not recover the 550 PSIg endpoint.
    """
    pressures = [730, 715, 700, 685]
    doses = [
        app._python_carbonate_pressure_drop_inventory_core(
            high_psig=pressure,
            delta_psig=pressure,
            headspace_volume_l=1.49,
            temperature_c=28.4,
        )["dose_mol"]
        for pressure in [*pressures[:3], 550]
    ]
    model = app.get_speciation_model("naoh_co2_pitzer_hmw")
    target, _species = model.predict_planning_ph(
        planning_context={
            "naoh_mass_g": 1120.0,
            "solution_volume_l": 2.51,
            "temperature_c": 28.4,
            "headspace_volume_l": 1.49,
        },
        cumulative_co2_moles=sum(doses),
        cycle_index=4,
    )
    assert 10.5 <= target <= 12.4
    harness, form, params = setup_plan(
        app,
        planning_charge_pressures_psig=pressures,
        carbonate_target_ph=target,
        mass_naoh_g=1120.0,
        reaction_naoh_mass=1120.0,
    )
    payload = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    rows = payload["cycle_transfer"]
    assert len(rows) == 4
    assert rows[-1]["selected_moles"] == pytest.approx(doses[-1], abs=1e-5)
    assert rows[-1]["delta_pressure_psi"] == pytest.approx(550, abs=0.01)
    assert rows[-1]["peak_pressure_psi"] == pytest.approx(550, abs=0.01)
    assert rows[-1]["ph_after"] == pytest.approx(target, abs=1e-5)
