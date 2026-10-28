"""Focused replay calibration and measured-pH continuation checks."""

from types import SimpleNamespace

import pytest

pytest_plugins = ("test_reaction_endpoint_calibration",)


def real_cycles(app, volume=1.49):
    """Build four measured-cycle fixtures using the app and headspace in liters.

    Returns an independent payload with PSIg bounds, Celsius temperatures and
    molar uptake for round-trip tests. Changes no state; solver errors propagate.
    """
    rows = []
    for index, pressure in enumerate((730, 730, 730, 481), 1):
        dose = app._carbonate_pressure_drop_inventory_core(
            high_psig=pressure,
            delta_psig=pressure,
            headspace_volume_l=volume,
            temperature_c=28.4,
        )
        rows.append(
            dict(
                cycle_id=index,
                peak_pressure_psi=pressure,
                trough_pressure_psi=0,
                mean_temperature_c=28.4,
                selected_moles=dose["dose_mol"],
            )
        )
    return dict(
        cycle_transfer=rows, cycle_payload_origin="real_identified_cycle_analysis"
    )


def test_mass_round_trip_and_fallback(app, monkeypatch):
    """Recover known volume and mass through routed/fallback math without mutation."""
    payload = real_cycles(app)
    mass = sum(r["selected_moles"] for r in payload["cycle_transfer"]) * app.SOL_MW_CO2
    result = app._replay_mass_calibrated_payload(payload, mass)
    assert result["replay_mass_calibration"]["headspace_volume_l"] == pytest.approx(
        1.49
    )
    assert result["total_moles_vdw"] * app.SOL_MW_CO2 == pytest.approx(mass)
    assert "replay_mass_calibration" not in payload
    monkeypatch.setattr(app, "_load_rust_backend", lambda: None)
    fallback = app._replay_mass_calibrated_payload(payload, mass)
    assert fallback["total_moles_vdw"] == pytest.approx(result["total_moles_vdw"])
    for invalid in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            app._replay_mass_calibrated_payload(payload, invalid)


def test_anchor_forward_pressure_round_trip(app):
    """Verify a real model's pH-anchor dose and inverse pressure agree; no UI writes."""
    payload = real_cycles(app)
    form = dict(
        reaction_solution_volume=2.51,
        reaction_naoh_mass=1100,
        carbonate_mode_enabled=True,
        carbonate_target_ph=11.4,
        analysis_ph_model_key="naoh_co2_pitzer_hmw",
        params=SimpleNamespace(headspace_volume_l=1.49, temperature_c=28.4),
    )
    anchor = dict(cycle_index=4, measured_ph=11.8)
    result = app._replay_anchor_continuation(payload, form, anchor)
    assert result["remaining_co2_g"] > 0
    assert 0 < result["partial_charge_psig"] <= 730
    full = app._carbonate_pressure_drop_inventory_core(
        high_psig=730,
        delta_psig=730,
        headspace_volume_l=1.49,
        temperature_c=28.4,
    )["dose_g"]
    partial = app._carbonate_pressure_drop_inventory_core(
        high_psig=result["partial_charge_psig"],
        delta_psig=result["partial_charge_psig"],
        headspace_volume_l=1.49,
        temperature_c=28.4,
    )["dose_g"]
    assert result["remaining_co2_g"] == pytest.approx(
        result["full_cycles"] * full + partial
    )
    reached = app._replay_anchor_continuation(
        payload, form, dict(cycle_index=4, measured_ph=11.3)
    )
    assert reached["remaining_co2_g"] == 0
    assert reached["partial_charge_psig"] is None


