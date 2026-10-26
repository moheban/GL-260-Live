"""Focused validation of saved Planning report content, layout and UI gating."""

import copy
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

pytest_plugins = ("test_reaction_endpoint_calibration",)


@pytest.fixture
def baseline():
    """Return a synthetic completed plan with a non-linear final pressure setpoint.

    Takes no inputs, returns a fresh mapping and has no side effects. Values make
    accidental fraction-times-pressure calculations visible in report checks.
    """
    return {
        "workflow_key": "Planning",
        "created_at": "2026-10-26T10:30:00",
        "inputs": {
            "reaction_naoh_mass": 1100,
            "reaction_solution_volume": 2.5,
            "planning_total_vessel_volume_l": 4,
            "planning_headspace_volume_l": 1.5,
            "planning_headspace_pressure_high_psi": 780,
            "planning_cycle_delta_p_psi": 780,
            "planning_ph_model_key": "naoh_co2_pitzer_hmw",
            "planning_spec_model_key": "naoh_co2_pitzer_hmw",
        },
        "cycle_payload": {
            "carbonate_forecast": {
                "estimated_cycles": 3.65,
                "target_ph": 11.4,
                "guard_ph": 11.65,
                "estimated_total_co2_g": 730,
                "cycle_size_median_g": 200,
                "speciation_verified": False,
                "speciation_message": "Target speciation requires review.",
                "operator_dosing_plan": {
                    "full_cycles_before_guard": 3,
                    "final_partial_cycle_fraction": 0.65,
                    "max_final_partial_co2_g": 130,
                    "final_partial_charge_pressure_psig": 590,
                    "final_partial_trough_pressure_psig": 0,
                    "final_partial_charge_delta_psi": 590,
                    "final_partial_pressure_source": "co2_vdw_absolute_inventory",
                },
            }
        },
        "timeline": [
            {
                "cycle_id": index,
                "co2_added_mass_g": 200,
                "cumulative_co2_added_mass_g": 200 * index,
                "ph": 14 - index * 0.7,
                "temperature_c": 28.4,
            }
            for index in range(1, 7)
        ],
    }


def test_snapshot_and_selected_content(app, baseline):
    """Check prominent instructions, optional exclusions and snapshot independence.

    Inputs are fixtures; returns None. Mutates only the local fixture after report
    construction and raises if original solver values are guessed or read later.
    """
    original = copy.deepcopy(baseline)
    report = app._build_planning_pdf_report(baseline, sections=[])
    assert baseline == original
    assert len(report["models"]) == 1
    cards = {row["label"]: row["value"] for row in report["models"][0]["kpis"]}
    assert cards["Full charge cycles"] == "3"
    assert cards["Full charge pressure"] == "780.0 PSIg"
    assert cards["Final charge pressure"] == "590.0 PSIg"
    assert "Cycle 4: charge from 0.0 to 590.0 PSIg" in str(report)
    assert "Target speciation requires review" in str(report)
    baseline["cycle_payload"]["carbonate_forecast"]["operator_dosing_plan"][
        "final_partial_charge_pressure_psig"
    ] = 100
    assert cards["Final charge pressure"] == "590.0 PSIg"
    assert not report["timeline"]


