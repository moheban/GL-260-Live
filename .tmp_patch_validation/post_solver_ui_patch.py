from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


@dataclass
class SolubilityStructuredPayload:
    highlights: Dict[str, str]
    warnings: List[str] = field(default_factory=list)
    species_rows: List[Dict[str, str]] = field(default_factory=list)
    saturation_rows: List[Dict[str, str]] = field(default_factory=list)
    sensitivity_rows: List[Dict[str, str]] = field(default_factory=list)
    sweep_rows: List[Dict[str, str]] = field(default_factory=list)
    sweep_plot: List[Dict[str, float]] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    chart_data: Dict[str, Any] = field(default_factory=dict)
    reaction_guidance: Optional[Dict[str, Any]] = None
    tracking_entries: List[Dict[str, Any]] = field(default_factory=list)
    cycle_timeline: Optional[List[Dict[str, Any]]] = None
    cycle_timeline_render_payload: Optional[Dict[str, Any]] = None
    planner_context: List[str] = field(default_factory=list)
    math_sections: List[Dict[str, Any]] = field(default_factory=list)
    math_preview_lines: List[str] = field(default_factory=list)
    mode_context: Dict[str, str] = field(default_factory=dict)
    workflow_key: str = ""
    guide_key: str = ""
    assumed_solution_volume_l: Optional[float] = None
    co2_guidance: str = ""
    reprocessing_context: Optional[Dict[str, Any]] = None
    analysis_dashboard: Optional[Dict[str, Any]] = None


