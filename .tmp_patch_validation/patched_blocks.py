# ruff: noqa: F821
from __future__ import annotations

import copy
import math
from dataclasses import asdict
from typing import Any, Dict, List, Mapping, Optional

import numpy as np


class UnifiedApp:
    def _install_rendered_plot_in_tab(
        self,
        frame,
        canvas,
        plot_key: str,
        fig: Figure,
        *,
        placement_state: dict[str, Any] | None = None,
    ) -> None:
        """Install a rendered figure into an existing plot tab.

        Purpose:
            Swap a newly rendered figure into its target tab/canvas.
        Why:
            Async rendering must reuse tabs to keep UI state and overlays intact.
        Inputs:
            frame: Plot tab frame hosting the canvas.
            canvas: FigureCanvasTkAgg instance to update.
            plot_key: Plot key identifier (e.g., "fig1", "fig_combined").
            fig: Rendered Matplotlib Figure to install.
            placement_state: Optional plot element placement state to restore.
        Outputs:
            None.
        Side Effects:
            Updates figure bindings, refreshes canvas display, retargets plot
            annotations, restores placement state, updates dirty flags, and
            clears loading overlays when auto-refresh is not pending/scheduled.
        Exceptions:
            Errors are caught to avoid interrupting UI workflows.
        """
        if frame is None or canvas is None or fig is None:
            return
        plot_id = self._plot_key_to_plot_id(plot_key)
        if not plot_id:
            plot_id = getattr(frame, "_plot_id", None)
        is_core_key = plot_key in {"fig1", "fig2"}
        if plot_id:
            try:
                self._teardown_layout_editor(plot_id, apply_changes=False)
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        if is_core_key:
            was_real_core = bool(getattr(frame, "_core_real_figure_installed", False))
            is_real_core = self._is_real_core_figure(fig)
            overlay_exists = bool(
                getattr(frame, "_plot_loading_overlay", None) is not None
            )
            try:
                frame._core_real_figure_installed = is_real_core
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            if is_real_core and not was_real_core and overlay_exists:
                try:
                    frame._core_overlay_refresh_invoked_count = 0
                    frame._core_overlay_refresh_completed_count = 0
                    frame._core_overlay_layout_sig_baseline = None
                    frame._core_overlay_need_second_refresh = True
                    frame._core_overlay_target_refreshes = 2
                    frame._core_overlay_ready_seen = False
                    frame._core_overlay_second_refresh_scheduled = False
                    frame._core_overlay_hold = True
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
                self._log_plot_tab_debug(
                    "Core real figure installed for %s; reset overlay refresh orchestration."
                    % plot_key
                )
        if plot_key == "fig_combined":
            was_real_combined = bool(
                getattr(frame, "_combined_real_figure_installed", False)
            )
            is_real_combined = self._is_real_combined_figure(fig)
            try:
                fig.set_canvas(canvas)
            except Exception:
                # Best-effort guard; ignore failures.
                pass
            try:
                canvas.figure = fig
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            try:
                frame._combined_real_figure_installed = is_real_combined
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            if is_real_combined and not was_real_combined:
                # Reset one-shot post-first-draw refresh flags when transitioning
                # from placeholder to the first real combined figure.
                prior_finalize_after_id = getattr(
                    frame, "_combined_overlay_finalize_after_id", None
                )
                if prior_finalize_after_id is not None:
                    try:
                        self.after_cancel(prior_finalize_after_id)
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                try:
                    default_target_refreshes = (
                        self._combined_overlay_default_target_refreshes()
                    )
                    frame._post_first_draw_refresh_done = False
                    frame._post_first_draw_refresh_invoked = False
                    frame._post_first_draw_refresh_hold_overlay = (
                        self._combined_requires_post_first_draw_refresh()
                    )
                    frame._post_first_draw_refresh_retry_count = 0
                    frame._post_first_draw_refresh_waiting_for_command = False
                    frame._post_first_draw_refresh_command_bind_id = None
                    frame._post_first_draw_refresh_command_timeout_after_id = None
                    frame._combined_refresh_geometry_wait = None
                    frame._combined_finalize_geometry_wait = None
                    frame._combined_overlay_refresh_invoked_count = 0
                    frame._combined_overlay_refresh_completed_count = 0
                    frame._combined_overlay_layout_sig_baseline = None
                    frame._combined_overlay_decision_sig_baseline = None
                    frame._combined_overlay_decision_sig_last = None
                    frame._combined_overlay_data_sig_current = None
                    frame._combined_overlay_need_second_refresh = (
                        default_target_refreshes > 1
                    )
                    frame._combined_overlay_target_refreshes = default_target_refreshes
                    frame._combined_overlay_ready_seen = False
                    frame._combined_overlay_second_refresh_scheduled = False
                    frame._combined_placeholder_draw_logged = False
                    frame._combined_overlay_last_geometry_sig = None
                    frame._combined_overlay_stable_draw_count = 0
                    frame._combined_overlay_finalize_started_at = None
                    frame._combined_overlay_finalize_after_id = None
                    frame._combined_overlay_completion_draw_pending = False
                    frame._combined_overlay_completion_fig_id = None
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
                self._log_plot_tab_debug(
                    "Combined real figure installed; reset post-draw refresh orchestration."
                )
            try:
                self._finalize_combined_plot_display(
                    frame, canvas, placement_state=placement_state
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        else:
            try:
                self._install_refreshed_figure_and_finalize(
                    frame,
                    canvas,
                    fig,
                    plot_id=plot_id,
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            if plot_id and placement_state:
                try:
                    self._restore_plot_element_placement_state(plot_id, placement_state)
                except Exception:
                    # Best-effort guard; ignore failures.
                    pass
            if is_core_key and bool(getattr(frame, "_core_overlay_hold", False)):
                renderer_ok = False
                try:
                    renderer_ok = canvas.get_renderer() is not None
                except Exception:
                    renderer_ok = False
                if renderer_ok and not bool(
                    getattr(frame, "_core_overlay_ready_seen", False)
                ):
                    try:
                        frame._core_overlay_ready_seen = True
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                    self._log_plot_tab_debug(
                        "Core overlay ready signal observed for %s." % plot_key
                    )
                invoked_count = getattr(frame, "_core_overlay_refresh_invoked_count", 0)
                completed_before = getattr(
                    frame, "_core_overlay_refresh_completed_count", 0
                )
                try:
                    invoked_count = int(invoked_count)
                except Exception:
                    invoked_count = 0
                try:
                    completed_before = int(completed_before)
                except Exception:
                    completed_before = 0
                completed_count = completed_before
                if invoked_count > completed_before:
                    completed_count = self._mark_core_overlay_refresh_completed(
                        frame,
                        fig=fig,
                    )
                    target_refreshes = getattr(
                        frame, "_core_overlay_target_refreshes", 2
                    )
                    self._log_plot_tab_debug(
                        "Core auto-refresh completion recorded for %s: invoked=%s completed=%s target=%s."
                        % (
                            plot_key,
                            invoked_count,
                            completed_count,
                            target_refreshes,
                        )
                    )
                else:
                    self._log_plot_tab_debug(
                        "Core render install skipped completion count for %s: invoked=%s completed=%s."
                        % (
                            plot_key,
                            invoked_count,
                            completed_before,
                        )
                    )
                target_refreshes = getattr(frame, "_core_overlay_target_refreshes", 2)
                try:
                    target_refreshes = int(target_refreshes)
                except Exception:
                    target_refreshes = 2
                if target_refreshes <= 0:
                    target_refreshes = 1
                if invoked_count <= 0 and completed_count <= 0:
                    self._schedule_core_refresh_pass(
                        frame,
                        canvas,
                        pass_index=1,
                    )
                elif (
                    completed_count >= 1
                    and completed_count < target_refreshes
                    and not bool(
                        getattr(frame, "_core_overlay_second_refresh_scheduled", False)
                    )
                ):
                    self._schedule_core_refresh_pass(
                        frame,
                        canvas,
                        pass_index=2,
                    )
                self._finalize_core_overlay(frame)
        if plot_id:
            try:
                self._set_plot_dirty_flags(
                    plot_id,
                    dirty_data=False,
                    dirty_layout=False,
                    dirty_elements=False,
                    dirty_trace=False,
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            try:
                self._record_plot_refresh_signature_bundle(
                    frame,
                    plot_id=plot_id,
                    plot_key=plot_key,
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        auto_state = getattr(frame, "_plot_auto_refresh_state", None)
        auto_enabled = getattr(frame, "_plot_auto_refresh_enabled", True)
        combined_overlay_hold = bool(
            plot_key == "fig_combined"
            and getattr(frame, "_post_first_draw_refresh_hold_overlay", False)
        )
        if is_core_key and bool(getattr(frame, "_core_overlay_hold", False)):
            # Completion-based core orchestration keeps the overlay until done.
            pass
        elif auto_state == "refreshing" and not combined_overlay_hold:
            self._complete_plot_auto_refresh(frame)
        elif combined_overlay_hold and auto_state == "refreshing":
            # Combined overlay release is draw-event gated; keep generic
            # completion from clearing the splash before adaptive passes finish.
            pass
        elif auto_enabled and auto_state in {"pending", "scheduled"}:
            # Keep the overlay active until the forced refresh pipeline completes.
            pass
        else:
            self._clear_plot_loading_overlay(frame)

    def _force_plot_refresh(
        self,
        frame,
        canvas,
        *,
        capture_combined_legend: bool = True,
        refresh_reason: Optional[str] = None,
        force_full_rebuild: bool = False,
    ):
        """Force a plot refresh and rebuild as needed.

        Purpose:
            Rebuild the requested plot with current settings and re-install it
            on the existing Tk canvas without changing overall layout rules.
        Why:
            Refresh needs to reuse cached data where possible while preserving
            user-driven legend placement for combined plots.

        Args:
            frame: Tkinter frame hosting the plot tab.
            canvas: FigureCanvasTkAgg displaying the figure.
            capture_combined_legend: When True, capture combined legend anchors
                before refresh if persistence is enabled and not locked.
            refresh_reason: Optional splash message shown while the refresh
                pipeline runs.
            force_full_rebuild: When True, bypass combined display reuse and
                force a fresh figure rebuild.

        Returns:
            None.

        Side Effects:
            Auto-applies staged Plot Settings dialog values before refresh so
            manual Refresh always uses the latest dialog inputs.
            Captures combined legend anchors before rebuild when enabled, applies
            or reattaches the loading overlay for refresh visibility, applies
            adaptive decision routing after refresh kickoff. No-change refreshes
            run a fast finalize-only reveal; safe non-combined
            layout/elements-only refreshes apply display layers in place; all
            other paths defer to the existing async rebuild pipeline. Full-path
            refreshes still defer combined work until geometry is ready, start
            background compute, and schedule UI-thread rendering/overlay
            updates. Refresh kickoff updates the stage/message without resetting
            active overlay progress so nested passes remain monotonic. When
            provided, `refresh_reason` is used as the initial overlay message.
            When `force_full_rebuild` is True, combined plot display reuse is
            bypassed for the refresh.

        Exceptions:
            Internal errors are caught and ignored to keep UI responsive.
        """
        plot_key = getattr(frame, "_plot_key", None)
        plot_id = self._plot_key_to_plot_id(plot_key)
        if not plot_id:
            plot_id = getattr(frame, "_plot_id", None)
        try:
            # Refresh should honor any in-flight Plot Settings edits before
            # building a new render snapshot to avoid stale/default margins.
            self._flush_open_plot_settings_dialog(refresh_after_apply=False)
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        auto_state = getattr(frame, "_plot_auto_refresh_state", None)
        if auto_state == "scheduled":
            # Manual refresh should satisfy the pending auto-refresh and avoid
            # duplicates.
            after_id = getattr(frame, "_plot_auto_refresh_after_id", None)
            if after_id is not None:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    # Best-effort guard; ignore failures.
                    pass
            frame._plot_auto_refresh_after_id = None
            frame._plot_auto_refresh_state = "refreshing"
            frame._plot_auto_refresh_in_progress = True
        overlay_message = (
            str(refresh_reason).strip()
            if isinstance(refresh_reason, str) and str(refresh_reason).strip()
            else (
                "Refreshing combined plot..."
                if plot_key == "fig_combined"
                else "Refreshing plot..."
            )
        )
        refresh_widget = None
        try:
            refresh_widget = canvas.get_tk_widget()
        except Exception:
            refresh_widget = None
        if refresh_widget is not None:
            try:
                if not refresh_widget.winfo_exists():
                    refresh_widget = None
            except Exception:
                refresh_widget = None
        if refresh_widget is not None:
            # Reattach the overlay before refresh so stale content never flashes.
            self._install_plot_loading_overlay(
                frame,
                refresh_widget,
                message=overlay_message,
            )
        # Keep refresh kickoff monotonic when the overlay is already in a later stage.
        self._update_plot_loading_overlay_progress(
            frame,
            progress=12.0,
            message=overlay_message,
            stage_key="refreshing",
        )
        try:
            adaptive_decision = self._resolve_plot_refresh_adaptive_decision(
                frame,
                plot_id=plot_id,
                plot_key=plot_key,
                force_full_rebuild=force_full_rebuild,
            )
        except Exception:
            adaptive_decision = {"path": "full_async_refresh"}
        try:
            if self._execute_adaptive_refresh_path(
                frame,
                canvas,
                plot_id=plot_id,
                plot_key=plot_key,
                decision=adaptive_decision,
            ):
                return
        except Exception:
            # Best-effort guard; fail closed to full async refresh.
            pass
        if force_full_rebuild and plot_key == "fig_combined":
            # Force rebuild path clears reusable combined state before async render.
            self._combined_plot_state = None
            self._combined_layout_state = None
            self._combined_layout_dirty = True
        combined_widget = None
        combined_size = None
        if plot_key == "fig_combined":
            try:
                frame._combined_render_ready = False
            except Exception:
                # Best-effort guard; ignore failures.
                pass
            try:
                self.nb.select(frame)
            except Exception:
                # Best-effort guard; ignore failures.
                pass
            # Ensure geometry is settled before rebuilding the combined figure.
            try:
                frame.update_idletasks()
                self.nb.update_idletasks()
            except Exception:
                # Best-effort guard; ignore failures.
                pass
            try:
                combined_widget = canvas.get_tk_widget()
            except Exception:
                combined_widget = None
            if combined_widget is not None:
                try:
                    combined_widget.update_idletasks()
                except Exception:
                    # Best-effort guard; ignore failures.
                    pass
                try:
                    width_px = int(combined_widget.winfo_width())
                    height_px = int(combined_widget.winfo_height())
                except Exception:
                    width_px = 0
                    height_px = 0
                if width_px <= 2 or height_px <= 2:
                    wait_state = getattr(frame, "_combined_refresh_geometry_wait", None)
                    if isinstance(wait_state, dict) and bool(wait_state.get("active")):
                        return

                    next_wait_state: Dict[str, Any] = {
                        "active": True,
                        "frame_bind_id": None,
                        "widget_bind_id": None,
                        "timeout_after_id": None,
                    }
                    try:
                        frame._combined_refresh_geometry_wait = next_wait_state
                    except Exception:
                        # Best-effort guard; ignore failures.
                        pass

                    def _cleanup_waiters() -> None:
                        """Clean up temporary geometry wait listeners for refresh.

                        Purpose:
                            Remove transient callbacks used for deferred refresh.
                        Why:
                            Prevents duplicated refresh resumes and stale event binds.
                        Inputs:
                            None.
                        Outputs:
                            None.
                        Side Effects:
                            Unbinds configure handlers, cancels timeout callback,
                            and clears frame wait-state markers.
                        Exceptions:
                            Cleanup failures are ignored to keep refresh resilient.
                        """
                        frame_bind_id = next_wait_state.get("frame_bind_id")
                        widget_bind_id = next_wait_state.get("widget_bind_id")
                        timeout_after_id = next_wait_state.get("timeout_after_id")
                        if frame_bind_id:
                            try:
                                frame.unbind("<Configure>", frame_bind_id)
                            except Exception:
                                # Best-effort guard; ignore failures.
                                pass
                        if widget_bind_id:
                            try:
                                combined_widget.unbind("<Configure>", widget_bind_id)
                            except Exception:
                                # Best-effort guard; ignore failures.
                                pass
                        if timeout_after_id is not None:
                            try:
                                self.after_cancel(timeout_after_id)
                            except Exception:
                                # Best-effort guard; ignore failures.
                                pass
                        next_wait_state["active"] = False
                        try:
                            frame._combined_refresh_geometry_wait = None
                        except Exception:
                            # Best-effort guard; ignore failures.
                            pass

                    def _resume_refresh(reason: str) -> None:
                        """Resume combined refresh after readiness or timeout.

                        Purpose:
                            Continue refresh once geometry wait conditions resolve.
                        Why:
                            Refresh should run immediately when geometry is ready
                            while still progressing after bounded timeout.
                        Inputs:
                            reason: Resume trigger source (`ready` or `timeout`).
                        Outputs:
                            None.
                        Side Effects:
                            Clears wait state and re-enters `_force_plot_refresh`.
                        Exceptions:
                            Errors fall back to a direct refresh invocation.
                        """
                        if not bool(next_wait_state.get("active")):
                            return
                        _cleanup_waiters()
                        if reason == "timeout":
                            self._log_plot_tab_debug(
                                "Combined refresh geometry wait timed out; continuing with fallback figure size."
                            )
                        try:
                            self.after_idle(
                                lambda: self._force_plot_refresh(
                                    frame,
                                    canvas,
                                    capture_combined_legend=capture_combined_legend,
                                    refresh_reason=refresh_reason,
                                    force_full_rebuild=force_full_rebuild,
                                )
                            )
                        except Exception:
                            self._force_plot_refresh(
                                frame,
                                canvas,
                                capture_combined_legend=capture_combined_legend,
                                refresh_reason=refresh_reason,
                                force_full_rebuild=force_full_rebuild,
                            )

                    def _on_geometry_signal(_event: Any = None) -> None:
                        """Handle configure/idle signals while refresh waits for geometry.

                        Purpose:
                            Re-probe widget size after geometry-related events.
                        Why:
                            Combined refresh should be readiness-driven, not fixed-delay.
                        Inputs:
                            _event: Optional Tk event payload.
                        Outputs:
                            None.
                        Side Effects:
                            Triggers deferred refresh resume when geometry is usable.
                        Exceptions:
                            Probe errors are ignored and readiness remains pending.
                        """
                        try:
                            combined_widget.update_idletasks()
                        except Exception:
                            # Best-effort guard; ignore failures.
                            pass
                        try:
                            ready_width = int(combined_widget.winfo_width())
                            ready_height = int(combined_widget.winfo_height())
                        except Exception:
                            ready_width = 0
                            ready_height = 0
                        if ready_width > 2 and ready_height > 2:
                            _resume_refresh("ready")

                    try:
                        next_wait_state["frame_bind_id"] = frame.bind(
                            "<Configure>", _on_geometry_signal, add="+"
                        )
                    except Exception:
                        next_wait_state["frame_bind_id"] = None
                    try:
                        next_wait_state["widget_bind_id"] = combined_widget.bind(
                            "<Configure>", _on_geometry_signal, add="+"
                        )
                    except Exception:
                        next_wait_state["widget_bind_id"] = None
                    try:
                        self.after_idle(_on_geometry_signal)
                    except Exception:
                        _on_geometry_signal()
                    try:
                        next_wait_state["timeout_after_id"] = self.after(
                            350, lambda: _resume_refresh("timeout")
                        )
                    except Exception:
                        _resume_refresh("timeout")
                    return
                combined_size = (max(width_px, 1), max(height_px, 1))
        if (
            plot_key == "fig_combined"
            and capture_combined_legend
            and self._combined_cycle_legend_capture_enabled()
        ):
            # Capture current legend anchors before rebuilding the combined figure.
            try:
                self._capture_combined_legend_anchor_from_fig(
                    getattr(canvas, "figure", None),
                    source="refresh",
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        try:
            self._refresh_canvas_display(frame, canvas, trigger_resize=True)
        except Exception:
            # Best-effort guard; ignore failures.
            pass
        placement_state = self._capture_plot_element_placement_state(plot_id)
        fig_size = None
        if plot_key in {"fig1", "fig2"}:
            fig_size = self._resolve_initial_canvas_figsize_inches(
                frame,
                canvas,
                timeout_ms=250,
                poll_ms=25,
                tag=f"{plot_key} refresh",
            )
        if plot_key == "fig_combined":
            try:
                if combined_size is None:
                    widget = canvas.get_tk_widget()
                    widget.update_idletasks()
                    width_px = max(int(widget.winfo_width()), 1)
                    height_px = max(int(widget.winfo_height()), 1)
                    combined_size = (width_px, height_px)
                dpi = float(getattr(canvas.figure, "dpi", 100.0))
                if not math.isfinite(dpi) or dpi <= 0:
                    dpi = 100.0
                fig_size = (
                    max((combined_size[0] if combined_size else 1) / dpi, 1.0),
                    max((combined_size[1] if combined_size else 1) / dpi, 1.0),
                )
            except Exception:
                fig_size = self._compute_target_figsize_inches()

        try:
            if plot_key in {"fig1", "fig2", "fig_peaks"}:
                snapshot = self._capture_plot_render_snapshot(
                    fig_size=fig_size if plot_key in {"fig1", "fig2"} else None,
                    plot_id=plot_id or "",
                    target="display",
                    requested_plot_keys=(plot_key,),
                    cycle_side_effects_mode=self._resolved_core_cycle_side_effects_mode(),
                )
                self._start_core_render_async(
                    snapshot,
                    [plot_key],
                    warn_on_failure=False,
                    placement_states={plot_key: placement_state},
                    force_full_rebuild=force_full_rebuild,
                )
                return
            if plot_key == "fig_combined":
                snapshot = self._capture_plot_render_snapshot(
                    fig_size=fig_size,
                    plot_id=plot_id or "fig_combined_triple_axis",
                    target="display",
                )
                self._start_combined_render_async(
                    snapshot,
                    warn_on_failure=False,
                    frame=frame,
                    canvas=canvas,
                    placement_state=placement_state,
                    force_full_rebuild=force_full_rebuild,
                )
                return
        except Exception:
            # Best-effort fallback: keep the existing figure visible.
            fig = getattr(canvas, "figure", None)
            if fig is None:
                return
            try:
                if plot_key == "fig_combined":
                    self._finalize_combined_plot_display(
                        frame,
                        canvas,
                        placement_state=placement_state,
                    )
                else:
                    self._finalize_plot_refresh(canvas, fig)
            except Exception:
                # Best-effort guard; ignore failures.
                pass
            if plot_key != "fig_combined":
                try:
                    if plot_key in {"fig1", "fig2"} and bool(
                        getattr(frame, "_core_overlay_hold", False)
                    ):
                        self._finalize_core_overlay(frame, force_clear=True)
                    elif (
                        getattr(frame, "_plot_auto_refresh_state", None) == "refreshing"
                    ):
                        self._complete_plot_auto_refresh(frame)
                except Exception:
                    # Best-effort guard; ignore failures.
                    pass
            return

    def _ensure_plot_dirty_flags(
        self, plot_id: Optional[str]
    ) -> Optional[Dict[str, bool]]:
        """Return mutable dirty flags for one plot id, creating defaults when needed.

        Purpose:
            Centralize per-plot dirty-flag initialization and lookup.
        Why:
            Adaptive refresh decisions require a consistent set of dirty flags
            (`data`, `layout`, `elements`, `trace`) for every managed plot id.
        Inputs:
            plot_id: Target plot identifier.
        Outputs:
            Dict of dirty flags for `plot_id`, or None when `plot_id` is empty.
        Side Effects:
            Creates and stores a new dirty-flag dict when one does not exist.
        Exceptions:
            None.
        """
        if not plot_id:
            return None
        flags = self._plot_dirty_flags.get(plot_id)
        if not isinstance(flags, dict):
            flags = {
                "dirty_data": True,
                "dirty_layout": True,
                "dirty_elements": True,
                "dirty_trace": True,
            }
            self._plot_dirty_flags[plot_id] = flags
        else:
            flags.setdefault("dirty_data", True)
            flags.setdefault("dirty_layout", True)
            flags.setdefault("dirty_elements", True)
            flags.setdefault("dirty_trace", True)
        return flags

    def _set_plot_dirty_flags(
        self,
        plot_id: Optional[str],
        *,
        dirty_data: Optional[bool] = None,
        dirty_layout: Optional[bool] = None,
        dirty_elements: Optional[bool] = None,
        dirty_trace: Optional[bool] = None,
    ) -> None:
        """Set one or more dirty flags for a plot id.

        Purpose:
            Persist targeted dirty-flag updates for adaptive refresh routing.
        Why:
            Different UI actions affect different render layers, so refresh must
            distinguish data, layout, elements, and trace-style changes.
        Inputs:
            plot_id: Target plot identifier.
            dirty_data: Optional new data-dirty flag.
            dirty_layout: Optional new layout-dirty flag.
            dirty_elements: Optional new plot-elements-dirty flag.
            dirty_trace: Optional new trace-style-dirty flag.
        Outputs:
            None.
        Side Effects:
            Mutates the dirty-flag entry for `plot_id` when available.
        Exceptions:
            None.
        """
        flags = self._ensure_plot_dirty_flags(plot_id)
        if flags is None:
            return
        if dirty_data is not None:
            flags["dirty_data"] = bool(dirty_data)
        if dirty_layout is not None:
            flags["dirty_layout"] = bool(dirty_layout)
        if dirty_elements is not None:
            flags["dirty_elements"] = bool(dirty_elements)
        if dirty_trace is not None:
            flags["dirty_trace"] = bool(dirty_trace)

    def _mark_plot_trace_dirty(self, plot_id: Optional[str] = None) -> None:
        """Mark trace-style state dirty for one plot or all tracked plots.

        Purpose:
            Track Data Trace Settings and trace-style changes separately from
            data/layout/element mutations.
        Why:
            Adaptive refresh should escalate trace-style changes to full refresh
            paths, especially for combined-layer reuse safety.
        Inputs:
            plot_id: Optional plot identifier. When omitted, all known plot ids
                are marked trace-dirty.
        Outputs:
            None.
        Side Effects:
            Updates per-plot dirty flags by setting `dirty_trace=True`.
        Exceptions:
            None.
        """
        if plot_id:
            self._set_plot_dirty_flags(plot_id, dirty_trace=True)
            return
        seen = set(self._plot_dirty_flags.keys())
        for key in list(self._plot_annotation_controllers.keys()):
            seen.add(key)
        for key in seen:
            self._set_plot_dirty_flags(key, dirty_trace=True)

    def _normalize_plot_refresh_signature_value(self, value: Any) -> Any:
        """Normalize one value into a deterministic refresh-signature form.

        Purpose:
            Convert mixed Python/state values into hash-stable tuples.
        Why:
            Adaptive refresh comparisons must be deterministic across nested
            dict/list/dataclass structures and runtime scalar types.
        Inputs:
            value: Arbitrary value to normalize.
        Outputs:
            Deterministic primitive/tuple representation.
        Side Effects:
            None.
        Exceptions:
            Normalization is best-effort; unsupported values fall back to string
            representations.
        """
        if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
            try:
                value = asdict(value)
            except Exception:
                return repr(value)
        if value is None or isinstance(value, (str, int, bool)):
            return value
        if isinstance(value, (float, np.floating)):
            try:
                value_f = float(value)
            except Exception:
                return None
            if not math.isfinite(value_f):
                return None
            return round(value_f, 12)
        if isinstance(value, np.integer):
            try:
                return int(value)
            except Exception:
                return repr(value)
        if isinstance(value, Mapping):
            normalized_items = []
            for key, item in value.items():
                normalized_items.append(
                    (
                        str(key),
                        self._normalize_plot_refresh_signature_value(item),
                    )
                )
            return tuple(sorted(normalized_items))
        if isinstance(value, set):
            return tuple(
                sorted(
                    self._normalize_plot_refresh_signature_value(item) for item in value
                )
            )
        if isinstance(value, (list, tuple)):
            return tuple(
                self._normalize_plot_refresh_signature_value(item) for item in value
            )
        if isinstance(value, np.ndarray):
            try:
                return (
                    tuple(value.shape),
                    str(value.dtype),
                    hash(np.ascontiguousarray(value).tobytes()),
                )
            except Exception:
                return repr(value)
        try:
            return str(value)
        except Exception:
            return repr(value)

    def _capture_plot_refresh_signature_bundle(
        self,
        *,
        plot_id: Optional[str],
        plot_key: Optional[str],
    ) -> Dict[str, Any]:
        """Capture the current adaptive-refresh signature bundle for one plot.

        Purpose:
            Snapshot all layer-relevant state used by refresh change detection.
        Why:
            Refresh should choose between no-op reveal, in-place layer apply, and
            full async rebuild based on deterministic state comparisons.
        Inputs:
            plot_id: Plot identifier for layout/elements signatures.
            plot_key: Plot key for decision context and diagnostics.
        Outputs:
            Dict containing normalized `data`, `layout`, `elements`, and
            `trace` signatures plus identity metadata.
        Side Effects:
            Reads current app settings/UI state to build signatures.
        Exceptions:
            Signature collection is best-effort; unavailable components are
            stored as None and treated conservatively by decision logic.
        """
        data_sig = None
        try:
            if self.df is not None:
                data_sig = self._normalize_plot_refresh_signature_value(
                    (
                        self._build_data_fingerprint(),
                        int(getattr(self, "_cycle_manual_revision", 0)),
                        bool(getattr(self, "_cycle_last_ignore_min_drop", False)),
                    )
                )
        except Exception:
            data_sig = None

        layout_sig = None
        try:
            args = tuple(self._collect_plot_args())
            layout_profile = (
                _get_layout_profile(plot_id)
                if isinstance(plot_id, str) and plot_id
                else None
            )
            layout_sig = self._normalize_plot_refresh_signature_value(
                {
                    "args": args,
                    "layout_profile": layout_profile,
                    "plot_id": plot_id,
                    "plot_key": plot_key,
                }
            )
        except Exception:
            layout_sig = None

        elements_sig = ()
        try:
            elements_sig = self._plot_elements_signature(plot_id)
        except Exception:
            elements_sig = ()

        trace_sig = None
        try:
            trace_sig = self._normalize_plot_refresh_signature_value(
                {
                    "scatter": self._gather_scatter_settings(),
                    "scatter_series": self._gather_series_scatter_settings(),
                }
            )
        except Exception:
            trace_sig = None

        return {
            "plot_id": plot_id,
            "plot_key": plot_key,
            "data": data_sig,
            "layout": layout_sig,
            "elements": self._normalize_plot_refresh_signature_value(elements_sig),
            "trace": trace_sig,
        }

    def _record_plot_refresh_signature_bundle(
        self,
        frame: Optional[ttk.Frame],
        *,
        plot_id: Optional[str],
        plot_key: Optional[str],
        bundle: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist the last applied refresh signature bundle on a plot frame.

        Purpose:
            Store the post-apply signature baseline used by the next refresh.
        Why:
            Adaptive refresh needs a previous-good state reference per tab.
        Inputs:
            frame: Plot tab frame to annotate.
            plot_id: Plot identifier used when bundle capture is required.
            plot_key: Plot key used when bundle capture is required.
            bundle: Optional precomputed signature bundle.
        Outputs:
            None.
        Side Effects:
            Sets `frame._plot_refresh_signature_bundle`.
        Exceptions:
            Attribute writes are guarded to preserve UI flow.
        """
        if frame is None:
            return
        signature_bundle = bundle
        if not isinstance(signature_bundle, dict):
            signature_bundle = self._capture_plot_refresh_signature_bundle(
                plot_id=plot_id,
                plot_key=plot_key,
            )
        try:
            frame._plot_refresh_signature_bundle = signature_bundle
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

    def _resolve_plot_refresh_adaptive_decision(
        self,
        frame: Optional[ttk.Frame],
        *,
        plot_id: Optional[str],
        plot_key: Optional[str],
        force_full_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """Decide which refresh path should run for the active plot tab.

        Purpose:
            Choose adaptive refresh behavior for the current refresh request.
        Why:
            A conservative layered strategy avoids unnecessary async rebuilds
            while preserving correctness for data/trace/combined-sensitive paths.
        Inputs:
            frame: Plot tab frame owning prior signature state.
            plot_id: Plot identifier used for dirty flags and signatures.
            plot_key: Plot key used for combined/non-combined routing.
            force_full_rebuild: True when callers explicitly require rebuild.
        Outputs:
            Dict with decision `path`, per-layer change booleans, and current
            signature bundle.
        Side Effects:
            Emits debug routing diagnostics.
        Exceptions:
            Missing baseline/signature data fails closed to full async refresh.
        """
        current_bundle = self._capture_plot_refresh_signature_bundle(
            plot_id=plot_id,
            plot_key=plot_key,
        )
        baseline_bundle = (
            getattr(frame, "_plot_refresh_signature_bundle", None)
            if frame is not None
            else None
        )
        flags = self._ensure_plot_dirty_flags(plot_id)
        dirty_data = (
            bool(flags.get("dirty_data", False)) if isinstance(flags, dict) else True
        )
        dirty_layout = (
            bool(flags.get("dirty_layout", False)) if isinstance(flags, dict) else True
        )
        dirty_elements = (
            bool(flags.get("dirty_elements", False))
            if isinstance(flags, dict)
            else True
        )
        dirty_trace = (
            bool(flags.get("dirty_trace", False)) if isinstance(flags, dict) else True
        )

        baseline_available = isinstance(baseline_bundle, Mapping)
        data_changed = dirty_data
        layout_changed = dirty_layout
        elements_changed = dirty_elements
        trace_changed = dirty_trace
        if baseline_available:
            data_changed = data_changed or (
                current_bundle.get("data") != baseline_bundle.get("data")
            )
            layout_changed = layout_changed or (
                current_bundle.get("layout") != baseline_bundle.get("layout")
            )
            elements_changed = elements_changed or (
                current_bundle.get("elements") != baseline_bundle.get("elements")
            )
            trace_changed = trace_changed or (
                current_bundle.get("trace") != baseline_bundle.get("trace")
            )
        else:
            # Missing baseline fails closed to full async refresh.
            data_changed = True
            layout_changed = True
            elements_changed = True
            trace_changed = True

        if force_full_rebuild:
            path = "full_async_refresh"
        elif not any((data_changed, layout_changed, elements_changed, trace_changed)):
            path = "no_change_fast_reveal"
        elif (
            plot_key != "fig_combined"
            and not data_changed
            and not trace_changed
            and (layout_changed or elements_changed)
        ):
            path = "in_place_display_apply"
        else:
            path = "full_async_refresh"

        self._log_plot_tab_debug(
            "Adaptive refresh decision for %s: path=%s data=%s layout=%s elements=%s trace=%s baseline=%s."
            % (
                plot_id or plot_key,
                path,
                data_changed,
                layout_changed,
                elements_changed,
                trace_changed,
                baseline_available,
            )
        )
        return {
            "path": path,
            "data_changed": data_changed,
            "layout_changed": layout_changed,
            "elements_changed": elements_changed,
            "trace_changed": trace_changed,
            "current_bundle": current_bundle,
            "baseline_available": baseline_available,
        }

    def _execute_adaptive_refresh_path(
        self,
        frame: Optional[ttk.Frame],
        canvas: Optional[FigureCanvasTkAgg],
        *,
        plot_id: Optional[str],
        plot_key: Optional[str],
        decision: Mapping[str, Any],
    ) -> bool:
        """Run a conservative adaptive refresh fast-path when eligible.

        Purpose:
            Execute no-change or in-place refresh paths without async rebuild.
        Why:
            Users should get fast refresh reveals when state is unchanged, while
            safe non-combined layout/element updates can apply in place.
        Inputs:
            frame: Plot tab frame being refreshed.
            canvas: Active canvas for figure finalization.
            plot_id: Plot identifier for settings/dirty state.
            plot_key: Plot key for combined/core routing.
            decision: Adaptive decision bundle from
                `_resolve_plot_refresh_adaptive_decision`.
        Outputs:
            True when a fast-path was executed, False when caller should fall
            back to the full async refresh pipeline.
        Side Effects:
            Applies display layers in place, runs deterministic layout finalize,
            updates/clears splash state, updates dirty flags, and records
            signature baselines.
        Exceptions:
            Any fast-path failure returns False so callers can fail closed to
            full async refresh.
        """
        if frame is None or canvas is None:
            return False
        path = str(decision.get("path") or "").strip().lower()
        if path not in {"no_change_fast_reveal", "in_place_display_apply"}:
            return False
        fig = getattr(canvas, "figure", None)
        if fig is None:
            return False

        try:
            frame._plot_auto_refresh_state = "refreshing"
            frame._plot_auto_refresh_in_progress = True
            frame._plot_auto_refresh_after_id = None
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        try:
            widget = canvas.get_tk_widget()
        except Exception:
            widget = None

        try:
            if path == "in_place_display_apply" and plot_id:
                self._update_plot_loading_overlay_progress(
                    frame,
                    progress=78.0,
                    message="Applying plot layer updates...",
                    stage_key="installing",
                )
                placement_state = self._capture_plot_element_placement_state(plot_id)
                self._apply_display_settings_for_plot(fig, plot_id, canvas)
                if placement_state:
                    self._restore_plot_element_placement_state(plot_id, placement_state)
            else:
                self._update_plot_loading_overlay_progress(
                    frame,
                    progress=78.0,
                    message="No plot changes detected. Verifying layout...",
                    stage_key="installing",
                )

            hold_combined_overlay = bool(
                plot_key == "fig_combined"
                and getattr(frame, "_post_first_draw_refresh_hold_overlay", False)
            )
            if hold_combined_overlay:
                # Fast-path combined refresh still needs draw-confirmed completion.
                try:
                    frame._post_first_draw_refresh_done = True
                    frame._post_first_draw_refresh_invoked = True
                    frame._combined_overlay_completion_draw_pending = True
                    frame._combined_overlay_completion_fig_id = id(fig)
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass

            self._update_plot_loading_overlay_progress(
                frame,
                progress=92.0,
                message="Final Layout Adjustments...",
                stage_key="finalizing",
            )
            self._finalize_matplotlib_canvas_layout(
                canvas=canvas,
                fig=fig,
                tk_widget=widget,
                keep_export_size=False,
                trigger_resize_event=True,
                force_draw=True,
            )

            if plot_id:
                self._set_plot_dirty_flags(
                    plot_id,
                    dirty_data=False,
                    dirty_layout=False,
                    dirty_elements=False,
                    dirty_trace=False,
                )
            self._record_plot_refresh_signature_bundle(
                frame,
                plot_id=plot_id,
                plot_key=plot_key,
                bundle=decision.get("current_bundle")
                if isinstance(decision.get("current_bundle"), dict)
                else None,
            )

            if hold_combined_overlay:
                # Combined overlay clear remains draw-gated in the shared handler.
                try:
                    frame._plot_auto_refresh_state = "pending"
                    frame._plot_auto_refresh_in_progress = False
                    frame._plot_auto_refresh_after_id = None
                    frame._plot_auto_refresh_phase = None
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
            else:
                try:
                    frame._plot_auto_refresh_state = "done"
                    frame._plot_auto_refresh_after_id = None
                    frame._plot_auto_refresh_in_progress = False
                    frame._plot_auto_refresh_phase = None
                    if plot_key in {"fig1", "fig2"}:
                        frame._core_overlay_hold = False
                        frame._core_overlay_second_refresh_scheduled = False
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
                self._update_plot_loading_overlay_progress(
                    frame,
                    progress=100.0,
                    message="Plot ready.",
                    stage_key="ready",
                )
                self._clear_plot_loading_overlay(frame)
            return True
        except Exception:
            return False

    def _refresh_plot_for_plot_id(
        self,
        plot_id: Optional[str],
        *,
        reason: Optional[str] = None,
        rearm_overlay: bool = False,
        capture_combined_legend: bool = True,
        force_full_rebuild: bool = False,
    ) -> None:
        """Run one unified refresh pipeline for a plot tab.

        Purpose:
            Route plot-tab refresh requests through one overlay-aware path.
        Why:
            Plot Settings/Data Trace/Layout apply actions and manual Refresh
            must share the same stabilization pipeline to avoid post-splash
            layout snaps.
        Inputs:
            plot_id: Plot identifier for the target tab.
            reason: Optional splash message shown at refresh start.
            rearm_overlay: When True, reset overlay orchestration state before
                invoking refresh.
            capture_combined_legend: When True, capture combined legend anchors
                before combined refresh rebuild.
            force_full_rebuild: When True, force the refresh pipeline to bypass
                combined display reuse and rebuild the figure from scratch.
        Outputs:
            None.
        Side Effects:
            Optionally resets overlay orchestration state and invokes
            `_force_plot_refresh` for the target tab/canvas. Data Trace Settings
            reasons additionally mark trace-dirty state before refresh routing.
        Exceptions:
            Best-effort guards suppress refresh failures to keep UI responsive.
        """
        if not plot_id:
            return
        if isinstance(reason, str) and "data trace settings" in reason.lower():
            self._mark_plot_trace_dirty(plot_id)
        if rearm_overlay:
            try:
                self._prepare_plot_refresh_overlay_for_settings(plot_id)
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        # Iterate over indexed elements from getattr(self, "_plot_tabs", []) or [] to apply the per-item logic.
        for idx, tab in enumerate(getattr(self, "_plot_tabs", []) or []):
            if getattr(tab, "_plot_id", None) != plot_id:
                continue
            if idx < len(getattr(self, "_canvases", []) or []):
                canvas = self._canvases[idx]
                try:
                    self._force_plot_refresh(
                        tab,
                        canvas,
                        capture_combined_legend=capture_combined_legend,
                        refresh_reason=reason,
                        force_full_rebuild=force_full_rebuild,
                    )
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
            break

    def _add_plot_tab(
        self, title, fig, *, plot_key: str | None = None, auto_refresh: bool = True
    ):
        """Add a plot tab and embed the provided figure.

        Purpose:
            Create a plot tab with toolbar controls and a Matplotlib canvas.
        Why:
            The UI renders plots into tabs so users can switch between figures
            without losing per-plot controls or annotations, while keeping save
            controls and format toggles grouped together.
        Inputs:
            title: Tab title string.
            fig: Matplotlib Figure to embed.
            plot_key: Optional plot key used to tag plot metadata and routing.
            auto_refresh: When True, schedule the auto-refresh pipeline that
                stabilizes the first render before removing overlays.
        Outputs:
            The created tab frame.
        Side Effects:
            Creates Tk widgets, binds canvas resize handlers, registers plot
            controllers, selects the new tab immediately, schedules display
            refresh logic (when enabled), and initializes plot loading/auto-
            refresh state for the generated tab.
        Exceptions:
            Widget and canvas errors are caught to avoid UI interruption.
        """

        frame = ttk.Frame(self.nb)
        frame._plot_key = plot_key
        frame._plot_auto_refresh_state = "pending"
        frame._plot_auto_refresh_phase = None
        frame._plot_auto_refresh_enabled = bool(auto_refresh)
        frame._plot_auto_refresh_after_id = None
        frame._plot_auto_refresh_in_progress = False
        frame._plot_initial_render_complete = False
        frame._plot_render_task_id = None
        frame._plot_loading_overlay = None
        frame._plot_loading_label = None
        frame._plot_loading_detail_label = None
        frame._plot_loading_progress_var = None
        frame._plot_loading_bar = None
        frame._plot_loading_progress_label = None
        frame._plot_loading_progress_value = 0.0
        frame._plot_loading_stage_key = "queued"
        frame._plot_loading_started_at = None
        frame._plot_loading_heartbeat_after_id = None
        frame._plot_loading_detail_base = ""
        frame._plot_loading_pending_message = None
        frame._plot_loading_pending_detail = None
        frame._refresh_command = None
        frame._post_first_draw_refresh_done = False
        frame._post_first_draw_refresh_invoked = False
        frame._post_first_draw_refresh_hold_overlay = False
        frame._post_first_draw_refresh_retry_count = 0
        frame._post_first_draw_refresh_waiting_for_command = False
        frame._post_first_draw_refresh_command_bind_id = None
        frame._post_first_draw_refresh_command_timeout_after_id = None
        frame._combined_refresh_geometry_wait = None
        frame._combined_finalize_geometry_wait = None
        frame._combined_overlay_completion_draw_pending = False
        frame._combined_overlay_completion_fig_id = None
        if plot_key in {"fig1", "fig2"}:
            is_real_core = self._is_real_core_figure(fig)
            frame._core_real_figure_installed = bool(is_real_core)
            frame._core_overlay_refresh_invoked_count = 0
            frame._core_overlay_refresh_completed_count = 0
            frame._core_overlay_layout_sig_baseline = None
            frame._core_overlay_need_second_refresh = True
            frame._core_overlay_target_refreshes = 2
            frame._core_overlay_ready_seen = False
            frame._core_overlay_second_refresh_scheduled = False
            frame._core_overlay_hold = not bool(is_real_core)
        if plot_key == "fig_combined":
            is_real_combined = self._is_real_combined_figure(fig)
            default_target_refreshes = self._combined_overlay_default_target_refreshes()
            frame._combined_render_ready = False
            frame._post_first_draw_refresh_hold_overlay = (
                self._combined_requires_post_first_draw_refresh()
            )
            frame._combined_real_figure_installed = bool(is_real_combined)
            frame._combined_overlay_refresh_invoked_count = 0
            frame._combined_overlay_refresh_completed_count = 0
            frame._combined_overlay_layout_sig_baseline = None
            frame._combined_overlay_decision_sig_baseline = None
            frame._combined_overlay_decision_sig_last = None
            frame._combined_overlay_data_sig_current = None
            frame._combined_overlay_need_second_refresh = default_target_refreshes > 1
            frame._combined_overlay_target_refreshes = default_target_refreshes
            frame._combined_overlay_ready_seen = False
            frame._combined_overlay_second_refresh_scheduled = False
            frame._combined_placeholder_draw_logged = False
            frame._combined_overlay_last_geometry_sig = None
            frame._combined_overlay_stable_draw_count = 0
            frame._combined_overlay_finalize_started_at = None
            frame._combined_overlay_finalize_after_id = None
            frame._combined_overlay_completion_draw_pending = False
            frame._combined_overlay_completion_fig_id = None

        self._log_plot_tab_debug(f"Creating tab frame for '{title}'")

        try:
            self.nb.add(frame, text=title)
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        try:
            self.nb.update_idletasks()

        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        if not hasattr(self, "_plot_tabs"):
            self._plot_tabs = []

            self._canvases = []

        # --- Toolbar shell for action controls and export format toggles.
        topbar_shell = ttk.Frame(frame)
        topbar_shell.pack(side="top", fill="x")
        topbar = ttk.Frame(topbar_shell)
        topbar.pack(side="top", fill="x")

        plot_id = self._plot_key_to_plot_id(plot_key, title)
        frame._plot_id = plot_id

        canvas = FigureCanvasTkAgg(fig, master=frame)
        try:
            # Bind the tab frame so draw-event handlers can route refresh state.
            canvas._plot_frame = frame  # type: ignore[attr-defined]
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        # Closure captures _add_plot_tab state for callback wiring, kept nested to
        # scope the handler, and invoked by bindings set in _add_plot_tab.
        def _refresh_panel_internal() -> None:
            """Refresh panel via internal orchestration callback.

            Purpose:
                Execute one refresh pass for auto-refresh orchestration.
            Why:
                Post-draw and adaptive refresh passes rely on the legacy direct
                refresh callback and must not re-arm overlay counters.
            Inputs:
                None.
            Outputs:
                None.
            Side Effects:
                Invokes `_force_plot_refresh` on the current frame/canvas pair.
            Exceptions:
                Errors are handled by the downstream refresh pipeline.
            """
            self._force_plot_refresh(frame, canvas)

        def _refresh_panel_user() -> None:
            """Refresh the plot panel using the user-facing unified pipeline.

            Purpose:
                Rebuild the current plot tab using the same Refresh logic.
            Why:
                Manual Refresh should re-arm overlay orchestration and avoid
                pre-refresh combined legend recapture drift.
            Inputs:
                None.
            Outputs:
                None.
            Side Effects:
                Triggers a plot rebuild and display refresh on the existing canvas.
            Exceptions:
                Errors are handled by the downstream refresh pipeline.
            """
            refresh_message = (
                "Refreshing combined plot..."
                if plot_key == "fig_combined"
                else "Refreshing plot..."
            )
            if plot_id:
                self._refresh_plot_for_plot_id(
                    plot_id,
                    reason=refresh_message,
                    rearm_overlay=True,
                    capture_combined_legend=False,
                )
                return
            self._force_plot_refresh(
                frame,
                canvas,
                capture_combined_legend=False,
                refresh_reason=refresh_message,
            )

        # Assign the refresh command before any draw/draw_idle can run.
        frame._refresh_command = _refresh_panel_internal
        try:
            frame.event_generate("<<GL260RefreshCommandReady>>", when="tail")
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        toolbar = NavigationToolbar2Tk(canvas, topbar)  # mount toolbar in the topbar

        toolbar.update()

        toolbar.pack(side="left", fill="x")

        widget = canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)

        try:
            self.nb.update_idletasks()
            self.update_idletasks()
            widget.update_idletasks()
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        overlay_message = (
            "Loading combined plot..."
            if plot_key == "fig_combined"
            else "Loading plot..."
        )
        # Hide the initial render behind a loading overlay until auto-refresh completes.
        self._install_plot_loading_overlay(frame, widget, message=overlay_message)
        # Select immediately so the loading overlay is visible without delay.
        try:
            self.nb.select(frame)
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        # Flush pending UI work so the new tab and overlay paint right away.
        for widget_obj in (self.nb, frame, widget):
            try:
                widget_obj.update_idletasks()
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        fig_size = None
        try:
            width_px = max(int(widget.winfo_width()), 1)
            height_px = max(int(widget.winfo_height()), 1)
            if width_px > 1 and height_px > 1:
                dpi = float(getattr(fig, "dpi", 100.0))
                if not math.isfinite(dpi) or dpi <= 0.0:
                    dpi = 100.0
                fig_size = (
                    max(width_px / dpi, 1.0),
                    max(height_px / dpi, 1.0),
                )
        except Exception:
            fig_size = None
        if fig_size is None:
            try:
                fig_size = self._compute_target_figsize_inches()
            except Exception:
                fig_size = None
        if fig_size is not None:
            try:
                fig.set_size_inches(fig_size, forward=False)
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        if plot_id and plot_key != "fig_combined":
            try:
                self._apply_display_settings_for_plot(fig, plot_id, canvas)
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        format_order = ("png", "pdf", "svg")
        format_specs = {
            "png": ("PNG files", "*.png"),
            "pdf": ("PDF files", "*.pdf"),
            "svg": ("SVG files", "*.svg"),
        }

        # Closure captures _add_plot_tab local context to keep helper logic scoped and invoked directly within _add_plot_tab.
        def _get_plot_export_formats_defaulted():
            """Return plot export formats defaulted.
            Used to retrieve plot export formats defaulted for downstream logic."""
            raw = settings.get("plot_export_formats")
            if not isinstance(raw, dict):
                raw = {}
            normalized = {fmt: bool(raw.get(fmt, False)) for fmt in format_order}
            if not any(normalized.values()):
                normalized["svg"] = True
            return normalized

        format_defaults = _get_plot_export_formats_defaulted()
        format_vars = {
            fmt: tk.BooleanVar(
                master=frame, value=bool(format_defaults.get(fmt, False))
            )
            # Iterate to apply the per-item logic.
            for fmt in format_order
        }

        # Closure captures _add_plot_tab local context to keep helper logic scoped and invoked directly within _add_plot_tab.
        def _persist_plot_export_formats():
            """Export formats.
            Used by persist plot workflows to export formats."""
            settings["plot_export_formats"] = {
                fmt: bool(format_vars[fmt].get()) for fmt in format_order
            }
            if hasattr(self, "_schedule_save_settings"):
                try:
                    self._schedule_save_settings()
                    return
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
            try:
                _save_settings_to_disk()
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        # Closure captures _add_plot_tab local context to keep helper logic scoped and invoked directly within _add_plot_tab.
        def _selected_formats():
            """Perform selected formats.
            Used to keep the workflow logic localized and testable."""
            return [fmt for fmt in format_order if format_vars[fmt].get()]

        save_button = None

        # Closure captures _add_plot_tab state for callback wiring, kept nested to scope the handler, and invoked by bindings set in _add_plot_tab.
        def _update_save_button_state():
            """Update save button state.
            Used to keep save button state in sync with current state."""
            if save_button is None:
                return
            self._set_widget_enabled(save_button, bool(_selected_formats()))

        # Closure captures _add_plot_tab state for callback wiring, kept nested to scope the handler, and invoked by bindings set in _add_plot_tab.
        def _on_format_toggle():
            """Handle format toggle.
            Used as an event callback for format toggle."""
            _persist_plot_export_formats()
            _update_save_button_state()

        # Closure captures _add_plot_tab local context to keep helper logic scoped and invoked directly within _add_plot_tab.
        def _save_selected_formats():
            """Export the active plot tab in each selected file format.

            Purpose:
                Save one or more output files for the current plot tab.
            Why:
                Users can batch-save display plots while keeping export geometry
                and profile margins consistent across formats.
            Inputs:
                None.
            Outputs:
                None.
            Side Effects:
                Opens a save dialog, rebuilds export figures, applies layout
                profile/legend sizing, writes files, and may display errors.
            Exceptions:
                Export failures are captured and reported without crashing UI.
            """

            _persist_plot_export_formats()

            selected_formats = _selected_formats()

            if not selected_formats:
                try:
                    messagebox.showinfo(
                        "No File Type Selected",
                        "Select at least one file type before saving.",
                    )

                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass

                return

            initial_ext = selected_formats[0]

            filetypes = [format_specs[fmt] for fmt in selected_formats]
            filetypes.append(("All files", "*.*"))

            path = filedialog.asksaveasfilename(
                title="Save Plot",
                defaultextension=f".{initial_ext}",
                filetypes=filetypes,
                initialfile=(
                    (title.replace(":", " - ") + f".{initial_ext}")
                    if title
                    else f"plot.{initial_ext}"
                ),
            )

            if not path:
                return

            base, _ = os.path.splitext(path)

            if not base:
                base = path

            prev_size = fig.get_size_inches()
            base_width, base_height = tuple(prev_size)

            prev_dpi = fig.dpi

            target_w, target_h = self._compute_output_dimensions(
                "plot_export", base_width, base_height
            )

            export_fig = fig
            close_export_fig = False
            resized_current_fig = False

            try:
                if plot_key == "fig_combined":
                    try:
                        preview_fig = getattr(self, "_combined_plot_preview_fig", None)
                        target_fig = preview_fig if preview_fig is not None else fig
                        if target_fig is not None and target_fig.canvas is not None:
                            try:
                                target_fig.canvas.draw()
                            except Exception:
                                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                                pass
                        self._capture_combined_legend_anchor_from_fig(
                            target_fig,
                            source="sync",
                        )
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                    export_fig = self.render_plot(
                        "fig_combined",
                        target="export",
                        mode="export",
                        plot_id=plot_id,
                        fig_size=(11.0, 8.5),
                    )
                    if export_fig is None:
                        msg = "Combined plot could not be rebuilt for export."
                        try:
                            messagebox.showerror("Save Error", msg)
                        except Exception:
                            print(f"Save Error: {msg}")
                        return
                    close_export_fig = True
                    if not self._assert_combined_export_size(export_fig):
                        return
                else:
                    export_fig = self.render_plot(
                        plot_key or "",
                        target="export",
                        mode="export",
                        plot_id=plot_id,
                        fig_size=(target_w, target_h),
                    )
                    if export_fig is None:
                        msg = "Plot could not be rebuilt for export."
                        try:
                            messagebox.showerror("Save Error", msg)
                        except Exception:
                            print(f"Save Error: {msg}")
                        return
                    close_export_fig = True
                if plot_id:
                    try:
                        _apply_layout_profile_to_figure(export_fig, plot_id, "export")
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass

                if plot_id and plot_key != "fig_combined":
                    try:
                        self._apply_plot_elements(export_fig, plot_id)
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                try:
                    self._apply_gl260_legend_sizing(
                        export_fig, plot_id=plot_id, plot_key=plot_key
                    )
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass

                errors = []
                export_dpi = self._get_export_dpi()

                if plot_key == "fig_combined":
                    try:
                        from matplotlib.backends.backend_agg import FigureCanvasAgg
                    except Exception:
                        FigureCanvasAgg = None
                    export_canvas = None
                    try:
                        export_canvas = export_fig.canvas
                    except Exception:
                        export_canvas = None
                    if FigureCanvasAgg is not None:
                        if export_canvas is None or not isinstance(
                            export_canvas, FigureCanvasAgg
                        ):
                            try:
                                export_canvas = FigureCanvasAgg(export_fig)
                            except Exception:
                                export_canvas = getattr(export_fig, "canvas", None)
                    if export_canvas is None:
                        export_canvas = getattr(export_fig, "canvas", None)
                    try:
                        self._finalize_matplotlib_canvas_layout(
                            canvas=export_canvas,
                            fig=export_fig,
                            tk_widget=None,
                            keep_export_size=True,
                            trigger_resize_event=False,
                            force_draw=True,
                        )
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass

                # Iterate over selected_formats to apply the per-item logic.
                for fmt in selected_formats:
                    out_path = f"{base}.{fmt}"

                    try:
                        save_kwargs = {"format": fmt}

                        if fmt.lower() in {"png", "pdf"}:
                            save_kwargs["dpi"] = export_dpi

                        export_fig.savefig(out_path, **save_kwargs)

                    except Exception as exc:
                        errors.append((fmt, exc))

                if errors:
                    try:
                        messagebox.showerror(
                            "Save Error",
                            "The following files could not be saved:\n"
                            + "\n".join(f"{fmt.upper()}: {exc}" for fmt, exc in errors),
                        )

                    except Exception:
                        # Iterate over errors to apply the per-item logic.
                        for _, exc in errors:
                            print(f"Save Error: {exc}")

            finally:
                if resized_current_fig:
                    try:
                        fig.set_size_inches(prev_size, forward=False)

                        fig.set_dpi(prev_dpi)

                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                    if plot_id and plot_key != "fig_combined":
                        try:
                            _apply_layout_profile_to_figure(fig, plot_id, "display")
                        except Exception:
                            # Best-effort guard; ignore failures to avoid interrupting the workflow.
                            pass

                if close_export_fig and export_fig is not fig:
                    try:
                        plt.close(export_fig)

                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass

                try:
                    canvas.draw_idle()

                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass

        # Closure captures _add_plot_tab state for callback wiring, kept nested to scope the handler, and invoked by bindings set in _add_plot_tab.
        def _close_this_plot():
            """Close the current plot tab and return to Plot Settings.

            Purpose:
                Tear down the selected plot tab and route focus back to the
                Plot Settings tab to keep the workflow centered on plotting.
            Why:
                Users expect to continue adjusting plot settings after closing
                a generated figure, not to land on Final Report.

            Args:
                None.

            Returns:
                None.

            Side Effects:
                Captures combined legend anchors when persistence is enabled,
                destroys the tab/canvas, and selects the Plot Settings tab.

            Exceptions:
                Errors are caught to avoid interrupting UI teardown.
            """

            self._log_plot_tab_debug(f"Close requested for '{title}'")

            if plot_key == "fig_combined":
                # Capture combined legend anchors before the figure is closed.
                if self._combined_cycle_legend_capture_enabled():
                    try:
                        self._capture_combined_legend_anchor_from_fig(
                            fig,
                            source="refresh",
                        )
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass

            if plot_id:
                controller = self._plot_annotation_controllers.pop(plot_id, None)
                if controller is not None:
                    try:
                        controller.disconnect()
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                self._plot_annotation_panels.pop(plot_id, None)
                window = self._plot_element_windows.pop(plot_id, None)
                if window is not None:
                    try:
                        window.destroy()
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                self._plot_element_editors.pop(plot_id, None)
                try:
                    self._teardown_layout_editor(plot_id, apply_changes=False)
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
                self._plot_dirty_flags.pop(plot_id, None)
                if getattr(self, "_plot_settings_target_id", None) == plot_id:
                    try:
                        self._close_plot_settings_dialog()
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass

            try:
                self.nb.forget(frame)

            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

            try:
                frame.destroy()

            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

            try:
                idx = self._plot_tabs.index(frame)

                del self._plot_tabs[idx]

                if idx < len(self._canvases):
                    del self._canvases[idx]

            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

            try:
                import matplotlib.pyplot as plt

                plt.close(fig)

            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

            plot_settings_tab = getattr(self, "_plot_settings_tab", None) or getattr(
                self, "tab_plot", None
            )
            if plot_settings_tab is not None:
                try:
                    # Explicitly route focus to Plot Settings after tab close.
                    self.nb.select(plot_settings_tab)
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass

        btn_close = _ui_button(topbar, text="Close Plot", command=_close_this_plot)

        btn_close.pack(side="right", padx=6, pady=4)

        btn_refresh = _ui_button(
            topbar,
            text="Refresh",
            command=_refresh_panel_user,
        )

        btn_refresh.pack(side="right", padx=6, pady=4)

        if plot_id:
            if plot_key == "fig_combined":
                btn_elements = _ui_button(
                    topbar,
                    text="Plot Elements...",
                    command=lambda: self._open_plot_elements_editor(
                        canvas.figure, canvas, plot_id
                    ),
                )
                btn_elements.pack(side="right", padx=6, pady=4)
                btn_settings = _ui_button(
                    topbar,
                    text="Plot Settings...",
                    command=lambda: self._open_plot_settings_dialog(plot_id),
                )
                btn_settings.pack(side="right", padx=6, pady=4)
                btn_trace_settings = _ui_button(
                    topbar,
                    text="Data Trace Settings...",
                    command=self._open_data_trace_settings_dialog,
                )
                btn_trace_settings.pack(side="right", padx=6, pady=4)
            else:
                btn_elements = _ui_button(
                    topbar,
                    text="Add Plot Elements...",
                    command=lambda: self._open_plot_elements_editor(
                        canvas.figure, canvas, plot_id
                    ),
                )
                btn_elements.pack(side="right", padx=6, pady=4)
                btn_settings = _ui_button(
                    topbar,
                    text="Plot Settings...",
                    command=lambda: self._open_plot_settings_dialog(plot_id),
                )
                btn_settings.pack(side="right", padx=6, pady=4)
                btn_trace_settings = _ui_button(
                    topbar,
                    text="Data Trace Settings...",
                    command=self._open_data_trace_settings_dialog,
                )
                btn_trace_settings.pack(side="right", padx=6, pady=4)

        save_controls = ttk.Frame(topbar)

        save_controls.pack(side="left", padx=6, pady=4)

        save_button = _ui_button(
            save_controls, text="Save As", command=_save_selected_formats
        )

        save_button.pack(side="left", padx=(0, 8))

        if plot_key == "fig_combined":
            preview_button = _ui_button(
                save_controls,
                text="Plot Preview",
                command=lambda: self._open_plot_preview(plot_key, plot_id, title),
            )
            preview_button.pack(side="left", padx=(0, 8))

        combined_export_row = plot_key == "fig_combined"
        checkbox_frame = ttk.Frame(save_controls)
        checkbox_frame.pack(side="left", padx=(0, 2) if combined_export_row else (0, 6))

        # Iterate over format_order to apply the per-item logic.
        for fmt in format_order:
            if combined_export_row:
                check_widget = ttk.Checkbutton(
                    checkbox_frame,
                    text=fmt.upper(),
                    variable=format_vars[fmt],
                    command=_on_format_toggle,
                )
            else:
                check_widget = _ui_checkbutton(
                    checkbox_frame,
                    text=fmt.upper(),
                    variable=format_vars[fmt],
                    command=_on_format_toggle,
                )
            check_widget.pack(
                side="left", padx=(0, 1) if combined_export_row else (0, 6)
            )

        _update_save_button_state()

        # --- Canvas below the topbar

        widget = canvas.get_tk_widget()

        refresh_state = {"scheduled": False}

        # Closure captures _add_plot_tab local context to keep helper logic scoped and invoked directly within _add_plot_tab.
        def _schedule_canvas_sync(_event=None):
            """Schedule a canvas sync on idle.

            Purpose:
                Queue a lightweight refresh of the canvas display on idle.
            Why:
                Canvas geometry can change during layout; syncing on idle keeps
                the UI responsive while avoiding redundant refresh work.
            Inputs:
                _event: Optional Tk event payload (unused).
            Outputs:
                None.
            Side Effects:
                Schedules a deferred refresh of the canvas display.
            Exceptions:
                Errors are caught to avoid interrupting the UI loop.
            """

            if refresh_state["scheduled"]:
                return
            if plot_key == "fig_combined" and not getattr(
                frame, "_combined_render_ready", False
            ):
                # Combined plots defer the first draw; skip premature sync.
                return

            refresh_state["scheduled"] = True

            # Closure captures _schedule_canvas_sync local context to keep helper logic scoped and invoked directly within _schedule_canvas_sync.
            def _do_refresh():
                """Refresh value.
                Used by do workflows to refresh value."""

                refresh_state["scheduled"] = False

                self._refresh_canvas_display(frame, canvas, trigger_resize=False)

            try:
                self.after_idle(_do_refresh)

            except Exception:
                _do_refresh()

        try:
            widget.bind("<Configure>", _schedule_canvas_sync, add="+")

        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

        _schedule_canvas_sync()

        if plot_key != "fig_combined":
            canvas.draw()

        # Closure captures _add_plot_tab local context to keep helper logic scoped and invoked directly within _add_plot_tab.
        def _finalize_tab_display():
            """Perform finalize tab display.
            Used to keep the workflow logic localized and testable."""

            try:
                if plot_key == "fig_combined":
                    self._finalize_combined_plot_display(frame, canvas)
                else:
                    self._refresh_canvas_display(frame, canvas, trigger_resize=True)
                    try:
                        frame._plot_initial_render_complete = True
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting the workflow.
                        pass
                    if getattr(frame, "_plot_auto_refresh_enabled", True):
                        self._schedule_plot_auto_refresh(frame, canvas)
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        _finalize_tab_display()

        self._plot_tabs.append(frame)

        self._canvases.append(canvas)

        if plot_id:
            try:
                self._set_plot_dirty_flags(
                    plot_id,
                    dirty_data=False,
                    dirty_layout=False,
                    dirty_elements=False,
                    dirty_trace=False,
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass

        return frame


def _regression_test_adaptive_refresh_decision_routing() -> None:
    """Validate adaptive refresh routing decisions for conservative layered mode.

    Purpose:
        Verify no-change, in-place, and full-refresh decision outcomes.
    Why:
        Refresh orchestration relies on deterministic routing and must fail
        closed for combined/trace-sensitive updates.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Executes `_resolve_plot_refresh_adaptive_decision` with a local harness.
    Exceptions:
        Raises AssertionError when decision routing regresses.
    """

    class _Harness:
        """Minimal harness for adaptive decision routing tests."""

        def __init__(self) -> None:
            self.flags = {
                "dirty_data": False,
                "dirty_layout": False,
                "dirty_elements": False,
                "dirty_trace": False,
            }
            self.current_bundle = {
                "plot_id": "fig_pressure_temp",
                "plot_key": "fig1",
                "data": ("data", 1),
                "layout": ("layout", 1),
                "elements": ("elements", 1),
                "trace": ("trace", 1),
            }
            self.logs: List[str] = []

        def _capture_plot_refresh_signature_bundle(self, **_kwargs) -> Dict[str, Any]:
            """Return deterministic current signature bundle for routing tests."""
            return copy.deepcopy(self.current_bundle)

        def _ensure_plot_dirty_flags(self, _plot_id: Optional[str]) -> Dict[str, bool]:
            """Return mutable dirty flags used by adaptive decision logic."""
            return dict(self.flags)

        def _log_plot_tab_debug(self, message: str) -> None:
            """Capture debug logs for assertion context."""
            self.logs.append(str(message))

    harness = _Harness()
    frame = type("_FrameStub", (), {})()
    frame._plot_refresh_signature_bundle = copy.deepcopy(harness.current_bundle)

    decision = UnifiedApp._resolve_plot_refresh_adaptive_decision(
        harness,
        frame,
        plot_id="fig_pressure_temp",
        plot_key="fig1",
        force_full_rebuild=False,
    )
    if decision.get("path") != "no_change_fast_reveal":
        raise AssertionError(
            f"Expected no-change fast reveal decision, got {decision.get('path')!r}."
        )

    harness.flags["dirty_layout"] = True
    decision = UnifiedApp._resolve_plot_refresh_adaptive_decision(
        harness,
        frame,
        plot_id="fig_pressure_temp",
        plot_key="fig1",
        force_full_rebuild=False,
    )
    if decision.get("path") != "in_place_display_apply":
        raise AssertionError(
            f"Expected in-place decision for layout-only non-combined change, got {decision.get('path')!r}."
        )

    harness.flags["dirty_layout"] = False
    harness.flags["dirty_trace"] = True
    decision = UnifiedApp._resolve_plot_refresh_adaptive_decision(
        harness,
        frame,
        plot_id="fig_pressure_temp",
        plot_key="fig1",
        force_full_rebuild=False,
    )
    if decision.get("path") != "full_async_refresh":
        raise AssertionError(
            f"Expected full async decision for trace change, got {decision.get('path')!r}."
        )

    harness.flags["dirty_trace"] = False
    harness.flags["dirty_layout"] = True
    decision = UnifiedApp._resolve_plot_refresh_adaptive_decision(
        harness,
        frame,
        plot_id="fig_combined_triple_axis",
        plot_key="fig_combined",
        force_full_rebuild=False,
    )
    if decision.get("path") != "full_async_refresh":
        raise AssertionError(
            f"Expected full async decision for combined layout change, got {decision.get('path')!r}."
        )


def _regression_test_force_refresh_adaptive_fastpath_short_circuit() -> None:
    """Validate `_force_plot_refresh` exits early when adaptive fast-path applies.

    Purpose:
        Ensure no-change adaptive fast-path avoids async/full refresh execution.
    Why:
        Refresh should reveal unchanged plots quickly from behind splash without
        scheduling worker renders.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Executes `_force_plot_refresh` with local frame/canvas harness stubs.
    Exceptions:
        Raises AssertionError when fast-path short-circuit behavior regresses.
    """

    class _WidgetStub:
        """Minimal Tk widget stub for overlay installation checks."""

        @staticmethod
        def winfo_exists() -> bool:
            """Return widget-exists status for refresh harness checks."""
            return True

    class _CanvasStub:
        """Minimal canvas stub used by `_force_plot_refresh` entry flow."""

        def __init__(self) -> None:
            self.figure = object()
            self._widget = _WidgetStub()

        def get_tk_widget(self) -> _WidgetStub:
            """Return Tk widget stub used by refresh overlay flow."""
            return self._widget

    class _Harness:
        """Harness that records whether fast-path short-circuit occurred."""

        def __init__(self) -> None:
            self.fast_path_called = False
            self.full_path_touched = False

        @staticmethod
        def _plot_key_to_plot_id(
            plot_key: Optional[str], title: Optional[str] = None
        ) -> Optional[str]:
            """Resolve plot id for regression harness mapping."""
            _ = title
            mapping = {
                "fig1": "fig_pressure_temp",
                "fig2": "fig_pressure_derivative",
                "fig_combined": "fig_combined_triple_axis",
                "fig_peaks": "fig_cycle_analysis",
            }
            return mapping.get(plot_key or "")

        def _flush_open_plot_settings_dialog(
            self, *, refresh_after_apply: bool = False
        ) -> bool:
            """No-op staged settings flush for fast-path regression."""
            _ = refresh_after_apply
            return False

        @staticmethod
        def _install_plot_loading_overlay(
            _frame, _widget, *, message: str, detail: Optional[str] = None
        ) -> None:
            """No-op overlay install hook for regression harness."""
            _ = message
            _ = detail

        @staticmethod
        def _update_plot_loading_overlay_progress(_frame, **_kwargs) -> None:
            """No-op overlay progress hook for regression harness."""

        @staticmethod
        def _resolve_plot_refresh_adaptive_decision(
            _frame,
            *,
            plot_id: Optional[str],
            plot_key: Optional[str],
            force_full_rebuild: bool = False,
        ) -> Dict[str, Any]:
            """Return deterministic no-change adaptive decision."""
            _ = plot_id
            _ = plot_key
            _ = force_full_rebuild
            return {"path": "no_change_fast_reveal"}

        def _execute_adaptive_refresh_path(
            self,
            _frame,
            _canvas,
            *,
            plot_id: Optional[str],
            plot_key: Optional[str],
            decision: Mapping[str, Any],
        ) -> bool:
            """Mark fast-path invocation and short-circuit refresh flow."""
            _ = plot_id
            _ = plot_key
            _ = decision
            self.fast_path_called = True
            return True

        def _refresh_canvas_display(
            self, _frame, _canvas, *, trigger_resize: bool = True
        ) -> None:
            """Mark unexpected full-path access in regression harness."""
            _ = trigger_resize
            self.full_path_touched = True

    harness = _Harness()
    frame = type("_FrameStub", (), {})()
    frame._plot_key = "fig1"
    frame._plot_id = "fig_pressure_temp"
    frame._plot_auto_refresh_state = "done"
    frame._plot_auto_refresh_after_id = None
    frame._plot_auto_refresh_in_progress = False
    canvas = _CanvasStub()

    UnifiedApp._force_plot_refresh(harness, frame, canvas)
    if not harness.fast_path_called:
        raise AssertionError(
            "Adaptive fast-path was not invoked during no-change refresh."
        )
    if harness.full_path_touched:
        raise AssertionError(
            "Full refresh path should not run after fast-path short-circuit."
        )
