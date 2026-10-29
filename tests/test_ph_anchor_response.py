"""Focused measured-pH response and authoritative uptake integration checks."""

from types import SimpleNamespace

import pytest

from ph_anchor_calibration import compatible_points, fit_response, response_ph

pytest_plugins = ("test_reaction_endpoint_calibration",)


def test_interpolation_retains_learning_and_inventory():
    """Fit two anchors; verify intervening and future pH, with unchanged mol inputs."""
    uptake = [1.0, 2.0, 3.0, 4.0]
    predicted, points, records = fit_response(
        uptake,
        [13.0, 12.8, 12.5, 12.0],
        [dict(cycle_index=1, measured_ph=12.0), dict(cycle_index=3, measured_ph=11.0)],
    )
    assert uptake == [1.0, 2.0, 3.0, 4.0]
    assert predicted == pytest.approx([12.0, 11.55, 11.0, 10.5])
    assert all(abs(row["residual_after"]) < 1e-12 for row in records)
    assert response_ph(5.0, 11.0, points, lambda *args: 99.0) == pytest.approx(9.5)


def test_fixed_uptake_real_model(app):
    """Use real chemistry to verify uptake identity, anchor fit and target inversion."""
    form = dict(
        reaction_naoh_mass=1100.0,
        reaction_solution_volume=2.51,
        reaction_target_ph=11.4,
        params=SimpleNamespace(temperature_c=28.4, water_mass_g=2510.0),
    )
    doses = [3.0, 3.0, 3.0, 3.0]
    anchors = [
        dict(cycle_index=2, measured_ph=12.1),
        dict(cycle_index=4, measured_ph=11.8),
    ]
    payload = app._fixed_uptake_ph_calibration(
        [{}] * 4, doses, anchors, "naoh_co2_pitzer_hmw", form
    )
    assert payload["solver_status"] == "ok"
    assert payload["corrected_cycle_uptake_mol_series"] == doses
    assert payload["corrected_cumulative_co2_mol_series"] == [3.0, 6.0, 9.0, 12.0]
    assert payload["corrected_ph_series"][1] == pytest.approx(12.1)
    assert payload["corrected_ph_series"][-1] == pytest.approx(11.8)
    assert not payload["uptake_scaling_applied"]
    record = payload["response_record"]
    assert compatible_points(record, "naoh_co2_pitzer_hmw", record)
    assert not compatible_points(record, "other", record)
    context = dict(record, ph_response_points=record["points"])
    ph, _, source, _ = app._predict_planning_ph_for_model(
        app.get_speciation_model("naoh_co2_pitzer_hmw"),
        planning_context=context,
        cumulative_co2_moles=payload["co2_required_for_target_ph_mol"],
        cycle_index=5,
    )
    assert source == "measured_anchor_response"
    assert ph == pytest.approx(11.4, abs=1e-6)


def test_native_response_parity_or_fallback(app):
    """Check installed native kernel when available and explicit failing fallback."""
    backend = app._load_rust_backend()
    native = getattr(backend, "ph_anchor_response_core", None)
    for uptake in (0.0, 1.0, 2.0, 3.0, 5.0):
        expected = response_ph(uptake, 12.0, [(1.0, -1.0), (3.0, -2.0)])
        if native:
            assert native(uptake, 12.0, [(1.0, -1.0), (3.0, -2.0)]) == pytest.approx(
                expected
            )
        assert response_ph(uptake, 12.0, [(1.0, -1.0), (3.0, -2.0)], native) == expected


def test_planning_uses_saved_response_for_endpoint(app, monkeypatch):
    """Verify saved anchors change actual Planning doses and survive timeline replay.

    Uses a deterministic model and real planner/pressure calculations. Only local
    settings are changed; assertions check endpoint pH and fixed gas accounting.
    """
    from test_planning_partial_endpoint import setup_plan

    harness, form, params = setup_plan(app)
    model = SimpleNamespace(
        key="naoh_co2_pitzer_hmw",
        predict_planning_ph=lambda **kw: (
            13.8 - 0.1 * kw["cumulative_co2_moles"],
            None,
        ),
    )
    monkeypatch.setattr(app, "get_speciation_model", lambda key: model)
    harness.settings["measured_ph_response_calibration"] = dict(
        model_key=model.key,
        naoh_mass_g=1100.0,
        solution_volume_l=2.51,
        temperature_c=28.4,
        points=[(6.0, -1.0), (12.0, -1.0)],
    )
    payload = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    rows = payload["cycle_transfer"]
    assert payload["total_moles_vdw"] == pytest.approx(14.0, abs=1e-5)
    assert rows[-1]["ph_after"] == pytest.approx(11.4, abs=1e-6)
    assert rows[-1]["ph_response_points"] == [(6.0, -1.0), (12.0, -1.0)]
    assert sum(row["selected_moles"] for row in rows) == pytest.approx(
        payload["total_moles_vdw"]
    )


