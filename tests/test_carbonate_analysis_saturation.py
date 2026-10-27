"""Check carbonate Analysis diagnostics use the finite Pitzer inventory."""

from types import SimpleNamespace

import pytest

pytest_plugins = ("test_reaction_endpoint_calibration",)


def test_finite_carbonate_diagnostics(app, monkeypatch):
    """Use real chemistry for four carbonate-rich cycles without generic solve.

    Imported app and monkeypatch fixtures isolate backend overrides. Asserts
    correct salt accounting and Python/native consistency without UI writes.
    """
    model = app.get_speciation_model("naoh_co2_pitzer_hmw")
    params = app.SolubilityInputs(
        mass_na_hco3_g=0,
        water_mass_g=2510,
        solution_volume_l=2.51,
        temperature_c=25,
        headspace_volume_l=1.38,
    )
    context = dict(
        workflow_key="Analysis",
        naoh_mass_g=1100,
        solution_volume_l=2.51,
        temperature_c=25,
        target_ph=11.4,
        carbonate_mode_enabled=True,
    )
    cycles = [dict(cycle_id=i, selected_moles=2.0) for i in range(1, 5)]

    def forbidden(*args, **kwargs):
        """Reject incompatible open-boundary chemistry; no side effects."""
        raise AssertionError("Generic bicarbonate solver must not be called")

    monkeypatch.setattr(model, "solve", forbidden)
    result = app.solubility_simulate_cycle_timeline(
        params, cycles, model=model, ph_model=model, reaction_context=context
    )
    assert not result["errors"]
    assert len(result["timeline"]) == 4
    for row in result["timeline"]:
        assert row["saturation_index"] < 1
        assert row["solid_nahco3_g"] == pytest.approx(0, abs=1e-8)
        assert row["fractions"]["HCO3-"] < 0.01
        assert row["solid_mass_g"] == pytest.approx(
            row["solid_na2co3_g"] + row["solid_nahco3_g"]
        )
        assert not any("NaHCO3 supersaturated" in w for w in row["warnings"])
        assert not any("charged NaHCO" in w for w in row["warnings"])
    monkeypatch.setattr(
        app, "_rust_pitzer_solve_total_carbon_core", lambda *a, **k: None
    )
    fallback = app.solubility_simulate_cycle_timeline(
        params, cycles, model=model, ph_model=model, reaction_context=context
    )
    assert not fallback["errors"]
    for native, python in zip(result["timeline"], fallback["timeline"], strict=True):
        assert native["saturation_index"] == pytest.approx(
            python["saturation_index"], rel=1e-4
        )
        assert native["calculated_ph"] == pytest.approx(
            python["calculated_ph"], abs=1e-4
        )


def test_nahcolite_activity_warning_is_not_suppressed(app, monkeypatch):
    """Check Q/K threshold using controlled activities, retaining true warnings.

    Uses the bundled phase constant and isolated unit activity coefficients;
    mutates no persisted data and raises assertions for wrong phase criteria.
    """
    model = app.get_speciation_model("naoh_co2_pitzer_hmw")
    context = dict(solution_volume_l=1.0, naoh_mass_g=40)
    species = dict(m_Na=1, m_H=1e-10, m_OH=1e-4, m_HCO3=0.01, m_CO3=1, m_CO2=0)
    monkeypatch.setattr(
        app._NAOH_PITZER_MODULE,
        "pitzer_gammas",
        lambda composition, params: ({k: 1.0 for k in composition}, 1.0),
    )
    result = app._finite_pitzer_cycle_speciation(model, context, 10, species)
    assert result.saturation_indices["NaHCO3"] == pytest.approx(10**0.742)
    assert any("supersaturated" in w for w in result.warnings)
    species["m_H"] = 1e-14
    assert not app._finite_pitzer_cycle_speciation(model, context, 14, species).warnings


def test_existing_ph_channel_ownership(app):
    """Run the existing independent-model channel contract without mutations."""
    app._regression_test_naoh_pitzer_analysis_calculated_ph_stays_trajectory_owned()


def test_parallel_uptake_chemistry(app):
    """Compare real VDW/corrected cases and preserve the source inventory.

    Uses one cycle spanning carbonate equivalence to distinguish chemistry;
    checks normalization preserves both cases, and absent correction stays
    absent. Only local objects are created; solver errors fail assertions.
    """
    model = app.get_speciation_model("naoh_co2_pitzer_hmw")
    params = app.SolubilityInputs(
        mass_na_hco3_g=0, water_mass_g=2510, solution_volume_l=2.51, temperature_c=25
    )
    context = dict(
        workflow_key="Analysis",
        naoh_mass_g=1100,
        solution_volume_l=2.51,
        temperature_c=25,
    )
    raw = app.solubility_simulate_cycle_timeline(
        params,
        [dict(cycle_id=1, selected_moles=12)],
        model=model,
        ph_model=model,
        reaction_context=context,
    )["timeline"]
    form = dict(
        params=params,
        _analysis_cycle_context=context,
        analysis_spec_model_key=model.key,
        analysis_ph_model_key=model.key,
    )
    pairs = app._analysis_uptake_basis_comparison(
        raw, [dict(raw[0], corrected_cycle_co2_mol=14)], form
    )
    left, right = pairs[0]["vdw"], pairs[0]["corrected"]
    assert left["uptake_g"] == pytest.approx(12 * app.SOL_MW_CO2)
    assert right["uptake_g"] == pytest.approx(14 * app.SOL_MW_CO2)
    assert left["consumed_g"] != right["consumed_g"]
    assert left["ph"] > right["ph"]
    assert left["fractions"] != right["fractions"]
    assert raw[0]["co2_moles"] == pytest.approx(12)
    row = dict(
        raw[0],
        uptake_basis_comparison=pairs[0],
        vdw_basis_result=app._analysis_basis_text(left),
        corrected_basis_result=app._analysis_basis_text(right),
    )
    for normalize in (
        app._python_cycle_timeline_normalize_core,
        app._rust_cycle_timeline_normalize_core,
    ):
        normalized = normalize([row])
        if normalized is not None:
            assert normalized[0]["uptake_basis_comparison"] == pairs[0]
            assert (
                normalized[0]["vdw_basis_result"]
                != normalized[0]["corrected_basis_result"]
            )
    absent = app._analysis_uptake_basis_comparison(raw, raw, form)
    assert absent[0]["corrected"]["uptake_g"] is None
    row["calculated_ph_corrected_co2"] = right["ph"]
    rendered_rows = [
        dict(row, corrected_cumulative_co2_g=100),
        dict(row, cycle_id=2, corrected_cumulative_co2_g=200),
    ]
    stub = SimpleNamespace(
        _resolve_cycle_timeline_view_entries=lambda *a, **k: (rendered_rows, False)
    )
    rendered = app.UnifiedApp._build_cycle_timeline_render_payload(
        stub,
        rendered_rows,
        workflow_key="Analysis",
        columns=("vdw_basis_result", "corrected_basis_result"),
    )
    assert rendered["tree_rows"][0]["vdw_basis_result"] == row["vdw_basis_result"]
    assert (
        rendered["tree_rows"][0]["corrected_basis_result"]
        == row["corrected_basis_result"]
    )
    assert all(r["calculated_ph_corrected_co2"] == right["ph"] for r in rendered_rows)
