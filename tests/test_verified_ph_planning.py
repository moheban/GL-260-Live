"""Verified carbonate run reuse, isotope inventory and shared-input checks."""

from types import SimpleNamespace

import pytest

from ph_anchor_calibration import completed_reference, select_verified_run

pytest_plugins = ("test_reaction_endpoint_calibration",)


def reference_run(app):
    """Return the confirmed five-charge fixture with measured mass and pH anchors.

    Uses measured PSIg/Celsius and 656.9 g of 45.002 g/mol gas. Returns a new
    reference mapping; changes no settings or source data. Solver errors propagate.
    """
    peaks = [730.0, 689.3, 664.4, 480.8, 721.6]
    troughs = [1.6, -1.9, 0.3, 0.9, -10.0]
    temperatures = [
        31.496455505278945,
        46.90438202247217,
        55.65202205882355,
        58.91407702523238,
        30.614425066508556,
    ]
    payload = app._replay_mass_calibrated_payload(
        dict(
            gas_molar_mass=45.002,
            cycle_transfer=[
                dict(
                    cycle_id=i + 1,
                    peak_pressure_psi=p,
                    trough_pressure_psi=t,
                    mean_temperature_c=c,
                )
                for i, (p, t, c) in enumerate(
                    zip(peaks, troughs, temperatures, strict=True)
                )
            ],
        ),
        656.9,
    )
    rows = payload["cycle_transfer"]
    return dict(
        reference_id="confirmed five-charge carbonate run",
        verified=True,
        completed=True,
        profile_key="test",
        naoh_mass_g=1100.0,
        water_mass_g=2200.0,
        solution_volume_l=2.51,
        temperature_c=28.266269580325194,
        gas_molar_mass=45.002,
        nominal_vessel_volume_l=4.0,
        effective_headspace_volume_l=payload["replay_mass_calibration"][
            "headspace_volume_l"
        ],
        measured_mass_g=656.9,
        cycle_temperatures_c=temperatures,
        observations=[
            (rows[3]["cumulative_co2_moles"], 13.01),
            (rows[4]["cumulative_co2_moles"], 11.21),
        ],
    )


@pytest.mark.parametrize(
    "pressures",
    ["730,689.3,664.4,480.8,721.6", "730,689,663,638,613,588"],
)
def test_verified_plan_uses_measured_mass_and_cycle_count(app, pressures):
    """Reproduce the reported discrepancy using real model, pressure math and planner.

    Uses compatible water/NaOH but competing legacy liquid volume to prove the
    measured run is retained. Checks target uptake and count, isotope accounting
    and provenance. Only an in-memory harness is changed.
    """
    from test_planning_partial_endpoint import setup_plan

    record = reference_run(app)
    harness, form, params = setup_plan(app, planning_charge_pressures_psig=pressures)
    params = app.replace(
        params,
        water_mass_g=2200.0,
        solution_volume_l=2.25,
        temperature_c=record["temperature_c"],
        headspace_volume_l=1.75,
    )
    harness.settings = {
        "verified_ph_reference_runs": [record],
        "vdw_gas_molar_mass": 45.002,
    }
    harness._analysis_profile_key = lambda: "next run workspace"
    form.update(water_mass_g=2200.0, reaction_solution_volume=2.25)
    payload = harness._generate_planning_cycle_payload(
        form, SimpleNamespace(params=params)
    )
    low, high = record["observations"]
    target_mol = low[0] + (high[0] - low[0]) * (low[1] - 11.4) / (low[1] - high[1])
    assert payload["verified_reference"]["reference_id"] == record["reference_id"]
    assert payload["total_moles_vdw"] == pytest.approx(target_mol, abs=1e-5)
    assert payload["gas_molar_mass"] == 45.002
    rows = payload["cycle_transfer"]
    assert len(rows) in (5, 6)
    assert rows[-1]["ph_after"] == pytest.approx(11.4, abs=1e-6)
    assert sum(r["selected_mass_g"] for r in rows) == pytest.approx(
        target_mol * 45.002, abs=0.001
    )
    assert 4 < payload["carbonate_forecast"]["estimated_cycles"] < 6
    final = rows[-1]
    plan = payload["carbonate_forecast"]["operator_dosing_plan"]
    assert plan["max_final_partial_co2_g"] == pytest.approx(final["selected_mass_g"])
    assert plan["final_partial_charge_pressure_psig"] == pytest.approx(
        final["peak_pressure_psi"]
    )
    inverse_check = app._carbonate_pressure_drop_inventory_core(
        high_psig=final["peak_pressure_psi"],
        delta_psig=final["delta_pressure_psi"],
        headspace_volume_l=record["effective_headspace_volume_l"],
        temperature_c=final["mean_temperature_c"],
    )
    assert inverse_check["dose_mol"] == pytest.approx(final["selected_moles"], abs=1e-6)
    model = app.get_speciation_model("naoh_co2_pitzer_hmw")
    timeline = app.solubility_simulate_cycle_timeline(
        params,
        rows,
        model=model,
        ph_model=model,
        reaction_context=dict(
            form,
            naoh_mass_g=1100.0,
            solution_volume_l=2.25,
            temperature_c=record["temperature_c"],
            target_ph=11.4,
        ),
    )
    assert timeline["total_added_mass_g"] == pytest.approx(
        target_mol * 45.002, abs=0.001
    )
    assert timeline["timeline"][-1]["ph"] == pytest.approx(11.4, abs=1e-6)
    print(
        "Verified plan:",
        pressures,
        target_mol * 45.002,
        "g;",
        payload["carbonate_forecast"]["estimated_cycles"],
        "cycles",
    )