@pytest.mark.parametrize("answer,mass", [(False, None), (True, None), (True, 500.0)])
def test_replay_prompt_routes_once(app, monkeypatch, answer, mass):
    """Exercise decline, cancel and accepted calibration through the UI handler.

    Uses in-memory widget/callback stubs; changes no real settings or windows.
    Assertions verify cancellation and the single calibrated Analysis dispatch.
    """
    payload = real_cycles(app)
    writes, runs, applied = [], [], []
    harness = SimpleNamespace(
        _get_cycle_payload_for_workflow=lambda workflow: payload,
        _analysis_cycle_signature_from_payload=lambda value: "source-cycles",
        _collect_solubility_form_data=lambda: {"reaction_solution_volume": 2.51},
        _solubility_vars={
            "analysis_total_vessel_volume_l": SimpleNamespace(set=writes.append)
        },
        _apply_cycle_payload_to_solubility=lambda **kwargs: applied.append(kwargs),
        _run_analysis_scenario=lambda **kwargs: runs.append(kwargs),
    )
    monkeypatch.setattr(app.messagebox, "askyesno", lambda *args, **kwargs: answer)
    monkeypatch.setattr(app.simpledialog, "askfloat", lambda *args, **kwargs: mass)
    monkeypatch.setattr(app.messagebox, "showinfo", lambda *args, **kwargs: None)
    app.UnifiedApp._prompt_replay_consumed_mass(harness)
    if answer and mass is not None:
        assert len(runs) == len(applied) == len(writes) == 1
        assert runs[0]["skip_apply"]
        calibrated = applied[0]["payload"]
        assert (
            calibrated["replay_mass_calibration"]["source_signature"] == "source-cycles"
        )
        assert calibrated["total_moles_vdw"] * app.SOL_MW_CO2 == pytest.approx(mass)
    else:
        assert not runs and not applied and not writes


def test_calibration_refresh_tracks_original_cycles(app):
    """Preserve calibration for its source but refresh when real observations change."""
    current = {
        "signature": "calibrated",
        "replay_mass_calibration": {"source_signature": "real"},
    }
    latest = {"signature": "real"}
    harness = SimpleNamespace(
        _real_cycle_analysis_payload_for_import=lambda: latest,
        _get_cycle_payload_for_workflow=lambda key: current,
        _analysis_cycle_signature_from_payload=lambda value: value["signature"],
    )
    assert not app.UnifiedApp._analysis_real_cycle_payload_needs_refresh(harness)
    latest["signature"] = "new-real-cycles"
    assert app.UnifiedApp._analysis_real_cycle_payload_needs_refresh(harness)


def test_saved_report_contains_calibration_and_charge(app):
    """Verify export consumes frozen calibration and recommendation without solving."""
    payload = app._replay_mass_calibrated_payload(real_cycles(app), 500.0)
    report = app._build_analysis_pdf_report(
        {
            "analysis_report_snapshot": app._freeze_analysis_pdf_snapshot({}, payload),
            "analysis_charge_recommendation": {"message": "Charge to 123.45 PSIg."},
            "timeline": [
                {
                    "cycle_id": 4,
                    "co2_added_mass_g": 50,
                    "cumulative_co2_added_mass_g": 500,
                    "ph": 11.8,
                }
            ],
        },
        sections=[],
    )
    notes = str(report["models"])
    assert "123.45 PSIg" in notes
    assert "500.000 g" in notes
    assert "inferred effective gas headspace" in notes


def test_continuation_accounts_for_later_cycles_and_full_charges(app, monkeypatch):
    """Check exact multi-charge accounting and stale-anchor uptake subtraction.

    A monotone model stub isolates scheduling from chemistry. Uses only local
    payloads and restores the model resolver through monkeypatch.
    """
    model = SimpleNamespace(
        predict_planning_ph=lambda **kwargs: (
            14 - 0.1 * kwargs["cumulative_co2_moles"],
            {},
        )
    )
    monkeypatch.setattr(app, "get_speciation_model", lambda key: model)
    payload = real_cycles(app)
    form = dict(
        reaction_solution_volume=2.51,
        reaction_naoh_mass=1100,
        reaction_target_ph=11.4,
        params=SimpleNamespace(headspace_volume_l=1.49, temperature_c=28.4),
    )
    current = app._replay_anchor_continuation(
        payload, form, dict(cycle_index=4, measured_ph=12)
    )
    earlier = app._replay_anchor_continuation(
        payload, form, dict(cycle_index=3, measured_ph=12)
    )
    assert current["remaining_co2_g"] == pytest.approx(6 * app.SOL_MW_CO2, abs=0.002)
    assert current["full_cycles"] >= 1
    assert earlier["remaining_co2_g"] == pytest.approx(
        current["remaining_co2_g"]
        - payload["cycle_transfer"][-1]["selected_moles"] * app.SOL_MW_CO2
    )
    with pytest.raises(ValueError):
        app._replay_anchor_continuation(
            payload,
            dict(form, reaction_target_ph=float("nan")),
            dict(cycle_index=4, measured_ph=12),
        )


