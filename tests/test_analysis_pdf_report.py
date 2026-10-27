"""Validate saved Analysis report provenance, optional content and PDF layout."""

from types import SimpleNamespace

import pytest
from pypdf import PdfReader

pytest_plugins = ("test_reaction_endpoint_calibration",)


@pytest.fixture
def analysis_result(app):
    """Return independent measured/calculated data; no external state is changed."""
    return {
        "analysis_report_snapshot": app._freeze_analysis_pdf_snapshot(
            {"reaction_naoh_mass": 1000}, {"gas_molar_mass": 44.01}
        ),
        "analysis_measured_ph_anchor": {"cycle_index": 2, "measured_ph": 11.2},
        "timeline": [
            {"cycle_id": 0, "ph": 14},
            *[
                {
                    "cycle_id": index,
                    "peak_pressure_psi": 730 - index * 15,
                    "trough_pressure_psi": 0,
                    "delta_pressure_psi": 730 - index * 15,
                    "temperature_c": 25,
                    "co2_added_mass_g": 100,
                    "cumulative_co2_added_mass_g": 100 * index,
                    "corrected_cycle_co2_g": 90,
                    "corrected_cumulative_co2_g": 90 * index,
                    "calculated_ph": 14 - index,
                    "calibrated_estimated_ph": 13.2 - index,
                    "actual_ph": 14 - index,
                    "fractions": {"CO3^2-": 0.8, "HCO3-": 0.2},
                }
                for index in (1, 2)
            ],
        ],
    }


def test_snapshot_and_provenance(app, analysis_result):
    """Check frozen inputs and explicit observations; raises on invented data."""
    form = {"model_options": {"key": "original"}}
    payload = {"cycle_transfer": [{"cycle_id": 1}]}
    snapshot = app._freeze_analysis_pdf_snapshot(form, payload)
    form["model_options"]["key"] = "changed"
    payload["cycle_transfer"].clear()
    assert snapshot["inputs"]["model_options"]["key"] == "original"
    assert len(snapshot["cycle_payload"]["cycle_transfer"]) == 1
    report = app._build_analysis_pdf_report(analysis_result, sections=["plot"])
    assert len(report["plot_rows"]) == 2
    assert report["plot_rows"][0]["observed_ph"] is None
    assert report["plot_rows"][1]["observed_ph"] == 11.2
    assert report["plot_rows"][0]["trough"] == 0
    assert report["plot_rows"][1]["raw_total_g"] == 200
    assert report["plot_rows"][1]["corrected_total_g"] == 180
    minimal = app._build_analysis_pdf_report(analysis_result, sections=[])
    assert not minimal["plot_rows"]
    assert len(minimal["models"]) == 2
    analysis_result["analysis_report_snapshot"]["workflow_key"] = "Planning"
    with pytest.raises(ValueError, match="Analysis"):
        app._build_analysis_pdf_report(analysis_result, sections=[])


@pytest.mark.parametrize("orientation", ["portrait", "landscape"])
def test_pdf_content_and_layout(app, analysis_result, tmp_path, orientation):
    """Write/read a PDF and verify table fit and landscape plots; closes figures."""
    report = app._build_analysis_pdf_report(
        analysis_result, sections=[key for key, _ in app.ANALYSIS_PDF_REPORT_SECTIONS]
    )
    preferences = app._normalize_reaction_dashboard_export_preferences(
        {"orientation": orientation, "font_size": 10}
    )
    figures = app._render_analysis_pdf_report(report, preferences, dpi=100)
    for index, figure in enumerate(figures, 1):
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
    path = tmp_path / "analysis.pdf"
    figures[0].savefig(tmp_path / "summary.png")
    figures[-1].savefig(tmp_path / "plot.png")
    app._write_reaction_dashboard_cycle_pdf(path, figures, report["metadata"])
    pdf = PdfReader(path)
    assert pdf.pages[-1].mediabox.width > pdf.pages[-1].mediabox.height
    for page in pdf.pages[:-1]:
        assert (page.mediabox.width > page.mediabox.height) == (
            orientation == "landscape"
        )
    text = "\n".join(page.extract_text() for page in pdf.pages)
    assert "11.20" in text
    assert "715" in text
    assert "Analysis" in pdf.metadata.title


def test_legacy_results_and_missing_data(app, analysis_result):
    """Allow historical cycles without inventing inputs or measured pH values."""
    analysis_result.pop("analysis_report_snapshot")
    analysis_result.pop("analysis_measured_ph_anchor")
    analysis_result["analysis_dashboard"] = {}
    report = app._build_analysis_pdf_report(
        analysis_result, sections=["inputs", "plot"]
    )
    assert "no frozen run inputs" in str(report)
    assert all(row["observed_ph"] is None for row in report["plot_rows"])
    analysis_result["timeline"] = []
    with pytest.raises(ValueError, match="real cycle data"):
        app._build_analysis_pdf_report(analysis_result, sections=[])


def test_analysis_action_state(app, analysis_result):
    """Check mode/pending gating with widget stand-ins; mutates only local state."""
    state = {}
    harness = SimpleNamespace(
        _sol_analysis_pdf_btn=SimpleNamespace(
            configure=lambda **kwargs: state.update(kwargs),
            grid=lambda: state.update(visible=True),
            grid_remove=lambda: state.update(visible=False),
        ),
        _current_solubility_workflow=lambda: "Analysis",
        _get_cycle_result_for_workflow=lambda workflow: analysis_result,
    )
    app.UnifiedApp._update_analysis_pdf_action_state(harness, True)
    assert state == {"visible": True, "state": "normal"}
    harness._analysis_pdf_pending = True
    app.UnifiedApp._update_analysis_pdf_action_state(harness, True)
    assert state["state"] == "disabled"
    harness._current_solubility_workflow = lambda: "Planning"
    app.UnifiedApp._update_analysis_pdf_action_state(harness, True)
    assert state == {"visible": False, "state": "disabled"}