def test_partial_run_cannot_replace_completed_reference(app):
    """Check recipe gates and completed-reference retention without file writes."""
    record = reference_run(app)
    context = dict(record, solution_volume_l=2.25, temperature_c=29.0)
    partial = dict(record, completed=False, reference_id="current partial run")
    assert (
        select_verified_run([record, partial], context, "test")["reference_id"]
        == record["reference_id"]
    )
    assert (
        select_verified_run([record], dict(context, water_mass_g=4000.0), "test")
        is None
    )
    assert (
        select_verified_run([record], dict(context, gas_molar_mass=44.0095), "test")
        is None
    )
    assert (
        completed_reference(
            record,
            dict(measured_mass_g=656.9, headspace_volume_l=1.3, cycle_count=5),
            [dict(cycle_index=4, measured_ph=13.01)],
            11.4,
            5,
            "test",
        )
        is None
    )
    assert record["observations"][-1][0] * 45.002 == pytest.approx(656.9)


def test_shared_recipe_variables_and_independent_liquor_volume(app, monkeypatch):
    """Use a headless Tcl interpreter to verify both screens share editable values.

    No windows or files are created. The carbonate solvent callback must preserve
    measured solution liters independently of solvent grams. Tk errors propagate.
    """
    interp = app.tk.Tcl()
    original = app.tk.StringVar
    monkeypatch.setattr(
        app.tk, "StringVar", lambda *args, **kwargs: original(master=interp)
    )
    monkeypatch.setattr(
        app,
        "settings",
        {"solubility_inputs": {"mass_naoh_g": "1100", "solution_volume_l": "2.51"}},
    )
    harness = SimpleNamespace(
        _bind_setting_var=lambda var, path, **kw: var.set(
            app.settings[path[0]].get(path[1], kw["default"])
        )
    )
    create = app.UnifiedApp._create_persistent_solubility_var
    planning = create(harness, "solution_volume_l")
    analysis = create(harness, "reaction_solution_volume_l")
    assert planning is analysis
    analysis.set("2.60")
    assert planning.get() == "2.60"
    assert create(harness, "mass_naoh_g") is create(harness, "reaction_naoh_mass_g")
    water = original(master=interp, value="2200")
    harness._solubility_vars = {"solution_volume_l": planning, "water_mass_g": water}
    harness._carbonate_mode_enabled_var = SimpleNamespace(get=lambda: True)
    app.UnifiedApp._sync_solvent_entries(harness)
    assert planning.get() == "2.60"
    assert water.get() == "2200"