def test_runtime_publishes_anchor_recommendation(app, monkeypatch):
    """Verify the Analysis runtime publishes continuation without losing pH outputs.

    Reuses the existing observed-pH runtime harness and stubs only the already
    separately tested chemistry helper. Captures in-memory output; no UI writes.
    """
    results = []
    original = app.UnifiedApp._build_analysis_runtime_payload

    def capture(self, **kwargs):
        """Capture a runtime result with carbonate enabled; propagate real errors."""
        kwargs["form_data"] = dict(kwargs["form_data"], carbonate_mode_enabled=True)
        result = original(self, **kwargs)
        results.append(result)
        return result

    monkeypatch.setattr(app.UnifiedApp, "_build_analysis_runtime_payload", capture)
    monkeypatch.setattr(
        app,
        "_replay_anchor_continuation",
        lambda payload, form, anchor, **kwargs: {
            "message": "Verified charge instruction",
            "anchor_cycle": anchor["cycle_index"],
            "remaining_co2_g": kwargs["remaining_co2_g"],
        },
    )
    app._regression_test_analysis_runtime_regime_prefers_actual_observed_ph()
    result = results[-1]
    assert result["charge_recommendation"]["anchor_cycle"] == 2
    assert "Verified charge instruction" in result["required_co2_text"]
    assert result["carbonate_forecast"]["status"] == "anchored_continuation"
    remaining = result["charge_recommendation"]["remaining_co2_g"]
    assert f"remaining {remaining:.2f} g" in result["required_co2_text"]



@pytest.mark.parametrize("remaining", [0.0, 126.24, 500.0])
def test_guidance_mass_drives_charge_pressure(app, monkeypatch, remaining):
    """Round-trip the displayed demand through pressure without re-solving pH.

    Uses screenshot headspace/temperature/trough inputs in L/C/PSIg and demand
    in grams. Exercises zero, partial and multiple charges, native routing and
    Python fallback. Local fixtures only; invalid demand must raise ValueError.
    """
    payload = real_cycles(app)
    payload["cycle_transfer"][-1]["trough_pressure_psi"] = 0.9
    form = dict(
        carbonate_mode_enabled=True,
        carbonate_target_ph=11.4,
        params=SimpleNamespace(headspace_volume_l=1.3516, temperature_c=29.26),
    )

    def forbidden(*args, **kwargs):
        """Reject a redundant pH model solve; no state is changed."""
        raise AssertionError("The guidance demand already owns the remaining dose")

    monkeypatch.setattr(app, "get_speciation_model", forbidden)
    anchor = dict(cycle_index=3, measured_ph=13.01)
    result = app._replay_anchor_continuation(
        payload, form, anchor, remaining_co2_g=remaining
    )
    assert result["remaining_co2_g"] == pytest.approx(remaining)
    assert result["dose_basis"] == "analysis_remaining"
    full = app._carbonate_pressure_drop_inventory_core(
        high_psig=730,
        delta_psig=729.1,
        headspace_volume_l=1.3516,
        temperature_c=29.26,
    )["dose_g"]
    partial = 0.0
    if result["partial_charge_psig"] is not None:
        partial = app._carbonate_pressure_drop_inventory_core(
            high_psig=result["partial_charge_psig"],
            delta_psig=result["partial_charge_psig"] - 0.9,
            headspace_volume_l=1.3516,
            temperature_c=29.26,
        )["dose_g"]
    assert result["full_cycles"] * full + partial == pytest.approx(remaining)
    monkeypatch.setattr(app, "_load_rust_backend", lambda: None)
    fallback = app._replay_anchor_continuation(
        payload, form, anchor, remaining_co2_g=remaining
    )
    assert fallback["partial_charge_psig"] == pytest.approx(
        result["partial_charge_psig"]
    )
    for invalid in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="Remaining CO2"):
            app._replay_anchor_continuation(
                payload, form, anchor, remaining_co2_g=invalid
            )



