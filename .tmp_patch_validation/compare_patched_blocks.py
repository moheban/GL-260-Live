from __future__ import annotations


class _PatchedCompareValidationHarness:
    """Container for patched Compare methods used by scoped validation."""

    pass

    def _build_developer_tools_runtime_tab(self, parent: ttk.Frame) -> None:
        """Build the runtime/advanced tools tab inside Developer Tools.

        Purpose:
            Expose concurrency/layout-health controls, Compare debug actions, and
            entrypoints to advanced diagnostics dialogs from a single tab.
        Why:
            Keeps unrelated expert tools accessible without overloading the main
            logging/debug tab.
        Inputs:
            parent: Notebook tab frame that will contain runtime controls.
        Outputs:
            None.
        Side Effects:
            Creates widgets that call existing runtime handlers, including
            concurrency/layout-health apply logic and separate dialog actions.
        Exceptions:
            Delegates to existing guarded handlers so failures remain non-fatal.
        """
        parent.columnconfigure(0, weight=1)

        ttk.Label(
            parent,
            text=(
                "Advanced developer utilities. Use caution when changing "
                "threading/concurrency options."
            ),
            justify="left",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 8))

        concurrency_frame = ttk.LabelFrame(parent, text="Concurrency Controls")
        concurrency_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        ttk.Label(
            concurrency_frame,
            text="Developer-only settings for the background task runner.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 6))

        ttk.Label(concurrency_frame, text="Worker threads:").grid(
            row=1, column=0, sticky="w", padx=8, pady=(0, 6)
        )
        spin = ttk.Spinbox(
            concurrency_frame,
            from_=1,
            to=32,
            textvariable=self._dev_worker_threads_var,
            width=6,
            command=self._apply_concurrency_controls,
        )
        spin.grid(row=1, column=1, sticky="w", pady=(0, 6))
        spin.bind("<FocusOut>", lambda _event: self._apply_concurrency_controls())
        spin.bind("<Return>", lambda _event: self._apply_concurrency_controls())

        ttk.Checkbutton(
            concurrency_frame,
            text="Enable parallel compute (developer option)",
            variable=self._dev_parallel_compute_var,
            command=self._apply_concurrency_controls,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        layout_health_frame = ttk.LabelFrame(parent, text="Layout Health")
        layout_health_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        for col_idx in range(4):
            layout_health_frame.columnconfigure(
                col_idx, weight=1 if col_idx in {1, 3} else 0
            )

        ttk.Checkbutton(
            layout_health_frame,
            text="Enable Layout Health Auto-Fix",
            variable=self._layout_health_autofix_enabled_var,
            command=self._apply_layout_health_controls,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))
        ttk.Checkbutton(
            layout_health_frame,
            text="Enable Strict Mode",
            variable=self._layout_health_strict_mode_var,
            command=self._apply_layout_health_controls,
        ).grid(row=0, column=2, columnspan=2, sticky="w", padx=8, pady=(8, 4))
        ttk.Checkbutton(
            layout_health_frame,
            text="Enable Layout Health Debug Events",
            variable=self._layout_health_emit_debug_events_var,
            command=self._apply_layout_health_controls,
        ).grid(row=1, column=0, columnspan=4, sticky="w", padx=8, pady=(0, 8))

        ttk.Label(layout_health_frame, text="Max Passes:").grid(
            row=2, column=0, sticky="w", padx=8, pady=(0, 6)
        )
        layout_pass_spin = ttk.Spinbox(
            layout_health_frame,
            from_=MIN_LAYOUT_HEALTH_MAX_PASSES,
            to=MAX_LAYOUT_HEALTH_MAX_PASSES,
            textvariable=self._layout_health_max_passes_var,
            width=8,
            command=self._apply_layout_health_controls,
        )
        layout_pass_spin.grid(row=2, column=1, sticky="w", padx=(0, 8), pady=(0, 6))
        layout_pass_spin.bind(
            "<FocusOut>", lambda _event: self._apply_layout_health_controls()
        )
        layout_pass_spin.bind(
            "<Return>", lambda _event: self._apply_layout_health_controls()
        )

        ttk.Label(layout_health_frame, text="Min Legend-XLabel Gap (pt):").grid(
            row=2, column=2, sticky="w", padx=8, pady=(0, 6)
        )
        min_gap_spin = ttk.Spinbox(
            layout_health_frame,
            from_=MIN_LAYOUT_HEALTH_GAP_PTS,
            to=MAX_LAYOUT_HEALTH_GAP_PTS,
            increment=0.5,
            textvariable=self._layout_health_min_gap_pts_var,
            width=10,
            command=self._apply_layout_health_controls,
        )
        min_gap_spin.grid(row=2, column=3, sticky="w", padx=(0, 8), pady=(0, 6))
        min_gap_spin.bind(
            "<FocusOut>", lambda _event: self._apply_layout_health_controls()
        )
        min_gap_spin.bind(
            "<Return>", lambda _event: self._apply_layout_health_controls()
        )

        ttk.Label(layout_health_frame, text="Max Legend-XLabel Gap (pt):").grid(
            row=3, column=0, sticky="w", padx=8, pady=(0, 8)
        )
        max_gap_spin = ttk.Spinbox(
            layout_health_frame,
            from_=MIN_LAYOUT_HEALTH_GAP_PTS,
            to=MAX_LAYOUT_HEALTH_GAP_PTS,
            increment=0.5,
            textvariable=self._layout_health_max_gap_pts_var,
            width=10,
            command=self._apply_layout_health_controls,
        )
        max_gap_spin.grid(row=3, column=1, sticky="w", padx=(0, 8), pady=(0, 8))
        max_gap_spin.bind(
            "<FocusOut>", lambda _event: self._apply_layout_health_controls()
        )
        max_gap_spin.bind(
            "<Return>", lambda _event: self._apply_layout_health_controls()
        )

        ttk.Button(
            layout_health_frame,
            text="Reset Layout Health Defaults",
            command=self._reset_layout_health_defaults,
        ).grid(row=3, column=2, sticky="w", padx=8, pady=(0, 8))
        ttk.Button(
            layout_health_frame,
            text="Run Layout Health Check on Active Figure",
            command=self._run_layout_health_check_on_active_figure,
        ).grid(row=3, column=3, sticky="w", padx=8, pady=(0, 8))

        compare_debug_frame = ttk.LabelFrame(parent, text="Compare Debug")
        compare_debug_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        compare_debug_frame.columnconfigure(0, weight=1)
        compare_debug_frame.columnconfigure(1, weight=1)
        compare_debug_frame.columnconfigure(2, weight=1)
        ttk.Button(
            compare_debug_frame,
            text="Dump Compare Snapshot",
            command=self._compare_dump_debug_snapshot,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Button(
            compare_debug_frame,
            text="Dump Compare Whitespace",
            command=self._compare_dump_debug_whitespace,
        ).grid(row=0, column=1, sticky="w", padx=8, pady=6)
        ttk.Button(
            compare_debug_frame,
            text="Dump Side Editor State",
            command=self._compare_dump_cycle_editor_state,
        ).grid(row=0, column=2, sticky="w", padx=8, pady=6)

        tools_frame = ttk.LabelFrame(parent, text="Advanced Tools")
        tools_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        tools_frame.columnconfigure(0, weight=1)
        tools_frame.columnconfigure(1, weight=1)
        ttk.Button(
            tools_frame,
            text="Free-Threading & GIL...",
            command=self._open_free_threading_dialog,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Button(
            tools_frame,
            text="Dependency Free-Threading Audit...",
            command=self._open_dependency_audit_dialog,
        ).grid(row=0, column=1, sticky="w", padx=8, pady=6)
        ttk.Button(
            tools_frame,
            text="Regression checks...",
            command=self._open_regression_checks_dialog,
        ).grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Button(
            tools_frame,
            text="Validate Timeline Table Export (PDF/PNG)",
            command=self._run_timeline_table_export_validation,
        ).grid(row=1, column=1, sticky="w", padx=8, pady=6)
        rust_install_button = ttk.Button(
            tools_frame,
            text="Install/Repair Rust Backend...",
            command=self._manual_install_rust_backend,
        )
        rust_install_button.grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self._dev_rust_install_button = rust_install_button

        rust_status_var = tk.StringVar(value="Rust backend install/repair idle.")
        self._dev_rust_status_var = rust_status_var
        ttk.Label(
            tools_frame,
            textvariable=rust_status_var,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 4))
        rust_progress = ttk.Progressbar(tools_frame, mode="indeterminate", length=300)
        rust_progress.grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6)
        )
        rust_progress.grid_remove()
        self._dev_rust_progress_bar = rust_progress
        self._set_dev_rust_install_busy(
            bool(getattr(self, "_dev_rust_install_task_id", None)),
            status_text=(
                "Installing/repairing Rust backend..."
                if getattr(self, "_dev_rust_install_task_id", None) is not None
                else "Rust backend install/repair idle."
            ),
        )

    def _compare_load_selected_profiles(self) -> None:
        """Load selected compare profiles without running comparison rendering.

        Purpose:
            Resolve selected profile names into Compare-side bundles.
        Why:
            Compare execution is now explicit; loading should stage inputs only
            while `Run Comparison` controls when rendering/table work runs.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Updates side bundle caches, refreshes diagnostics, resets Compare
            output surfaces to manual-run placeholders, and persists state.
        Exceptions:
            Missing/invalid profiles are handled per side without aborting.
        """
        profile_a = str(self.compare_profile_a_var.get() or "").strip()
        profile_b = str(self.compare_profile_b_var.get() or "").strip()
        self._compare_refresh_profile_choices()
        if not bool(getattr(self, "_compare_rust_preflight_done", False)):
            try:
                self._ensure_rust_backend_for_workflow()
            except Exception:
                # Best-effort guard; Compare continues with Python fallback paths.
                pass
            self._compare_rust_preflight_done = True
        self._compare_load_diagnostics_state = {
            "A": {},
            "B": {},
            "summary": "Loading Compare profiles...",
        }
        self._compare_refresh_diagnostics_panel()
        self._compare_show_load_splash("Loading Compare Profiles")
        try:
            self._compare_update_load_splash(
                message="Initializing Compare load...",
                progress=8.0,
                stage_key="initialize",
                detail="Preparing side-by-side profile load stages.",
                reset=True,
            )

            for side_key, profile_name, progress_value in (
                ("A", profile_a, 24.0),
                ("B", profile_b, 44.0),
            ):
                panel = self._compare_panels.get(side_key) or {}
                if not profile_name:
                    panel["bundle"] = None
                    panel["cycle_rows"] = []
                    panel["total_drop"] = None
                    panel["cycle_fallback_used"] = False
                    panel["cycle_rows_synthesized"] = False
                    panel["cycle_compute_backend"] = ""
                    panel["load_error_message"] = "No profile selected."
                    panel["render_success"] = False
                    panel["render_error_message"] = "No profile selected."
                    self._compare_update_side_status(side_key, "No profile selected.")
                    self._compare_update_side_diagnostics(
                        side_key,
                        profile_name="",
                        status="Not selected",
                        detail="Select a saved profile and click Load Profiles.",
                        render_success=False,
                    )
                    self._compare_log_profile_load_event(
                        side_key=side_key,
                        profile_name="",
                        load_ctx={
                            "profile_name": "",
                            "status": "not_selected",
                            "status_label": "Not selected",
                            "detail": "Select a saved profile and click Load Profiles.",
                            "dataset_path": "",
                            "bundle": None,
                        },
                    )
                    self._compare_refresh_diagnostics_panel()
                    continue

                self._compare_update_load_splash(
                    message=f"Loading Profile {side_key}...",
                    progress=progress_value,
                    stage_key=f"load_{side_key.lower()}",
                    detail=f"Resolving profile '{profile_name}'.",
                )
                load_ctx = self._compare_load_profile_bundle_for_side(
                    side_key,
                    profile_name,
                    prompt_relink=True,
                )
                self._compare_log_profile_load_event(
                    side_key=side_key,
                    profile_name=profile_name,
                    load_ctx=load_ctx,
                )
                bundle = load_ctx.get("bundle")
                ui_status = str(
                    load_ctx.get("ui_status") or "Profile load failed."
                ).strip()
                panel["bundle"] = bundle if isinstance(bundle, dict) else None
                panel["cycle_rows"] = []
                panel["total_drop"] = None
                panel["cycle_fallback_used"] = False
                panel["cycle_rows_synthesized"] = False
                panel["cycle_compute_backend"] = ""
                panel["render_success"] = False
                if panel["bundle"] is None:
                    panel["load_error_message"] = ui_status
                    panel["render_error_message"] = ui_status
                    self._compare_update_side_status(side_key, ui_status)
                else:
                    panel["load_error_message"] = (
                        "Profile loaded. Click Run Comparison."
                    )
                    panel["render_error_message"] = (
                        "Profile loaded. Click Run Comparison."
                    )
                    self._compare_update_side_status(
                        side_key, "Profile loaded. Click Run Comparison."
                    )
                detail_text = str(load_ctx.get("detail") or "").strip()
                if panel["bundle"] is not None and not detail_text:
                    detail_text = (
                        "Profile loaded. Click Run Comparison to render this side."
                    )
                self._compare_update_side_diagnostics(
                    side_key,
                    profile_name=str(load_ctx.get("profile_name") or profile_name),
                    dataset_path=str(load_ctx.get("dataset_path") or ""),
                    status=str(load_ctx.get("status_label") or "Load failed"),
                    detail=detail_text,
                    render_success=False,
                )
                self._compare_refresh_diagnostics_panel()
        except Exception as exc:
            self._compare_update_load_splash(
                message="Compare load failed.",
                progress=100.0,
                stage_key="failed",
                detail=f"{type(exc).__name__}: {exc}",
            )
            self._compare_hide_load_splash()
            return

        loaded_count = sum(
            1
            for side_key in ("A", "B")
            if isinstance(
                (self._compare_panels.get(side_key) or {}).get("bundle"), dict
            )
        )
        if loaded_count == 2:
            summary = "Compare profiles loaded: both sides ready. Click Run Comparison."
        elif loaded_count == 1:
            summary = "Compare profiles loaded: one side ready. Click Run Comparison."
        else:
            summary = (
                "No compare profiles loaded. Select profiles, then click Load Profiles."
            )
        diagnostics_state = dict(
            getattr(self, "_compare_load_diagnostics_state", {}) or {}
        )
        diagnostics_state["summary"] = summary
        self._compare_load_diagnostics_state = diagnostics_state
        self._compare_refresh_diagnostics_panel()
        self._compare_reset_outputs_for_manual_run()
        self._compare_persist_state()
        self._compare_update_load_splash(
            message="Compare profiles loaded.",
            progress=100.0,
            stage_key="ready",
            detail=summary,
        )
        self._compare_hide_load_splash()

    def _compare_refresh_loaded_sides_async(
        self,
        *,
        reason: str,
        show_overlay: bool,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """Refresh loaded Compare sides with background cycle-context prep.

        Purpose:
            Keep Compare rendering responsive by offloading per-side prep work.
        Why:
            Cycle context and profile-level extraction can be expensive and should
            run off the UI thread while overlays communicate progress.
        Args:
            reason: Render-reason token used for status messaging.
            show_overlay: When True, shows the in-tab Compare loading overlay.
            on_complete: Optional completion callback after refresh finalization.
        Returns:
            None.
        Side Effects:
            Submits worker tasks, updates overlay progress, rerenders side figures,
            refreshes table/yield outputs, and updates status chips.
        Exceptions:
            Worker failures are captured per side without aborting sibling renders.
        """
        panels = getattr(self, "_compare_panels", {})
        loaded_sides = [
            side_key
            for side_key in ("A", "B")
            if isinstance((panels or {}).get(side_key), dict)
            and isinstance(((panels or {}).get(side_key) or {}).get("bundle"), dict)
        ]
        if not loaded_sides:
            if show_overlay:
                # Guard against stale overlays when callers requested an overlaid
                # refresh but no side is currently loaded.
                self._compare_hide_load_splash()
            self._compare_update_status_chips()
            if callable(on_complete):
                on_complete()
            return

        self._compare_render_request_token = (
            int(getattr(self, "_compare_render_request_token", 0)) + 1
        )
        request_token = int(self._compare_render_request_token)
        self._compare_render_jobs_active = int(len(loaded_sides))
        if show_overlay:
            self._compare_show_load_splash("Applying Compare changes")
            self._compare_update_load_splash(
                message="Preparing Compare render...",
                progress=8.0,
                stage_key="queued",
                detail=f"Queued {len(loaded_sides)} side render(s).",
                reset=True,
            )

        def _finalize_if_current() -> None:
            """Finalize one compare refresh request when all side jobs complete."""
            if request_token != int(getattr(self, "_compare_render_request_token", 0)):
                return
            self._compare_render_jobs_active = 0
            self._compare_apply_locked_x_axis()
            self._compare_refresh_cycle_table()
            self._compare_refresh_yield_summary()
            self._compare_persist_state()
            self._compare_update_status_chips()
            if show_overlay:
                self._compare_update_load_splash(
                    message="Compare render complete.",
                    progress=100.0,
                    stage_key="ready",
                    detail=f"Applied {len(loaded_sides)} side render(s).",
                )
                self._compare_hide_load_splash()
            if callable(on_complete):
                on_complete()

        def _mark_side_done() -> None:
            """Decrement active-side counter and finalize when no jobs remain."""
            if request_token != int(getattr(self, "_compare_render_request_token", 0)):
                return
            self._compare_render_jobs_active = max(
                0, int(getattr(self, "_compare_render_jobs_active", 0)) - 1
            )
            if int(getattr(self, "_compare_render_jobs_active", 0)) == 0:
                _finalize_if_current()

        runner = getattr(self, "_combined_render_runner", None)
        if runner is None or not hasattr(runner, "submit"):
            runner = getattr(self, "_task_runner", None)

        if runner is None or not hasattr(runner, "submit"):
            for idx, side_key in enumerate(loaded_sides, start=1):
                if show_overlay:
                    self._compare_update_load_splash(
                        message=f"Rendering Profile {side_key}...",
                        progress=12.0 + (idx * (72.0 / max(1, len(loaded_sides)))),
                        stage_key=f"render_{side_key.lower()}",
                        detail=f"Installing combined figure for side {side_key}.",
                    )
                self._compare_render_profile_side(side_key, reason=reason)
            _finalize_if_current()
            return

        for idx, side_key in enumerate(loaded_sides, start=1):
            panel = (panels or {}).get(side_key) or {}
            bundle = copy.deepcopy(panel.get("bundle") or {})

            def _worker(
                side_token: str = side_key,
                bundle_snapshot: Dict[str, Any] = bundle,
            ) -> Dict[str, Any]:
                """Build compare render context in the worker thread."""
                if not isinstance(bundle_snapshot, dict):
                    return {"ok": False, "error": "No compare bundle loaded."}
                try:
                    prepared = self._compare_build_render_context_from_bundle(
                        bundle_snapshot,
                        side_key=side_token,
                    )
                except Exception as exc:
                    return {
                        "ok": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                return {"ok": True, "prepared": prepared}

            def _on_ok(
                payload: Dict[str, Any],
                *,
                side_token: str = side_key,
                side_idx: int = idx,
            ) -> None:
                """Install one async compare side render result on the UI thread."""
                if request_token != int(
                    getattr(self, "_compare_render_request_token", 0)
                ):
                    return
                if show_overlay:
                    self._compare_update_load_splash(
                        message=f"Rendering Profile {side_token}...",
                        progress=12.0 + (side_idx * (72.0 / max(1, len(loaded_sides)))),
                        stage_key=f"render_{side_token.lower()}",
                        detail=f"Installing combined figure for side {side_token}.",
                    )
                if bool((payload or {}).get("ok")) and (payload or {}).get("prepared"):
                    self._compare_render_profile_side(
                        side_token,
                        reason=reason,
                        prepared=(payload or {}).get("prepared"),
                    )
                else:
                    panel_local = (getattr(self, "_compare_panels", {}) or {}).get(
                        side_token
                    ) or {}
                    error_text = str((payload or {}).get("error") or "").strip()
                    panel_local["cycle_rows"] = []
                    panel_local["total_drop"] = None
                    panel_local["cycle_fallback_used"] = False
                    panel_local["cycle_rows_synthesized"] = False
                    panel_local["cycle_compute_backend"] = ""
                    panel_local["render_success"] = False
                    panel_local["render_error_message"] = (
                        error_text or "Compare render preparation failed."
                    )
                    self._compare_update_side_status(
                        side_token, panel_local["render_error_message"]
                    )
                    self._compare_log_render_completion_event(side_token)
                _mark_side_done()

            def _on_err(exc: BaseException, *, side_token: str = side_key) -> None:
                """Handle one compare async worker failure."""
                if request_token != int(
                    getattr(self, "_compare_render_request_token", 0)
                ):
                    return
                panel_local = (getattr(self, "_compare_panels", {}) or {}).get(
                    side_token
                ) or {}
                panel_local["cycle_rows"] = []
                panel_local["total_drop"] = None
                panel_local["cycle_fallback_used"] = False
                panel_local["cycle_rows_synthesized"] = False
                panel_local["cycle_compute_backend"] = ""
                panel_local["render_success"] = False
                panel_local["render_error_message"] = (
                    f"Compare render worker failed: {type(exc).__name__}"
                )
                self._compare_update_side_status(
                    side_token, panel_local["render_error_message"]
                )
                self._compare_log_render_completion_event(side_token)
                _mark_side_done()

            runner.submit(
                f"compare_render_prepare_{side_key.lower()}",
                _worker,
                _on_ok,
                _on_err,
            )

    def _compare_build_render_context_from_bundle(
        self,
        bundle: Dict[str, Any],
        *,
        side_key: Optional[str] = None,
    ) -> Tuple[RenderContext, List[Dict[str, Any]], Optional[float], Dict[str, Any]]:
        """Build render context and cycle-transfer payload for one compare bundle.

        Purpose:
            Produce full render context needed by combined display rendering.
        Why:
            Compare panes need isolated contexts derived from each profile bundle.
        Args:
            bundle: Compare profile bundle.
        Returns:
            Tuple of render context, cycle-transfer rows, total uptake value, and
            cycle extraction diagnostics metadata.
        Side Effects:
            Computes cycle context/overlays via shared cycle resolver.
        Exceptions:
            Context-resolution failures propagate to caller for pane-level handling.
        """
        data_ctx = bundle.get("data_ctx") or {}
        plot_settings = bundle.get("plot_settings") or {}
        fingerprint = DataFingerprint(
            file_path=str(bundle.get("dataset_path") or ""),
            sheet_key=tuple(bundle.get("sheet_key") or ()),
            columns_key=tuple(bundle.get("columns_key") or ()),
            cycle_temp_column=str(
                data_ctx.get("cycle_temp_column", CYCLE_TEMP_DEFAULT_LABEL)
                or CYCLE_TEMP_DEFAULT_LABEL
            ),
            elapsed_unit=str(self._elapsed_unit_label() or ""),
            multi_sheet=bool(bundle.get("multi_sheet", False)),
            prep_signature=tuple(bundle.get("prep_signature") or ()),
        )
        snapshot = self._compare_cycle_snapshot_from_plot_settings(
            plot_settings,
            side_key=side_key,
            profile_cycle_markers=bundle.get("cycle_markers"),
        )
        data_len = int(data_ctx.get("data_len") or 0)
        if data_len <= 0:
            x_values = (data_ctx.get("series_np") or {}).get("x")
            if x_values is not None:
                try:
                    data_len = int(np.asarray(x_values).size)
                except Exception:
                    data_len = 0
        # Compare must never inherit the main-tab cycle mask; always provide an
        # explicit full-range mask for this side's profile-local data context.
        snapshot["cycle_mask"] = (
            np.ones(data_len, dtype=bool) if data_len > 0 else np.zeros(0, dtype=bool)
        )
        cycle_ctx, overlay_ctx = self._resolve_cycle_context(
            data_ctx,
            fingerprint,
            perf=None,
            snapshot=snapshot,
        )
        cycle_overlay = (overlay_ctx or {}).get("cycle_overlay")
        cycle_rows, synthesized_rows = self._compare_extract_cycle_rows_from_overlay(
            cycle_overlay or {},
            data_ctx=data_ctx,
        )
        cycle_fallback_used = False
        if not cycle_rows:
            # Force one compare-local auto-detect retry when no rows are produced.
            fallback_snapshot = dict(snapshot)
            fallback_snapshot["auto_enabled"] = True
            fallback_snapshot["add_peaks"] = set()
            fallback_snapshot["add_troughs"] = set()
            fallback_snapshot["rm_peaks"] = set()
            fallback_snapshot["rm_troughs"] = set()
            fallback_snapshot["manual_revision"] = 0
            cycle_ctx_fallback, overlay_ctx_fallback = self._resolve_cycle_context(
                data_ctx,
                fingerprint,
                perf=None,
                snapshot=fallback_snapshot,
            )
            cycle_overlay_fallback = (overlay_ctx_fallback or {}).get("cycle_overlay")
            fallback_rows, fallback_synthesized = (
                self._compare_extract_cycle_rows_from_overlay(
                    cycle_overlay_fallback or {},
                    data_ctx=data_ctx,
                )
            )
            if fallback_rows:
                cycle_fallback_used = True
                synthesized_rows = bool(fallback_synthesized)
                cycle_rows = list(fallback_rows)
                cycle_ctx = cycle_ctx_fallback
                overlay_ctx = overlay_ctx_fallback
                cycle_overlay = cycle_overlay_fallback

        args = tuple(bundle.get("args") or ())
        show_cycle_markers = bool(args[-3]) if len(args) >= 3 else False
        compare_state = _normalize_compare_tab_settings(settings.get("compare_tab"))
        show_cycle_legend = bool(
            self.compare_show_cycle_legend_var.get()
            if hasattr(self, "compare_show_cycle_legend_var")
            else compare_state.get("show_cycle_legend", True)
        )
        include_moles = bool(args[-1]) if len(args) >= 1 else False
        overlay_ctx = dict(overlay_ctx or {})
        overlay_ctx["markers"] = cycle_overlay if show_cycle_markers else None
        overlay_ctx["cycle_legend"] = cycle_overlay if show_cycle_legend else None
        overlay_ctx["moles_summary"] = (
            overlay_ctx.get("moles_summary") if include_moles else None
        )
        cycle_payload = (
            dict(cycle_overlay.get("payload") or {})
            if isinstance(cycle_overlay, Mapping)
            else {}
        )
        segmentation_backend = (
            str(
                cycle_ctx.get("segmentation_backend")
                or cycle_payload.get("segmentation_backend")
                or "python"
            )
            .strip()
            .lower()
        )
        metrics_backend = (
            str(
                cycle_ctx.get("metrics_backend")
                or cycle_payload.get("metrics_backend")
                or "python"
            )
            .strip()
            .lower()
        )
        cycle_compute_backend = (
            str(
                cycle_ctx.get("cycle_compute_backend")
                or cycle_payload.get("cycle_compute_backend")
                or (
                    "rust"
                    if (segmentation_backend == "rust" or metrics_backend == "rust")
                    else "python"
                )
            )
            .strip()
            .lower()
        )
        gates_ctx = {
            "show_cycle_markers": show_cycle_markers,
            "show_cycle_legend": show_cycle_legend,
            "include_moles": include_moles,
        }
        scatter_config = {
            "enabled": bool(
                plot_settings.get(
                    "scatter_enabled", settings.get("scatter_enabled", False)
                )
            ),
            "marker": str(
                plot_settings.get("scatter_marker", settings.get("scatter_marker", "o"))
                or "o"
            ),
            "size": float(
                plot_settings.get("scatter_size", settings.get("scatter_size", 24.0))
                or 24.0
            ),
            "color": str(
                plot_settings.get("scatter_color", settings.get("scatter_color", ""))
                or ""
            ).strip(),
            "alpha": float(
                plot_settings.get("scatter_alpha", settings.get("scatter_alpha", 1.0))
                or 1.0
            ),
            "edgecolor": str(
                plot_settings.get(
                    "scatter_edgecolor", settings.get("scatter_edgecolor", "")
                )
                or ""
            ).strip(),
            "linewidth": float(
                plot_settings.get(
                    "scatter_linewidth", settings.get("scatter_linewidth", 0.0)
                )
                or 0.0
            ),
            "linestyle": "",
        }
        render_ctx = RenderContext(
            data_ctx=data_ctx,
            cycle_ctx=cycle_ctx,
            overlay_ctx=overlay_ctx,
            gates_ctx=gates_ctx,
            style_ctx={
                "scatter_config": scatter_config,
                "scatter_series_configs": self._sanitize_series_settings_dict(
                    plot_settings.get("scatter_series")
                ),
                "font_family": settings.get("font_family"),
                "core_legend_fontsize": plot_settings.get(
                    "core_legend_fontsize", settings.get("core_legend_fontsize")
                ),
                "core_cycle_legend_fontsize": plot_settings.get(
                    "core_cycle_legend_fontsize",
                    settings.get("core_cycle_legend_fontsize"),
                ),
                "core_plot_render_profiles": copy.deepcopy(
                    plot_settings.get("core_plot_render_profiles")
                    or settings.get("core_plot_render_profiles")
                    or _get_core_plot_render_profiles()
                ),
            },
            layout_ctx={
                "plot_id": "fig_combined_triple_axis",
                "profile": _get_layout_profile("fig_combined_triple_axis"),
                "target": "display",
            },
            plot_elements_ctx={
                "plot_id": "fig_combined_triple_axis",
                "elements": {},
            },
        )
        total_drop = None
        if isinstance(cycle_overlay, dict):
            try:
                total_drop = float(cycle_overlay.get("total_drop", 0.0))
            except Exception:
                total_drop = None
        if total_drop is None and cycle_rows:
            last_row = dict(cycle_rows[-1] or {})
            total_drop = self._compare_cycle_cumulative_mass_value(last_row)
        metadata = {
            "cycle_fallback_used": bool(cycle_fallback_used),
            "cycle_rows_synthesized": bool(synthesized_rows),
            "cycle_compute_backend": cycle_compute_backend,
            "segmentation_backend": segmentation_backend,
            "metrics_backend": metrics_backend,
        }
        self._compare_log_render_context_event(
            side_key=str(side_key or "").strip().upper() or "?",
            bundle=bundle,
            cycle_rows=cycle_rows,
            total_drop=total_drop,
            metadata=metadata,
        )
        return render_ctx, list(cycle_rows or []), total_drop, metadata

    def _compare_render_profile_side(
        self,
        side_key: str,
        *,
        reason: str = "",
        prepared: Optional[
            Tuple[RenderContext, List[Dict[str, Any]], Optional[float], Dict[str, Any]]
        ] = None,
    ) -> None:
        """Render one Compare pane using the combined-plot display pipeline.

        Purpose:
            Build and install one profile's combined triple-axis figure.
        Why:
            Compare rendering must reuse the existing combined preview/display
            pipeline so resize behavior and annotation/layout interactions remain
            consistent with the main Plot tab.
        Args:
            side_key: Compare side token ("A" or "B").
            reason: Optional reason label for debug/status context.
        Returns:
            None.
        Side Effects:
            Rebuilds the target pane canvas figure, updates side status text, and
            caches cycle rows/total uptake used by comparison tables.
        Exceptions:
            Errors are captured and converted into side-local status text so one
            failed pane does not break the other pane.
        """
        panel = self._compare_panels.get(side_key) or {}
        canvas = panel.get("canvas")
        widget = panel.get("widget")
        bundle = panel.get("bundle")
        if canvas is None or widget is None:
            return
        if not isinstance(bundle, dict):
            fig = Figure(figsize=(5.0, 3.2), dpi=100)
            ax = fig.add_subplot(111)
            load_error_message = str(panel.get("load_error_message") or "").strip()
            placeholder_text = (
                load_error_message if load_error_message else "No profile selected."
            )
            ax.text(0.5, 0.5, placeholder_text, ha="center", va="center")
            ax.set_axis_off()
            try:
                fig.set_canvas(canvas)
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            try:
                canvas.figure = fig
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            self._finalize_matplotlib_canvas_layout(
                canvas=canvas,
                fig=fig,
                tk_widget=widget,
                keep_export_size=False,
                trigger_resize_event=True,
                force_draw=True,
            )
            panel["figure"] = fig
            panel["cycle_rows"] = []
            panel["total_drop"] = None
            panel["cycle_fallback_used"] = False
            panel["cycle_rows_synthesized"] = False
            panel["cycle_compute_backend"] = ""
            panel["render_success"] = False
            panel["render_error_message"] = placeholder_text
            self._compare_update_side_status(side_key, placeholder_text)
            self._compare_log_render_completion_event(side_key)
            return

        try:
            if prepared is not None:
                (
                    render_ctx,
                    cycle_rows,
                    total_drop,
                    cycle_meta,
                ) = prepared
            else:
                (
                    render_ctx,
                    cycle_rows,
                    total_drop,
                    cycle_meta,
                ) = self._compare_build_render_context_from_bundle(
                    bundle,
                    side_key=side_key,
                )
        except Exception as exc:
            panel["cycle_rows"] = []
            panel["total_drop"] = None
            panel["cycle_fallback_used"] = False
            panel["cycle_rows_synthesized"] = False
            panel["cycle_compute_backend"] = ""
            panel["render_success"] = False
            panel["render_error_message"] = f"Cycle prep failed: {type(exc).__name__}"
            self._compare_update_side_status(
                side_key, f"Cycle prep failed: {type(exc).__name__}"
            )
            self._compare_log_render_completion_event(side_key)
            return

        compare_state = _normalize_compare_tab_settings(settings.get("compare_tab"))
        use_profile_layout = bool(
            self.compare_use_profile_layout_var.get()
            if hasattr(self, "compare_use_profile_layout_var")
            else compare_state.get("use_profile_layout", False)
        )
        custom_presets = _normalize_compare_custom_plot_presets(
            getattr(
                self,
                "_compare_custom_plot_presets",
                compare_state.get("custom_plot_presets"),
            )
        )
        selected_preset_name = str(
            self.compare_plot_preset_var.get()
            if hasattr(self, "compare_plot_preset_var")
            else compare_state.get("plot_preset_name")
            or DEFAULT_COMPARE_PLOT_PRESET_NAME
        ).strip()
        compare_preset_values = _resolve_compare_plot_preset_values(
            selected_preset_name,
            custom_presets=custom_presets,
        )
        compare_layout_overrides = _normalize_compare_layout_overrides(
            getattr(
                self, "_compare_layout_overrides", compare_state.get("layout_overrides")
            )
        )
        pair_plot_elements_override = (
            self._compare_effective_pair_plot_elements_override()
        )
        side_override_map = (
            pair_plot_elements_override.get("side_overrides")
            if isinstance(pair_plot_elements_override, Mapping)
            else {}
        )
        side_override_map = (
            side_override_map if isinstance(side_override_map, Mapping) else {}
        )
        side_plot_override = (
            side_override_map.get(side_key)
            if isinstance(side_override_map.get(side_key), Mapping)
            else {}
        )
        retain_profile_elements = bool(
            pair_plot_elements_override.get("retain_profile_elements", True)
            if isinstance(pair_plot_elements_override, Mapping)
            else True
        )
        hide_text_family = bool(
            pair_plot_elements_override.get("hide_text_family", False)
            if isinstance(pair_plot_elements_override, Mapping)
            else False
        )

        fig_size = self._compare_resolve_figsize_for_panel(side_key)
        prior_df = getattr(self, "df", None)
        prior_combined_state = getattr(self, "_combined_plot_state", None)
        prior_combined_layout_state = getattr(self, "_combined_layout_state", None)
        prior_combined_layout_dirty = getattr(self, "_combined_layout_dirty", False)
        prior_layout_profiles = settings.get("layout_profiles")
        anchor_layout_keys = (
            "combined_legend_anchor",
            "combined_legend_loc",
            "combined_cycle_legend_anchor",
            "combined_cycle_legend_loc",
            "combined_cycle_legend_anchor_space",
            "combined_cycle_legend_anchor_mode",
            "combined_cycle_legend_ref_dx_px",
            "combined_cycle_legend_ref_dy_px",
        )
        compare_layout_section_keys = (
            "xlabel_pad_pts",
            "detached_spine_offset",
            "detached_labelpad",
        )
        sentinel = object()
        overridden_keys: Dict[str, Any] = {}
        overridden_tk_vars: Dict[str, Any] = {}
        args_for_render = list(bundle.get("args") or ())
        if len(args_for_render) < 14:
            args_for_render.extend([""] * (14 - len(args_for_render)))
        args_for_render[12] = str(side_plot_override.get("title_text") or "").strip()
        args_for_render[13] = str(side_plot_override.get("suptitle_text") or "").strip()

        def _override_tk_var(
            setting_key: str, var_attr_name: str, payload: Mapping[str, Any]
        ) -> None:
            """Temporarily apply one compare layout value directly to the matching Tk var."""
            if setting_key not in payload:
                return
            var_obj = getattr(self, var_attr_name, None)
            if var_obj is None:
                return
            if var_attr_name not in overridden_tk_vars:
                try:
                    overridden_tk_vars[var_attr_name] = var_obj.get()
                except Exception:
                    overridden_tk_vars[var_attr_name] = sentinel
            try:
                var_obj.set(payload.get(setting_key))
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        try:
            # Combined rendering still consults active settings for style/layout;
            # temporarily apply profile-local settings so pane output matches profile.
            profile_plot_settings = dict(bundle.get("plot_settings") or {})
            for key, value in profile_plot_settings.items():
                overridden_keys[key] = settings.get(key, sentinel)
                settings[key] = copy.deepcopy(value)
            # Compare preset values must win over profile spacing defaults so the
            # side-by-side panes remain readable on smaller canvases.
            for key, value in compare_preset_values.items():
                if key not in overridden_keys:
                    overridden_keys[key] = settings.get(key, sentinel)
                settings[key] = copy.deepcopy(value)
            # Compare layout-manager overrides are applied last and remain
            # authoritative over profile/preset spacing in Compare panes.
            for key, value in compare_layout_overrides.items():
                if key not in overridden_keys:
                    overridden_keys[key] = settings.get(key, sentinel)
                settings[key] = copy.deepcopy(value)
            # Some combined layout fields are sourced from Tk vars; apply compare
            # values directly to those vars so Compare manager controls remain effective.
            for setting_key, attr_name in (
                ("combined_legend_gap_pts", "combined_legend_label_gap"),
                ("combined_legend_bottom_margin_pts", "combined_legend_bottom_margin"),
                ("combined_xlabel_tick_gap_pts", "combined_xlabel_tick_gap"),
                ("combined_left_pad_pct", "combined_left_padding_pct"),
                ("combined_right_pad_pct", "combined_right_padding_pct"),
                ("combined_top_margin_pct", "combined_top_margin_pct"),
                ("combined_title_pad_pts", "combined_title_pad_pts"),
                ("combined_suptitle_pad_pts", "combined_suptitle_pad_pts"),
                ("combined_suptitle_y", "combined_suptitle_y"),
                ("combined_legend_fontsize", "combined_legend_fontsize"),
                ("combined_cycle_legend_fontsize", "combined_cycle_legend_fontsize"),
            ):
                _override_tk_var(setting_key, attr_name, compare_preset_values)
                _override_tk_var(setting_key, attr_name, compare_layout_overrides)

            merged_elements = (
                copy.deepcopy(settings.get("plot_elements"))
                if isinstance(settings.get("plot_elements"), dict)
                else {}
            )
            profile_elements_map = bundle.get("plot_elements")
            profile_elements_map = (
                profile_elements_map
                if isinstance(profile_elements_map, Mapping)
                else {}
            )
            profile_elements_raw = (
                list(profile_elements_map.get("fig_combined_triple_axis") or [])
                if retain_profile_elements
                else []
            )
            normalized_profile_elements = _normalize_plot_elements(
                {"fig_combined_triple_axis": profile_elements_raw}
            ).get("fig_combined_triple_axis", [])
            if hide_text_family:
                filtered_elements: List[Dict[str, Any]] = []
                for element in normalized_profile_elements:
                    if not isinstance(element, Mapping):
                        continue
                    raw_type = str(element.get("type") or "").strip().lower()
                    canonical_type = _canonicalize_annotation_type(raw_type) or raw_type
                    if canonical_type in {"text", "callout", "arrow", "point"}:
                        continue
                    filtered_elements.append(dict(element))
                normalized_profile_elements = filtered_elements
            merged_elements["fig_combined_triple_axis"] = copy.deepcopy(
                normalized_profile_elements
            )
            overridden_keys["plot_elements"] = settings.get("plot_elements", sentinel)
            settings["plot_elements"] = merged_elements
            overridden_keys["layout_health_context"] = settings.get(
                "layout_health_context", sentinel
            )
            settings["layout_health_context"] = "compare"

            profile_layouts = bundle.get("layout_profiles") or {}
            merged_layouts = (
                copy.deepcopy(prior_layout_profiles)
                if isinstance(prior_layout_profiles, dict)
                else {}
            )
            if use_profile_layout and isinstance(profile_layouts, dict):
                merged_layout = copy.deepcopy(
                    profile_layouts.get("fig_combined_triple_axis", {})
                )
                # Profile layout is the base in this mode, but Compare preset and
                # manager values remain deterministic final authorities.
                for key, value in compare_preset_values.items():
                    merged_layout[key] = copy.deepcopy(value)
                for key, value in compare_layout_overrides.items():
                    merged_layout[key] = copy.deepcopy(value)
                if compare_layout_overrides:
                    for layout_key in anchor_layout_keys:
                        merged_layout.pop(layout_key, None)
                        if layout_key not in overridden_keys:
                            overridden_keys[layout_key] = settings.get(
                                layout_key, sentinel
                            )
                        settings.pop(layout_key, None)
                # Compare-local layout section keys must always apply last.
                for layout_key in compare_layout_section_keys:
                    if layout_key in compare_layout_overrides:
                        merged_layout[layout_key] = copy.deepcopy(
                            compare_layout_overrides.get(layout_key)
                        )
                merged_layouts["fig_combined_triple_axis"] = merged_layout
            else:
                # Ignore persisted compare/profile anchors by default so layout
                # starts from one normalized compare baseline.
                merged_layout = {}
                for layout_key in compare_layout_section_keys:
                    if layout_key in compare_layout_overrides:
                        merged_layout[layout_key] = copy.deepcopy(
                            compare_layout_overrides.get(layout_key)
                        )
                merged_layouts["fig_combined_triple_axis"] = merged_layout
                for layout_key in anchor_layout_keys:
                    if layout_key not in overridden_keys:
                        overridden_keys[layout_key] = settings.get(layout_key, sentinel)
                    settings.pop(layout_key, None)
            settings["layout_profiles"] = merged_layouts

            self.df = bundle.get("df_reference")
            fig = self._build_combined_triple_axis_from_state(
                args=tuple(args_for_render),
                fig_size=fig_size,
                mode="display",
                reuse=False,
                canvas=canvas,
                render_ctx=render_ctx,
                perf_run=None,
            )
        except Exception as exc:
            fig = None
            panel["render_success"] = False
            panel["render_error_message"] = f"Render failed: {type(exc).__name__}."
            self._compare_update_side_status(
                side_key, f"Render failed: {type(exc).__name__}."
            )
        finally:
            for key, prior_value in overridden_keys.items():
                if prior_value is sentinel:
                    settings.pop(key, None)
                else:
                    settings[key] = prior_value
            if prior_layout_profiles is None:
                settings.pop("layout_profiles", None)
            else:
                settings["layout_profiles"] = prior_layout_profiles
            for attr_name, prior_value in overridden_tk_vars.items():
                var_obj = getattr(self, attr_name, None)
                if var_obj is None:
                    continue
                try:
                    if prior_value is sentinel:
                        continue
                    var_obj.set(prior_value)
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
            self.df = prior_df
            self._combined_plot_state = prior_combined_state
            self._combined_layout_state = prior_combined_layout_state
            self._combined_layout_dirty = prior_combined_layout_dirty

        if fig is None:
            fig = Figure(figsize=(5.0, 3.2), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Combined plot unavailable.", ha="center", va="center")
            ax.set_axis_off()
            panel["cycle_rows"] = []
            panel["total_drop"] = None
            panel["cycle_fallback_used"] = False
            panel["cycle_rows_synthesized"] = False
            panel["cycle_compute_backend"] = ""
            panel["render_success"] = False
            if not str(panel.get("render_error_message") or "").strip():
                panel["render_error_message"] = "Combined plot unavailable."
        else:
            panel["cycle_rows"] = list(cycle_rows or [])
            panel["total_drop"] = total_drop
            panel["cycle_fallback_used"] = bool(
                (cycle_meta or {}).get("cycle_fallback_used", False)
            )
            panel["cycle_rows_synthesized"] = bool(
                (cycle_meta or {}).get("cycle_rows_synthesized", False)
            )
            panel["cycle_compute_backend"] = str(
                (cycle_meta or {}).get("cycle_compute_backend") or ""
            ).strip()
            panel["render_success"] = True
            panel["render_error_message"] = ""

        try:
            fig.set_canvas(canvas)
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        try:
            canvas.figure = fig
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        self._finalize_matplotlib_canvas_layout(
            canvas=canvas,
            fig=fig,
            tk_widget=widget,
            keep_export_size=False,
            trigger_resize_event=(reason != "lock_x_axis"),
            force_draw=True,
        )
        panel["figure"] = fig

        profile_name = str(bundle.get("profile_name") or "").strip() or "(unnamed)"
        cycle_count = len(panel.get("cycle_rows") or [])
        uptake_value = self._compare_parse_float_entry(panel.get("total_drop"))
        uptake_text = "--" if uptake_value is None else f"{uptake_value:.4f} g"
        reason_text = f" [{reason}]" if reason else ""
        if bool(panel.get("render_success", False)):
            self._compare_update_side_status(
                side_key,
                f"{profile_name}{reason_text}\nCycles: {cycle_count}  |  Total dP uptake: {uptake_text}",
            )
        else:
            render_error_message = str(panel.get("render_error_message") or "").strip()
            self._compare_update_side_status(
                side_key,
                render_error_message or f"{profile_name}: render failed.",
            )
        self._compare_update_status_chips()
        self._compare_log_render_completion_event(side_key)

    def _compare_open_profile_in_cycle_analysis(self, side_key: str) -> bool:
        """Open one side-scoped marker assignment Cycle Analysis window.

        Purpose:
            Launch/focus a dedicated side-specific cycle marker assignment window.
        Why:
            Compare marker editing must not replace the active workspace profile.
        Args:
            side_key: Compare side key (`"A"` or `"B"`).
        Returns:
            True when the side editor window is opened or focused.
        Side Effects:
            Creates/updates one side-scoped toplevel editor and caches marker
            payload state for `Pull Current Markers`.
        Exceptions:
            Missing side data returns False.
        """
        side_token = str(side_key or "").strip().upper()
        if side_token not in {"A", "B"}:
            return False
        panels = getattr(self, "_compare_panels", {})
        panel = (panels.get(side_token) or {}) if isinstance(panels, dict) else {}
        bundle = panel.get("bundle")
        if not isinstance(bundle, Mapping):
            return False
        profile_name = str(bundle.get("profile_name") or "").strip()
        if not profile_name:
            profile_var = (
                self.compare_profile_a_var
                if side_token == "A"
                else self.compare_profile_b_var
            )
            profile_name = str(profile_var.get() or "").strip()

        editor_states = (
            getattr(self, "_compare_cycle_editor_states", {})
            if isinstance(getattr(self, "_compare_cycle_editor_states", {}), dict)
            else {}
        )
        self._compare_cycle_editor_states = editor_states
        existing_state = editor_states.get(side_token) or {}
        existing_window = existing_state.get("window")
        if existing_window is not None and bool(
            getattr(existing_window, "winfo_exists", lambda: False)()
        ):
            try:
                existing_window.deiconify()
                existing_window.lift()
                existing_window.focus_force()
                return True
            except Exception:
                pass

        data_ctx = bundle.get("data_ctx")
        data_ctx = data_ctx if isinstance(data_ctx, Mapping) else {}
        series_np = data_ctx.get("series_np")
        series_np = series_np if isinstance(series_np, Mapping) else {}
        series_map = data_ctx.get("series")
        series_map = series_map if isinstance(series_map, Mapping) else {}
        x_source = series_np.get("x", series_map.get("x"))
        y_source = series_np.get("y1", series_map.get("y1"))
        if x_source is None or y_source is None:
            return False
        try:
            x_all = np.asarray(x_source, dtype=float).reshape(-1)
            y_all = np.asarray(y_source, dtype=float).reshape(-1)
        except Exception:
            return False
        data_len = int(min(x_all.size, y_all.size))
        if data_len <= 1:
            return False
        x_all = x_all[:data_len]
        y_all = y_all[:data_len]
        valid_mask = np.isfinite(x_all) & np.isfinite(y_all)
        if int(np.count_nonzero(valid_mask)) < 2:
            return False
        valid_indices = np.asarray(np.where(valid_mask)[0], dtype=int)

        plot_settings = bundle.get("plot_settings")
        plot_settings = plot_settings if isinstance(plot_settings, Mapping) else {}

        saved_payload = _normalize_profile_cycle_markers(existing_state.get("payload"))
        compare_override_payload = _normalize_profile_cycle_markers(
            (getattr(self, "_compare_marker_overrides", {}) or {}).get(side_token)
        )
        profile_payload = _normalize_profile_cycle_markers(bundle.get("cycle_markers"))
        marker_payload = saved_payload or compare_override_payload or profile_payload

        min_drop_default = float(
            plot_settings.get("min_cycle_drop", settings.get("min_cycle_drop", 0.0))
            or 0.0
        )
        prominence_default = float(
            plot_settings.get("peak_prominence", settings.get("peak_prominence", 1.0))
            or 1.0
        )
        distance_default = max(
            1,
            int(
                plot_settings.get("peak_distance", settings.get("peak_distance", 1))
                or 1
            ),
        )
        width_default = max(
            1,
            int(plot_settings.get("peak_width", settings.get("peak_width", 1)) or 1),
        )
        auto_default = bool(
            plot_settings.get(
                "cycle_auto_detect_enabled",
                settings.get("cycle_auto_detect_enabled", True),
            )
        )
        manual_revision = 0
        add_peaks: Set[int] = set()
        add_troughs: Set[int] = set()
        rm_peaks: Set[int] = set()
        rm_troughs: Set[int] = set()
        if marker_payload is not None:
            auto_default = bool(marker_payload.get("auto_detect_enabled", auto_default))
            add_peaks = set(marker_payload.get("add_peaks") or [])
            add_troughs = set(marker_payload.get("add_troughs") or [])
            rm_peaks = set(marker_payload.get("rm_peaks") or [])
            rm_troughs = set(marker_payload.get("rm_troughs") or [])
            manual_revision = int(marker_payload.get("manual_revision") or 0)
            thresholds = dict(marker_payload.get("thresholds") or {})
            if thresholds.get("min_cycle_drop") is not None:
                min_drop_default = float(thresholds["min_cycle_drop"])
            if thresholds.get("pk_prominence") is not None:
                prominence_default = float(thresholds["pk_prominence"])
            if thresholds.get("pk_distance") is not None:
                distance_default = max(1, int(thresholds["pk_distance"]))
            if thresholds.get("pk_width") is not None:
                width_default = max(1, int(thresholds["pk_width"]))

        base_snapshot = self._compare_cycle_snapshot_from_plot_settings(
            plot_settings,
            side_key=side_token,
            profile_cycle_markers=bundle.get("cycle_markers"),
        )
        base_snapshot["cycle_mask"] = np.ones(data_len, dtype=bool)
        fingerprint = DataFingerprint(
            file_path=str(bundle.get("dataset_path") or ""),
            sheet_key=tuple(bundle.get("sheet_key") or ()),
            columns_key=tuple(bundle.get("columns_key") or ()),
            cycle_temp_column=str(
                data_ctx.get("cycle_temp_column", CYCLE_TEMP_DEFAULT_LABEL)
                or CYCLE_TEMP_DEFAULT_LABEL
            ),
            elapsed_unit=str(self._elapsed_unit_label() or ""),
            multi_sheet=bool(bundle.get("multi_sheet", False)),
            prep_signature=tuple(bundle.get("prep_signature") or ()),
        )

        window = tk.Toplevel(self)
        window.title(f"Compare Cycle Analysis - Side {side_token}")
        window.transient(self)
        window.geometry("980x620")
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)

        controls = ttk.Frame(window, padding=10)
        controls.grid(row=0, column=0, sticky="nsw")
        controls.grid_columnconfigure(0, weight=1)

        mode_var = tk.StringVar(value="add_peak")
        auto_detect_var = tk.BooleanVar(value=bool(auto_default))
        min_drop_var = tk.StringVar(value=f"{float(min_drop_default):.6g}")
        prominence_var = tk.StringVar(value=f"{float(prominence_default):.6g}")
        distance_var = tk.StringVar(value=str(int(distance_default)))
        width_var = tk.StringVar(value=str(int(width_default)))
        status_var = tk.StringVar(value="")
        summary_var = tk.StringVar(value="")

        state: Dict[str, Any] = {
            "window": window,
            "profile_name": profile_name,
            "bundle": bundle,
            "payload": marker_payload,
            "add_peaks": set(int(v) for v in add_peaks),
            "add_troughs": set(int(v) for v in add_troughs),
            "rm_peaks": set(int(v) for v in rm_peaks),
            "rm_troughs": set(int(v) for v in rm_troughs),
            "manual_revision": int(max(0, manual_revision)),
            "latest_overlay": {},
            "latest_cycle_rows": [],
            "series_gap_metrics": {},
        }

        ttk.Label(
            controls,
            text=(
                f"Profile: {profile_name or '--'}\n"
                f"Side: {side_token}\n\n"
                "Click the plot to assign markers using the selected mode."
            ),
            justify="left",
            anchor="w",
            wraplength=250,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        mode_frame = ttk.LabelFrame(controls, text="Click Mode")
        mode_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        mode_options = (
            ("Add Peak", "add_peak"),
            ("Add Trough", "add_trough"),
            ("Remove Peak", "remove_peak"),
            ("Remove Trough", "remove_trough"),
        )
        for row_idx, (label, value) in enumerate(mode_options):
            ttk.Radiobutton(
                mode_frame,
                text=label,
                value=value,
                variable=mode_var,
            ).grid(row=row_idx, column=0, sticky="w", padx=6, pady=2)

        ttk.Checkbutton(
            controls,
            text="Enable auto-detect",
            variable=auto_detect_var,
        ).grid(row=2, column=0, sticky="w", pady=(0, 8))

        threshold_frame = ttk.LabelFrame(controls, text="Thresholds")
        threshold_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        threshold_rows = (
            ("Min dP", min_drop_var),
            ("Prominence", prominence_var),
            ("Distance", distance_var),
            ("Width", width_var),
        )
        for row_idx, (label, var_obj) in enumerate(threshold_rows):
            ttk.Label(threshold_frame, text=label).grid(
                row=row_idx, column=0, sticky="w", padx=(6, 6), pady=2
            )
            ttk.Entry(threshold_frame, textvariable=var_obj, width=12).grid(
                row=row_idx, column=1, sticky="w", padx=(0, 6), pady=2
            )

        ttk.Label(
            controls,
            textvariable=status_var,
            justify="left",
            anchor="w",
            wraplength=250,
        ).grid(row=4, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(
            controls,
            textvariable=summary_var,
            justify="left",
            anchor="w",
            wraplength=250,
        ).grid(row=5, column=0, sticky="ew", pady=(0, 10))

        plot_shell = ttk.Frame(window, padding=(0, 10, 10, 10))
        plot_shell.grid(row=0, column=1, sticky="nsew")
        plot_shell.grid_rowconfigure(1, weight=1)
        plot_shell.grid_columnconfigure(0, weight=1)
        fig = Figure(figsize=(8.2, 5.6), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=plot_shell)
        toolbar = NavigationToolbar2Tk(canvas, plot_shell, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=0, column=0, sticky="ew")
        self._apply_toolbar_scaling(toolbar)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=1, column=0, sticky="nsew")

        action_row = ttk.Frame(controls)
        action_row.grid(row=6, column=0, sticky="ew")

        def _safe_float(var_obj: tk.StringVar, default_value: float) -> float:
            """Parse one float control value with safe fallback."""
            try:
                parsed = float(var_obj.get())
            except Exception:
                parsed = float(default_value)
            return float(parsed) if math.isfinite(parsed) else float(default_value)

        def _safe_int(var_obj: tk.StringVar, default_value: int) -> int:
            """Parse one positive integer control value with safe fallback."""
            try:
                parsed = int(float(var_obj.get()))
            except Exception:
                parsed = int(default_value)
            return max(1, int(parsed))

        def _current_snapshot() -> Dict[str, Any]:
            """Build one cycle-context snapshot from current side editor state."""
            snapshot = dict(base_snapshot)
            snapshot["auto_enabled"] = bool(auto_detect_var.get())
            snapshot["min_cycle_drop"] = _safe_float(min_drop_var, min_drop_default)
            snapshot["prominence"] = _safe_float(prominence_var, prominence_default)
            snapshot["distance"] = _safe_int(distance_var, distance_default)
            snapshot["width"] = _safe_int(width_var, width_default)
            snapshot["add_peaks"] = set(state.get("add_peaks") or set())
            snapshot["add_troughs"] = set(state.get("add_troughs") or set())
            snapshot["rm_peaks"] = set(state.get("rm_peaks") or set())
            snapshot["rm_troughs"] = set(state.get("rm_troughs") or set())
            snapshot["manual_revision"] = int(max(0, state.get("manual_revision") or 0))
            snapshot["cycle_mask"] = np.ones(data_len, dtype=bool)
            return snapshot

        def _build_payload() -> Optional[Dict[str, Any]]:
            """Create normalized marker payload from current editor controls."""
            payload = {
                "schema_version": 1,
                "auto_detect_enabled": bool(auto_detect_var.get()),
                "manual_revision": int(max(0, state.get("manual_revision") or 0)),
                "add_peaks": sorted(int(v) for v in (state.get("add_peaks") or set())),
                "add_troughs": sorted(
                    int(v) for v in (state.get("add_troughs") or set())
                ),
                "rm_peaks": sorted(int(v) for v in (state.get("rm_peaks") or set())),
                "rm_troughs": sorted(
                    int(v) for v in (state.get("rm_troughs") or set())
                ),
                "thresholds": {
                    "min_cycle_drop": _safe_float(min_drop_var, min_drop_default),
                    "pk_prominence": _safe_float(prominence_var, prominence_default),
                    "pk_distance": _safe_int(distance_var, distance_default),
                    "pk_width": _safe_int(width_var, width_default),
                },
                "source_profile_name": profile_name,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
            return _normalize_profile_cycle_markers(payload)

        def _update_summary_from_overlay(overlay: Mapping[str, Any]) -> None:
            """Update side editor summary text from current overlay payload."""
            cycles = list(overlay.get("cycles") or [])
            total_drop = self._compare_parse_float_entry(overlay.get("total_drop"))
            total_drop_text = "--" if total_drop is None else f"{total_drop:.2f} PSI"
            peaks_count = len(list(overlay.get("peaks_idx") or []))
            troughs_count = len(list(overlay.get("troughs_idx") or []))
            summary_var.set(
                f"Cycles: {len(cycles)}\n"
                f"Peaks: {peaks_count}  |  Troughs: {troughs_count}\n"
                f"Total dP: {total_drop_text}"
            )

        def _render_overlay() -> None:
            """Recompute and draw cycle overlay for current side editor settings.

            Purpose:
                Refresh one side-specific marker-assignment plot and summary state.
            Why:
                Compare-side marker editing needs deterministic visual feedback that
                preserves data discontinuities for stitched/gapped profiles.
            Args:
                None.
            Returns:
                None.
            Side Effects:
                Updates side editor cache state, redraws plot artists, and emits
                cycle-editor diagnostics for collaborative debugging.
            Exceptions:
                Cycle-context resolution failures are converted into status text.
            """
            try:
                _cycle_ctx, overlay_ctx = self._resolve_cycle_context(
                    data_ctx,
                    fingerprint,
                    perf=None,
                    snapshot=_current_snapshot(),
                )
            except Exception as exc:
                status_var.set(f"Cycle recompute failed: {type(exc).__name__}")
                return
            cycle_overlay = (
                overlay_ctx.get("cycle_overlay")
                if isinstance(overlay_ctx, Mapping)
                else None
            )
            cycle_overlay = cycle_overlay if isinstance(cycle_overlay, Mapping) else {}
            cycle_rows, _synth = self._compare_extract_cycle_rows_from_overlay(
                cycle_overlay,
                data_ctx=data_ctx,
            )
            state["latest_overlay"] = dict(cycle_overlay)
            state["latest_cycle_rows"] = list(cycle_rows or [])
            normalized_payload = _build_payload()
            state["payload"] = normalized_payload
            editor_states[side_token] = state
            self._compare_cycle_editor_states = editor_states

            ax.clear()
            x_plot = np.asarray(x_all, dtype=float)
            y_plot = np.asarray(y_all, dtype=float)
            non_finite = ~(np.isfinite(x_plot) & np.isfinite(y_plot))
            if int(np.count_nonzero(non_finite)) > 0:
                # Preserve explicit trace breaks by keeping separator rows as NaN.
                x_plot[non_finite] = np.nan
                y_plot[non_finite] = np.nan
            ax.plot(
                x_plot,
                y_plot,
                color="#1565c0",
                linewidth=1.2,
                label="Pressure (PSI)",
            )
            peak_points = list(cycle_overlay.get("peak_points") or [])
            trough_points = list(cycle_overlay.get("trough_points") or [])
            if peak_points:
                px = np.asarray([float(p[0]) for p in peak_points], dtype=float)
                py = np.asarray([float(p[1]) for p in peak_points], dtype=float)
                finite = np.isfinite(px) & np.isfinite(py)
                ax.scatter(
                    px[finite],
                    py[finite],
                    marker="^",
                    s=28,
                    color="#2e7d32",
                    label="Peak",
                    zorder=4,
                )
            if trough_points:
                tx = np.asarray([float(p[0]) for p in trough_points], dtype=float)
                ty = np.asarray([float(p[1]) for p in trough_points], dtype=float)
                finite = np.isfinite(tx) & np.isfinite(ty)
                ax.scatter(
                    tx[finite],
                    ty[finite],
                    marker="v",
                    s=28,
                    color="#1565c0",
                    label="Trough",
                    zorder=4,
                )
            x_label = str(
                (data_ctx.get("selected_columns") or {}).get("x") or "Elapsed Time"
            )
            ax.set_xlabel(x_label.replace("_", " "))
            ax.set_ylabel("Pressure (PSI)")
            ax.set_title(f"Compare Side {side_token} Marker Assignment")
            ax.grid(True, alpha=0.25, linewidth=0.5)
            try:
                ax.legend(loc="upper right", **_legend_shadowbox_kwargs())
            except Exception:
                pass
            canvas.draw_idle()
            gap_metrics = self._compare_series_gap_metrics(x_all, y_all)
            state["series_gap_metrics"] = dict(gap_metrics)
            _update_summary_from_overlay(cycle_overlay)
            status_var.set(
                f"Mode: {str(mode_var.get() or '').replace('_', ' ').title()}  |  "
                f"Manual revision: {int(state.get('manual_revision') or 0)}"
            )
            self._compare_log_cycle_editor_event(
                side_key=side_token,
                event_name="recompute",
                payload={
                    "cycles": len(list(cycle_overlay.get("cycles") or [])),
                    "peaks": len(list(cycle_overlay.get("peaks_idx") or [])),
                    "troughs": len(list(cycle_overlay.get("troughs_idx") or [])),
                    "manual_revision": int(state.get("manual_revision") or 0),
                    "series_gaps": gap_metrics,
                },
            )

        def _nearest_valid_index(
            x_value: float, y_value: Optional[float]
        ) -> Optional[int]:
            """Resolve nearest finite data index to clicked axis coordinates."""
            if not math.isfinite(x_value):
                return None
            local_x = x_all[valid_indices]
            local_y = y_all[valid_indices]
            if local_x.size == 0:
                return None
            x_span = max(float(np.nanmax(local_x) - np.nanmin(local_x)), 1e-9)
            if y_value is None or not math.isfinite(y_value):
                score = np.abs((local_x - float(x_value)) / x_span)
            else:
                y_span = max(float(np.nanmax(local_y) - np.nanmin(local_y)), 1e-9)
                score = ((local_x - float(x_value)) / x_span) ** 2 + (
                    (local_y - float(y_value)) / y_span
                ) ** 2
            try:
                nearest_pos = int(np.nanargmin(score))
            except Exception:
                return None
            if nearest_pos < 0 or nearest_pos >= valid_indices.size:
                return None
            return int(valid_indices[nearest_pos])

        def _on_click(event: Any) -> None:
            """Handle mouse clicks for side-specific marker assignment edits."""
            if event is None or event.inaxes is not ax:
                return
            if event.xdata is None:
                return
            nearest_idx = _nearest_valid_index(float(event.xdata), event.ydata)
            if nearest_idx is None:
                return
            mode_value = str(mode_var.get() or "").strip().lower()
            if mode_value == "add_peak":
                state["add_peaks"].add(int(nearest_idx))
                state["rm_peaks"].discard(int(nearest_idx))
            elif mode_value == "add_trough":
                state["add_troughs"].add(int(nearest_idx))
                state["rm_troughs"].discard(int(nearest_idx))
            elif mode_value == "remove_peak":
                state["rm_peaks"].add(int(nearest_idx))
                state["add_peaks"].discard(int(nearest_idx))
            elif mode_value == "remove_trough":
                state["rm_troughs"].add(int(nearest_idx))
                state["add_troughs"].discard(int(nearest_idx))
            else:
                return
            state["manual_revision"] = (
                int(max(0, state.get("manual_revision") or 0)) + 1
            )
            _render_overlay()

        def _reset_to_starting_payload() -> None:
            """Reset editor marker state back to initial payload values."""
            base_payload = _normalize_profile_cycle_markers(marker_payload)
            state["add_peaks"] = (
                set(base_payload.get("add_peaks") or []) if base_payload else set()
            )
            state["add_troughs"] = (
                set(base_payload.get("add_troughs") or []) if base_payload else set()
            )
            state["rm_peaks"] = (
                set(base_payload.get("rm_peaks") or []) if base_payload else set()
            )
            state["rm_troughs"] = (
                set(base_payload.get("rm_troughs") or []) if base_payload else set()
            )
            state["manual_revision"] = (
                int(base_payload.get("manual_revision") or 0) if base_payload else 0
            )
            if base_payload is not None:
                thresholds_payload = dict(base_payload.get("thresholds") or {})
                if thresholds_payload.get("min_cycle_drop") is not None:
                    min_drop_var.set(
                        f"{float(thresholds_payload.get('min_cycle_drop')):.6g}"
                    )
                else:
                    min_drop_var.set(f"{float(min_drop_default):.6g}")
                if thresholds_payload.get("pk_prominence") is not None:
                    prominence_var.set(
                        f"{float(thresholds_payload.get('pk_prominence')):.6g}"
                    )
                else:
                    prominence_var.set(f"{float(prominence_default):.6g}")
                if thresholds_payload.get("pk_distance") is not None:
                    distance_var.set(
                        str(max(1, int(thresholds_payload.get("pk_distance"))))
                    )
                else:
                    distance_var.set(str(int(distance_default)))
                if thresholds_payload.get("pk_width") is not None:
                    width_var.set(str(max(1, int(thresholds_payload.get("pk_width")))))
                else:
                    width_var.set(str(int(width_default)))
                auto_detect_var.set(
                    bool(base_payload.get("auto_detect_enabled", auto_default))
                )
            else:
                min_drop_var.set(f"{float(min_drop_default):.6g}")
                prominence_var.set(f"{float(prominence_default):.6g}")
                distance_var.set(str(int(distance_default)))
                width_var.set(str(int(width_default)))
                auto_detect_var.set(bool(auto_default))
            _render_overlay()

        def _close_window() -> None:
            """Close side editor window while retaining last payload state."""
            state["window"] = None
            editor_states[side_token] = state
            self._compare_cycle_editor_states = editor_states
            try:
                window.destroy()
            except Exception:
                pass

        self._compare_make_button(
            action_row,
            text="Recompute",
            command=_render_overlay,
            compact=True,
        ).pack(side="left", padx=(0, 6))
        self._compare_make_button(
            action_row,
            text="Reset",
            command=_reset_to_starting_payload,
            compact=True,
        ).pack(side="left", padx=(0, 6))
        self._compare_make_button(
            action_row,
            text="Close",
            command=_close_window,
            compact=True,
        ).pack(side="left")

        try:
            canvas.mpl_connect("button_press_event", _on_click)
        except Exception:
            pass
        window.protocol("WM_DELETE_WINDOW", _close_window)
        editor_states[side_token] = state
        self._compare_cycle_editor_states = editor_states
        _render_overlay()
        self._compare_log_cycle_editor_event(
            side_key=side_token,
            event_name="editor_window_ready",
            payload={"profile_name": profile_name},
        )
        return True

    def _open_compare_marker_editor(self, side_key: str) -> None:
        """Open Compare-side marker correction popup for one profile side.

        Purpose:
            Provide fast marker-correction workflows from Compare side A/B.
        Why:
            One profile can require manual peak/trough correction before accurate
            uptake comparison; this popup links Cycle Analysis and Compare apply.
        Args:
            side_key: Compare side key (`"A"` or `"B"`).
        Returns:
            None.
        Side Effects:
            Opens modal popup, launches/focuses side-scoped marker editor windows,
            updates compare marker overrides, and can persist marker payloads to
            profiles.
        Exceptions:
            Invalid side keys or missing profile selections show user feedback.
        """
        if side_key not in {"A", "B"}:
            return
        profile_name = str(
            (
                self.compare_profile_a_var
                if side_key == "A"
                else self.compare_profile_b_var
            ).get()
            or ""
        ).strip()
        if not profile_name:
            try:
                messagebox.showinfo(
                    "Compare Marker Editor",
                    f"Select a profile for side {side_key} first.",
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Compare Marker Editor - Side {side_key}")
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grid_columnconfigure(0, weight=1)

        staged_payload: Dict[str, Optional[Dict[str, Any]]] = {
            "value": _normalize_profile_cycle_markers(
                (getattr(self, "_compare_marker_overrides", {}) or {}).get(side_key)
            )
        }
        status_var = tk.StringVar(value="")
        summary_var = tk.StringVar(value="")
        save_profile_var = tk.BooleanVar(value=False)

        def _format_payload_summary(payload: Optional[Mapping[str, Any]]) -> str:
            """Build one compact marker payload summary string for popup display."""
            normalized = _normalize_profile_cycle_markers(payload)
            if normalized is None:
                return "Source: none (profile auto-detect only)"
            thresholds_payload = dict(normalized.get("thresholds") or {})
            return (
                f"Source: compare override\n"
                f"Add peaks: {len(normalized.get('add_peaks') or [])}  |  "
                f"Add troughs: {len(normalized.get('add_troughs') or [])}\n"
                f"Remove peaks: {len(normalized.get('rm_peaks') or [])}  |  "
                f"Remove troughs: {len(normalized.get('rm_troughs') or [])}\n"
                f"Auto-detect: {'On' if normalized.get('auto_detect_enabled', True) else 'Off'}  |  "
                f"min_drop: {thresholds_payload.get('min_cycle_drop', '--')}"
            )

        def _refresh_summary() -> None:
            """Refresh staged marker summary and profile status text."""
            summary_var.set(_format_payload_summary(staged_payload.get("value")))
            status_var.set(f"Target profile: {profile_name}  |  Side: {side_key}")

        def _pull_from_cycle_analysis() -> None:
            """Pull side-editor marker edits into staged Compare override payload.

            Purpose:
                Import the latest marker payload from the side-specific cycle editor.
            Why:
                Compare marker correction must consume side-matched edits without
                relying on the main workspace Cycle Analysis state.
            Args:
                None.
            Returns:
                None.
            Side Effects:
                Updates staged override payload, refreshes popup summary text, and
                emits one cycle-editor diagnostics event.
            Exceptions:
                Missing side window/editor payload updates status text and exits.
            """
            current_payload = self._compare_collect_current_cycle_marker_payload(
                side_key=side_key
            )
            if current_payload is None:
                status_var.set(
                    "No side-matched Cycle Analysis window state found. Open Side "
                    f"{side_key} first, edit markers, then pull."
                )
                self._compare_log_cycle_editor_event(
                    side_key=side_key,
                    event_name="pull_missing_editor_state",
                    payload={"profile_name": profile_name},
                )
                return
            staged_payload["value"] = current_payload
            _refresh_summary()
            status_var.set("Pulled markers from side-specific Cycle Analysis window.")
            self._compare_log_cycle_editor_event(
                side_key=side_key,
                event_name="pull_markers",
                payload={
                    "profile_name": profile_name,
                    "manual_revision": int(current_payload.get("manual_revision") or 0),
                    "add_peaks": len(list(current_payload.get("add_peaks") or [])),
                    "add_troughs": len(list(current_payload.get("add_troughs") or [])),
                    "rm_peaks": len(list(current_payload.get("rm_peaks") or [])),
                    "rm_troughs": len(list(current_payload.get("rm_troughs") or [])),
                },
            )

        def _open_cycle_analysis() -> None:
            """Open/focus the side-specific cycle editor window for marker reassignment.

            Purpose:
                Launch the side-targeted Cycle Analysis editor from marker popup flow.
            Why:
                Compare marker correction requires isolated side editing so the
                workspace profile context is not replaced.
            Args:
                None.
            Returns:
                None.
            Side Effects:
                Opens/focuses side editor window, updates popup status text, and
                emits one cycle-editor diagnostics event.
            Exceptions:
                Window launch failures update status text and continue safely.
            """
            opened = self._compare_open_profile_in_cycle_analysis(side_key)
            if opened:
                status_var.set(
                    f"Opened side {side_key} Cycle Analysis window for '{profile_name}'. "
                    "Reassign markers, then pull."
                )
                self._compare_log_cycle_editor_event(
                    side_key=side_key,
                    event_name="open_side_editor",
                    payload={"profile_name": profile_name, "opened": True},
                )
            else:
                status_var.set("Could not open profile in Cycle Analysis.")
                self._compare_log_cycle_editor_event(
                    side_key=side_key,
                    event_name="open_side_editor",
                    payload={"profile_name": profile_name, "opened": False},
                )

        def _apply_to_compare(save_to_profile: bool, close_after: bool) -> None:
            """Apply staged marker payload to Compare and optionally persist to profile.

            Purpose:
                Commit staged marker overrides to the selected Compare side.
            Why:
                Marker correction workflows require explicit apply semantics with
                optional profile persistence for reuse.
            Args:
                save_to_profile: True to persist payload into the profile JSON.
                close_after: True to close popup after apply.
            Returns:
                None.
            Side Effects:
                Updates compare override state, optionally writes profile data,
                schedules Compare rerender, and emits cycle-editor diagnostics.
            Exceptions:
                Profile save failures are surfaced through status text.
            """
            normalized = _normalize_profile_cycle_markers(staged_payload.get("value"))
            marker_overrides = _normalize_compare_marker_overrides(
                getattr(self, "_compare_marker_overrides", {})
            )
            marker_overrides[side_key] = normalized
            self._compare_marker_overrides = dict(marker_overrides)
            save_requested = bool(save_to_profile or save_profile_var.get())
            if save_requested and normalized is not None:
                saved = self._compare_save_marker_payload_to_profile(
                    profile_name, normalized
                )
                if not saved:
                    status_var.set("Apply succeeded, but profile save failed.")
                else:
                    status_var.set("Applied marker override and saved to profile.")
            else:
                status_var.set("Applied marker override to Compare.")
            self._compare_persist_state()
            self._compare_refresh_loaded_sides_async(
                reason="marker_override",
                show_overlay=True,
                on_complete=self._compare_refresh_diagnostics_panel,
            )
            self._compare_log_cycle_editor_event(
                side_key=side_key,
                event_name="apply_override",
                payload={
                    "profile_name": profile_name,
                    "saved_to_profile": bool(save_requested and normalized is not None),
                    "override_present": bool(normalized is not None),
                    "manual_revision": int(
                        (normalized or {}).get("manual_revision") or 0
                    ),
                    "close_after": bool(close_after),
                },
            )
            if close_after:
                try:
                    dialog.destroy()
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass

        ttk.Label(
            dialog,
            text=(
                "Use Cycle Analysis to reassign peak/trough markers, then pull and apply "
                "the corrected marker set to this Compare side."
            ),
            justify="left",
            anchor="w",
            wraplength=520,
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        ttk.Label(
            dialog,
            textvariable=status_var,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))
        ttk.Label(
            dialog,
            textvariable=summary_var,
            justify="left",
            anchor="w",
            wraplength=520,
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

        actions = ttk.Frame(dialog)
        actions.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 8))
        self._compare_make_button(
            actions,
            text="Open In Cycle Analysis",
            command=_open_cycle_analysis,
            compact=True,
        ).pack(side="left")
        self._compare_make_button(
            actions,
            text="Pull Current Markers",
            command=_pull_from_cycle_analysis,
            compact=True,
        ).pack(side="left", padx=(6, 0))
        self._compare_make_button(
            actions,
            text="Reset Override",
            command=lambda: (
                staged_payload.__setitem__("value", None),
                _refresh_summary(),
            ),
            compact=True,
        ).pack(side="left", padx=(6, 0))

        ttk.Checkbutton(
            dialog,
            text="Save applied markers to this profile",
            variable=save_profile_var,
        ).grid(row=4, column=0, sticky="w", padx=10, pady=(0, 8))

        apply_row = ttk.Frame(dialog)
        apply_row.grid(row=5, column=0, sticky="e", padx=10, pady=(0, 10))
        self._compare_make_button(
            apply_row,
            text="Apply to Compare",
            command=lambda: _apply_to_compare(False, False),
            compact=True,
        ).pack(side="right", padx=(6, 0))
        self._compare_make_button(
            apply_row,
            text="Apply + Save Profile",
            command=lambda: _apply_to_compare(True, True),
            compact=True,
        ).pack(side="right", padx=(6, 0))
        self._compare_make_button(
            apply_row,
            text="Close",
            command=dialog.destroy,
            compact=True,
        ).pack(side="right")

        _refresh_summary()
        try:
            dialog.grab_set()
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

    def _build_tab_compare(self) -> None:
        """Build the Compare tab UI and initialize comparison state.

        Purpose:
            Construct controls and output surfaces for two-profile comparison.
        Why:
            Compare workflows require a dedicated workspace for side-by-side
            combined plots, per-cycle uptake tables, and yield analysis.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Creates Compare-tab widgets, binds callbacks, and initializes state
            caches used by rendering and table updates.
        Exceptions:
            Returns early when tab frame is unavailable.
        """
        tab_frame = getattr(self, "tab_compare", None)
        if tab_frame is None:
            return
        for child in list(tab_frame.winfo_children()):
            try:
                child.destroy()
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting rebuild.
                pass
        compare_state = _normalize_compare_tab_settings(settings.get("compare_tab"))
        settings["compare_tab"] = compare_state

        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=1)
        outer = ttk.Frame(tab_frame)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        compare_canvas = tk.Canvas(outer, highlightthickness=0, borderwidth=0)
        compare_canvas.grid(row=0, column=0, sticky="nsew")
        compare_scrollbar = _ui_scrollbar(
            outer, orient="vertical", command=compare_canvas.yview
        )
        compare_scrollbar.grid(row=0, column=1, sticky="ns")
        compare_canvas.configure(yscrollcommand=compare_scrollbar.set)

        frame = ttk.Frame(compare_canvas)
        compare_canvas_window = compare_canvas.create_window(
            (0, 0), window=frame, anchor="nw"
        )
        self._compare_tab_canvas = compare_canvas
        self._compare_tab_canvas_window_id = compare_canvas_window
        self._compare_tab_content_frame = frame

        def _refresh_compare_tab_scrollregion(
            _event: Optional[tk.Event] = None,
        ) -> None:
            """Refresh Compare tab outer scroll region after layout changes."""
            canvas_local = getattr(self, "_compare_tab_canvas", None)
            if canvas_local is None:
                return
            try:
                canvas_local.configure(scrollregion=canvas_local.bbox("all"))
            except Exception:
                pass

        def _sync_compare_tab_window_geometry(
            *,
            width_px: Optional[int] = None,
            height_px: Optional[int] = None,
        ) -> None:
            """Sync Compare canvas-window geometry using shared helper."""
            self._compare_sync_tab_canvas_geometry(
                width_px=width_px,
                height_px=height_px,
                canvas=compare_canvas,
                window_id=compare_canvas_window,
                content_frame=frame,
            )

        def _on_compare_tab_canvas_configure(event: tk.Event) -> None:
            """Update Compare canvas-window geometry from viewport configure events."""
            _sync_compare_tab_window_geometry(
                width_px=int(getattr(event, "width", 0) or 0),
                height_px=int(getattr(event, "height", 0) or 0),
            )

        def _skip_compare_tab_scroll(widget: Any) -> bool:
            """Return whether a widget should keep native mousewheel behavior."""
            if isinstance(widget, (tk.Text, tk.Listbox, ttk.Treeview)):
                return True
            side_canvas = getattr(self, "_compare_side_canvas", None)
            current = widget
            while current is not None:
                if side_canvas is not None and current is side_canvas:
                    return True
                current = getattr(current, "master", None)
            return False

        def _on_compare_tab_mousewheel(event: Any) -> Optional[str]:
            """Scroll the full Compare tab canvas on mousewheel events."""
            if _skip_compare_tab_scroll(event.widget):
                return None
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return None
            step = -1 if delta > 0 else 1
            if abs(delta) >= 120:
                step = int(-delta / 120)
            compare_canvas.yview_scroll(step, "units")
            return "break"

        def _bind_compare_tab_mousewheel(widget: Any) -> None:
            """Bind full-tab mousewheel scrolling recursively for Compare widgets."""
            try:
                widget.bind("<MouseWheel>", _on_compare_tab_mousewheel, add="+")
                widget.bind(
                    "<Button-4>",
                    lambda evt: None
                    if _skip_compare_tab_scroll(evt.widget)
                    else compare_canvas.yview_scroll(-1, "units"),
                    add="+",
                )
                widget.bind(
                    "<Button-5>",
                    lambda evt: None
                    if _skip_compare_tab_scroll(evt.widget)
                    else compare_canvas.yview_scroll(1, "units"),
                    add="+",
                )
            except Exception:
                pass
            for child in list(widget.winfo_children() or []):
                _bind_compare_tab_mousewheel(child)

        try:
            frame.bind(
                "<Configure>",
                lambda _event: _sync_compare_tab_window_geometry(),
                add="+",
            )
            compare_canvas.bind(
                "<Configure>", _on_compare_tab_canvas_configure, add="+"
            )
        except Exception:
            pass
        self.after_idle(lambda: _bind_compare_tab_mousewheel(frame))
        self.after_idle(_sync_compare_tab_window_geometry)

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        controls = ttk.LabelFrame(frame, text="Profile Selection")
        controls.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        for col in range(15):
            # Compare controls contain long labels; keep columns flexible so wrapped
            # text remains readable at different window sizes/scales.
            controls.grid_columnconfigure(col, weight=1)

        self.compare_profile_a_var = tk.StringVar(
            value=str(compare_state.get("profile_a_name") or "")
        )
        self.compare_profile_b_var = tk.StringVar(
            value=str(compare_state.get("profile_b_name") or "")
        )
        self.compare_lock_x_axis_var = tk.BooleanVar(
            value=bool(compare_state.get("lock_x_axis", True))
        )
        self.compare_use_profile_layout_var = tk.BooleanVar(
            value=bool(compare_state.get("use_profile_layout", False))
        )
        self.compare_show_cycle_legend_var = tk.BooleanVar(
            value=bool(compare_state.get("show_cycle_legend", True))
        )
        self.compare_yield_mode_var = tk.StringVar(
            value=str(compare_state.get("yield_basis_mode", "auto") or "auto")
        )
        self._compare_layout_overrides = _normalize_compare_layout_overrides(
            compare_state.get("layout_overrides")
        )
        self._compare_marker_overrides = _normalize_compare_marker_overrides(
            compare_state.get("marker_overrides")
        )
        self._compare_plot_elements_overrides_by_pair = (
            _normalize_compare_plot_elements_overrides_by_pair(
                compare_state.get("plot_elements_overrides_by_pair")
            )
        )
        self._compare_report_preferences = _normalize_compare_report_preferences(
            compare_state.get("report_preferences")
        )
        self._compare_layout_manager_window: Optional[tk.Toplevel] = None
        self._compare_plot_elements_window: Optional[tk.Toplevel] = None
        self._compare_assign_profiles_window: Optional[tk.Toplevel] = None
        self._compare_assign_profiles_search_var: Optional[tk.StringVar] = None
        self._compare_assign_profiles_listbox: Optional[tk.Listbox] = None
        self._compare_assign_profiles_stage_a_var: Optional[tk.StringVar] = None
        self._compare_assign_profiles_stage_b_var: Optional[tk.StringVar] = None
        self._compare_assign_profiles_status_var: Optional[tk.StringVar] = None
        self._compare_assign_profiles_filtered_names: List[str] = []
        self._compare_rust_preflight_done = bool(
            getattr(self, "_compare_rust_preflight_done", False)
        )
        custom_presets = _normalize_compare_custom_plot_presets(
            compare_state.get("custom_plot_presets")
        )
        self._compare_custom_plot_presets = dict(custom_presets)
        builtin_preset_names = list(_builtin_compare_plot_presets().keys())
        custom_preset_names = [
            name for name in sorted(custom_presets) if name not in builtin_preset_names
        ]
        self._compare_plot_preset_names = builtin_preset_names + custom_preset_names
        preset_name = str(compare_state.get("plot_preset_name") or "").strip()
        if preset_name not in self._compare_plot_preset_names:
            preset_name = DEFAULT_COMPARE_PLOT_PRESET_NAME
        self.compare_plot_preset_var = tk.StringVar(value=preset_name)
        self.compare_isolated_mass_a_var = tk.StringVar(
            value=(
                ""
                if compare_state.get("isolated_mass_a_g") is None
                else f"{float(compare_state.get('isolated_mass_a_g')):.6g}"
            )
        )
        self.compare_isolated_mass_b_var = tk.StringVar(
            value=(
                ""
                if compare_state.get("isolated_mass_b_g") is None
                else f"{float(compare_state.get('isolated_mass_b_g')):.6g}"
            )
        )
        override_state = compare_state.get("yield_override") or {}
        self.compare_override_starting_mass_var = tk.StringVar(
            value=(
                ""
                if override_state.get("starting_mass_g") is None
                else f"{float(override_state.get('starting_mass_g')):.6g}"
            )
        )
        self.compare_override_mw_var = tk.StringVar(
            value=(
                ""
                if override_state.get("starting_material_mw_g_mol") is None
                else f"{float(override_state.get('starting_material_mw_g_mol')):.6g}"
            )
        )
        self.compare_override_stoich_var = tk.StringVar(
            value=(
                ""
                if override_state.get("stoich_mol_gas_per_mol_starting") is None
                else f"{float(override_state.get('stoich_mol_gas_per_mol_starting')):.6g}"
            )
        )
        self.compare_override_gas_mw_var = tk.StringVar(
            value=(
                ""
                if override_state.get("gas_molar_mass") is None
                else f"{float(override_state.get('gas_molar_mass')):.6g}"
            )
        )
        self._compare_cycle_table_view_profiles = (
            _normalize_compare_cycle_table_view_profiles(
                compare_state.get("cycle_table_view_profiles")
            )
        )
        self._compare_cycle_table_active_view_mode = (
            _normalize_compare_cycle_table_view_mode(
                compare_state.get("cycle_table_view_mode"),
                default="standard",
            )
        )
        self._compare_cycle_table_view_mode_var = tk.StringVar(
            value=COMPARE_CYCLE_TABLE_VIEW_MODE_LABELS.get(
                self._compare_cycle_table_active_view_mode,
                COMPARE_CYCLE_TABLE_VIEW_MODE_LABELS["standard"],
            )
        )
        self._compare_cycle_table_column_resize_active = False
        self._compare_profile_a_combo: Optional[ttk.Combobox] = None
        self._compare_profile_b_combo: Optional[ttk.Combobox] = None
        existing_cycle_editor_states = getattr(
            self, "_compare_cycle_editor_states", None
        )
        self._compare_cycle_editor_states = (
            existing_cycle_editor_states
            if isinstance(existing_cycle_editor_states, dict)
            else {}
        )

        self._compare_make_button(
            controls,
            text="Open Assign Profiles...",
            command=self._open_compare_assign_profiles_dialog,
        ).grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=6)

        self._compare_make_button(
            controls,
            text="Load Profiles",
            command=self._compare_load_selected_profiles,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 4), pady=6)
        self._compare_make_button(
            controls,
            text="Run Comparison",
            command=self._compare_run_comparison,
        ).grid(row=0, column=2, sticky="ew", padx=(0, 4), pady=6)
        self._compare_make_button(
            controls,
            text="Swap",
            command=self._compare_swap_profiles,
        ).grid(row=0, column=3, sticky="ew", padx=(0, 4), pady=6)
        refresh_profiles_button = self._compare_make_button(
            controls,
            text="Refresh Profiles",
            command=self._compare_refresh_profile_choices,
        )
        refresh_profiles_button.grid(row=0, column=4, sticky="ew", padx=(0, 8), pady=6)
        current_to_a_button = self._compare_make_button(
            controls,
            text="Current -> A",
            command=lambda: self._compare_set_current_profile_for_side("A"),
        )
        current_to_a_button.grid(row=0, column=5, sticky="ew", padx=(0, 4), pady=6)
        current_to_b_button = self._compare_make_button(
            controls,
            text="Current -> B",
            command=lambda: self._compare_set_current_profile_for_side("B"),
        )
        current_to_b_button.grid(row=0, column=6, sticky="ew", padx=(0, 6), pady=6)
        try:
            controls.update_idletasks()
            current_to_b_width_px = int(current_to_b_button.winfo_reqwidth() or 0)
        except Exception:
            current_to_b_width_px = 0
        if current_to_b_width_px > 1:
            # Match Refresh/Current-A button footprint to Current-B so the quick
            # assignment controls remain visually consistent in Compare.
            for column_index in (4, 5):
                try:
                    controls.grid_columnconfigure(
                        column_index, minsize=current_to_b_width_px
                    )
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
        _ui_checkbutton(
            controls,
            text="Lock X-axis",
            variable=self.compare_lock_x_axis_var,
            command=lambda: (
                self._compare_apply_locked_x_axis(),
                self._compare_persist_state(),
            ),
        ).grid(row=0, column=7, sticky="w", padx=(0, 4), pady=6)
        self._compare_make_button(
            controls,
            text="Generate Comparison Report...",
            command=self._compare_generate_report_artifacts,
        ).grid(row=0, column=8, sticky="ew", padx=(0, 8), pady=6)
        self._compare_make_button(
            controls,
            text="Report Options...",
            command=self._compare_open_report_preferences_dialog,
        ).grid(row=0, column=9, sticky="ew", padx=(0, 8), pady=6)

        ttk.Label(controls, text="Compare Preset").grid(
            row=1, column=0, sticky="w", padx=(8, 4), pady=(2, 6)
        )
        self._compare_plot_preset_combo = ttk.Combobox(
            controls,
            textvariable=self.compare_plot_preset_var,
            values=self._compare_plot_preset_names,
            state="readonly",
        )
        self._compare_plot_preset_combo.grid(
            row=1, column=1, columnspan=4, sticky="ew", padx=(0, 8), pady=(2, 6)
        )
        try:
            self._compare_plot_preset_combo.bind(
                "<<ComboboxSelected>>",
                lambda _event: self._compare_apply_plot_preset_selection(
                    rerender_loaded=True, persist_state=True
                ),
                add="+",
            )
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        self._compare_make_button(
            controls,
            text="Save Preset",
            command=self._compare_save_plot_preset,
        ).grid(row=1, column=6, sticky="ew", padx=(0, 4), pady=(2, 6))
        self._compare_make_button(
            controls,
            text="Delete Preset",
            command=self._compare_delete_plot_preset,
        ).grid(row=1, column=7, sticky="ew", padx=(0, 8), pady=(2, 6))
        self._compare_make_button(
            controls,
            text="Layout Manager...",
            command=self._open_compare_layout_manager,
        ).grid(row=1, column=8, sticky="ew", padx=(0, 8), pady=(2, 6))
        self._compare_make_button(
            controls,
            text="Plot Elements...",
            command=self._open_compare_plot_elements_dialog,
        ).grid(row=1, column=9, sticky="ew", padx=(0, 8), pady=(2, 6))
        _ui_checkbutton(
            controls,
            text="Use profile layout anchors",
            variable=self.compare_use_profile_layout_var,
            command=self._compare_apply_layout_mode_change,
        ).grid(row=1, column=10, sticky="w", padx=(0, 8), pady=(2, 6))
        _ui_checkbutton(
            controls,
            text="Cycle Legend",
            variable=self.compare_show_cycle_legend_var,
            command=self._compare_apply_cycle_legend_toggle,
        ).grid(row=1, column=11, columnspan=2, sticky="w", padx=(0, 8), pady=(2, 6))
        self._compare_make_button(
            controls,
            text="Fix A Markers...",
            command=lambda: self._open_compare_marker_editor("A"),
        ).grid(row=1, column=13, sticky="ew", padx=(0, 4), pady=(2, 6))
        self._compare_make_button(
            controls,
            text="Fix B Markers...",
            command=lambda: self._open_compare_marker_editor("B"),
        ).grid(row=1, column=14, sticky="ew", padx=(0, 0), pady=(2, 6))

        self._compare_profile_assignment_summary_var = tk.StringVar(
            value="Selected A: --  |  Selected B: --"
        )
        summary_label = ttk.Label(
            controls,
            textvariable=self._compare_profile_assignment_summary_var,
            anchor="w",
            justify="left",
            wraplength=1320,
        )
        summary_label.grid(
            row=2, column=0, columnspan=15, sticky="ew", padx=8, pady=(0, 4)
        )
        self._compare_profile_assignment_summary_label = summary_label

        self._compare_status_chip_var = tk.StringVar(
            value=(
                "Backend: awaiting load  |  Marker source: profile detection  |  "
                "Report readiness: waiting for Profile A + B"
            )
        )
        ttk.Label(
            controls,
            textvariable=self._compare_status_chip_var,
            anchor="w",
            justify="left",
        ).grid(row=3, column=0, columnspan=15, sticky="ew", padx=8, pady=(0, 6))

        self._compare_paned = ttk.Panedwindow(frame, orient="vertical")
        self._compare_paned.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        try:
            self._compare_paned.bind(
                "<ButtonRelease-1>", self._on_compare_paned_release, add="+"
            )
            self._compare_paned.bind(
                "<Configure>",
                lambda _event: self._compare_update_split_persist_debounced(),
                add="+",
            )
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        plot_shell = ttk.Frame(self._compare_paned)
        plot_shell.grid_columnconfigure(0, weight=1)
        plot_shell.grid_columnconfigure(1, weight=1)
        plot_shell.grid_rowconfigure(0, weight=1)

        self._compare_panels: Dict[str, Dict[str, Any]] = {}
        for idx, side in enumerate(("A", "B")):
            panel = ttk.LabelFrame(plot_shell, text=f"Profile {side}")
            panel.grid(
                row=0,
                column=idx,
                sticky="nsew",
                padx=(0, 4) if idx == 0 else (4, 0),
            )
            panel.grid_rowconfigure(1, weight=1)
            panel.grid_columnconfigure(0, weight=1)
            status_var = tk.StringVar(value="No profile loaded.")
            ttk.Label(
                panel,
                textvariable=status_var,
                anchor="w",
                justify="left",
            ).grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 0))
            fig = Figure(figsize=(5.0, 3.2), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Load a profile to render.", ha="center", va="center")
            ax.set_axis_off()
            canvas = FigureCanvasTkAgg(fig, master=panel)
            widget = canvas.get_tk_widget()
            widget.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
            try:
                canvas.draw()
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            self._compare_panels[side] = {
                "frame": panel,
                "canvas": canvas,
                "widget": widget,
                "status_var": status_var,
                "figure": fig,
                "bundle": None,
                "cycle_rows": [],
                "total_drop": None,
                "cycle_fallback_used": False,
                "cycle_rows_synthesized": False,
                "cycle_compute_backend": "",
                "load_error_message": "",
                "render_success": False,
                "render_error_message": "",
            }
            try:
                widget.bind(
                    "<Configure>",
                    lambda _event, side_key=side: self._compare_schedule_resize(
                        side_key
                    ),
                    add="+",
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        bottom = ttk.Frame(self._compare_paned)
        bottom.grid_rowconfigure(0, weight=1)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)
        self._compare_paned.add(plot_shell, weight=3)
        self._compare_paned.add(bottom, weight=2)
        self._apply_initial_compare_split()

        table_box = ttk.LabelFrame(bottom, text="Per-Cycle Uptake Comparison")
        table_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        table_box.grid_rowconfigure(0, weight=1)
        table_box.grid_columnconfigure(0, weight=1)

        self._compare_cycle_columns: Tuple[str, ...] = (
            "cycle",
            "uptake_a_g",
            "uptake_b_g",
            "delta_g",
            "cum_a_g",
            "cum_b_g",
            "cum_delta_g",
        )
        self._compare_cycle_tree = ttk.Treeview(
            table_box,
            columns=self._compare_cycle_columns,
            show="headings",
            height=12,
        )
        self._compare_cycle_column_headings = {
            "cycle": "Cycle",
            "uptake_a_g": "Uptake A (g)",
            "uptake_b_g": "Uptake B (g)",
            "delta_g": "Delta (B-A) (g)",
            "cum_a_g": "Cumulative A (g)",
            "cum_b_g": "Cumulative B (g)",
            "cum_delta_g": "Cumulative Delta (g)",
        }
        for col in self._compare_cycle_columns:
            self._compare_cycle_tree.heading(
                col, text=self._compare_cycle_column_headings.get(col, col)
            )
            self._compare_cycle_tree.column(
                col,
                anchor="center",
                width=130 if col != "cycle" else 92,
                stretch=(col != "cycle"),
            )
        self._compare_cycle_tree.grid(row=0, column=0, sticky="nsew")
        cycle_scroll = _ui_scrollbar(
            table_box, orient="vertical", command=self._compare_cycle_tree.yview
        )
        cycle_scroll.grid(row=0, column=1, sticky="ns")
        cycle_x_scroll = _ui_scrollbar(
            table_box, orient="horizontal", command=self._compare_cycle_tree.xview
        )
        cycle_x_scroll.grid(row=1, column=0, sticky="ew")
        self._compare_cycle_tree.configure(yscrollcommand=cycle_scroll.set)
        self._compare_cycle_tree.configure(xscrollcommand=cycle_x_scroll.set)
        try:
            self._compare_cycle_tree.bind(
                "<ButtonPress-1>",
                self._compare_cycle_table_on_tree_button_press,
                add="+",
            )
            self._compare_cycle_tree.bind(
                "<Double-1>",
                self._compare_cycle_table_on_tree_double_click,
                add="+",
            )
            self._compare_cycle_tree.bind(
                "<ButtonRelease-1>",
                self._compare_cycle_table_on_tree_button_release,
                add="+",
            )
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        action_row = ttk.Frame(table_box)
        action_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(6, 4))
        action_row.grid_columnconfigure(2, weight=1)
        ttk.Label(action_row, text="View Mode").grid(
            row=0, column=0, sticky="w", padx=(0, 6)
        )
        self._compare_cycle_table_view_mode_combo = ttk.Combobox(
            action_row,
            textvariable=self._compare_cycle_table_view_mode_var,
            state="readonly",
            values=tuple(
                COMPARE_CYCLE_TABLE_VIEW_MODE_LABELS[token]
                for token in COMPARE_CYCLE_TABLE_VIEW_MODE_TOKENS
            ),
            width=16,
        )
        self._compare_cycle_table_view_mode_combo.grid(
            row=0, column=1, sticky="w", padx=(0, 8)
        )
        self._compare_make_button(
            action_row,
            text="Fit All Visible",
            command=self._compare_cycle_table_fit_all_visible_columns,
            compact=True,
        ).grid(row=0, column=3, sticky="e", padx=(0, 6))
        self._compare_make_button(
            action_row,
            text="Export CSV",
            command=self._compare_export_cycle_table_csv,
            compact=True,
        ).grid(row=0, column=4, sticky="e")

        side_scroll_shell = ttk.Frame(bottom)
        side_scroll_shell.grid(row=0, column=1, sticky="nsew")
        side_scroll_shell.grid_rowconfigure(0, weight=1)
        side_scroll_shell.grid_columnconfigure(0, weight=1)
        self._compare_side_canvas = tk.Canvas(side_scroll_shell, highlightthickness=0)
        self._compare_side_canvas.grid(row=0, column=0, sticky="nsew")
        side_scroll = _ui_scrollbar(
            side_scroll_shell,
            orient="vertical",
            command=self._compare_side_canvas.yview,
        )
        side_scroll.grid(row=0, column=1, sticky="ns")
        self._compare_side_canvas.configure(yscrollcommand=side_scroll.set)
        side_content = ttk.Frame(self._compare_side_canvas)
        side_window_id = self._compare_side_canvas.create_window(
            (0, 0),
            window=side_content,
            anchor="nw",
        )
        side_content.grid_columnconfigure(0, weight=1)
        self._compare_side_content = side_content
        self._compare_side_canvas_window_id = side_window_id

        def _refresh_compare_side_wraplengths() -> None:
            """Update Compare right-pane wraplengths from current viewport width.

            Purpose:
                Keep Yield and diagnostics text readable without horizontal clipping.
            Why:
                Fixed wrap lengths can truncate long output strings at smaller
                widths or under UI scaling.
            Args:
                None.
            Returns:
                None.
            Side Effects:
                Updates wraplength values for right-pane labels.
            Exceptions:
                Missing widgets are ignored.
            """
            canvas = getattr(self, "_compare_side_canvas", None)
            if canvas is None:
                return
            try:
                viewport_width = int(canvas.winfo_width() or 0)
            except Exception:
                viewport_width = 0
            try:
                content_width = int(side_content.winfo_width() or 0)
            except Exception:
                content_width = 0
            available_width = max(viewport_width, content_width, 320)
            wrap_px = max(220, available_width - 28)
            for label_name in (
                "_compare_yield_warning_label",
                "_compare_yield_summary_label",
                "_compare_diagnostics_label",
            ):
                label_widget = getattr(self, label_name, None)
                if label_widget is None:
                    continue
                try:
                    label_widget.configure(wraplength=wrap_px)
                except Exception:
                    continue

        def _sync_side_scrollregion(_event: Optional[tk.Event] = None) -> None:
            """Synchronize Compare right-pane scroll region after content changes."""
            canvas = getattr(self, "_compare_side_canvas", None)
            if canvas is None:
                return
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        def _sync_side_width(event: tk.Event) -> None:
            """Keep Compare right-pane content width matched to canvas viewport."""
            canvas = getattr(self, "_compare_side_canvas", None)
            window_id = getattr(self, "_compare_side_canvas_window_id", None)
            if canvas is None or window_id is None:
                return
            try:
                canvas.itemconfigure(window_id, width=max(120, int(event.width)))
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            _refresh_compare_side_wraplengths()

        def _on_side_mousewheel(event: Any) -> Optional[str]:
            """Scroll the Compare right-side panel on mousewheel events."""
            canvas = getattr(self, "_compare_side_canvas", None)
            if canvas is None:
                return None
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return None
            step = -1 if delta > 0 else 1
            if abs(delta) >= 120:
                step = int(-delta / 120)
            try:
                canvas.yview_scroll(step, "units")
            except Exception:
                return None
            return "break"

        def _bind_side_mousewheel(widget: Any) -> None:
            """Bind recursive mousewheel routing for Compare right-side panel."""
            try:
                widget.bind("<MouseWheel>", _on_side_mousewheel, add="+")
                widget.bind(
                    "<Button-4>",
                    lambda _event: self._compare_side_canvas.yview_scroll(-1, "units"),
                    add="+",
                )
                widget.bind(
                    "<Button-5>",
                    lambda _event: self._compare_side_canvas.yview_scroll(1, "units"),
                    add="+",
                )
            except Exception:
                pass
            for child in list(widget.winfo_children() or []):
                _bind_side_mousewheel(child)

        try:
            side_content.bind(
                "<Configure>",
                lambda _event: (
                    _sync_side_scrollregion(),
                    _refresh_compare_side_wraplengths(),
                ),
                add="+",
            )
            self._compare_side_canvas.bind("<Configure>", _sync_side_width, add="+")
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        self.after_idle(lambda: _bind_side_mousewheel(side_content))
        self.after_idle(_refresh_compare_side_wraplengths)

        yield_box = ttk.LabelFrame(side_content, text="Yield Comparison")
        yield_box.grid(row=0, column=0, sticky="nsew")
        yield_box.grid_columnconfigure(0, weight=1)

        def _add_stacked_yield_field(
            parent: ttk.Frame,
            row_start: int,
            *,
            label_text: str,
            widget: tk.Widget,
            inner_padx: Tuple[int, int] = (6, 6),
        ) -> int:
            """Add one stacked label-input row group in the Compare Yield panel.

            Purpose:
                Render label + control rows using vertical stacking.
            Why:
                Stacked rows reduce horizontal pressure and keep long labels/inputs
                visible in narrower Compare right-pane widths.
            Args:
                parent: Frame receiving the row group.
                row_start: Starting row index for the group.
                label_text: Human-readable label text.
                widget: Input widget bound to the corresponding variable.
                inner_padx: Left/right padding for this row group.
            Returns:
                Next available row index after placing label and input rows.
            Side Effects:
                Grids one label widget and one input widget into `parent`.
            Exceptions:
                None.
            """
            ttk.Label(parent, text=label_text).grid(
                row=row_start,
                column=0,
                sticky="w",
                padx=inner_padx,
                pady=(4, 1),
            )
            widget.grid(
                row=row_start + 1,
                column=0,
                sticky="ew",
                padx=inner_padx,
                pady=(0, 4),
            )
            return row_start + 2

        row_idx = 0
        yield_basis_combo = ttk.Combobox(
            yield_box,
            textvariable=self.compare_yield_mode_var,
            values=("auto", "override"),
            state="readonly",
            width=14,
        )
        row_idx = _add_stacked_yield_field(
            yield_box,
            row_idx,
            label_text="Yield Basis",
            widget=yield_basis_combo,
        )
        row_idx = _add_stacked_yield_field(
            yield_box,
            row_idx,
            label_text="Isolated Mass A (g)",
            widget=ttk.Entry(yield_box, textvariable=self.compare_isolated_mass_a_var),
        )
        row_idx = _add_stacked_yield_field(
            yield_box,
            row_idx,
            label_text="Isolated Mass B (g)",
            widget=ttk.Entry(yield_box, textvariable=self.compare_isolated_mass_b_var),
        )
        override_frame = ttk.LabelFrame(yield_box, text="Override Basis (optional)")
        override_frame.grid(row=row_idx, column=0, sticky="ew", padx=6, pady=(4, 6))
        override_frame.grid_columnconfigure(0, weight=1)
        override_row = 0
        override_row = _add_stacked_yield_field(
            override_frame,
            override_row,
            label_text="Starting mass (g)",
            widget=ttk.Entry(
                override_frame,
                textvariable=self.compare_override_starting_mass_var,
            ),
            inner_padx=(4, 4),
        )
        override_row = _add_stacked_yield_field(
            override_frame,
            override_row,
            label_text="Starting MW (g/mol)",
            widget=ttk.Entry(override_frame, textvariable=self.compare_override_mw_var),
            inner_padx=(4, 4),
        )
        override_row = _add_stacked_yield_field(
            override_frame,
            override_row,
            label_text="Stoich (mol gas/mol start)",
            widget=ttk.Entry(
                override_frame,
                textvariable=self.compare_override_stoich_var,
            ),
            inner_padx=(4, 4),
        )
        _add_stacked_yield_field(
            override_frame,
            override_row,
            label_text="Gas MW (g/mol)",
            widget=ttk.Entry(
                override_frame,
                textvariable=self.compare_override_gas_mw_var,
            ),
            inner_padx=(4, 4),
        )
        row_idx += 1

        kpi_frame = ttk.LabelFrame(yield_box, text="Yield KPI Snapshot")
        kpi_frame.grid(row=row_idx, column=0, sticky="ew", padx=6, pady=(2, 6))
        kpi_frame.grid_columnconfigure(0, weight=1)
        self._compare_yield_kpi_a_var = tk.StringVar(value="A: --")
        self._compare_yield_kpi_b_var = tk.StringVar(value="B: --")
        self._compare_yield_kpi_delta_var = tk.StringVar(value="Delta (B-A): --")
        self._compare_yield_warning_var = tk.StringVar(value="")
        ttk.Label(
            kpi_frame, textvariable=self._compare_yield_kpi_a_var, anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        ttk.Label(
            kpi_frame, textvariable=self._compare_yield_kpi_b_var, anchor="w"
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=2)
        ttk.Label(
            kpi_frame, textvariable=self._compare_yield_kpi_delta_var, anchor="w"
        ).grid(row=2, column=0, sticky="ew", padx=4, pady=2)
        self._compare_yield_warning_label = ttk.Label(
            kpi_frame,
            textvariable=self._compare_yield_warning_var,
            anchor="w",
            justify="left",
            wraplength=330,
            foreground="#9a6700",
        )
        self._compare_yield_warning_label.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=4,
            pady=(2, 4),
        )
        row_idx += 1

        self._compare_yield_summary_var = tk.StringVar(
            value="Load profiles to compute yield."
        )
        self._compare_yield_summary_label = ttk.Label(
            yield_box,
            textvariable=self._compare_yield_summary_var,
            justify="left",
            anchor="w",
            wraplength=340,
        )
        self._compare_yield_summary_label.grid(
            row=row_idx,
            column=0,
            sticky="ew",
            padx=6,
            pady=(2, 6),
        )

        diagnostics_box = ttk.LabelFrame(side_content, text="Load Diagnostics")
        diagnostics_box.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        diagnostics_box.grid_columnconfigure(0, weight=1)
        diagnostics_box.grid_rowconfigure(0, weight=1)
        self._compare_diagnostics_var = tk.StringVar(
            value="No compare load activity yet."
        )
        self._compare_diagnostics_label = ttk.Label(
            diagnostics_box,
            textvariable=self._compare_diagnostics_var,
            justify="left",
            anchor="nw",
            wraplength=360,
        )
        self._compare_diagnostics_label.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=6,
            pady=(6, 4),
        )
        diagnostics_actions = ttk.Frame(diagnostics_box)
        diagnostics_actions.grid(row=1, column=0, sticky="e", padx=6, pady=(0, 6))
        self._compare_make_button(
            diagnostics_actions,
            text="Debug Snapshot",
            command=self._compare_dump_debug_snapshot,
            compact=True,
        ).pack(side="left", padx=(0, 6))
        self._compare_make_button(
            diagnostics_actions,
            text="Debug Whitespace",
            command=self._compare_dump_debug_whitespace,
            compact=True,
        ).pack(side="left")
        self.after_idle(_refresh_compare_side_wraplengths)

        self._compare_cycle_table_rows: List[Dict[str, Any]] = []
        self._compare_resize_after_id: Optional[str] = None
        self._compare_resize_pending_sides: Set[str] = set()
        self._compare_split_settle_after_id: Optional[str] = None
        self._compare_load_diagnostics_state: Dict[str, Any] = {
            "A": {},
            "B": {},
            "summary": "No compare load activity yet.",
        }
        self._compare_load_splash_window: Optional[tk.Widget] = None
        self._compare_load_splash_label: Optional[ttk.Label] = None
        self._compare_load_splash_detail_label: Optional[ttk.Label] = None
        self._compare_load_splash_progress_var: Optional[tk.DoubleVar] = None
        self._compare_load_splash_progress_label: Optional[ttk.Label] = None
        self._compare_load_splash_stage_key: str = "ready"
        self._compare_load_splash_started_at: Optional[float] = None
        self._compare_load_splash_detail_base: str = ""
        self._compare_load_splash_heartbeat_after_id: Optional[str] = None
        self._compare_render_request_token = int(
            getattr(self, "_compare_render_request_token", 0)
        )
        self._compare_render_jobs_active = 0
        watched_vars = (
            self.compare_profile_a_var,
            self.compare_profile_b_var,
            self.compare_yield_mode_var,
            self.compare_isolated_mass_a_var,
            self.compare_isolated_mass_b_var,
            self.compare_override_starting_mass_var,
            self.compare_override_mw_var,
            self.compare_override_stoich_var,
            self.compare_override_gas_mw_var,
        )
        for var in watched_vars:
            try:
                var.trace_add(
                    "write",
                    lambda *_args: (
                        self._compare_refresh_yield_summary(),
                        self._compare_refresh_profile_assignment_summary(),
                        self._compare_refresh_profile_selection_tooltips(),
                        self._compare_refresh_assign_profiles_dialog_inventory(),
                        self._compare_persist_state(),
                    ),
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        try:
            self.compare_use_profile_layout_var.trace_add(
                "write",
                lambda *_args: self._compare_persist_state(),
            )
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        try:
            self.compare_plot_preset_var.trace_add(
                "write",
                lambda *_args: self._compare_persist_state(),
            )
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        try:
            self.compare_show_cycle_legend_var.trace_add(
                "write",
                lambda *_args: self._compare_persist_state(),
            )
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        try:
            self._compare_cycle_table_view_mode_var.trace_add(
                "write",
                lambda *_args: self._compare_cycle_table_apply_view_mode_from_var(
                    persist=True
                ),
            )
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        self._compare_apply_plot_preset_selection(
            rerender_loaded=False,
            persist_state=False,
        )
        self._compare_refresh_profile_choices()
        self._compare_refresh_cycle_table()
        self._compare_cycle_table_apply_view_mode_from_var(persist=False)
        self._compare_refresh_yield_summary()
        self._compare_update_status_chips()

    def _compare_series_gap_metrics(
        self, x_values: Any, y_values: Any
    ) -> Dict[str, Any]:
        """Compute finite/break segment diagnostics for one Compare pressure series.

        Purpose:
            Quantify trace continuity characteristics used by side-cycle editor
            debugging for whitespace and gap investigations.
        Why:
            Compare side plots must preserve non-finite separators as visual breaks;
            explicit metrics make hidden continuity issues detectable from logs.
        Args:
            x_values: Candidate x-axis sequence for one side profile.
            y_values: Candidate y-axis sequence for one side profile.
        Returns:
            Dict containing point totals, finite-pair counts, non-finite break
            rows, and contiguous finite segment count.
        Side Effects:
            None.
        Exceptions:
            Invalid array payloads return zeroed metrics.
        """
        metrics: Dict[str, Any] = {
            "total_points": 0,
            "finite_pairs": 0,
            "break_rows": 0,
            "finite_segments": 0,
        }
        try:
            x_arr = np.asarray(x_values, dtype=float).reshape(-1)
            y_arr = np.asarray(y_values, dtype=float).reshape(-1)
        except Exception:
            return metrics
        pair_len = int(min(x_arr.size, y_arr.size))
        if pair_len <= 0:
            return metrics
        x_arr = x_arr[:pair_len]
        y_arr = y_arr[:pair_len]
        finite_pairs = np.isfinite(x_arr) & np.isfinite(y_arr)
        finite_count = int(np.count_nonzero(finite_pairs))
        metrics["total_points"] = pair_len
        metrics["finite_pairs"] = finite_count
        metrics["break_rows"] = int(pair_len - finite_count)
        if finite_count <= 0:
            return metrics
        finite_int = finite_pairs.astype(np.int8, copy=False)
        # Count contiguous finite runs to verify that NaN separators are retained.
        transitions = np.diff(finite_int, prepend=np.array([0], dtype=np.int8))
        metrics["finite_segments"] = int(np.count_nonzero(transitions == 1))
        return metrics

    def _compare_figure_whitespace_metrics(
        self, fig: Optional[Figure]
    ) -> Dict[str, Any]:
        """Compute whitespace diagnostics for one rendered Compare figure.

        Purpose:
            Measure legend/x-label gap and axes compression metrics for one pane.
        Why:
            The persistent Compare whitespace issue requires direct, repeatable
            measurements rather than visual-only inspection.
        Args:
            fig: Candidate rendered figure from one Compare panel.
        Returns:
            Dict containing computed whitespace metrics and latest layout-health
            auto-fix metadata when available.
        Side Effects:
            May trigger one canvas draw to obtain a renderer.
        Exceptions:
            Renderer/artist failures return partial metrics.
        """
        metrics: Dict[str, Any] = {
            "plot_id": "",
            "legend_xlabel_gap_pts": None,
            "axes_union_height_frac": None,
            "layout_health_passes": None,
            "layout_health_issues": [],
            "layout_health_applied": None,
        }
        if fig is None:
            return metrics
        metrics["plot_id"] = str(getattr(fig, "_gl260_plot_id", "") or "")
        canvas = getattr(fig, "canvas", None)
        if canvas is None:
            try:
                canvas = FigureCanvasAgg(fig)
                fig.set_canvas(canvas)
            except Exception:
                canvas = None
        if canvas is None:
            return metrics
        try:
            canvas.draw()
            renderer = canvas.get_renderer()
        except Exception:
            return metrics
        legend = _layout_health_primary_legend(fig)
        xlabel = _layout_health_primary_xlabel(fig)
        legend_bbox = _layout_health_bbox_in_fig(fig, legend, renderer)
        xlabel_bbox = _layout_health_bbox_in_fig(fig, xlabel, renderer)
        try:
            fig_h_pts = max(float(fig.get_size_inches()[1]) * 72.0, 1.0)
        except Exception:
            fig_h_pts = 1.0
        if legend_bbox is not None and xlabel_bbox is not None:
            metrics["legend_xlabel_gap_pts"] = float(
                (xlabel_bbox.y0 - legend_bbox.y1) * fig_h_pts
            )
        axes_positions: List[Bbox] = []
        try:
            for axis in fig.get_axes():
                if axis is None or getattr(axis, "_gl260_legend_only", False):
                    continue
                if not bool(axis.get_visible()):
                    continue
                axes_positions.append(axis.get_position())
        except Exception:
            axes_positions = []
        if axes_positions:
            try:
                axes_union = Bbox.union(axes_positions)
                metrics["axes_union_height_frac"] = float(axes_union.height)
            except Exception:
                metrics["axes_union_height_frac"] = None
        layout_result = getattr(fig, "_gl260_last_layout_health_result", None)
        if isinstance(layout_result, Mapping):
            metrics["layout_health_passes"] = int(layout_result.get("passes", 0))
            metrics["layout_health_issues"] = list(layout_result.get("issues") or [])
            metrics["layout_health_applied"] = bool(layout_result.get("applied", False))
        return metrics

    def _compare_collect_debug_snapshot(self) -> Dict[str, Any]:
        """Build one structured Compare diagnostics snapshot for debugging.

        Purpose:
            Consolidate Compare runtime state into one serializable diagnostics payload.
        Why:
            Whitespace and cycle-editor issues cross multiple state holders
            (panes, diagnostics, markers, layout overrides), requiring one
            consistent snapshot for troubleshooting.
        Args:
            None.
        Returns:
            Dict containing compare panels, whitespace metrics, marker override
            state, cycle-editor cache, and current diagnostics summary payload.
        Side Effects:
            None.
        Exceptions:
            Invalid intermediate state is sanitized into safe defaults.
        """
        snapshot: Dict[str, Any] = {
            "summary": str(
                (getattr(self, "_compare_load_diagnostics_state", {}) or {}).get(
                    "summary", ""
                )
                or ""
            ).strip(),
            "preset_name": str(
                self.compare_plot_preset_var.get()
                if hasattr(self, "compare_plot_preset_var")
                else ""
            ).strip(),
            "layout_overrides": _normalize_compare_layout_overrides(
                getattr(self, "_compare_layout_overrides", {})
            ),
            "marker_overrides": {},
            "panels": {},
            "cycle_editor_states": {},
        }
        marker_overrides = _normalize_compare_marker_overrides(
            getattr(self, "_compare_marker_overrides", {})
        )
        for side_key in ("A", "B"):
            payload = _normalize_profile_cycle_markers(marker_overrides.get(side_key))
            snapshot["marker_overrides"][side_key] = {
                "present": bool(payload is not None),
                "add_peaks": len(list((payload or {}).get("add_peaks") or [])),
                "add_troughs": len(list((payload or {}).get("add_troughs") or [])),
                "rm_peaks": len(list((payload or {}).get("rm_peaks") or [])),
                "rm_troughs": len(list((payload or {}).get("rm_troughs") or [])),
                "manual_revision": int((payload or {}).get("manual_revision") or 0),
                "auto_detect_enabled": bool(
                    (payload or {}).get("auto_detect_enabled", True)
                ),
            }
        panels = getattr(self, "_compare_panels", {})
        panels = panels if isinstance(panels, Mapping) else {}
        diagnostics_state = dict(
            getattr(self, "_compare_load_diagnostics_state", {}) or {}
        )
        for side_key in ("A", "B"):
            panel = panels.get(side_key) if isinstance(panels, Mapping) else None
            panel = panel if isinstance(panel, Mapping) else {}
            bundle = panel.get("bundle")
            bundle = bundle if isinstance(bundle, Mapping) else {}
            panel_payload: Dict[str, Any] = {
                "profile_name": str(bundle.get("profile_name") or "").strip(),
                "dataset_path": str(bundle.get("dataset_path") or "").strip(),
                "render_success": bool(panel.get("render_success", False)),
                "render_error_message": str(
                    panel.get("render_error_message") or ""
                ).strip(),
                "cycle_count": len(list(panel.get("cycle_rows") or [])),
                "total_drop_g": self._compare_parse_float_entry(
                    panel.get("total_drop")
                ),
                "cycle_fallback_used": bool(panel.get("cycle_fallback_used", False)),
                "cycle_rows_synthesized": bool(
                    panel.get("cycle_rows_synthesized", False)
                ),
                "cycle_compute_backend": str(
                    panel.get("cycle_compute_backend") or ""
                ).strip(),
                "diag_status": str(
                    (diagnostics_state.get(side_key) or {}).get("status") or ""
                ).strip(),
                "diag_detail": str(
                    (diagnostics_state.get(side_key) or {}).get("detail") or ""
                ).strip(),
            }
            panel_payload["whitespace"] = self._compare_figure_whitespace_metrics(
                panel.get("figure") if isinstance(panel, Mapping) else None
            )
            data_ctx = bundle.get("data_ctx") if isinstance(bundle, Mapping) else {}
            data_ctx = data_ctx if isinstance(data_ctx, Mapping) else {}
            series_np = data_ctx.get("series_np")
            series_np = series_np if isinstance(series_np, Mapping) else {}
            series_map = data_ctx.get("series")
            series_map = series_map if isinstance(series_map, Mapping) else {}
            panel_payload["series_gaps"] = self._compare_series_gap_metrics(
                series_np.get("x", series_map.get("x")),
                series_np.get("y1", series_map.get("y1")),
            )
            snapshot["panels"][side_key] = panel_payload
        editor_states = getattr(self, "_compare_cycle_editor_states", {})
        editor_states = editor_states if isinstance(editor_states, Mapping) else {}
        for side_key in ("A", "B"):
            editor_state = editor_states.get(side_key)
            editor_state = editor_state if isinstance(editor_state, Mapping) else {}
            payload = _normalize_profile_cycle_markers(editor_state.get("payload"))
            snapshot["cycle_editor_states"][side_key] = {
                "window_open": bool(
                    (editor_state.get("window") is not None)
                    and bool(
                        getattr(
                            editor_state.get("window"), "winfo_exists", lambda: False
                        )()
                    )
                ),
                "profile_name": str(editor_state.get("profile_name") or "").strip(),
                "manual_revision": int((payload or {}).get("manual_revision") or 0),
                "add_peaks": len(list((payload or {}).get("add_peaks") or [])),
                "add_troughs": len(list((payload or {}).get("add_troughs") or [])),
                "rm_peaks": len(list((payload or {}).get("rm_peaks") or [])),
                "rm_troughs": len(list((payload or {}).get("rm_troughs") or [])),
                "latest_cycle_rows": len(
                    list(editor_state.get("latest_cycle_rows") or [])
                ),
                "series_gaps": dict(editor_state.get("series_gap_metrics") or {}),
            }
        return snapshot

    def _compare_emit_debug_report(
        self,
        *,
        header: str,
        category: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Emit one Compare diagnostics report to stderr and debug logger.

        Purpose:
            Centralize Compare debug report emission across UI actions and hooks.
        Why:
            Troubleshooting sessions require guaranteed terminal output even when
            debug categories are disabled, while still supporting category-gated logs.
        Args:
            header: Human-readable report title.
            category: Debug category key for `_dbg` routing.
            payload: Structured diagnostics payload to serialize.
        Returns:
            None.
        Side Effects:
            Prints one JSON payload to stderr and emits one `_dbg` entry.
        Exceptions:
            Serialization/output failures are handled best-effort.
        """
        report = {
            "header": str(header or "").strip(),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "payload": dict(payload or {}),
        }
        try:
            serialized = json.dumps(
                report, ensure_ascii=False, default=str, sort_keys=True
            )
        except Exception:
            serialized = str(report)
        try:
            print(serialized, file=sys.stderr)
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        self._dbg(category, "%s", serialized, once_key=None)

    def _compare_dump_debug_snapshot(self) -> None:
        """Emit one full Compare state snapshot for collaborative debugging.

        Purpose:
            Provide an on-demand dump action for current Compare state.
        Why:
            Debugging whitespace/marker issues needs one explicit state capture
            without waiting for automatic render events.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Writes a structured diagnostics report to stderr/debug log.
        Exceptions:
            Snapshot collection failures are reported with best-effort payloads.
        """
        try:
            payload = self._compare_collect_debug_snapshot()
        except Exception as exc:
            payload = {"error": f"snapshot_failed:{type(exc).__name__}"}
        self._compare_emit_debug_report(
            header="Compare Snapshot",
            category="compare.render",
            payload=payload,
        )

    def _compare_dump_debug_whitespace(self) -> None:
        """Emit focused Compare whitespace diagnostics for both render panes.

        Purpose:
            Produce a compact report of pane whitespace metrics and layout-health state.
        Why:
            The Compare whitespace defect requires frequent metric checks while
            adjusting layout settings and rerendering.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Writes a structured diagnostics report to stderr/debug log.
        Exceptions:
            Missing panes/figures are tolerated and reported as empty metrics.
        """
        payload: Dict[str, Any] = {"panes": {}}
        panels = getattr(self, "_compare_panels", {})
        panels = panels if isinstance(panels, Mapping) else {}
        for side_key in ("A", "B"):
            panel = panels.get(side_key) if isinstance(panels, Mapping) else None
            panel = panel if isinstance(panel, Mapping) else {}
            payload["panes"][side_key] = self._compare_figure_whitespace_metrics(
                panel.get("figure")
            )
        self._compare_emit_debug_report(
            header="Compare Whitespace",
            category="compare.whitespace",
            payload=payload,
        )

    def _compare_dump_cycle_editor_state(self) -> None:
        """Emit side Compare cycle-editor state for marker-assignment debugging.

        Purpose:
            Provide direct visibility into side editor marker payloads and revisions.
        Why:
            Marker correction issues are easiest to diagnose with explicit side cache
            dumps rather than inferring from popup text.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Writes a structured diagnostics report to stderr/debug log.
        Exceptions:
            Invalid/missing editor state is normalized to empty defaults.
        """
        payload = {
            "cycle_editor_states": self._compare_collect_debug_snapshot().get(
                "cycle_editor_states", {}
            )
        }
        self._compare_emit_debug_report(
            header="Compare Cycle Editor State",
            category="compare.cycle_editor",
            payload=payload,
        )

    def _compare_log_profile_load_event(
        self,
        *,
        side_key: str,
        profile_name: str,
        load_ctx: Mapping[str, Any],
    ) -> None:
        """Emit one focused profile-load diagnostics event for Compare.

        Purpose:
            Log side-local profile load outcomes at the point of bundle staging.
        Why:
            Load-stage diagnostics are needed to separate data-loading failures
            from later render/layout issues.
        Args:
            side_key: Compare side key (`"A"` or `"B"`).
            profile_name: Profile requested by the user for this side.
            load_ctx: Result payload returned by `_compare_load_profile_bundle_for_side`.
        Returns:
            None.
        Side Effects:
            Writes one structured diagnostics report to stderr/debug log.
        Exceptions:
            Invalid payload values are normalized to safe strings.
        """
        payload = {
            "side": str(side_key or "").strip().upper(),
            "requested_profile": str(profile_name or "").strip(),
            "resolved_profile": str(load_ctx.get("profile_name") or "").strip(),
            "status": str(load_ctx.get("status") or "").strip(),
            "status_label": str(load_ctx.get("status_label") or "").strip(),
            "detail": str(load_ctx.get("detail") or "").strip(),
            "dataset_path": str(load_ctx.get("dataset_path") or "").strip(),
            "bundle_ready": isinstance(load_ctx.get("bundle"), Mapping),
        }
        self._compare_emit_debug_report(
            header="Compare Profile Load",
            category="compare.render",
            payload=payload,
        )

    def _compare_log_render_context_event(
        self,
        *,
        side_key: str,
        bundle: Mapping[str, Any],
        cycle_rows: Sequence[Mapping[str, Any]],
        total_drop: Optional[float],
        metadata: Mapping[str, Any],
    ) -> None:
        """Emit one focused render-context diagnostics event for Compare.

        Purpose:
            Capture cycle extraction/render-context outputs before pane rendering.
        Why:
            Distinguishes cycle-context issues from draw/layout faults when Compare
            output diverges from main Cycle Analysis behavior.
        Args:
            side_key: Compare side key (`"A"` or `"B"`).
            bundle: Active compare profile bundle.
            cycle_rows: Extracted cycle-transfer rows for this side.
            total_drop: Optional total drop/uptake value.
            metadata: Extraction metadata produced by context builder.
        Returns:
            None.
        Side Effects:
            Writes one structured diagnostics report to stderr/debug log.
        Exceptions:
            Invalid values are sanitized to safe defaults.
        """
        payload = {
            "side": str(side_key or "").strip().upper(),
            "profile_name": str(bundle.get("profile_name") or "").strip(),
            "dataset_path": str(bundle.get("dataset_path") or "").strip(),
            "cycle_rows": int(len(list(cycle_rows or []))),
            "total_drop": self._compare_parse_float_entry(total_drop),
            "cycle_fallback_used": bool(metadata.get("cycle_fallback_used", False)),
            "cycle_rows_synthesized": bool(
                metadata.get("cycle_rows_synthesized", False)
            ),
            "cycle_compute_backend": str(
                metadata.get("cycle_compute_backend") or ""
            ).strip(),
            "segmentation_backend": str(
                metadata.get("segmentation_backend") or ""
            ).strip(),
            "metrics_backend": str(metadata.get("metrics_backend") or "").strip(),
        }
        self._compare_emit_debug_report(
            header="Compare Render Context",
            category="compare.render",
            payload=payload,
        )

    def _compare_log_render_completion_event(self, side_key: str) -> None:
        """Emit one focused Compare pane render completion diagnostics event.

        Purpose:
            Capture pane-level render success/error and whitespace metrics.
        Why:
            Allows direct correlation between render outcomes and measured
            whitespace state for each side.
        Args:
            side_key: Compare side key (`"A"` or `"B"`).
        Returns:
            None.
        Side Effects:
            Writes one structured diagnostics report to stderr/debug log.
        Exceptions:
            Missing panel state is normalized to defaults.
        """
        panels = getattr(self, "_compare_panels", {})
        panels = panels if isinstance(panels, Mapping) else {}
        panel = panels.get(side_key) if isinstance(panels, Mapping) else None
        panel = panel if isinstance(panel, Mapping) else {}
        bundle = panel.get("bundle")
        bundle = bundle if isinstance(bundle, Mapping) else {}
        payload = {
            "side": str(side_key or "").strip().upper(),
            "profile_name": str(bundle.get("profile_name") or "").strip(),
            "render_success": bool(panel.get("render_success", False)),
            "render_error_message": str(
                panel.get("render_error_message") or ""
            ).strip(),
            "cycle_count": len(list(panel.get("cycle_rows") or [])),
            "total_drop_g": self._compare_parse_float_entry(panel.get("total_drop")),
            "cycle_fallback_used": bool(panel.get("cycle_fallback_used", False)),
            "cycle_rows_synthesized": bool(panel.get("cycle_rows_synthesized", False)),
            "cycle_compute_backend": str(
                panel.get("cycle_compute_backend") or ""
            ).strip(),
            "whitespace": self._compare_figure_whitespace_metrics(panel.get("figure")),
        }
        self._compare_emit_debug_report(
            header="Compare Render Completion",
            category="compare.render",
            payload=payload,
        )

    def _compare_log_cycle_editor_event(
        self,
        *,
        side_key: str,
        event_name: str,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Emit one side-cycle-editor diagnostics event.

        Purpose:
            Record key marker-editor transitions (recompute/pull/apply) for Compare.
        Why:
            Marker correction debugging requires explicit event traces tied to side
            and payload state transitions.
        Args:
            side_key: Compare side key (`"A"` or `"B"`).
            event_name: Short event token describing the editor action.
            payload: Optional event-specific diagnostics payload.
        Returns:
            None.
        Side Effects:
            Writes one structured diagnostics report to stderr/debug log.
        Exceptions:
            Missing payload is normalized to an empty mapping.
        """
        report = {
            "side": str(side_key or "").strip().upper(),
            "event": str(event_name or "").strip(),
        }
        if isinstance(payload, Mapping):
            report.update(dict(payload))
        self._compare_emit_debug_report(
            header="Compare Cycle Editor Event",
            category="compare.cycle_editor",
            payload=report,
        )
