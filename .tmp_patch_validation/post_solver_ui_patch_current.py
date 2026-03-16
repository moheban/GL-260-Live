from __future__ import annotations
from dataclasses import asdict, dataclass, field
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

    def to_dict(self) -> Dict[str, Any]:
        """Perform to dict.
        Used to keep the workflow logic localized and testable."""
        return asdict(self)


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
        self._set_speciation_diagnostics_status(
            "Speciation debug preset enabled."
        )

    def _build_structured_payload(
        self,
        solver_inputs: SolubilitySolverInputs,
        result: SolubilitySpeciationResult,
        forced_result: Optional[SolubilitySpeciationResult],
        closed_system_result: Optional[SolubilitySpeciationResult],
        measurement_warning: Optional[str],
        measurement_scale: Optional[float],
        reaction_guidance: Optional[Dict[str, Any]],
        sweep_data: List[Dict[str, float]],
        sensitivity_rows: List[Dict[str, str]],
        planner_context: List[str],
        tracking_entries: List[Dict[str, Any]],
        cycle_summary: Dict[str, Any],
        mode_context: Dict[str, str],
        chart_data: Dict[str, Any],
        math_sections: List[Dict[str, Any]],
        math_preview_lines: List[str],
        forced_error: Optional[str],
        analysis_dashboard: Optional[Dict[str, Any]] = None,
    ) -> SolubilityStructuredPayload:
        """Build one structured payload object for solver/UI synchronization.

        Purpose:
            Consolidate solver outputs, warnings, tables, workflow context, and
            optional Analysis dashboard payload into one serializable object.
        Why:
            The UI refresh pipeline consumes one structured object and should not
            rebuild this mapping in multiple places.
        Inputs:
            solver_inputs: Normalized workflow inputs used by the solver.
            result: Primary speciation result for the active workflow.
            forced_result: Optional forced-pH companion result.
            closed_system_result: Optional closed-system companion result.
            measurement_warning: Optional warning string from measurement alignment.
            measurement_scale: Optional scale factor used for alignment.
            reaction_guidance: Optional guidance/summary payload.
            sweep_data: Species sweep samples for table/plot output.
            sensitivity_rows: Sensitivity table rows.
            planner_context: Planning context strings for user display.
            tracking_entries: Tracking entries shown in runtime tables.
            cycle_summary: Cycle simulation summary payload.
            mode_context: Workflow mode label/start/goal/assumption strings.
            chart_data: Plot-ready chart payloads.
            math_sections: Full detailed-math section payloads.
            math_preview_lines: Preview math lines for inline display.
            forced_error: Optional warning generated during forced solve.
            analysis_dashboard: Optional dashboard payload for Analysis workflow.
        Outputs:
            SolubilityStructuredPayload: Structured payload used by UI renderers.
        Side Effects:
            None.
        Exceptions:
            None; caller controls upstream error handling.
        """
        ordered_species = ["Na+", "H+", "HCO3-", "CO3^2-", "H2CO3", "OH-"]
        species_rows: List[Dict[str, str]] = []
        # Iterate over ordered_species to apply the per-item logic.
        for species in ordered_species:
            species_rows.append(
                {
                    "species": species,
                    "molar": f"{result.concentrations_m.get(species, 0.0):.6e}",
                    "mass": f"{result.mass_concentrations_g_per_l.get(species, 0.0):.6e}",
                    "moles": f"{result.moles.get(species, 0.0):.6e}",
                    "gamma": f"{result.activity_coefficients.get(species, 1.0):.4f}",
                }
            )
        saturation_rows: List[Dict[str, str]] = []
        # Iterate over items from result.saturation_indices to apply the per-item logic.
        for salt, ratio in result.saturation_indices.items():
            status = "Supersaturated" if ratio > 1.0 else "Stable"
            saturation_rows.append(
                {"salt": salt, "ratio": f"{ratio:.3f}", "status": status}
            )
        warnings: List[str] = list(result.warnings)
        if closed_system_result:
            warnings.extend(
                [f"Closed system: {warn}" for warn in closed_system_result.warnings]
            )
        if measurement_warning:
            warnings.append(measurement_warning)
        if forced_result and forced_result.warnings:
            warnings.extend(
                [
                    f"Forced ({forced_result.ph:.2f}): {warn}"
                    # Iterate to apply the per-item logic.
                    for warn in forced_result.warnings
                ]
            )
        if forced_error:
            warnings.append(forced_error)
        if reaction_guidance and reaction_guidance.get("warnings"):
            warnings.extend(
                [f"Reaction: {msg}" for msg in reaction_guidance["warnings"]]
            )
        if closed_system_result:
            warnings.append(
                "Closed-system equilibrium predicted "
                f"pH {closed_system_result.ph:.2f}; measurement-calibrated "
                f"state anchored at {result.ph:.2f}."
            )
        if measurement_scale is not None and abs(measurement_scale - 1.0) > 0.01:
            delta_pct = (measurement_scale - 1.0) * 100.0
            warnings.append(
                f"Measurement alignment adjusted dissolved NaHCO3 by {delta_pct:+.1f}% "
                f"relative to entered {solver_inputs.params.mass_na_hco3_g:.2f} g."
            )
        alkalinity_value = (
            f"{result.alkalinity_meq_per_l:.1f} meq/L (acid-neutralizing capacity)"
        )
        if closed_system_result:
            alkalinity_value += (
                f" | closed {closed_system_result.alkalinity_meq_per_l:.1f} meq/L"
            )
        charge_value = (
            f"{result.charge_balance_residual:+.2e} mol/L "
            "(positive minus negative ionic charge)"
        )
        ph_value = f"{result.ph:.2f}"
        if closed_system_result:
            ph_value += f" | closed {closed_system_result.ph:.2f}"
        dissolved_val = (
            f"{result.dissolved_mass_na_hco3_g:.2f} g"
            if result.dissolved_mass_na_hco3_g is not None
            else "â€”"
        )
        solids_val = (
            f"{result.undissolved_mass_na_hco3_g:.2f} g"
            if result.undissolved_mass_na_hco3_g is not None
            else "â€”"
        )
        highlight_map = {
            "ph": ph_value,
            "ionic_strength": f"{result.ionic_strength:.3e} M",
            "alkalinity": alkalinity_value,
            "carbonate": (
                f"{result.carbonate_as_na2co3_wt_percent:.3f} wt%"
                if result.carbonate_as_na2co3_wt_percent is not None
                else "â€”"
            ),
            "charge": charge_value,
            "dissolved": dissolved_val,
            "solids": solids_val,
        }
        sweep_rows = [
            {
                "ph": f"{row['ph']:.2f}",
                "hco3_pct": f"{row['hco3_pct']:.2f}",
                "co3_pct": f"{row['co3_pct']:.2f}",
                "h2co3_pct": f"{row['h2co3_pct']:.2f}",
            }
            # Iterate to apply the per-item logic.
            for row in sweep_data
        ]
        assumptions: List[str] = []
        seen: Set[str] = set()
        # Iterate to apply the per-item logic.
        for bucket in (
            result.assumptions,
            forced_result.assumptions if forced_result else [],
        ):
            # Iterate over bucket to apply the per-item logic.
            for note in bucket:
                if note not in seen:
                    seen.add(note)
                    assumptions.append(note)
        if reaction_guidance:
            # Iterate over reaction_guidance.get("notes", []) to apply the per-item logic.
            for note in reaction_guidance.get("notes", []):
                tagged = f"Reaction note: {note}"
                if tagged not in seen:
                    seen.add(tagged)
                    assumptions.append(tagged)
        if (
            solver_inputs.mode_key == "contaminated_bicarb_diagnostic"
            and solver_inputs.diagnostic_data
        ):
            assumed_water = solver_inputs.diagnostic_data.get("assumed_water_mass_g")
            sample_mass = solver_inputs.diagnostic_data.get("sample_mass_g")
            if assumed_water:
                note = (
                    f"Assumed {assumed_water:.1f} g water to dissolve "
                    f"{sample_mass or 0.0:.1f} g sample (no slurry pH provided)."
                )
            else:
                note = "Atmospheric slurry pH used directly for the diagnostic seed."
            if note not in seen:
                seen.add(note)
                assumptions.append(note)
        if solver_inputs.assumed_solution_volume_l:
            note = (
                f"Assumed {solver_inputs.assumed_solution_volume_l:.1f} L slurry volume "
                "for the reprocessing scenario."
            )
            if note not in seen:
                seen.add(note)
                assumptions.append(note)
        if closed_system_result:
            note = (
                f"Measurement-calibrated basis at pH {result.ph:.2f}; "
                f"closed-system prediction {closed_system_result.ph:.2f} kept for context."
            )
            if note not in seen:
                seen.add(note)
                assumptions.append(note)
        if measurement_scale is not None and abs(measurement_scale - 1.0) > 0.01:
            note = (
                f"Effective dissolved mass scaled by {measurement_scale:.3f}x "
                f"to match measured alkalinity."
            )
            if note not in seen:
                seen.add(note)
                assumptions.append(note)
        reprocessing_context = (
            reaction_guidance.get("reprocessing_workflow")
            if reaction_guidance
            else None
        )
        payload = SolubilityStructuredPayload(
            highlights=highlight_map,
            warnings=warnings,
            species_rows=species_rows,
            saturation_rows=saturation_rows,
            sensitivity_rows=sensitivity_rows,
            sweep_rows=sweep_rows,
            sweep_plot=sweep_data,
            assumptions=assumptions,
            chart_data=chart_data,
            reaction_guidance=reaction_guidance,
            tracking_entries=tracking_entries,
            cycle_timeline=cycle_summary.get("timeline"),
            cycle_timeline_render_payload=cycle_summary.get("timeline_render_payload"),
            planner_context=planner_context,
            math_sections=math_sections,
            math_preview_lines=math_preview_lines,
            mode_context=mode_context,
            workflow_key=solver_inputs.workflow_key,
            guide_key=solver_inputs.guide_key,
            assumed_solution_volume_l=solver_inputs.assumed_solution_volume_l,
            reprocessing_context=reprocessing_context,
            analysis_dashboard=analysis_dashboard,
        )
        return payload

    def _update_solubility_structured_widgets(
        self, structured: Optional[Dict[str, Any]]
    ) -> None:
        """Refresh Advanced Speciation widgets from structured solver output.

        Purpose:
            Synchronize summary/status panes, plots, and helper labels using the
            latest structured solubility payload.
        Why:
            Multiple workflow surfaces depend on the same payload and must update
            together while preserving repaired display strings.
        Inputs:
            structured: Optional structured payload dictionary/dataclass.
        Outputs:
            None.
        Side Effects:
            Updates Tk variables, Treeviews, plots, and timeline displays.
        Exceptions:
            None.
        """
        self._sol_last_structured = structured
        existing_entries = list(getattr(self, "_sol_tracking_entries", []))
        context_label = getattr(self, "_sol_context_label_var", None)
        context_start = getattr(self, "_sol_context_start_var", None)
        context_goal = getattr(self, "_sol_context_goal_var", None)
        context_assumption = getattr(self, "_sol_context_assumption_var", None)
        preview_tree = getattr(self, "_sol_new_metric_tree", None)
        preview_columns = getattr(self, "_sol_new_metric_columns", ())
        preview_summary_var = getattr(self, "_sol_new_reaction_summary_var", None)

        def _payload_from_struct(data: Dict[str, Any]) -> SolubilityStructuredPayload:
            """Convert dictionary payloads into `SolubilityStructuredPayload`.

            Purpose:
                Normalize dict-based payloads into the dataclass schema expected
                by downstream structured-widget update logic.
            Why:
                Callers may persist/transmit structured data as dictionaries.
            Inputs:
                data: Raw structured payload dictionary.
            Outputs:
                SolubilityStructuredPayload: Dataclass instance for UI updates.
            Side Effects:
                None.
            Exceptions:
                Missing keys fall back to safe defaults.
            """
            return SolubilityStructuredPayload(
                highlights=data.get("highlights") or {},
                warnings=data.get("warnings") or [],
                species_rows=data.get("species_rows") or [],
                saturation_rows=data.get("saturation_rows") or [],
                sensitivity_rows=data.get("sensitivity_rows") or [],
                sweep_rows=data.get("sweep_rows") or [],
                sweep_plot=data.get("sweep_plot") or [],
                assumptions=data.get("assumptions") or [],
                chart_data=data.get("chart_data") or {},
                reaction_guidance=data.get("reaction_guidance"),
                tracking_entries=data.get("tracking_entries") or [],
                cycle_timeline=data.get("cycle_timeline"),
                cycle_timeline_render_payload=data.get("cycle_timeline_render_payload"),
                planner_context=data.get("planner_context") or [],
                math_sections=data.get("math_sections") or [],
                math_preview_lines=data.get("math_preview_lines") or [],
                mode_context=data.get("mode_context") or {},
                workflow_key=data.get("workflow_key", ""),
                guide_key=data.get("guide_key", ""),
                assumed_solution_volume_l=data.get("assumed_solution_volume_l"),
                co2_guidance=data.get("co2_guidance", ""),
                analysis_dashboard=data.get("analysis_dashboard"),
            )

        if structured is None:
            self._sol_math_sections = []
            # Iterate over items from self._sol_highlight_defaults to apply the per-item logic.
            for key, default in self._sol_highlight_defaults.items():
                var = self._sol_highlight_vars.get(key)
                if var is not None:
                    _set_stringvar_repaired(var, default)
            _set_stringvar_repaired(
                self._sol_warning_var,
                "Warnings will appear after running the analysis.",
            )
            self._populate_treeview(
                self._sol_species_tree, [], self._sol_species_columns
            )
            self._populate_treeview(
                self._sol_saturation_tree, [], self._sol_saturation_columns
            )
            self._populate_treeview(
                self._sol_sensitivity_tree, [], self._sol_sensitivity_columns
            )
            self._populate_treeview(self._sol_sweep_tree, [], self._sol_sweep_columns)
            self._update_solubility_plots(None)
            self._update_solubility_preview_plots(None)
            self._update_solubility_sweep_plot(None)
            _set_stringvar_repaired(
                self._sol_assumptions_var,
                "Assumptions will be listed after running the module.",
            )
            summary_var = getattr(self, "_sol_reaction_summary_var", None)
            default_msg = getattr(
                self,
                "_sol_reaction_default_msg",
                "Enter NaOH/CO2 inputs to activate the guidance overlay.",
            )
            if summary_var is not None:
                _set_stringvar_repaired(summary_var, default_msg)
            if preview_tree is not None:
                self._populate_treeview(preview_tree, [], preview_columns)
            if preview_summary_var is not None:
                _set_stringvar_repaired(preview_summary_var, default_msg)
            self._update_sol_math_text_lines([])
            self._refresh_math_viewer_state()
            self._refresh_sol_tracking_table(existing_entries)
            self._update_sol_simulation_plot(None, existing_entries)
            self._update_cycle_spec_view([])
            self._update_analysis_dashboard(None, workflow_key=None)
            mode_var = getattr(self, "_sol_mode_var", None)
            mode_key = mode_var.get() if mode_var is not None else SOL_DEFAULT_SIM_MODE
            meta = SOL_SIMULATION_MODES.get(mode_key, {})
            if context_label is not None:
                _set_stringvar_repaired(
                    context_label, meta.get("label", "Advanced Solubility")
                )
            placeholder = "Starting point will appear after running the analysis."
            if context_start is not None:
                _set_stringvar_repaired(context_start, placeholder)
            if context_goal is not None:
                _set_stringvar_repaired(
                    context_goal, "Solver goals and recommendations will be shown here."
                )
            if context_assumption is not None:
                _set_stringvar_repaired(
                    context_assumption,
                    meta.get("assumption", "Mode assumptions will be echoed here."),
                )
            self._refresh_sol_mode_guidance()
            return

        payload = (
            structured
            if isinstance(structured, SolubilityStructuredPayload)
            else _payload_from_struct(structured)
        )
        self._sol_reaction_guidance = payload.reaction_guidance or {}

        # Iterate over items from self._sol_highlight_meta to apply the per-item logic.
        for key, label in self._sol_highlight_meta.items():
            var = self._sol_highlight_vars.get(key)
            if var is None:
                continue
            value = payload.highlights.get(key, "â€”")
            _set_stringvar_repaired(var, f"{label}: {value}")

        if payload.warnings:
            _set_stringvar_repaired(self._sol_warning_var, "\n".join(payload.warnings))
        else:
            _set_stringvar_repaired(self._sol_warning_var, "No warnings detected.")

        preview_rows: List[Dict[str, Any]] = []
        # Iterate over items from self._sol_highlight_meta to apply the per-item logic.
        for key, label in self._sol_highlight_meta.items():
            value = payload.highlights.get(key)
            if value is not None:
                preview_rows.append({"metric": label, "value": value})
        workflow_label = ""
        workflow_meta = SOL_WORKFLOW_TEMPLATES.get(payload.workflow_key, {})
        if workflow_meta:
            workflow_label = workflow_meta.get("label", payload.workflow_key)
        elif payload.workflow_key:
            workflow_label = payload.workflow_key
        if workflow_label:
            preview_rows.insert(0, {"metric": "Workflow", "value": workflow_label})
        if payload.planner_context:
            preview_rows.append(
                {
                    "metric": "Planner context",
                    "value": " | ".join(payload.planner_context),
                }
            )
        if preview_tree is not None:
            self._populate_treeview(preview_tree, preview_rows, preview_columns)

        self._populate_treeview(
            self._sol_species_tree, payload.species_rows, self._sol_species_columns
        )
        self._populate_treeview(
            self._sol_saturation_tree,
            payload.saturation_rows,
            self._sol_saturation_columns,
        )
        self._populate_treeview(
            self._sol_sensitivity_tree,
            payload.sensitivity_rows,
            self._sol_sensitivity_columns,
        )
        self._populate_treeview(
            self._sol_sweep_tree, payload.sweep_rows, self._sol_sweep_columns
        )

        self._update_solubility_plots(payload.chart_data)
        self._update_solubility_preview_plots(payload.chart_data)
        self._update_solubility_sweep_plot(payload.sweep_plot)

        if payload.assumptions:
            bullet = "\n".join(f"â€¢ {item}" for item in payload.assumptions)
            _set_stringvar_repaired(self._sol_assumptions_var, bullet)
        else:
            _set_stringvar_repaired(
                self._sol_assumptions_var,
                "Assumptions will be listed after running the module.",
            )

        summary_var = getattr(self, "_sol_reaction_summary_var", None)
        default_msg = getattr(
            self,
            "_sol_reaction_default_msg",
            "Enter NaOH/CO2 inputs to activate the guidance overlay.",
        )
        guidance_text = payload.co2_guidance or default_msg
        if payload.planner_context:
            guidance_text = f"{guidance_text}\n\nPlan inputs:\n" + "\n".join(
                payload.planner_context
            )
        if summary_var is not None:
            _set_stringvar_repaired(summary_var, guidance_text)
        if preview_summary_var is not None:
            _set_stringvar_repaired(preview_summary_var, guidance_text)

        math_preview = payload.math_preview_lines
        if not math_preview and payload.reaction_guidance:
            math_preview = payload.reaction_guidance.get("math_lines", [])
        self._sol_math_sections = payload.math_sections
        self._update_sol_math_text_lines(math_preview)
        self._refresh_math_viewer_state()
        self._refresh_math_viewer_contents()

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

        mode_context = payload.mode_context or {}
        if mode_context:
            if context_label is not None:
                _set_stringvar_repaired(
                    context_label, mode_context.get("label", "Advanced Solubility")
                )
            if context_start is not None:
                _set_stringvar_repaired(context_start, mode_context.get("starting", ""))
            if context_goal is not None:
                _set_stringvar_repaired(context_goal, mode_context.get("goal", ""))
            if context_assumption is not None:
                _set_stringvar_repaired(
                    context_assumption,
                    mode_context.get(
                        "assumption", "Mode assumptions will be echoed here."
                    ),
                )
        self._refresh_sol_mode_guidance()
        _sanitize_widget_text_tree(getattr(self, "_sol_scroll_inner", None))

    def _run_solubility_analysis(self) -> None:
        """Run the solubility analysis workflow asynchronously.
        Purpose: Orchestrate solver execution, projection scheduling, and UI updates.
        Why: Keep the Advanced Speciation tab responsive while running heavy solvers.
        Inputs:
            None.
        Outputs:
            None.
        Side Effects:
            - Updates stored form data, solver state, and summary outputs.
            - Schedules background solver execution and UI callbacks.
            - Updates status messages and overlay visibility.
        Exceptions:
            - Best-effort; handles input errors without raising.
        """
        form_data: dict[str, Any] = {}
        self._ensure_rust_backend_for_workflow(
            status_var=getattr(self, "_sol_context_var", None)
        )
        try:
            form_data = self._collect_solubility_form_data()
        except Exception as exc:
            self._update_solubility_summary(
                f"Advanced Solubility Module error: {exc}", structured=None
            )
            try:
                messagebox.showerror(
                    "Advanced Solubility Module", f"Unable to run analysis:\\n{exc}"
                )
            except Exception:
                pass
            return
        self._sol_last_form_data = form_data
        solver_inputs = self._prepare_solver_inputs(form_data)
        solver_session_id = self._begin_solubility_loading_phase(
            phase="solver",
            message="Solving speciation...",
            detail="Computing equilibrium state and summary outputs.",
        )
        self._sol_solver_progress_session_id = solver_session_id
        mode_context = self._build_sol_mode_context(
            solver_inputs.params,
            form_data,
            workflow_key=form_data.get("workflow_key"),
        )
        if form_data.get("workflow_key") == "Planning":
            self._schedule_planning_projection(
                form_data,
                solver_inputs,
                loading_session_id=solver_session_id,
            )
        enabled_axes = self._read_sensitivity_axes()
        tracking_entries = list(getattr(self, "_sol_tracking_entries", []))
        cycle_summary = (
            self._get_cycle_result_for_workflow(form_data.get("workflow_key")) or {}
        ).copy()
        capture_math = bool(
            getattr(self, "_sol_show_math_var", tk.BooleanVar(value=False)).get()
        )
        default_guidance = getattr(
            self,
            "_sol_reaction_default_msg",
            "Enter NaOH/COâ‚‚ inputs to activate the guidance overlay.",
        )
        model_key = solver_inputs.model_key
        settings = getattr(self, "settings", {})
        self._sol_model_key = model_key
        if isinstance(settings, dict):
            settings["solubility_model_key"] = model_key
        try:
            model = get_speciation_model(model_key)
        except Exception as exc:
            self._complete_solubility_loading_phase(
                solver_session_id,
                message="Speciation setup failed.",
                detail="Unable to resolve the selected speciation model.",
            )
            try:
                messagebox.showerror(
                    "Advanced Solubility Module",
                    f"Unable to prepare speciation model:\n{exc}",
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            return
        solver_inputs_snapshot = solver_inputs
        enabled_axes_snapshot = dict(enabled_axes)
        tracking_entries_snapshot = copy.deepcopy(tracking_entries)
        cycle_summary_snapshot = copy.deepcopy(cycle_summary)
        mode_context_snapshot = dict(mode_context)
        default_guidance_snapshot = str(default_guidance)
        capture_math_snapshot = bool(capture_math)

        # Solver pipeline runs in a background worker to keep the UI responsive
        # while capturing structured outputs for plots, summaries, and exports.
        # Closure captures _run_solubility_analysis state for callback wiring,
        # kept nested to scope the handler, and invoked by bindings set in
        # _run_solubility_analysis.
        def _worker():
            """Perform worker.
            Used to keep the workflow logic localized and testable."""
            return self._execute_solubility_job(
                solver_inputs_snapshot,
                model,
                solver_inputs_snapshot.model_options,
                enabled_axes_snapshot,
                tracking_entries_snapshot,
                cycle_summary_snapshot,
                mode_context_snapshot,
                default_guidance_snapshot,
                capture_math_snapshot,
            )

        # Closure captures _run_solubility_analysis state for callback wiring,
        # kept nested to scope the handler, and invoked by bindings set in
        # _run_solubility_analysis.
        def _on_ok(result):
            """Apply successful solver output on the UI thread.

            Purpose:
                Install solver outputs into summary/state widgets after async
                completion.
            Why:
                Freeze investigations need explicit markers around post-solver
                UI update boundaries to identify hangs after solver completion.
            Inputs:
                result: Tuple payload returned by `_execute_solubility_job`.
            Outputs:
                None.
            Side Effects:
                Updates summary/state widgets, loading session state, and emits
                debug markers for post-solver UI phases.
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

        # Closure captures _run_solubility_analysis state for callback wiring,
        # kept nested to scope the handler, and invoked by bindings set in
        # _run_solubility_analysis.
        def _on_err(exc):
            """Handle err.
            Used as an event callback for err."""
            self._update_solubility_summary(
                f"Advanced Solubility Module error: {exc}", structured=None
            )
            self._complete_solubility_loading_phase(
                solver_session_id,
                message="Speciation failed.",
                detail="See error details in summary output.",
            )
            self._sol_solver_progress_session_id = None
            try:
                messagebox.showerror(
                    "Advanced Solubility Module", f"Unable to run analysis:\\n{exc}"
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        # Submit async job so UI progress and callbacks can update when ready.
        try:
            self._submit_solubility_job(_worker, _on_ok, _on_err)
        except Exception as exc:
            _on_err(exc)