def test_measured_negative_gauge_cycle_calibrates(app, monkeypatch):
    """Reproduce the recorded cycle-2 negative trough without clamping observations.

    Builds local rows with the four recorded pressure/temperature pairs and fits
    an arbitrary positive mass. Checks native routing and Python-only results;
    no saved run or settings are mutated. Assertions expose dropped-cycle errors.
    """
    conditions = [
        (730.0, 1.6, 31.496455505278945),
        (689.3, -1.9, 46.90438202247217),
        (664.4, 0.3, 55.65202205882355),
        (480.8, 0.9, 58.91407702523238),
    ]
    payload = {
        "cycle_transfer": [
            dict(
                cycle_id=index,
                peak_pressure_psi=high,
                trough_pressure_psi=low,
                mean_temperature_c=temp,
            )
            for index, (high, low, temp) in enumerate(conditions, 1)
        ]
    }
    result = app._replay_mass_calibrated_payload(payload, 500.0)
    assert len(result["cycle_transfer"]) == 4
    assert result["cycle_transfer"][1]["trough_pressure_psi"] == -1.9
    assert result["total_moles_vdw"] * app.SOL_MW_CO2 == pytest.approx(500.0)
    volume = result["replay_mass_calibration"]["headspace_volume_l"]
    assert volume > 0
    recomputed = sum(
        app._python_carbonate_pressure_drop_inventory_core(
            high_psig=high,
            delta_psig=high - low,
            headspace_volume_l=volume,
            temperature_c=temp,
            allow_subatmospheric=True,
        )["dose_g"]
        for high, low, temp in conditions
    )
    assert recomputed == pytest.approx(500.0)
    monkeypatch.setattr(app, "_load_rust_backend", lambda: None)
    fallback = app._replay_mass_calibrated_payload(payload, 500.0)
    assert fallback["replay_mass_calibration"]["headspace_volume_l"] == pytest.approx(
        volume
    )
    payload["cycle_transfer"][1]["trough_pressure_psi"] = -20
    with pytest.raises(ValueError, match="Cycle 2.*absolute"):
        app._replay_mass_calibrated_payload(payload, 500.0)


def test_negative_gauge_inventory_and_inverse_preserve_planning_limits(app):
    """Check physical absolute bounds, negative-gauge inversion and legacy defaults.

    Pure calculations take PSIg, liters and Celsius; no external mutation beyond
    backend health routing. Raises on incorrect native/fallback pressure inventory.
    """
    inputs = dict(
        high_psig=-0.2, delta_psig=1.7, headspace_volume_l=1.49, temperature_c=25
    )
    dose = app._carbonate_pressure_drop_inventory_core(
        **inputs, allow_subatmospheric=True
    )
    charge = app._python_carbonate_charge_pressure_setpoint_core(
        target_dose_mol=dose["dose_mol"],
        trough_psig=-1.9,
        maximum_charge_psig=730,
        headspace_volume_l=1.49,
        temperature_c=25,
        allow_subatmospheric=True,
    )
    assert charge["charge_pressure_psig"] == pytest.approx(-0.2, abs=1e-8)
    with pytest.raises(ValueError):
        app._python_carbonate_pressure_drop_inventory_core(**inputs)
    with pytest.raises(ValueError):
        app._python_carbonate_charge_pressure_setpoint_core(
            target_dose_mol=dose["dose_mol"],
            trough_psig=-1.9,
            maximum_charge_psig=730,
            headspace_volume_l=1.49,
            temperature_c=25,
        )
    for high, drop in [(10, 24.696), (10, 25), (10, 0), (10, -1), (float("nan"), 1)]:
        with pytest.raises(ValueError):
            app._python_carbonate_pressure_drop_inventory_core(
                high_psig=high,
                delta_psig=drop,
                headspace_volume_l=1,
                temperature_c=25,
                allow_subatmospheric=True,
            )