class UnifiedApp:
    def _enable_speciation_debug_preset(self) -> None:
        """Enable a focused debug-category preset for speciation troubleshooting.

        Purpose:
            Turn on the most useful debug categories for Rust/speciation fallback
            diagnostics in one action.
        Why:
            Freeze/performance investigations require coordinated category toggles
            across engine/solver/fallback/runtime/performance scopes.
        Inputs:
            None.
        Outputs:
            None.
        Side Effects:
            Enables selected debug categories, enables global debug logging, and
            updates Runtime-tab status text.
        Exceptions:
            Category toggle failures are handled by existing setters.
        """
        self._set_debug_enabled(True)
        categories = (
            "speciation.engine",
            "speciation.solver",
            "speciation.chemistry",
            "speciation.results",
            "speciation.fallback",
            "speciation.runtime",
            "plotting.render",
            "perf.timing",
            "rust.backend",
        )
        for category in categories:
            self._set_debug_category_enabled(category, True)
        self._set_speciation_diagnostics_status("Speciation debug preset enabled.")

    def _post_solver_timeline_fragment(
        self,
        payload: SolubilityStructuredPayload,
        existing_entries: List[Dict[str, Any]],
    ) -> None:
        """Model the patched timeline-update branch in `_update_solubility_structured_widgets`.

        Purpose:
            Validate staged timeline routing and fallback control flow.
        Why:
            Keep patched-block lint/format checks scoped without processing the full
            application file.
        Inputs:
            payload: Structured payload emitted by the solver workflow.
            existing_entries: Existing tracking-entry fallback list.
        Outputs:
            None.
        Side Effects:
            Calls timeline/dashboard/tracking update helpers.
        Exceptions:
            Timeline staged apply failures fall back to synchronous timeline updates.
        """
        cycle_timeline = payload.cycle_timeline or []
        workflow_key = str(payload.workflow_key or self._current_solubility_workflow())
        timeline_render_payload_raw = payload.cycle_timeline_render_payload
        if cycle_timeline:
            timeline_rows = int(len(cycle_timeline))
            self._dbg(
                "plotting.render",
                "post_solver_timeline_stage_start workflow=%s timeline_rows=%s",
                workflow_key,
                timeline_rows,
            )
            try:
                timeline_render_payload = (
                    dict(timeline_render_payload_raw)
                    if isinstance(timeline_render_payload_raw, Mapping)
                    else {}
                )
                if not timeline_render_payload:
                    timeline_render_payload = self._build_cycle_timeline_render_payload(
                        cycle_timeline,
                        workflow_key=workflow_key,
                        reaction_guidance=payload.reaction_guidance,
                        columns=getattr(self, "_sol_cycle_timeline_columns", ()),
                    )
                timeline_rows = int(
                    timeline_render_payload.get("display_row_count")
                    or len(timeline_render_payload.get("tree_rows") or [])
                )

                def _on_timeline_stage_done() -> None:
                    """Emit a debug marker when staged timeline rendering completes.

                    Purpose:
                        Record completion of chunked timeline table/callout updates.
                    Why:
                        Freeze diagnostics need one reliable marker proving post-solver
                        timeline staging drained successfully.
                    Inputs:
                        None.
                    Outputs:
                        None.
                    Side Effects:
                        Emits one debug log line in `plotting.render`.
                    Exceptions:
                        Logging failures are handled by `_dbg`.
                    """
                    self._dbg(
                        "plotting.render",
                        "post_solver_timeline_stage_done workflow=%s timeline_rows=%s",
                        workflow_key,
                        timeline_rows,
                    )

                self._apply_cycle_timeline_render_payload_staged(
                    timeline_render_payload,
                    workflow_key=workflow_key,
                    on_complete=_on_timeline_stage_done,
                )
            except Exception as exc:
                # Fail closed to synchronous rendering so timelines still update
                # when staged scheduling or payload normalization fails.
                self._dbg_exc(
                    "plotting.render",
                    "Timeline staged apply failed; falling back to synchronous update",
                    exc,
                )
                self._update_cycle_spec_view(cycle_timeline, workflow_key=workflow_key)
                self._dbg(
                    "plotting.render",
                    "post_solver_timeline_stage_done workflow=%s timeline_rows=%s",
                    workflow_key,
                    timeline_rows,
                )
        else:
            self._update_cycle_spec_view(cycle_timeline, workflow_key=workflow_key)
        self._update_analysis_dashboard(
            payload.analysis_dashboard,
            workflow_key=workflow_key,
        )
        entries = payload.tracking_entries or existing_entries
        self._sol_tracking_entries = list(entries)
        self._refresh_sol_tracking_table(entries)
        self._update_sol_simulation_plot(payload.reaction_guidance, entries)

    def _post_solver_on_ok_fragment(
        self,
        result: Any,
        solver_session_id: int,
    ) -> None:
        """Model patched `_on_ok` callback debug boundaries.

        Purpose:
            Validate post-solver UI boundary markers and state application order.
        Why:
            Freeze diagnostics depend on deterministic start/done markers.
        Inputs:
            result: Tuple payload returned by `_execute_solubility_job`.
            solver_session_id: Loading-session identifier for completion callbacks.
        Outputs:
            None.
        Side Effects:
            Updates summary/guidance state and logs post-solver markers.
        Exceptions:
            Downstream UI handlers retain their own best-effort guards.
        """
        summary, payload, co2_guidance, last_result = result
        workflow_key = str(payload.workflow_key or self._current_solubility_workflow())
        timeline_rows = int(len(payload.cycle_timeline or []))
        self._dbg(
            "plotting.render",
            "post_solver_ui_start workflow=%s timeline_rows=%s",
            workflow_key,
            timeline_rows,
        )
        self._sol_last_result = last_result
        guidance_var = getattr(self, "_sol_new_reaction_summary_var", None)
        if guidance_var is not None:
            guidance_var.set(co2_guidance)
        self._sol_math_sections = payload.math_sections
        self._update_solubility_summary(summary, structured=payload.to_dict())
        self._dbg(
            "plotting.render",
            "post_solver_ui_done workflow=%s timeline_rows=%s",
            workflow_key,
            timeline_rows,
        )
        self._complete_solubility_loading_phase(
            solver_session_id,
            message="Finalizing workflow layout...",
            detail="Applying solver outputs to summary, plots, and timeline.",
        )
        self._sol_solver_progress_session_id = None
