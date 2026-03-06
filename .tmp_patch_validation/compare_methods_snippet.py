from typing import Any, Dict, List, Mapping, Optional, Tuple


class _Snippet:
    def _open_compare_side_plot_editor(self, side_key: str) -> None:
        """Open the per-side Compare plot editor with toolbar and margin controls.

        Purpose:
            Provide one side-local workspace to tune subplot margins interactively.
        Why:
            Compare panes are compact and require manual margin controls that persist
            per selected A/B pair and side.
        Args:
            side_key: Compare side token (`"A"` or `"B"`).
        Returns:
            None.
        Side Effects:
            Creates one editor window, updates persisted side margins, and may
            rerender one compare pane when Apply+Rerender is used.
        Exceptions:
            Missing side figures show an informational prompt.
        """
        side_token = str(side_key or "").strip().upper()
        if side_token not in {"A", "B"}:
            return
        windows = getattr(self, "_compare_plot_editor_windows", None)
        if not isinstance(windows, dict):
            windows = {}
            self._compare_plot_editor_windows = windows
        existing = windows.get(side_token)
        if existing is not None and existing.winfo_exists():
            try:
                existing.deiconify()
                existing.lift()
                existing.focus_force()
            except Exception:
                pass
            return

        panels = getattr(self, "_compare_panels", {})
        panel = (panels or {}).get(side_token) if isinstance(panels, Mapping) else None
        panel = panel if isinstance(panel, Mapping) else {}
        source_fig = panel.get("figure")
        if source_fig is None:
            try:
                messagebox.showinfo(
                    "Compare Plot Editor",
                    f"Load and render Profile {side_token} before opening the plot editor.",
                )
            except Exception:
                pass
            return
        preview_fig = self._compare_clone_figure_for_plot_editor(source_fig)
        if preview_fig is None:
            preview_fig = Figure(figsize=(8.6, 4.8), dpi=100)
            preview_axis = preview_fig.add_subplot(111)
            preview_axis.text(
                0.5,
                0.5,
                "Preview clone unavailable.\nApply margins directly using controls.",
                ha="center",
                va="center",
            )
            preview_axis.set_axis_off()

        window = tk.Toplevel(self)
        window.title(f"Compare Plot Editor - Side {side_token}")
        window.transient(self)
        window.geometry("1280x760")
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)
        windows[side_token] = window

        root = ttk.Frame(window, padding=10)
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        ttk.Label(
            root,
            text=(
                "Use toolbar and controls to tune subplot margins for this side. "
                "Captured values persist per selected A/B pair."
            ),
            justify="left",
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        main_body = ttk.Frame(root)
        main_body.grid(row=1, column=0, sticky="nsew")
        main_body.grid_rowconfigure(0, weight=1)
        main_body.grid_columnconfigure(0, weight=4)
        main_body.grid_columnconfigure(1, weight=0)

        preview_shell = ttk.Frame(main_body)
        preview_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        preview_shell.grid_rowconfigure(1, weight=1)
        preview_shell.grid_columnconfigure(0, weight=1)
        preview_canvas = FigureCanvasTkAgg(preview_fig, master=preview_shell)
        toolbar = NavigationToolbar2Tk(
            preview_canvas, preview_shell, pack_toolbar=False
        )
        toolbar.update()
        toolbar.grid(row=0, column=0, sticky="ew")
        self._apply_toolbar_scaling(toolbar)
        preview_widget = preview_canvas.get_tk_widget()
        preview_widget.grid(row=1, column=0, sticky="nsew")
        preview_figure_ref: Dict[str, Figure] = {"figure": preview_fig}

        def _current_preview_figure() -> Figure:
            """Return the current preview figure used by editor callbacks.

            Purpose:
                Resolve the active preview figure after rerender-triggered refreshes.
            Why:
                Plot-editor apply+rerender replaces the preview figure object, so
                callbacks must dereference the latest figure each time.
            Args:
                None.
            Returns:
                Active preview figure instance.
            Side Effects:
                None.
            Exceptions:
                None.
            """
            return preview_figure_ref["figure"]

        controls = ttk.LabelFrame(main_body, text="Margins")
        controls.grid(row=0, column=1, sticky="ns")
        controls.grid_columnconfigure(1, weight=1)
        defaults = self._compare_default_plot_editor_margins()
        resolved = self._compare_resolve_side_plot_editor_margins(side_token)
        staged_vars: Dict[str, tk.DoubleVar] = {
            key: tk.DoubleVar(value=float(resolved.get(key, defaults.get(key, 0.0))))
            for key in COMPARE_PLOT_EDITOR_MARGIN_KEYS
        }

        def _collect_staged_margins() -> Dict[str, float]:
            """Collect one normalized margins payload from staged editor controls."""
            payload: Dict[str, float] = {}
            for margin_key in COMPARE_PLOT_EDITOR_MARGIN_KEYS:
                var_obj = staged_vars.get(margin_key)
                if var_obj is None:
                    continue
                try:
                    payload[margin_key] = float(var_obj.get())
                except Exception:
                    continue
            normalized = _normalize_compare_plot_editor_margins(
                payload,
                defaults=defaults,
            )
            return dict(normalized or defaults)

        def _apply_preview_margins(*, redraw: bool) -> None:
            """Apply staged margins to the preview figure and optionally redraw."""
            margins_payload = _collect_staged_margins()
            preview_local = _current_preview_figure()
            try:
                preview_local.subplots_adjust(**margins_payload)
            except Exception:
                pass
            layout_mgr = getattr(preview_local, "_gl260_layout_manager", None)
            if layout_mgr is not None:
                try:
                    layout_mgr._baseline_left = float(margins_payload.get("left"))
                    layout_mgr._baseline_right = float(margins_payload.get("right"))
                    layout_mgr._baseline_top = float(margins_payload.get("top"))
                    layout_mgr._baseline_bottom = float(margins_payload.get("bottom"))
                    layout_mgr.solve(max_passes=1, allow_draw=False)
                except Exception:
                    pass
            if not redraw:
                return
            try:
                preview_canvas.draw_idle()
            except Exception:
                try:
                    preview_canvas.draw()
                except Exception:
                    pass

        def _capture_current_margins() -> None:
            """Capture the preview figure's current subplotpars into staged controls."""
            preview_local = _current_preview_figure()
            subplotpars = getattr(preview_local, "subplotpars", None)
            if subplotpars is None:
                return
            for margin_key in COMPARE_PLOT_EDITOR_MARGIN_KEYS:
                var_obj = staged_vars.get(margin_key)
                if var_obj is None:
                    continue
                try:
                    var_obj.set(float(getattr(subplotpars, margin_key)))
                except Exception:
                    continue
            _apply_preview_margins(redraw=True)

        def _reset_defaults() -> None:
            """Reset staged controls to Compare default margins for this plot type."""
            for margin_key in COMPARE_PLOT_EDITOR_MARGIN_KEYS:
                var_obj = staged_vars.get(margin_key)
                if var_obj is None:
                    continue
                try:
                    var_obj.set(float(defaults.get(margin_key, 0.0)))
                except Exception:
                    continue
            _apply_preview_margins(redraw=True)

        def _apply_to_compare(*, rerender: bool) -> None:
            """Commit staged margins to Compare state and optionally rerender side."""
            self._compare_apply_side_plot_editor_margins(
                side_token,
                _collect_staged_margins(),
                rerender_side=rerender,
                persist_state=True,
            )
            if rerender:
                refreshed_panel = (getattr(self, "_compare_panels", {}) or {}).get(
                    side_token
                ) or {}
                refreshed_fig = refreshed_panel.get("figure")
                cloned = self._compare_clone_figure_for_plot_editor(refreshed_fig)
                if cloned is not None:
                    preview_figure_ref["figure"] = cloned
                    try:
                        cloned.set_canvas(preview_canvas)
                    except Exception:
                        pass
                    try:
                        preview_canvas.figure = cloned
                    except Exception:
                        pass
                    try:
                        toolbar.update()
                    except Exception:
                        pass
                    _capture_current_margins()
                    try:
                        preview_canvas.draw_idle()
                    except Exception:
                        pass

        row_idx = 0
        for margin_key, label_text in (
            ("left", "Left"),
            ("right", "Right"),
            ("top", "Top"),
            ("bottom", "Bottom"),
        ):
            ttk.Label(controls, text=label_text).grid(
                row=row_idx,
                column=0,
                sticky="w",
                padx=(8, 6),
                pady=(6 if row_idx == 0 else 2, 2),
            )
            spin = ttk.Spinbox(
                controls,
                from_=0.0,
                to=1.0,
                increment=0.005,
                textvariable=staged_vars[margin_key],
                width=10,
                command=lambda: _apply_preview_margins(redraw=True),
            )
            spin.grid(
                row=row_idx,
                column=1,
                sticky="ew",
                padx=(0, 8),
                pady=(6 if row_idx == 0 else 2, 2),
            )
            spin.bind("<FocusOut>", lambda _event: _apply_preview_margins(redraw=True))
            spin.bind("<Return>", lambda _event: _apply_preview_margins(redraw=True))
            row_idx += 1

        actions = ttk.Frame(controls)
        actions.grid(
            row=row_idx,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=(10, 8),
        )
        actions.grid_columnconfigure(0, weight=1)
        self._compare_make_button(
            actions,
            text="Capture Current Margins",
            command=_capture_current_margins,
            compact=True,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._compare_make_button(
            actions,
            text="Apply",
            command=lambda: _apply_to_compare(rerender=False),
            compact=True,
        ).grid(row=1, column=0, sticky="ew", pady=2)
        self._compare_make_button(
            actions,
            text="Apply + Rerender",
            command=lambda: _apply_to_compare(rerender=True),
            compact=True,
        ).grid(row=2, column=0, sticky="ew", pady=2)
        self._compare_make_button(
            actions,
            text="Reset",
            command=_reset_defaults,
            compact=True,
        ).grid(row=3, column=0, sticky="ew", pady=2)

        def _close_window() -> None:
            """Close this side editor window and release stored window references."""
            try:
                window.destroy()
            except Exception:
                pass
            windows.pop(side_token, None)

        window.protocol("WM_DELETE_WINDOW", _close_window)
        _capture_current_margins()

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
            try:
                fig._gl260_layout_health_context = "compare"  # type: ignore[attr-defined]
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
        prior_combined_legend_anchor = getattr(self, "_combined_legend_anchor", None)
        prior_combined_legend_loc = getattr(self, "_combined_legend_loc", None)
        prior_layout_profiles = settings.get("layout_profiles")
        sentinel = object()
        overridden_keys: Dict[str, Any] = {}
        overridden_tk_vars: Dict[str, Any] = {}
        args_for_render = list(bundle.get("args") or ())
        if len(args_for_render) < 14:
            args_for_render.extend([""] * (14 - len(args_for_render)))
        default_titles = self._compare_profile_title_defaults(side_key, bundle)
        override_title_text = str(side_plot_override.get("title_text") or "").strip()
        override_suptitle_text = str(
            side_plot_override.get("suptitle_text") or ""
        ).strip()
        args_for_render[12] = (
            override_title_text or str(default_titles.get("title_text") or "").strip()
        )
        args_for_render[13] = (
            override_suptitle_text
            or str(default_titles.get("suptitle_text") or "").strip()
        )

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
            for setting_key, attr_name in COMPARE_COMBINED_TK_OVERRIDE_BINDINGS:
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
            # Compare panes should not inherit the main-tab persisted legend anchor.
            self._combined_legend_anchor = None
            self._combined_legend_loc = None

            profile_layouts = bundle.get("layout_profiles") or {}
            profile_layout_source: Any = {}
            if use_profile_layout and isinstance(profile_layouts, Mapping):
                profile_layout_source = profile_layouts.get(
                    "fig_combined_triple_axis", {}
                )
            resolved_layout_profile = _normalize_layout_profile(
                profile_layout_source,
                "fig_combined_triple_axis",
            )
            display_section = _layout_profile_section(
                resolved_layout_profile, "display"
            )
            default_display_margins = _default_layout_margins(
                "fig_combined_triple_axis", "display"
            )
            side_margin_override = _normalize_compare_plot_editor_margins(
                self._compare_resolve_side_plot_editor_margins(side_key),
                defaults=default_display_margins,
            )
            display_section["margins"] = _normalize_layout_margins(
                side_margin_override or default_display_margins,
                default_display_margins,
            )
            for layout_key in COMPARE_LAYOUT_PROFILE_SECTION_KEYS:
                if layout_key not in compare_layout_overrides:
                    continue
                display_section[layout_key] = copy.deepcopy(
                    compare_layout_overrides.get(layout_key)
                )
            if not use_profile_layout:
                for mode_key in ("display", "export"):
                    section = _layout_profile_section(resolved_layout_profile, mode_key)
                    for key in (
                        "title_xy",
                        "suptitle_xy",
                        "legend_anchor",
                        "legend_anchor_y",
                        "legend_loc",
                        "cycle_legend_anchor",
                        "cycle_legend_loc",
                    ):
                        section[key] = None
            merged_layouts = _normalize_layout_profiles(prior_layout_profiles)
            merged_layouts["fig_combined_triple_axis"] = resolved_layout_profile
            settings["layout_profiles"] = merged_layouts
            for layout_key in COMPARE_LAYOUT_ANCHOR_KEYS:
                if layout_key not in overridden_keys:
                    overridden_keys[layout_key] = settings.get(layout_key, sentinel)
                settings.pop(layout_key, None)

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
            self._combined_legend_anchor = prior_combined_legend_anchor
            self._combined_legend_loc = prior_combined_legend_loc

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
        try:
            fig._gl260_layout_health_context = "compare"  # type: ignore[attr-defined]
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