def test_integer_mass_and_invalid_schedules(app, baseline):
    """Check whole final charges, mass-only runs and incomplete saved forecasts.

    Local fixture mutations exercise presentation branches without computing gas
    inventories. Returns None and raises if a missing setpoint becomes a command.
    """
    forecast = baseline["cycle_payload"]["carbonate_forecast"]
    forecast["estimated_cycles"] = 4
    forecast["operator_dosing_plan"]["final_partial_cycle_fraction"] = 1
    report = app._build_planning_pdf_report(baseline, sections=[])
    assert report["models"][0]["kpis"][0]["value"] == "4"
    assert report["models"][0]["kpis"][2]["value"] == "Not required"
    forecast["estimated_cycles"] = 3.65
    forecast["operator_dosing_plan"]["final_partial_cycle_fraction"] = 0.65
    baseline["inputs"]["planning_cycle_co2_g"] = 200
    report = app._build_planning_pdf_report(baseline, sections=[])
    assert "130.000 g CO2" in str(report)
    assert report["models"][0]["kpis"][2]["value"] == "Mass dosing"
    baseline["inputs"].pop("planning_cycle_co2_g")
    forecast["operator_dosing_plan"].pop("final_partial_charge_pressure_psig")
    report = app._build_planning_pdf_report(baseline, sections=[])
    assert report["models"][0]["kpis"][2]["value"] == "Unavailable"
    forecast["estimated_cycles"] = 6
    report = app._build_planning_pdf_report(baseline, sections=[])
    assert "does not reach the modeled target" in str(report)
    baseline["timeline"] = []
    with pytest.raises(ValueError, match="Complete"):
        app._build_planning_pdf_report(baseline, sections=[])


@pytest.mark.parametrize("orientation", ["portrait", "landscape"])
def test_pdf_pages_and_metadata(app, baseline, tmp_path, orientation):
    """Render and read the actual compiled PDF in both supported orientations.

    Uses fixtures and pytest's temporary output path. Writes one PDF, closes all
    figures through the shared writer, and raises on lost content/page numbering.
    """
    sections = [key for key, _label in app.PLANNING_PDF_REPORT_SECTIONS]
    report = app._build_planning_pdf_report(baseline, sections=sections)
    preferences = app._normalize_reaction_dashboard_export_preferences(
        {"orientation": orientation, "font_size": 10}
    )
    figures = app._render_planning_pdf_report(report, preferences, dpi=100)
    assert len(figures) >= 6
    for index, figure in enumerate(figures, start=1):
        figure.canvas.draw()
        assert any(
            text.get_text() == f"Page {index} of {len(figures)}"
            for text in figure.texts
        )
        for axis in figure.axes:
            for table in axis.tables:
                for cell in table.get_celld().values():
                    text_box = cell.get_text().get_window_extent()
                    cell_box = cell.get_window_extent()
                    assert text_box.width <= cell_box.width + 3
                    assert text_box.height <= cell_box.height + 3
    path = tmp_path / f"planning-{orientation}.pdf"
    pages = app._write_reaction_dashboard_cycle_pdf(path, figures, report["metadata"])
    pdf = PdfReader(path)
    assert len(pdf.pages) == pages
    assert pdf.metadata.title == "Sodium Carbonate Run Plan"
    assert "Planning" in pdf.metadata.subject
    text = "\n".join(page.extract_text() for page in pdf.pages)
    assert "590.0 PSIg" in text
    assert "780.0 PSIg" in text
    assert "11.40" in text
    assert "Calculation Basis" in text
    assert "Full-Cycle Forecast" in text


def test_planning_only_ready_button(app, baseline):
    """Check visibility/readiness without creating a desktop window.

    Inputs are fixtures; local stand-ins record widget mutations. Returns None
    and raises if Analysis or a pending Planning run enables the report button.
    """
    state = {}
    button = SimpleNamespace(
        configure=lambda **kwargs: state.update(kwargs),
        grid=lambda: state.update(visible=True),
        grid_remove=lambda: state.update(visible=False),
    )
    harness = SimpleNamespace(
        _sol_planning_pdf_btn=button,
        _current_solubility_workflow=lambda: "Planning",
        _workflow_comparison_state=lambda: {"planning_baseline": baseline},
    )
    app.UnifiedApp._update_planning_pdf_action_state(harness, False)
    assert state == {"visible": True, "state": "disabled"}
    app.UnifiedApp._update_planning_pdf_action_state(harness, True)
    assert state["state"] == "normal"
    harness._planning_pdf_pending = True
    app.UnifiedApp._update_planning_pdf_action_state(harness, True)
    assert state["state"] == "disabled"
    harness._current_solubility_workflow = lambda: "Analysis"
    app.UnifiedApp._update_planning_pdf_action_state(harness, True)
    assert state == {"visible": False, "state": "disabled"}
