from __future__ import annotations

import copy
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np
from matplotlib.figure import Figure


class _PatchedCompareValidationHarness:
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
        frame = getattr(self, "tab_compare", None)
        if frame is None:
            return
        compare_state = _normalize_compare_tab_settings(settings.get("compare_tab"))
        settings["compare_tab"] = compare_state

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        controls = ttk.LabelFrame(frame, text="Profile Selection")
        controls.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        for col in range(10):
            controls.grid_columnconfigure(col, weight=1 if col in {1, 4, 9} else 0)

        self.compare_profile_a_var = tk.StringVar(
            value=str(compare_state.get("profile_a_name") or "")
        )
        self.compare_profile_b_var = tk.StringVar(
            value=str(compare_state.get("profile_b_name") or "")
        )
        self.compare_lock_x_axis_var = tk.BooleanVar(
            value=bool(compare_state.get("lock_x_axis", True))
        )
        self.compare_yield_mode_var = tk.StringVar(
            value=str(compare_state.get("yield_basis_mode", "auto") or "auto")
        )
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

        ttk.Label(controls, text="Profile A").grid(
            row=0, column=0, sticky="w", padx=(8, 4), pady=6
        )
        self._compare_profile_a_combo = ttk.Combobox(
            controls, textvariable=self.compare_profile_a_var, state="readonly"
        )
        self._compare_profile_a_combo.grid(
            row=0, column=1, sticky="ew", padx=(0, 8), pady=6
        )
        ttk.Label(controls, text="Profile B").grid(
            row=0, column=3, sticky="w", padx=(4, 4), pady=6
        )
        self._compare_profile_b_combo = ttk.Combobox(
            controls, textvariable=self.compare_profile_b_var, state="readonly"
        )
        self._compare_profile_b_combo.grid(
            row=0, column=4, sticky="ew", padx=(0, 8), pady=6
        )

        _ui_button(
            controls,
            text="Load",
            command=self._compare_load_selected_profiles,
        ).grid(row=0, column=6, sticky="ew", padx=(4, 4), pady=6)
        _ui_button(
            controls,
            text="Swap",
            command=self._compare_swap_profiles,
        ).grid(row=0, column=7, sticky="ew", padx=(0, 4), pady=6)
        _ui_button(
            controls,
            text="Refresh Profiles",
            command=self._compare_refresh_profile_choices,
        ).grid(row=0, column=8, sticky="ew", padx=(0, 8), pady=6)
        _ui_checkbutton(
            controls,
            text="Lock X-axis",
            variable=self.compare_lock_x_axis_var,
            command=lambda: (
                self._compare_apply_locked_x_axis(),
                self._compare_persist_state(),
            ),
        ).grid(row=0, column=9, sticky="e", padx=(0, 8), pady=6)

        plot_shell = ttk.Frame(frame)
        plot_shell.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
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

        bottom = ttk.Frame(frame)
        bottom.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 8))
        bottom.grid_rowconfigure(1, weight=1)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        table_box = ttk.LabelFrame(bottom, text="Per-Cycle Uptake Comparison")
        table_box.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 8))
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
        headings = {
            "cycle": "Cycle",
            "uptake_a_g": "Uptake A (g)",
            "uptake_b_g": "Uptake B (g)",
            "delta_g": "Delta (B-A) (g)",
            "cum_a_g": "Cumulative A (g)",
            "cum_b_g": "Cumulative B (g)",
            "cum_delta_g": "Cumulative Delta (g)",
        }
        for col in self._compare_cycle_columns:
            self._compare_cycle_tree.heading(col, text=headings.get(col, col))
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
        self._compare_cycle_tree.configure(yscrollcommand=cycle_scroll.set)

        action_row = ttk.Frame(table_box)
        action_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(6, 4))
        action_row.grid_columnconfigure(0, weight=1)
        _ui_button(
            action_row,
            text="Export CSV",
            command=self._compare_export_cycle_table_csv,
        ).grid(row=0, column=1, sticky="e")

        yield_box = ttk.LabelFrame(bottom, text="Yield Comparison")
        yield_box.grid(row=0, column=1, sticky="nsew")
        for col in range(2):
            yield_box.grid_columnconfigure(col, weight=1 if col == 1 else 0)

        row_idx = 0
        ttk.Label(yield_box, text="Yield Basis").grid(
            row=row_idx, column=0, sticky="w", padx=6, pady=4
        )
        ttk.Combobox(
            yield_box,
            textvariable=self.compare_yield_mode_var,
            values=("auto", "override"),
            state="readonly",
            width=14,
        ).grid(row=row_idx, column=1, sticky="ew", padx=6, pady=4)
        row_idx += 1
        ttk.Label(yield_box, text="Isolated Mass A (g)").grid(
            row=row_idx, column=0, sticky="w", padx=6, pady=4
        )
        ttk.Entry(yield_box, textvariable=self.compare_isolated_mass_a_var).grid(
            row=row_idx, column=1, sticky="ew", padx=6, pady=4
        )
        row_idx += 1
        ttk.Label(yield_box, text="Isolated Mass B (g)").grid(
            row=row_idx, column=0, sticky="w", padx=6, pady=4
        )
        ttk.Entry(yield_box, textvariable=self.compare_isolated_mass_b_var).grid(
            row=row_idx, column=1, sticky="ew", padx=6, pady=4
        )
        row_idx += 1
        override_frame = ttk.LabelFrame(yield_box, text="Override Basis (optional)")
        override_frame.grid(
            row=row_idx, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 6)
        )
        override_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(override_frame, text="Starting mass (g)").grid(
            row=0, column=0, sticky="w", padx=4, pady=3
        )
        ttk.Entry(
            override_frame, textvariable=self.compare_override_starting_mass_var
        ).grid(row=0, column=1, sticky="ew", padx=4, pady=3)
        ttk.Label(override_frame, text="Starting MW (g/mol)").grid(
            row=1, column=0, sticky="w", padx=4, pady=3
        )
        ttk.Entry(override_frame, textvariable=self.compare_override_mw_var).grid(
            row=1, column=1, sticky="ew", padx=4, pady=3
        )
        ttk.Label(override_frame, text="Stoich (mol gas/mol start)").grid(
            row=2, column=0, sticky="w", padx=4, pady=3
        )
        ttk.Entry(override_frame, textvariable=self.compare_override_stoich_var).grid(
            row=2, column=1, sticky="ew", padx=4, pady=3
        )
        ttk.Label(override_frame, text="Gas MW (g/mol)").grid(
            row=3, column=0, sticky="w", padx=4, pady=3
        )
        ttk.Entry(override_frame, textvariable=self.compare_override_gas_mw_var).grid(
            row=3, column=1, sticky="ew", padx=4, pady=3
        )
        row_idx += 1

        self._compare_yield_summary_var = tk.StringVar(
            value="Load profiles to compute yield."
        )
        ttk.Label(
            yield_box,
            textvariable=self._compare_yield_summary_var,
            justify="left",
            anchor="w",
            wraplength=340,
        ).grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=6, pady=(2, 6))

        diagnostics_box = ttk.LabelFrame(bottom, text="Load Diagnostics")
        diagnostics_box.grid(row=1, column=1, sticky="nsew", pady=(8, 0))
        diagnostics_box.grid_columnconfigure(0, weight=1)
        diagnostics_box.grid_rowconfigure(0, weight=1)
        self._compare_diagnostics_var = tk.StringVar(
            value="No compare load activity yet."
        )
        ttk.Label(
            diagnostics_box,
            textvariable=self._compare_diagnostics_var,
            justify="left",
            anchor="nw",
            wraplength=360,
        ).grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self._compare_cycle_table_rows: List[Dict[str, Any]] = []
        self._compare_resize_after_ids: Dict[str, Optional[str]] = {
            "A": None,
            "B": None,
        }
        self._compare_load_diagnostics_state: Dict[str, Any] = {
            "A": {},
            "B": {},
            "summary": "No compare load activity yet.",
        }
        self._compare_load_splash_window: Optional[tk.Toplevel] = None
        self._compare_load_splash_label: Optional[ttk.Label] = None
        self._compare_load_splash_detail_label: Optional[ttk.Label] = None
        self._compare_load_splash_progress_var: Optional[tk.DoubleVar] = None
        self._compare_load_splash_progress_label: Optional[ttk.Label] = None
        self._compare_load_splash_stage_key: str = "ready"
        self._compare_load_splash_started_at: Optional[float] = None
        self._compare_load_splash_detail_base: str = ""
        self._compare_load_splash_heartbeat_after_id: Optional[str] = None
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
                        self._compare_persist_state(),
                    ),
                )
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        self._compare_refresh_profile_choices()
        self._compare_refresh_cycle_table()
        self._compare_refresh_yield_summary()

    def _compare_update_side_diagnostics(
        self,
        side_key: str,
        *,
        profile_name: Optional[str] = None,
        dataset_path: Optional[str] = None,
        status: Optional[str] = None,
        detail: Optional[str] = None,
        cycle_count: Optional[int] = None,
        total_drop_g: Optional[float] = None,
        render_success: Optional[bool] = None,
    ) -> None:
        """Update one Compare-side diagnostics payload.

        Purpose:
            Persist side-specific load/render diagnostics in one mutable payload.
        Why:
            Compare load now handles A/B sides independently, so users need clear
            per-side diagnostics for dataset resolution, load state, and render state.
        Args:
            side_key: Compare side key ("A" or "B").
            profile_name: Optional selected profile name for this side.
            dataset_path: Optional resolved dataset path for this side.
            status: Optional side status text (for example, Loaded, Failed).
            detail: Optional side detail/error text.
            cycle_count: Optional rendered cycle count.
            total_drop_g: Optional rendered total uptake mass in grams.
            render_success: Optional rendered-success flag for summary reporting.
        Returns:
            None.
        Side Effects:
            Mutates `self._compare_load_diagnostics_state`.
        Exceptions:
            Invalid side keys are ignored.
        """
        if side_key not in {"A", "B"}:
            return
        state = dict(getattr(self, "_compare_load_diagnostics_state", {}) or {})
        side_payload = dict(state.get(side_key) or {})
        updates = {
            "profile_name": profile_name,
            "dataset_path": dataset_path,
            "status": status,
            "detail": detail,
            "cycle_count": cycle_count,
            "total_drop_g": total_drop_g,
            "render_success": render_success,
        }
        for key, value in updates.items():
            if value is not None:
                side_payload[key] = value
        state[side_key] = side_payload
        self._compare_load_diagnostics_state = state

    def _compare_refresh_diagnostics_panel(self) -> None:
        """Rebuild the Compare diagnostics text panel.

        Purpose:
            Render a user-facing diagnostics summary for the latest Compare load.
        Why:
            A/B loads can fail independently; diagnostics should expose side-level
            outcomes and resolved dataset sources without opening logs.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Updates `_compare_diagnostics_var` text in the Compare tab.
        Exceptions:
            Missing diagnostics variable is treated as no-op.
        """
        var = getattr(self, "_compare_diagnostics_var", None)
        if not isinstance(var, tk.StringVar):
            return
        state = dict(getattr(self, "_compare_load_diagnostics_state", {}) or {})
        summary = str(state.get("summary") or "No compare load activity yet.").strip()
        lines = [summary]
        for side_key in ("A", "B"):
            side_payload = dict(state.get(side_key) or {})
            profile_name = str(side_payload.get("profile_name") or "--").strip() or "--"
            status_text = str(side_payload.get("status") or "Idle").strip() or "Idle"
            detail_text = str(side_payload.get("detail") or "").strip()
            dataset_path = str(side_payload.get("dataset_path") or "").strip()
            cycle_count = side_payload.get("cycle_count")
            total_drop_g = self._compare_parse_float_entry(
                side_payload.get("total_drop_g")
            )
            lines.append("")
            lines.append(f"Profile {side_key}: {profile_name}")
            lines.append(f"Status: {status_text}")
            if detail_text:
                lines.append(f"Detail: {detail_text}")
            if dataset_path:
                lines.append(f"Dataset: {dataset_path}")
            if cycle_count is not None:
                lines.append(f"Cycles: {int(cycle_count)}")
            if total_drop_g is not None:
                lines.append(f"Total dP uptake: {float(total_drop_g):.4f} g")
        var.set("\n".join(lines))

    def _compare_show_load_splash(self, title: str) -> None:
        """Show the Compare load modal splash with determinate progress.

        Purpose:
            Present one modal splash while Compare profile load/render stages run.
        Why:
            Compare loads can perform profile I/O, cycle analysis, and redraw work;
            users need explicit stage feedback and a blocking in-progress surface.
        Args:
            title: Splash window title for the current compare load action.
        Returns:
            None.
        Side Effects:
            Creates or reuses splash widgets, resets progress/timer state, and
            acquires a local modal grab while load work is in progress.
        Exceptions:
            Widget/window-manager failures are handled best-effort.
        """
        window = getattr(self, "_compare_load_splash_window", None)
        if window is not None and bool(
            getattr(window, "winfo_exists", lambda: False)()
        ):
            try:
                window.title(title)
                window.deiconify()
                window.lift()
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            self._compare_update_load_splash(
                message="Preparing Compare load...",
                progress=5.0,
                stage_key="queued",
                detail="Initializing profile load pipeline",
                reset=True,
            )
            return

        window = tk.Toplevel(self)
        window.title(title)
        window.transient(self)
        window.resizable(False, False)
        window.protocol("WM_DELETE_WINDOW", lambda: None)
        container = ttk.Frame(window, padding=12)
        container.pack(fill="both", expand=True)
        label = ttk.Label(container, text="Preparing Compare load...", justify="left")
        label.pack(fill="x")
        detail_label = ttk.Label(
            container,
            text="",
            justify="left",
            anchor="w",
            wraplength=420,
        )
        detail_label.pack(fill="x", pady=(6, 6))
        progress_var = tk.DoubleVar(master=window, value=0.0)
        ttk.Progressbar(
            container,
            mode="determinate",
            length=320,
            maximum=100.0,
            variable=progress_var,
        ).pack(fill="x", pady=(10, 0))
        progress_label = ttk.Label(container, text="0%")
        progress_label.pack(anchor="e", pady=(6, 0))

        self._compare_load_splash_window = window
        self._compare_load_splash_label = label
        self._compare_load_splash_detail_label = detail_label
        self._compare_load_splash_progress_var = progress_var
        self._compare_load_splash_progress_label = progress_label
        self._compare_load_splash_stage_key = "queued"
        self._compare_load_splash_started_at = time.monotonic()
        self._compare_load_splash_detail_base = ""
        self._compare_load_splash_heartbeat_after_id = None
        try:
            window.update_idletasks()
            width = int(window.winfo_reqwidth())
            height = int(window.winfo_reqheight())
            pos_x = max(0, (int(window.winfo_screenwidth()) - width) // 2)
            pos_y = max(0, (int(window.winfo_screenheight()) - height) // 2)
            window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
            window.grab_set()
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        self._compare_update_load_splash(
            message="Preparing Compare load...",
            progress=5.0,
            stage_key="queued",
            detail="Initializing profile load pipeline",
            reset=True,
        )

    def _compare_resolve_load_splash_stage_key(
        self,
        *,
        message: Optional[str],
        stage_key: Optional[str],
    ) -> str:
        """Resolve one normalized Compare load splash stage key.

        Purpose:
            Normalize explicit or message-derived splash stage identifiers.
        Why:
            Stage normalization keeps heartbeat/progress behavior deterministic
            across compare load orchestration and side-level fallback paths.
        Args:
            message: Optional user-facing status message.
            stage_key: Optional explicit stage token.
        Returns:
            Canonical stage key string.
        Side Effects:
            None.
        Exceptions:
            Invalid values fall back to `queued`.
        """
        if isinstance(stage_key, str) and stage_key.strip():
            return stage_key.strip().lower().replace(" ", "_")
        text = str(message or "").strip().lower()
        if not text:
            return "queued"
        if "failed" in text:
            return "failed"
        if "ready" in text or "final" in text:
            return "ready"
        if "render" in text:
            return "render"
        if "table" in text or "yield" in text:
            return "refresh"
        if "load" in text:
            return "load"
        return "queued"

    def _compare_stop_load_splash_heartbeat(self) -> None:
        """Stop the Compare splash elapsed-time heartbeat timer.

        Purpose:
            Cancel scheduled splash timer callbacks during terminal states.
        Why:
            Splash teardown and ready/failed states must not leave orphan timers.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Cancels one scheduled `after` callback when present.
        Exceptions:
            Cancellation failures are ignored by design.
        """
        after_id = getattr(self, "_compare_load_splash_heartbeat_after_id", None)
        if after_id is None:
            return
        try:
            self.after_cancel(after_id)
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass
        self._compare_load_splash_heartbeat_after_id = None

    def _compare_start_load_splash_heartbeat(self) -> None:
        """Start the Compare splash elapsed-time heartbeat timer.

        Purpose:
            Keep splash detail text synchronized with live wall-clock elapsed time.
        Why:
            Profile I/O and rendering may take multiple seconds and should show
            visible in-progress activity.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Schedules recurring timer callbacks while splash is active.
        Exceptions:
            Missing or destroyed widgets short-circuit safely.
        """
        if getattr(self, "_compare_load_splash_heartbeat_after_id", None) is not None:
            return

        def _tick() -> None:
            """Update Compare splash elapsed detail text for one timer tick."""
            self._compare_load_splash_heartbeat_after_id = None
            window = getattr(self, "_compare_load_splash_window", None)
            if window is None:
                return
            try:
                if not window.winfo_exists():
                    return
            except Exception:
                return
            stage_key = str(
                getattr(self, "_compare_load_splash_stage_key", "queued") or "queued"
            )
            if stage_key in {"ready", "failed"}:
                return
            started_at = getattr(self, "_compare_load_splash_started_at", None)
            if not isinstance(started_at, (int, float)):
                started_at = time.monotonic()
                self._compare_load_splash_started_at = float(started_at)
            elapsed = max(0.0, time.monotonic() - float(started_at))
            elapsed_text = self._format_wall_clock_elapsed(elapsed)
            detail_base = str(
                getattr(self, "_compare_load_splash_detail_base", "") or ""
            ).strip()
            detail_text = (
                f"{detail_base} | Elapsed: {elapsed_text}"
                if detail_base
                else f"Elapsed: {elapsed_text}"
            )
            detail_label = getattr(self, "_compare_load_splash_detail_label", None)
            if detail_label is not None:
                try:
                    detail_label.configure(text=detail_text)
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
            try:
                self._compare_load_splash_heartbeat_after_id = self.after(100, _tick)
            except Exception:
                self._compare_load_splash_heartbeat_after_id = None

        _tick()

    def _compare_update_load_splash(
        self,
        *,
        message: Optional[str] = None,
        progress: Optional[float] = None,
        detail: Optional[str] = None,
        stage_key: Optional[str] = None,
        reset: bool = False,
    ) -> None:
        """Update Compare load splash text/progress with stage-aware semantics.

        Purpose:
            Mutate Compare splash labels and determinate progress for each stage.
        Why:
            Compare load orchestrates multiple side-level phases that must report
            deterministic, monotonic progress and stage detail.
        Args:
            message: Optional splash status text.
            progress: Optional progress value in the 0..100 range.
            detail: Optional detail text shown under status.
            stage_key: Optional explicit normalized stage key.
            reset: When True, reset elapsed/progress baseline before update.
        Returns:
            None.
        Side Effects:
            Updates splash widgets/state and starts/stops heartbeat timers.
        Exceptions:
            Widget update failures are suppressed best-effort.
        """
        window = getattr(self, "_compare_load_splash_window", None)
        if window is None or not bool(getattr(window, "winfo_exists", lambda: False)()):
            return
        progress_var = getattr(self, "_compare_load_splash_progress_var", None)
        current_value = 0.0
        if progress_var is not None:
            try:
                current_value = float(progress_var.get())
            except Exception:
                current_value = 0.0
        if not math.isfinite(current_value):
            current_value = 0.0
        if reset:
            current_value = 0.0
            self._compare_load_splash_started_at = time.monotonic()
            self._compare_load_splash_detail_base = ""
        if message is not None:
            label = getattr(self, "_compare_load_splash_label", None)
            if label is not None:
                try:
                    label.configure(text=str(message).strip() or "Working...")
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
        normalized_stage = self._compare_resolve_load_splash_stage_key(
            message=message,
            stage_key=stage_key,
        )
        self._compare_load_splash_stage_key = normalized_stage
        if detail is not None:
            self._compare_load_splash_detail_base = str(detail).strip()
        if progress is not None:
            try:
                candidate_value = max(0.0, min(100.0, float(progress)))
            except Exception:
                candidate_value = 0.0
            target_value = (
                candidate_value if reset else max(current_value, candidate_value)
            )
            if progress_var is not None:
                try:
                    progress_var.set(target_value)
                    current_value = float(target_value)
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
            progress_label = getattr(self, "_compare_load_splash_progress_label", None)
            if progress_label is not None:
                try:
                    progress_label.configure(text=f"{int(round(current_value))}%")
                except Exception:
                    # Best-effort guard; ignore failures to avoid interrupting the workflow.
                    pass
        detail_label = getattr(self, "_compare_load_splash_detail_label", None)
        detail_base = str(
            getattr(self, "_compare_load_splash_detail_base", "") or ""
        ).strip()
        started_at = getattr(self, "_compare_load_splash_started_at", None)
        if not isinstance(started_at, (int, float)):
            started_at = time.monotonic()
            self._compare_load_splash_started_at = float(started_at)
        elapsed_text = self._format_wall_clock_elapsed(
            max(0.0, time.monotonic() - float(started_at))
        )
        composed_detail = (
            f"{detail_base} | Elapsed: {elapsed_text}"
            if detail_base
            else f"Elapsed: {elapsed_text}"
        )
        if detail_label is not None:
            try:
                detail_label.configure(text=composed_detail)
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        if normalized_stage in {"ready", "failed"}:
            self._compare_stop_load_splash_heartbeat()
        else:
            self._compare_start_load_splash_heartbeat()
        try:
            window.update_idletasks()
            window.update()
        except Exception:
            # Best-effort guard; ignore failures to avoid interrupting the workflow.
            pass

    def _compare_hide_load_splash(self) -> None:
        """Hide and destroy the Compare load splash safely.

        Purpose:
            Tear down Compare splash UI and clear splash runtime references.
        Why:
            Compare load completion and failure paths must always release modal
            grabs and timer callbacks.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Stops heartbeat timers, releases modal grab, destroys splash widgets,
            and clears Compare splash state attributes.
        Exceptions:
            Teardown failures are handled best-effort.
        """
        self._compare_stop_load_splash_heartbeat()
        window = getattr(self, "_compare_load_splash_window", None)
        if window is not None:
            try:
                window.grab_release()
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
            try:
                window.destroy()
            except Exception:
                # Best-effort guard; ignore failures to avoid interrupting the workflow.
                pass
        self._compare_load_splash_window = None
        self._compare_load_splash_label = None
        self._compare_load_splash_detail_label = None
        self._compare_load_splash_progress_var = None
        self._compare_load_splash_progress_label = None
        self._compare_load_splash_stage_key = "ready"
        self._compare_load_splash_started_at = None
        self._compare_load_splash_detail_base = ""
        self._compare_load_splash_heartbeat_after_id = None

    def _compare_load_selected_profiles(self) -> None:
        """Load both selected profiles and refresh all Compare outputs.

        Purpose:
            Resolve selected profile names into renderable compare bundles.
        Why:
            Compare visual/table/yield outputs depend on loaded profile payloads.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Updates pane bundle caches, rerenders panes, refreshes tables/yields,
            and persists Compare settings.
        Exceptions:
            Missing/invalid profiles are handled per pane without aborting.
        """
        profile_a = str(self.compare_profile_a_var.get() or "").strip()
        profile_b = str(self.compare_profile_b_var.get() or "").strip()
        self._compare_refresh_profile_choices()
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
                ("A", profile_a, 22.0),
                ("B", profile_b, 40.0),
            ):
                panel = self._compare_panels.get(side_key) or {}
                if not profile_name:
                    panel["bundle"] = None
                    panel["cycle_rows"] = []
                    panel["total_drop"] = None
                    panel["load_error_message"] = "No profile selected."
                    panel["render_success"] = False
                    panel["render_error_message"] = "No profile selected."
                    self._compare_update_side_status(side_key, "No profile selected.")
                    self._compare_update_side_diagnostics(
                        side_key,
                        profile_name="",
                        status="Not selected",
                        detail="Select a saved profile and click Load.",
                        render_success=False,
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
                bundle = load_ctx.get("bundle")
                ui_status = str(
                    load_ctx.get("ui_status") or "Profile load failed."
                ).strip()
                panel["bundle"] = bundle if isinstance(bundle, dict) else None
                panel["cycle_rows"] = []
                panel["total_drop"] = None
                panel["load_error_message"] = ui_status
                panel["render_success"] = False
                panel["render_error_message"] = ui_status
                if panel["bundle"] is None:
                    self._compare_update_side_status(side_key, ui_status)
                self._compare_update_side_diagnostics(
                    side_key,
                    profile_name=str(load_ctx.get("profile_name") or profile_name),
                    dataset_path=str(load_ctx.get("dataset_path") or ""),
                    status=str(load_ctx.get("status_label") or "Load failed"),
                    detail=str(load_ctx.get("detail") or ""),
                    render_success=False,
                )
                self._compare_refresh_diagnostics_panel()

            for side_key, progress_value in (("A", 58.0), ("B", 76.0)):
                self._compare_update_load_splash(
                    message=f"Rendering Profile {side_key}...",
                    progress=progress_value,
                    stage_key=f"render_{side_key.lower()}",
                    detail=f"Building combined compare figure for side {side_key}.",
                )
                self._compare_render_profile_side(side_key, reason="load")
                panel = self._compare_panels.get(side_key) or {}
                cycle_count = int(len(panel.get("cycle_rows") or []))
                total_drop_value = self._compare_parse_float_entry(
                    panel.get("total_drop")
                )
                render_success = bool(panel.get("render_success", False))
                status_label = "Rendered" if render_success else "Render failed"
                detail_text = str(panel.get("render_error_message") or "").strip()
                self._compare_update_side_diagnostics(
                    side_key,
                    status=status_label,
                    detail=detail_text,
                    cycle_count=cycle_count,
                    total_drop_g=total_drop_value,
                    render_success=render_success,
                )
                self._compare_refresh_diagnostics_panel()

            self._compare_update_load_splash(
                message="Refreshing Compare table and yield summary...",
                progress=90.0,
                stage_key="refresh",
                detail="Updating per-cycle uptake rows and yield metrics.",
            )
            self._compare_apply_locked_x_axis()
            self._compare_refresh_cycle_table()
            self._compare_refresh_yield_summary()
            self._compare_persist_state()

            diagnostics_state = dict(
                getattr(self, "_compare_load_diagnostics_state", {}) or {}
            )
            rendered_count = sum(
                1
                for side_key in ("A", "B")
                if bool((diagnostics_state.get(side_key) or {}).get("render_success"))
            )
            if rendered_count == 2:
                summary = "Compare load completed: both profiles rendered successfully."
            elif rendered_count == 1:
                summary = (
                    "Compare load completed with partial success: one profile rendered."
                )
            else:
                summary = "Compare load completed with no successful profile renders."
            diagnostics_state["summary"] = summary
            self._compare_load_diagnostics_state = diagnostics_state
            self._compare_refresh_diagnostics_panel()
            self._compare_update_load_splash(
                message="Compare load complete.",
                progress=100.0,
                stage_key="ready",
                detail=summary,
            )
        finally:
            self._compare_hide_load_splash()

    def _compare_build_profile_bundle_from_state(
        self,
        *,
        profile_name: str,
        profile_path: Path,
        state: Mapping[str, Any],
        dataset_path: str,
    ) -> Optional[Dict[str, Any]]:
        """Build one normalized Compare bundle from profile state and dataset path.

        Purpose:
            Convert profile payload state into a compare-ready render bundle.
        Why:
            Compare and Ledger flows both need the same isolated bundle assembly.
        Args:
            profile_name: Saved profile name associated with the payload.
            profile_path: Path to the profile JSON document.
            state: Deserialized profile workspace state.
            dataset_path: Resolved dataset path for profile data loading.
        Returns:
            Compare bundle dict, or None when data context prep fails.
        Side Effects:
            Reads workbook sheets while preparing data context.
        Exceptions:
            Invalid state/data content returns None.
        """
        plot_settings = dict(state.get("plot_settings") or {})
        data_bundle = self._compare_build_profile_data_context(
            dataset_path=dataset_path,
            state=state,
            plot_settings=plot_settings,
        )
        if data_bundle is None:
            return None
        default_args = self._collect_plot_args()
        args_keys = (
            "min_time",
            "max_time",
            "min_y",
            "max_y",
            "twin_y_min",
            "twin_y_max",
            "deriv_y_min",
            "deriv_y_max",
            "auto_time_ticks",
            "auto_y_ticks",
            "auto_temp_ticks",
            "auto_deriv_ticks",
            "title_text",
            "suptitle_text",
            "x_major_tick",
            "x_minor_tick",
            "y_major_tick",
            "y_minor_tick",
            "temp_major_tick",
            "temp_minor_tick",
            "deriv_major_tick",
            "deriv_minor_tick",
            "enable_temp_axis",
            "enable_deriv_axis",
            "min_cycle_drop",
            "peak_prominence",
            "peak_distance",
            "peak_width",
            "show_cycle_markers_on_core_plots",
            "show_cycle_legend_on_core_plots",
            "include_moles_in_core_plot_legend",
        )
        resolved_args = list(default_args)
        for idx, key in enumerate(args_keys):
            if key in plot_settings:
                resolved_args[idx] = plot_settings.get(key)
        return {
            "profile_name": str(profile_name or "").strip(),
            "profile_path": str(profile_path),
            "dataset_path": str(dataset_path),
            "state": dict(state or {}),
            "plot_settings": plot_settings,
            "reaction_basis": dict(state.get("reaction_basis") or {}),
            "plot_elements": copy.deepcopy(state.get("plot_elements") or {}),
            "layout_profiles": copy.deepcopy(state.get("layout_profiles") or {}),
            "data_ctx": data_bundle["data_ctx"],
            "df_reference": data_bundle["df_reference"],
            "sheet_key": tuple(data_bundle.get("sheet_key") or ()),
            "columns_key": tuple(data_bundle.get("columns_key") or ()),
            "prep_signature": tuple(data_bundle.get("prep_signature") or ()),
            "multi_sheet": bool(data_bundle.get("multi_sheet")),
            "args": tuple(resolved_args),
            "cycle_rows": [],
            "total_drop": None,
        }

    def _compare_load_profile_bundle_for_side(
        self,
        side_key: str,
        profile_name: str,
        *,
        prompt_relink: bool,
    ) -> Dict[str, Any]:
        """Load one Compare side bundle with explicit status and dataset recovery.

        Purpose:
            Resolve one side's profile into a compare bundle plus diagnostics.
        Why:
            Compare loads must tolerate side-level failures and keep loading the
            other side while reporting clear reasons in diagnostics.
        Args:
            side_key: Compare side key ("A" or "B").
            profile_name: Saved profile name selected for this side.
            prompt_relink: When True, prompt for dataset relink if path is missing.
        Returns:
            Dict containing bundle/status/detail/profile-path diagnostics.
        Side Effects:
            Reads profile/data files and may show relink dialogs.
        Exceptions:
            Failures are captured in returned status payload.
        """
        resolved_name = str(profile_name or "").strip()
        result: Dict[str, Any] = {
            "profile_name": resolved_name,
            "dataset_path": "",
            "status_label": "Load failed",
            "status": "failed",
            "detail": "",
            "ui_status": "Profile load failed.",
            "bundle": None,
        }
        if not resolved_name:
            result["status_label"] = "Not selected"
            result["status"] = "not_selected"
            result["detail"] = "No profile selected for this side."
            result["ui_status"] = "No profile selected."
            return result

        profile_path = self._profile_path(resolved_name)
        if profile_path is None or not profile_path.exists():
            result["detail"] = f"Profile '{resolved_name}' was not found."
            result["ui_status"] = f"Profile {side_key}: profile not found."
            return result

        doc = self._read_profile_document(profile_path)
        if not isinstance(doc, dict):
            result["detail"] = f"Profile '{resolved_name}' could not be read."
            result["ui_status"] = f"Profile {side_key}: profile read failed."
            return result

        state = self._deserialize_workspace_state(doc.get("payload") or {})
        if not state:
            result["detail"] = f"Profile '{resolved_name}' payload is invalid."
            result["ui_status"] = f"Profile {side_key}: profile payload invalid."
            return result

        dataset_path = str(state.get("dataset_path") or "").strip()
        if not dataset_path or not os.path.exists(dataset_path):
            if prompt_relink:
                self._compare_update_load_splash(
                    message=f"Relinking Profile {side_key} dataset...",
                    stage_key="relink_dataset",
                    detail=f"Waiting for dataset relink for '{resolved_name}'.",
                )
                splash_window = getattr(self, "_compare_load_splash_window", None)
                # Release the splash grab while file dialogs are open so native
                # picker windows can receive focus and input.
                if splash_window is not None:
                    try:
                        splash_window.grab_release()
                    except Exception:
                        # Best-effort guard; ignore failures to avoid interrupting workflow.
                        pass
                try:
                    dataset_path = str(
                        self._resolve_profile_dataset_path(dataset_path) or ""
                    ).strip()
                finally:
                    if splash_window is not None and bool(
                        getattr(splash_window, "winfo_exists", lambda: False)()
                    ):
                        try:
                            splash_window.grab_set()
                        except Exception:
                            # Best-effort guard; ignore failures to avoid interrupting workflow.
                            pass
            if not dataset_path or not os.path.exists(dataset_path):
                result["detail"] = (
                    f"Dataset path could not be resolved for profile '{resolved_name}'."
                )
                result["ui_status"] = f"Profile {side_key}: dataset path unresolved."
                return result

        bundle = self._compare_build_profile_bundle_from_state(
            profile_name=resolved_name,
            profile_path=profile_path,
            state=state,
            dataset_path=dataset_path,
        )
        if not isinstance(bundle, dict):
            result["detail"] = (
                f"Data preparation failed for profile '{resolved_name}' dataset."
            )
            result["ui_status"] = f"Profile {side_key}: data preparation failed."
            return result

        result["dataset_path"] = dataset_path
        result["status_label"] = "Loaded"
        result["status"] = "loaded"
        result["detail"] = "Profile loaded successfully."
        result["ui_status"] = f"Profile {side_key}: loaded '{resolved_name}'."
        result["bundle"] = bundle
        return result

    def _compare_load_profile_bundle(
        self, profile_name: str
    ) -> Optional[Dict[str, Any]]:
        """Load and normalize one profile payload for Compare rendering.

        Purpose:
            Build an isolated compare bundle from a saved profile.
        Why:
            Compare rendering should not mutate active workspace state.
        Args:
            profile_name: Saved profile name to load.
        Returns:
            Compare bundle dict, or None when loading/prep fails.
        Side Effects:
            Reads profile file and source dataset from disk.
        Exceptions:
            Invalid profile/state/data paths return None.
        """
        load_ctx = self._compare_load_profile_bundle_for_side(
            "A",
            profile_name,
            prompt_relink=False,
        )
        bundle = load_ctx.get("bundle")
        return dict(bundle) if isinstance(bundle, dict) else None

    def _compare_build_render_context_from_bundle(
        self, bundle: Dict[str, Any]
    ) -> Tuple[RenderContext, List[Dict[str, Any]], Optional[float]]:
        """Build render context and cycle-transfer payload for one compare bundle.

        Purpose:
            Produce full render context needed by combined display rendering.
        Why:
            Compare panes need isolated contexts derived from each profile bundle.
        Args:
            bundle: Compare profile bundle.
        Returns:
            Tuple of render context, cycle-transfer rows, and total uptake value.
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
        snapshot = self._compare_cycle_snapshot_from_plot_settings(plot_settings)
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
        args = tuple(bundle.get("args") or ())
        show_cycle_markers = bool(args[-3]) if len(args) >= 3 else False
        show_cycle_legend = bool(args[-2]) if len(args) >= 2 else False
        include_moles = bool(args[-1]) if len(args) >= 1 else False
        cycle_overlay = (overlay_ctx or {}).get("cycle_overlay")
        overlay_ctx = dict(overlay_ctx or {})
        overlay_ctx["markers"] = cycle_overlay if show_cycle_markers else None
        overlay_ctx["cycle_legend"] = cycle_overlay if show_cycle_legend else None
        overlay_ctx["moles_summary"] = (
            overlay_ctx.get("moles_summary") if include_moles else None
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
        cycle_rows: List[Dict[str, Any]] = []
        total_drop = None
        if isinstance(cycle_overlay, dict):
            payload = cycle_overlay.get("payload") or {}
            cycle_rows = list(payload.get("cycle_transfer") or [])
            try:
                total_drop = float(cycle_overlay.get("total_drop", 0.0))
            except Exception:
                total_drop = None
        return render_ctx, cycle_rows, total_drop

    def _compare_render_profile_side(self, side_key: str, *, reason: str = "") -> None:
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
            panel["render_success"] = False
            panel["render_error_message"] = placeholder_text
            self._compare_update_side_status(side_key, placeholder_text)
            return

        try:
            render_ctx, cycle_rows, total_drop = (
                self._compare_build_render_context_from_bundle(bundle)
            )
        except Exception as exc:
            panel["cycle_rows"] = []
            panel["total_drop"] = None
            panel["render_success"] = False
            panel["render_error_message"] = f"Cycle prep failed: {type(exc).__name__}"
            self._compare_update_side_status(
                side_key, f"Cycle prep failed: {type(exc).__name__}"
            )
            return

        fig_size = self._compare_resolve_figsize_for_panel(side_key)
        prior_df = getattr(self, "df", None)
        prior_combined_state = getattr(self, "_combined_plot_state", None)
        prior_combined_layout_state = getattr(self, "_combined_layout_state", None)
        prior_combined_layout_dirty = getattr(self, "_combined_layout_dirty", False)
        prior_layout_profiles = settings.get("layout_profiles")
        sentinel = object()
        overridden_keys: Dict[str, Any] = {}

        try:
            # Combined rendering still consults active settings for style/layout;
            # temporarily apply profile-local settings so pane output matches profile.
            profile_plot_settings = dict(bundle.get("plot_settings") or {})
            for key, value in profile_plot_settings.items():
                overridden_keys[key] = settings.get(key, sentinel)
                settings[key] = copy.deepcopy(value)

            # Compare intentionally suppresses plot elements/annotations so side
            # visuals stay focused on traces and cycle overlays only.
            merged_elements = (
                copy.deepcopy(settings.get("plot_elements"))
                if isinstance(settings.get("plot_elements"), dict)
                else {}
            )
            merged_elements["fig_combined_triple_axis"] = []
            overridden_keys["plot_elements"] = settings.get("plot_elements", sentinel)
            settings["plot_elements"] = merged_elements

            profile_layouts = bundle.get("layout_profiles") or {}
            if isinstance(profile_layouts, dict):
                merged_layouts = (
                    copy.deepcopy(prior_layout_profiles)
                    if isinstance(prior_layout_profiles, dict)
                    else {}
                )
                merged_layouts["fig_combined_triple_axis"] = copy.deepcopy(
                    profile_layouts.get("fig_combined_triple_axis", {})
                )
                settings["layout_profiles"] = merged_layouts

            self.df = bundle.get("df_reference")
            fig = self._build_combined_triple_axis_from_state(
                args=tuple(bundle.get("args") or ()),
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
            panel["render_success"] = False
            if not str(panel.get("render_error_message") or "").strip():
                panel["render_error_message"] = "Combined plot unavailable."
        else:
            panel["cycle_rows"] = list(cycle_rows or [])
            panel["total_drop"] = total_drop
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

    def _compare_cycle_mass_value(self, row: Mapping[str, Any]) -> Optional[float]:
        """Extract one per-cycle uptake mass value from a cycle-transfer row.

        Purpose:
            Normalize per-cycle uptake fields from mixed cycle payload schemas.
        Why:
            Compare tables must support legacy and current cycle-transfer key names
            across profiles generated by different app versions.
        Args:
            row: One cycle-transfer row mapping.
        Returns:
            Optional float mass in grams for the cycle uptake.
        Side Effects:
            None.
        Exceptions:
            Invalid values return None.
        """
        for key in (
            "selected_mass_g",
            "selected_mass",
            "co2_added_g",
            "co2_added_mass_g",
            "co2_mass_g",
            "co2_g",
            "cycle_mass_g",
            "cycle_co2_mass_g",
        ):
            value = self._compare_parse_float_entry(row.get(key))
            if value is not None:
                return float(value)
        return None

    def _compare_cycle_cumulative_mass_value(
        self, row: Mapping[str, Any]
    ) -> Optional[float]:
        """Extract one cumulative uptake mass value from a cycle-transfer row.

        Purpose:
            Normalize cumulative uptake fields from cycle payload variants.
        Why:
            Table alignment and delta math need one consistent cumulative basis.
        Args:
            row: One cycle-transfer row mapping.
        Returns:
            Optional float cumulative mass in grams.
        Side Effects:
            None.
        Exceptions:
            Invalid values return None.
        """
        for key in (
            "cumulative_co2_mass_g",
            "cumulative_co2_added_mass_g",
            "cumulative_co2_added_g",
            "cumulative_co2_g",
            "cumulative_added_g",
            "cumulative_mass_g",
        ):
            value = self._compare_parse_float_entry(row.get(key))
            if value is not None:
                return float(value)
        return None

    def _compare_refresh_cycle_table(self) -> None:
        """Rebuild the Compare per-cycle table with deltas and summary rows.

        Purpose:
            Render aligned cycle uptake metrics for profile A/B.
        Why:
            Users need cycle-by-cycle and cumulative deltas to quantify run
            differences beyond visual plot inspection.
        Args:
            None.
        Returns:
            None.
        Side Effects:
            Clears/repopulates the Compare treeview and updates the cached rows
            used by CSV export.
        Exceptions:
            Missing panes/treeview are treated as no-op.
        """
        tree = getattr(self, "_compare_cycle_tree", None)
        if tree is None:
            return
        panel_a = self._compare_panels.get("A") or {}
        panel_b = self._compare_panels.get("B") or {}
        rows_a = list(panel_a.get("cycle_rows") or [])
        rows_b = list(panel_b.get("cycle_rows") or [])

        def _cycle_row_index(row: Mapping[str, Any], fallback_index: int) -> int:
            """Resolve one deterministic cycle index from mixed row schemas."""
            for key in ("cycle_id", "cycle", "cycle_number", "cycle_index", "index"):
                raw_value = row.get(key)
                if raw_value in (None, ""):
                    continue
                try:
                    return max(1, int(raw_value))
                except Exception:
                    continue
            return int(max(1, fallback_index))

        map_a: Dict[int, Dict[str, Any]] = {}
        map_b: Dict[int, Dict[str, Any]] = {}
        for idx, row in enumerate(rows_a, start=1):
            if not isinstance(row, Mapping):
                continue
            cycle_id = _cycle_row_index(row, idx)
            if cycle_id not in map_a:
                map_a[cycle_id] = dict(row)
        for idx, row in enumerate(rows_b, start=1):
            if not isinstance(row, Mapping):
                continue
            cycle_id = _cycle_row_index(row, idx)
            if cycle_id not in map_b:
                map_b[cycle_id] = dict(row)

        all_cycles = sorted(set(map_a.keys()) | set(map_b.keys()))
        for item_id in tree.get_children():
            tree.delete(item_id)

        export_rows: List[Dict[str, Any]] = []
        sum_uptake_a = 0.0
        sum_uptake_b = 0.0
        last_cum_a = 0.0
        last_cum_b = 0.0
        valid_a = False
        valid_b = False

        for cycle_id in all_cycles:
            row_a = map_a.get(cycle_id, {})
            row_b = map_b.get(cycle_id, {})
            uptake_a = self._compare_cycle_mass_value(row_a)
            uptake_b = self._compare_cycle_mass_value(row_b)
            cum_a = self._compare_cycle_cumulative_mass_value(row_a)
            cum_b = self._compare_cycle_cumulative_mass_value(row_b)

            prior_cum_a = float(last_cum_a) if valid_a else 0.0
            prior_cum_b = float(last_cum_b) if valid_b else 0.0
            # Some legacy payloads only persist cumulative uptake. Rebuild the
            # per-cycle uptake from cumulative deltas when direct values are absent.
            if uptake_a is None and cum_a is not None:
                uptake_a = float(cum_a) - prior_cum_a
            if uptake_b is None and cum_b is not None:
                uptake_b = float(cum_b) - prior_cum_b

            if uptake_a is not None:
                sum_uptake_a += float(uptake_a)
            if uptake_b is not None:
                sum_uptake_b += float(uptake_b)

            if cum_a is None:
                cum_a = (last_cum_a + uptake_a) if uptake_a is not None else None
            if cum_b is None:
                cum_b = (last_cum_b + uptake_b) if uptake_b is not None else None
            if cum_a is not None:
                last_cum_a = float(cum_a)
                valid_a = True
            if cum_b is not None:
                last_cum_b = float(cum_b)
                valid_b = True

            delta = None
            if uptake_a is not None and uptake_b is not None:
                delta = float(uptake_b) - float(uptake_a)
            cum_delta = None
            if cum_a is not None and cum_b is not None:
                cum_delta = float(cum_b) - float(cum_a)

            def _fmt(value: Optional[float]) -> str:
                return "" if value is None else f"{float(value):.4f}"

            row_payload = {
                "cycle": cycle_id,
                "uptake_a_g": uptake_a,
                "uptake_b_g": uptake_b,
                "delta_g": delta,
                "cum_a_g": cum_a,
                "cum_b_g": cum_b,
                "cum_delta_g": cum_delta,
            }
            export_rows.append(row_payload)
            tree.insert(
                "",
                "end",
                values=(
                    str(cycle_id),
                    _fmt(uptake_a),
                    _fmt(uptake_b),
                    _fmt(delta),
                    _fmt(cum_a),
                    _fmt(cum_b),
                    _fmt(cum_delta),
                ),
            )

        total_delta = sum_uptake_b - sum_uptake_a
        cum_total_delta = (last_cum_b - last_cum_a) if (valid_a or valid_b) else None
        tree.insert(
            "",
            "end",
            values=(
                "Totals",
                f"{sum_uptake_a:.4f}" if rows_a else "",
                f"{sum_uptake_b:.4f}" if rows_b else "",
                f"{total_delta:+.4f}" if (rows_a and rows_b) else "",
                f"{last_cum_a:.4f}" if valid_a else "",
                f"{last_cum_b:.4f}" if valid_b else "",
                (
                    f"{cum_total_delta:+.4f}"
                    if cum_total_delta is not None and valid_a and valid_b
                    else ""
                ),
            ),
        )
        mean_a = (sum_uptake_a / len(rows_a)) if rows_a else None
        mean_b = (sum_uptake_b / len(rows_b)) if rows_b else None
        max_a = (
            max(
                (
                    self._compare_cycle_mass_value(row)
                    for row in rows_a
                    if self._compare_cycle_mass_value(row) is not None
                ),
                default=None,
            )
            if rows_a
            else None
        )
        max_b = (
            max(
                (
                    self._compare_cycle_mass_value(row)
                    for row in rows_b
                    if self._compare_cycle_mass_value(row) is not None
                ),
                default=None,
            )
            if rows_b
            else None
        )
        tree.insert(
            "",
            "end",
            values=(
                "Mean Uptake",
                "" if mean_a is None else f"{mean_a:.4f}",
                "" if mean_b is None else f"{mean_b:.4f}",
                (
                    ""
                    if mean_a is None or mean_b is None
                    else f"{(mean_b - mean_a):+.4f}"
                ),
                "",
                "",
                "",
            ),
        )
        tree.insert(
            "",
            "end",
            values=(
                "Max Uptake",
                "" if max_a is None else f"{float(max_a):.4f}",
                "" if max_b is None else f"{float(max_b):.4f}",
                (
                    ""
                    if max_a is None or max_b is None
                    else f"{(float(max_b) - float(max_a)):+.4f}"
                ),
                "",
                "",
                "",
            ),
        )
        tree.insert(
            "",
            "end",
            values=("Cycle Count", str(len(rows_a)), str(len(rows_b)), "", "", "", ""),
        )
        self._compare_cycle_table_rows = export_rows