def test_analysis_application_keeps_entered_uptake(app, monkeypatch):
    """Run Analysis calibration wiring with real row mapping and in-memory settings.

    A linear chemistry model isolates response learning; no files or UI change.
    Asserts anchor agreement, unmeasured prediction and untouched uptake columns.
    """
    anchors = [
        dict(cycle_index=1, measured_ph=12.0),
        dict(cycle_index=3, measured_ph=11.0),
    ]
    model = SimpleNamespace(
        predict_planning_ph=lambda **kw: (14.0 - kw["cumulative_co2_moles"] * 0.2, None)
    )
    monkeypatch.setattr(app, "get_speciation_model", lambda key: model)
    harness = SimpleNamespace(
        settings={},
        _resolve_workflow_model_keys=lambda *args: ("test", "test", True),
        _analysis_calibration_basis_signature=lambda form: {},
        _analysis_resolve_measured_anchors=lambda **kw: anchors,
        _analysis_anchor_learning_controls=lambda form: {"learning_enabled": True},
        _analysis_profile_key=lambda: "test",
        _analysis_store_profile_calibration=lambda **kw: None,
    )
    rows = [
        dict(
            cycle_id=i,
            co2_moles=1.0,
            co2_mass_g=app.SOL_MW_CO2,
            equilibrium_ph=14.0 - i * 0.2,
        )
        for i in range(1, 5)
    ]
    form = dict(
        workflow_key="Analysis",
        reaction_naoh_mass=100.0,
        reaction_solution_volume=1.0,
        reaction_target_ph=10.0,
        temperature_c=25.0,
    )
    result, payload, _ = app.UnifiedApp._apply_analysis_measured_ph_calibration(
        harness, rows, form_snapshot=form, reference_trace={}
    )
    assert [r["corrected_cycle_co2_mol"] for r in result] == [1.0] * 4
    assert [r["co2_moles"] for r in result] == [1.0] * 4
    assert [r["corrected_ph"] for r in result] == pytest.approx(
        [12.0, 11.5, 11.0, 10.8]
    )
    assert payload["anchor_residual_after"] == pytest.approx(0.0)
    assert harness.settings["measured_ph_response_calibration"]["points"]
    assert all("corrected_ph" not in r for r in rows)


def test_dashboard_uses_learned_target_over_uncalibrated_guidance(app):
    """Check dashboard target precedence with conflicting legacy guidance.

    Uses in-memory rows/settings and real dashboard assembly; no UI or file writes.
    Learned target and remaining dose must agree with the unchanged uptake.
    """
    harness = SimpleNamespace(
        _analysis_uptake_correction=None,
        _analysis_anchor_fit_tolerance_ph=lambda: 0.1,
        _resolve_workflow_model_keys=lambda *args: (
            app.DEFAULT_SPEC_MODEL_KEY,
            app.DEFAULT_SPEC_MODEL_KEY,
            True,
        ),
    )
    for name in (
        "_analysis_dashboard_fraction_fallback",
        "_build_analysis_reference_series",
    ):
        setattr(harness, name, getattr(app.UnifiedApp, name).__get__(harness))
    rows = [
        dict(
            cycle_id=1,
            co2_moles=1.0,
            co2_mass_g=app.SOL_MW_CO2,
            cumulative_co2_added_moles=1.0,
            cumulative_co2_added_mass_g=app.SOL_MW_CO2,
            corrected_cumulative_co2_mol=1.0,
            corrected_cumulative_co2_g=app.SOL_MW_CO2,
            corrected_ph=11.8,
            ph=12.5,
            co2_to_target_g=1.0,
        )
    ]
    correction = dict(
        solver_status="ok",
        uptake_correction_mode="fixed_uptake_ph_response",
        co2_required_for_target_ph_g=100.0,
        co2_required_for_target_ph_mol=100.0 / app.SOL_MW_CO2,
    )
    result = app.UnifiedApp._build_analysis_dashboard_data(
        harness,
        rows,
        form_data=dict(
            workflow_key="Analysis",
            params=app.SolubilityInputs(
                mass_na_hco3_g=1.0, water_mass_g=1000.0, solution_volume_l=1.0
            ),
            reaction_naoh_mass=100.0,
            reaction_solution_volume=1.0,
            reaction_target_ph=11.4,
            _analysis_uptake_correction=correction,
        ),
    )
    summary = result["summary"]
    assert summary["co2_requirement_source"] == "measured_ph_calibration"
    assert summary["co2_required_for_target_ph_g"] == pytest.approx(100.0)
    assert summary["additional_co2_required_g"] == pytest.approx(100.0 - app.SOL_MW_CO2)
