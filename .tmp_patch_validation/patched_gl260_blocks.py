# ruff: noqa: F821
from __future__ import annotations
import importlib
import os
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def _evaluate_rust_backend_capability_with_probe_preference(
    backend: Any,
) -> Tuple[Any, Dict[str, Any], str]:
    """Evaluate Rust capability using extension-first probe selection.

    Purpose:
        Produce capability payloads from the most accurate import surface while
        preserving a compatibility fallback path.
    Why:
        Extension-first probing avoids false missing-kernel states after rebuilds,
        but package fallback preserves compatibility if extension probing fails.
    Inputs:
        backend: Imported Rust backend package/module candidate.
    Outputs:
        Tuple `(active_backend, capability_payload, probe_source)`.
    Side Effects:
        May import the extension submodule and updates selected backend handle.
    Exceptions:
        Capability evaluator exceptions are handled by
        `_evaluate_rust_backend_capability`.
    """
    probe_backend, probe_source = _resolve_rust_backend_capability_probe_module(backend)
    capability_payload = _evaluate_rust_backend_capability(probe_backend)
    if (
        probe_backend is not backend
        and str(capability_payload.get("state") or "").strip().lower() == "deprecated"
    ):
        # Keep one compatibility fallback to package-level probing so legacy
        # environments remain usable if submodule probing is unavailable.
        fallback_payload = _evaluate_rust_backend_capability(backend)
        if str(fallback_payload.get("state") or "").strip().lower() == "ready":
            return backend, fallback_payload, "package_compat_fallback"
    return probe_backend, capability_payload, probe_source


def _invalidate_rust_backend_cache() -> None:
    """Reset cached Rust backend module state.

    Purpose:
        Force the next backend access to re-attempt module import.
    Why:
        Install/build actions can make the module available during runtime; cache
        invalidation ensures the app sees that update immediately.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Clears module import cache variables and purges Rust package/submodule
        entries from `sys.modules`.
    Exceptions:
        None.
    """
    global _RUST_BACKEND_MODULE
    global _RUST_BACKEND_IMPORT_ERROR
    global _RUST_BACKEND_IMPORT_ATTEMPTED
    global _RUST_BACKEND_ACTIVE_IDENTITY_KEY
    _RUST_BACKEND_MODULE = None
    _RUST_BACKEND_IMPORT_ERROR = None
    _RUST_BACKEND_IMPORT_ATTEMPTED = False
    _RUST_BACKEND_ACTIVE_IDENTITY_KEY = ""
    _purge_rust_backend_module_import_cache()
    _set_rust_backend_capability_status(None)


def _load_rust_backend(force_reload: bool = False, *, enforce_identity: bool = True):
    """Load and cache the optional Rust backend extension module.

    Purpose:
        Centralize import and cache behavior for the Rust acceleration module.
    Why:
        Repeated import attempts on hot paths add overhead and complicate fallback
        behavior; this helper provides a single cache-aware access point.
    Inputs:
        force_reload: When True, clear cache and re-import the module.
        enforce_identity: When True, fail closed when active module identity
            mismatches the startup/repair-validated identity for this session.
    Outputs:
        Imported module object, or None when unavailable/disabled.
    Side Effects:
        Updates module import cache and error tracking globals; records session
        no-GIL mismatch state when extension import re-enables the GIL.
    Exceptions:
        Import failures are captured and returned as None (no raise).
    """
    global _RUST_BACKEND_MODULE
    global _RUST_BACKEND_IMPORT_ERROR
    global _RUST_BACKEND_IMPORT_ATTEMPTED
    global _RUST_BACKEND_GIL_REENABLE_DETECTED

    if not _is_rust_backend_enabled():
        return None
    if force_reload:
        _invalidate_rust_backend_cache()
    if _RUST_BACKEND_GIL_REENABLE_DETECTED:
        _RUST_BACKEND_MODULE = None
        _RUST_BACKEND_IMPORT_ATTEMPTED = True
        _RUST_BACKEND_IMPORT_ERROR = RuntimeError(
            f"{_RUST_BACKEND_GIL_MISMATCH_PREFIX} Rust backend import previously "
            "re-enabled the GIL in this process; restart is required before Rust "
            "acceleration can be used again."
        )
        _set_rust_backend_capability_status(None)
        return None
    if _RUST_BACKEND_IMPORT_ATTEMPTED:
        if _RUST_BACKEND_MODULE is not None:
            capability_payload = _snapshot_rust_backend_capability_status()
            if not capability_payload:
                (
                    _RUST_BACKEND_MODULE,
                    capability_payload,
                    _,
                ) = _evaluate_rust_backend_capability_with_probe_preference(
                    _RUST_BACKEND_MODULE
                )
                _set_rust_backend_capability_status(capability_payload)
            elif (
                str(capability_payload.get("state") or "").strip().lower()
                == "deprecated"
            ):
                (
                    _RUST_BACKEND_MODULE,
                    capability_payload,
                    _,
                ) = _evaluate_rust_backend_capability_with_probe_preference(
                    _RUST_BACKEND_MODULE
                )
                _set_rust_backend_capability_status(capability_payload)
            if (
                str(capability_payload.get("state") or "").strip().lower()
                == "deprecated"
            ):
                detail_text = str(capability_payload.get("details") or "").strip()
                reason_text = str(
                    capability_payload.get("reason") or "deprecated"
                ).strip()
                _RUST_BACKEND_MODULE = None
                _RUST_BACKEND_IMPORT_ERROR = RuntimeError(
                    f"{_RUST_BACKEND_DEPRECATED_PREFIX}{reason_text}"
                    + (f" ({detail_text})" if detail_text else "")
                )
                return None
            active_key = str(capability_payload.get("identity_key") or "").strip()
            if enforce_identity and not _is_rust_backend_identity_consistent(
                active_key
            ):
                expected_key = str(_RUST_BACKEND_EXPECTED_IDENTITY_KEY or "").strip()
                _RUST_BACKEND_MODULE = None
                _RUST_BACKEND_IMPORT_ERROR = RuntimeError(
                    f"{_RUST_BACKEND_IDENTITY_MISMATCH_PREFIX}expected={expected_key} active={active_key}"
                )
                return None
        return _RUST_BACKEND_MODULE
    _RUST_BACKEND_IMPORT_ATTEMPTED = True
    gil_before_import = _current_gil_status()
    try:
        imported_backend = importlib.import_module(_RUST_BACKEND_MODULE_NAME)
        gil_after_import = _note_gil_reenable(
            _RUST_BACKEND_MODULE_NAME, gil_before_import
        )
        if gil_before_import is False and gil_after_import is True:
            _RUST_BACKEND_MODULE = None
            _RUST_BACKEND_GIL_REENABLE_DETECTED = True
            _RUST_BACKEND_IMPORT_ERROR = RuntimeError(
                f"{_RUST_BACKEND_GIL_MISMATCH_PREFIX} Importing "
                f"'{_RUST_BACKEND_MODULE_NAME}' re-enabled the GIL on a "
                "free-threaded runtime."
            )
            _set_rust_backend_capability_status(None)
            return None
        (
            _RUST_BACKEND_MODULE,
            capability_payload,
            _,
        ) = _evaluate_rust_backend_capability_with_probe_preference(imported_backend)
        _set_rust_backend_capability_status(capability_payload)
        if str(capability_payload.get("state") or "").strip().lower() == "deprecated":
            detail_text = str(capability_payload.get("details") or "").strip()
            reason_text = str(capability_payload.get("reason") or "deprecated").strip()
            _RUST_BACKEND_MODULE = None
            _RUST_BACKEND_IMPORT_ERROR = RuntimeError(
                f"{_RUST_BACKEND_DEPRECATED_PREFIX}{reason_text}"
                + (f" ({detail_text})" if detail_text else "")
            )
            return None
        active_key = str(capability_payload.get("identity_key") or "").strip()
        if enforce_identity and not _is_rust_backend_identity_consistent(active_key):
            expected_key = str(_RUST_BACKEND_EXPECTED_IDENTITY_KEY or "").strip()
            _RUST_BACKEND_MODULE = None
            _RUST_BACKEND_IMPORT_ERROR = RuntimeError(
                f"{_RUST_BACKEND_IDENTITY_MISMATCH_PREFIX}expected={expected_key} active={active_key}"
            )
            return None
        _RUST_BACKEND_IMPORT_ERROR = None
        if _is_rust_backend_identity_consistent(active_key):
            _record_rust_backend_ready_for_current_runtime(persist=False)
    except Exception as exc:
        _RUST_BACKEND_MODULE = None
        _RUST_BACKEND_IMPORT_ERROR = exc
        _set_rust_backend_capability_status(None)
    return _RUST_BACKEND_MODULE


def _purge_rust_backend_module_import_cache() -> Tuple[str, ...]:
    """Purge Rust backend package/submodule entries from Python import caches.

    Purpose:
        Remove in-process Rust backend modules so the next import resolves the
        newly built extension instead of stale package state.
    Why:
        `maturin develop` can finish successfully while `sys.modules` still holds
        a stale `gl260_rust_ext` object that lacks newly exported kernels.
    Inputs:
        None.
    Outputs:
        Tuple[str, ...]: Module names removed from `sys.modules` in removal order.
    Side Effects:
        Mutates `sys.modules` and invalidates import caches.
    Exceptions:
        Cache invalidation failures are tolerated to keep fallback paths safe.
    """
    purged_names: List[str] = []
    for module_name in (
        _RUST_BACKEND_EXTENSION_MODULE_NAME,
        _RUST_BACKEND_MODULE_NAME,
    ):
        token = str(module_name or "").strip()
        if not token:
            continue
        if token in sys.modules:
            sys.modules.pop(token, None)
            purged_names.append(token)
    try:
        importlib.invalidate_caches()
    except Exception:
        # Best-effort guard; ignore failures to avoid interrupting the workflow.
        pass
    return tuple(purged_names)


def _regression_test_rust_backend_cache_invalidation_purges_sys_modules() -> None:
    """Validate Rust cache invalidation purges package/submodule import cache state.

    Purpose:
        Ensure `_invalidate_rust_backend_cache` removes stale Rust package and
        extension submodule entries from `sys.modules`.
    Why:
        Rebuild validation must force a fresh import surface after `maturin`
        installs to avoid stale package-export contract checks.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Temporarily mutates Rust backend globals and `sys.modules`.
    Exceptions:
        Raises AssertionError when purge/reset semantics regress.
    """
    package_name = str(_RUST_BACKEND_MODULE_NAME or "").strip()
    extension_name = str(_RUST_BACKEND_EXTENSION_MODULE_NAME or "").strip()
    had_package_entry = package_name in sys.modules
    had_extension_entry = extension_name in sys.modules
    original_package_entry = sys.modules.get(package_name)
    original_extension_entry = sys.modules.get(extension_name)
    original_module = globals().get("_RUST_BACKEND_MODULE")
    original_error = globals().get("_RUST_BACKEND_IMPORT_ERROR")
    original_attempted = globals().get("_RUST_BACKEND_IMPORT_ATTEMPTED")
    original_active = globals().get("_RUST_BACKEND_ACTIVE_IDENTITY_KEY")
    original_capability = _snapshot_rust_backend_capability_status()
    try:
        sys.modules[package_name] = object()
        sys.modules[extension_name] = object()
        globals()["_RUST_BACKEND_MODULE"] = object()
        globals()["_RUST_BACKEND_IMPORT_ERROR"] = RuntimeError("synthetic-cache-state")
        globals()["_RUST_BACKEND_IMPORT_ATTEMPTED"] = True
        globals()["_RUST_BACKEND_ACTIVE_IDENTITY_KEY"] = "synthetic-active-identity"
        _set_rust_backend_capability_status(
            {
                "state": "deprecated",
                "reason": "missing_kernels",
                "details": "synthetic stale state",
                "required_kernels": list(RUST_REQUIRED_KERNEL_EXPORTS),
                "missing_kernels": ["measured_ph_uptake_calibration_core"],
            }
        )
        _invalidate_rust_backend_cache()
        if package_name in sys.modules:
            raise AssertionError(
                "Expected package module entry to be purged from sys.modules."
            )
        if extension_name in sys.modules:
            raise AssertionError(
                "Expected extension submodule entry to be purged from sys.modules."
            )
        if globals().get("_RUST_BACKEND_MODULE") is not None:
            raise AssertionError("Expected backend module cache to be cleared.")
        if globals().get("_RUST_BACKEND_IMPORT_ERROR") is not None:
            raise AssertionError("Expected backend import error cache to be cleared.")
        if bool(globals().get("_RUST_BACKEND_IMPORT_ATTEMPTED")):
            raise AssertionError(
                "Expected backend import-attempted flag reset during invalidation."
            )
        if str(globals().get("_RUST_BACKEND_ACTIVE_IDENTITY_KEY") or ""):
            raise AssertionError(
                "Expected active backend identity key reset during invalidation."
            )
    finally:
        if had_package_entry:
            sys.modules[package_name] = original_package_entry
        else:
            sys.modules.pop(package_name, None)
        if had_extension_entry:
            sys.modules[extension_name] = original_extension_entry
        else:
            sys.modules.pop(extension_name, None)
        globals()["_RUST_BACKEND_MODULE"] = original_module
        globals()["_RUST_BACKEND_IMPORT_ERROR"] = original_error
        globals()["_RUST_BACKEND_IMPORT_ATTEMPTED"] = original_attempted
        globals()["_RUST_BACKEND_ACTIVE_IDENTITY_KEY"] = original_active
        _set_rust_backend_capability_status(original_capability)


def _regression_test_rust_backend_load_prefers_extension_probe_module() -> None:
    """Validate `_load_rust_backend` evaluates capability against extension first.

    Purpose:
        Ensure extension-submodule probing is used before package fallback when
        choosing the module surface for capability checks.
    Why:
        Extension-first probing prevents stale package export surfaces from
        triggering false deprecated missing-kernel failures after rebuild.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Temporarily monkeypatches import/evaluation helpers and backend globals.
    Exceptions:
        Raises AssertionError when extension-first probe behavior regresses.
    """
    original_import_module = importlib.import_module
    original_enabled = globals().get("_is_rust_backend_enabled")
    original_eval_capability = globals().get("_evaluate_rust_backend_capability")
    original_record_ready = globals().get(
        "_record_rust_backend_ready_for_current_runtime"
    )
    original_module = globals().get("_RUST_BACKEND_MODULE")
    original_error = globals().get("_RUST_BACKEND_IMPORT_ERROR")
    original_attempted = globals().get("_RUST_BACKEND_IMPORT_ATTEMPTED")
    original_capability = _snapshot_rust_backend_capability_status()
    original_expected_identity = str(_RUST_BACKEND_EXPECTED_IDENTITY_KEY or "")
    original_active_identity = str(_RUST_BACKEND_ACTIVE_IDENTITY_KEY or "")
    evaluated_backend_names: List[str] = []

    class _PackageStub:
        """Package-level Rust stub representing stale `__init__` export surface."""

        __file__ = "C:/tmp/gl260_rust_ext/__init__.py"
        __name__ = "gl260_rust_ext"

    class _ExtensionStub:
        """Extension-level Rust stub representing fresh compiled export surface."""

        __file__ = "C:/tmp/gl260_rust_ext/gl260_rust_ext.cp314t-win_amd64.pyd"
        __name__ = "gl260_rust_ext.gl260_rust_ext"

    package_stub = _PackageStub()
    extension_stub = _ExtensionStub()

    def _import_module_stub(module_name: str, package: Optional[str] = None) -> Any:
        """Return deterministic package/submodule stubs for import-path testing."""
        _ = package
        if module_name == _RUST_BACKEND_MODULE_NAME:
            return package_stub
        if module_name == _RUST_BACKEND_EXTENSION_MODULE_NAME:
            return extension_stub
        raise ImportError(
            f"Unexpected import request in regression stub: {module_name}"
        )

    def _evaluate_capability_stub(backend_obj: Any) -> Dict[str, Any]:
        """Return ready/deprecated payloads to assert extension-first probe ordering."""
        backend_name = str(getattr(backend_obj, "__name__", "") or "")
        evaluated_backend_names.append(backend_name)
        base_payload: Dict[str, Any] = {
            "details": "",
            "required_kernels": list(RUST_REQUIRED_KERNEL_EXPORTS),
            "manifest": {
                "interface_id": RUST_BACKEND_INTERFACE_ID_EXPECTED,
                "interface_version": RUST_BACKEND_INTERFACE_VERSION_EXPECTED,
                "crate_version": "0.1.0",
                "module_name": "gl260_rust_ext",
                "exported_kernels": list(RUST_REQUIRED_KERNEL_EXPORTS),
                "manifest_error": "",
            },
            "module_path": str(getattr(backend_obj, "__file__", "") or ""),
            "module_identity": {
                "module_path": str(getattr(backend_obj, "__file__", "") or ""),
                "module_name": "gl260_rust_ext",
                "crate_version": "0.1.0",
                "interface_id": RUST_BACKEND_INTERFACE_ID_EXPECTED,
                "interface_version": RUST_BACKEND_INTERFACE_VERSION_EXPECTED,
            },
            "runtime_profile": RUST_RUNTIME_PROFILE_FREE_THREADED,
            "cargo_path": "C:/tmp/cargo.exe",
            "cargo_source": RUST_TOOL_SOURCE_RUSTUP,
            "cargo_valid": True,
            "rustc_path": "C:/tmp/rustc.exe",
            "rustc_source": RUST_TOOL_SOURCE_RUSTUP,
            "rustc_valid": True,
            "toolchain_consistency_state": "consistent",
            "toolchain_consistency_reason": "ready",
            "toolchain_consistency_details": "",
        }
        if backend_obj is extension_stub:
            base_payload.update(
                {
                    "state": "ready",
                    "reason": "ready",
                    "missing_kernels": [],
                    "identity_key": "extension-probe-identity",
                    "identity_consistent": True,
                }
            )
        else:
            base_payload.update(
                {
                    "state": "deprecated",
                    "reason": "missing_kernels",
                    "details": "missing kernels=measured_ph_uptake_calibration_core",
                    "missing_kernels": ["measured_ph_uptake_calibration_core"],
                    "identity_key": "package-probe-identity",
                    "identity_consistent": True,
                }
            )
        return base_payload

    try:
        importlib.import_module = _import_module_stub
        globals()["_is_rust_backend_enabled"] = lambda: True
        globals()["_evaluate_rust_backend_capability"] = _evaluate_capability_stub
        globals()["_record_rust_backend_ready_for_current_runtime"] = (
            lambda *, persist=False: None
        )
        globals()["_RUST_BACKEND_EXPECTED_IDENTITY_KEY"] = ""
        globals()["_RUST_BACKEND_ACTIVE_IDENTITY_KEY"] = ""
        _invalidate_rust_backend_cache()
        loaded_backend = _load_rust_backend(force_reload=True, enforce_identity=False)
        if loaded_backend is not extension_stub:
            raise AssertionError(
                "Expected Rust loader to retain extension probe backend when it is ready."
            )
        if not evaluated_backend_names:
            raise AssertionError(
                "Expected capability evaluator to be invoked at least once."
            )
        if evaluated_backend_names[0] != _RUST_BACKEND_EXTENSION_MODULE_NAME:
            raise AssertionError(
                "Expected extension submodule to be evaluated before package fallback."
            )
        payload = _snapshot_rust_backend_capability_status()
        if str(payload.get("state") or "") != "ready":
            raise AssertionError(
                "Expected extension-first probe to produce ready capability payload."
            )
    finally:
        importlib.import_module = original_import_module
        if original_enabled is not None:
            globals()["_is_rust_backend_enabled"] = original_enabled
        else:
            globals().pop("_is_rust_backend_enabled", None)
        if original_eval_capability is not None:
            globals()["_evaluate_rust_backend_capability"] = original_eval_capability
        else:
            globals().pop("_evaluate_rust_backend_capability", None)
        if original_record_ready is not None:
            globals()["_record_rust_backend_ready_for_current_runtime"] = (
                original_record_ready
            )
        else:
            globals().pop("_record_rust_backend_ready_for_current_runtime", None)
        globals()["_RUST_BACKEND_MODULE"] = original_module
        globals()["_RUST_BACKEND_IMPORT_ERROR"] = original_error
        globals()["_RUST_BACKEND_IMPORT_ATTEMPTED"] = original_attempted
        globals()["_RUST_BACKEND_EXPECTED_IDENTITY_KEY"] = original_expected_identity
        globals()["_RUST_BACKEND_ACTIVE_IDENTITY_KEY"] = original_active_identity
        _set_rust_backend_capability_status(original_capability)


def _regression_test_rust_capability_measured_ph_kernel_contract() -> None:
    """Validate measured-pH kernel participates in Rust capability contract checks.

    Purpose:
        Ensure capability evaluation marks `measured_ph_uptake_calibration_core`
        missing when absent and ready when exported as callable.
    Why:
        Post-build backend validation must fail closed only for real missing-kernel
        contract violations, not stale import surfaces.
    Inputs:
        None.
    Outputs:
        None.
    Side Effects:
        Temporarily monkeypatches runtime toolchain diagnostics helper.
    Exceptions:
        Raises AssertionError when measured-pH kernel contract checks regress.
    """
    original_toolchain_diag = globals().get(
        "_resolve_runtime_rust_toolchain_diagnostics"
    )
    try:
        globals()["_resolve_runtime_rust_toolchain_diagnostics"] = lambda **_kwargs: {
            "runtime_profile": RUST_RUNTIME_PROFILE_FREE_THREADED,
            "cargo_path": "C:/tmp/cargo.exe",
            "cargo_source": RUST_TOOL_SOURCE_RUSTUP,
            "cargo_valid": True,
            "cargo_reason": "ok",
            "cargo_details": "cargo 1.0.0",
            "rustc_path": "C:/tmp/rustc.exe",
            "rustc_source": RUST_TOOL_SOURCE_RUSTUP,
            "rustc_valid": True,
            "rustc_reason": "ok",
            "rustc_details": "rustc 1.0.0",
            "toolchain_consistency_state": "consistent",
            "toolchain_consistency_reason": "ready",
            "toolchain_consistency_details": "",
        }

        class _BackendStub:
            """Backend stub exposing manifest and synthetic callable kernel exports."""

            __file__ = "C:/tmp/gl260_rust_ext.cp314t-win_amd64.pyd"
            __name__ = "gl260_rust_ext.gl260_rust_ext"

            @staticmethod
            def rust_backend_manifest() -> Dict[str, Any]:
                """Return manifest payload matching expected Rust interface contract."""
                return {
                    "interface_id": RUST_BACKEND_INTERFACE_ID_EXPECTED,
                    "interface_version": RUST_BACKEND_INTERFACE_VERSION_EXPECTED,
                    "crate_version": "0.1.0",
                    "module_name": "gl260_rust_ext",
                    "exported_kernels": list(RUST_REQUIRED_KERNEL_EXPORTS),
                }

        def _kernel_stub(*_args: Any, **_kwargs: Any) -> None:
            """Callable kernel stub used to satisfy required export checks."""
            return None

        for kernel_name in RUST_REQUIRED_KERNEL_EXPORTS:
            if kernel_name == "measured_ph_uptake_calibration_core":
                continue
            setattr(_BackendStub, kernel_name, staticmethod(_kernel_stub))
        missing_payload = _evaluate_rust_backend_capability(_BackendStub())
        if str(missing_payload.get("reason") or "") != "missing_kernels":
            raise AssertionError(
                "Expected missing measured-pH callable to mark capability as missing_kernels."
            )
        missing_tokens = list(missing_payload.get("missing_kernels") or ())
        if "measured_ph_uptake_calibration_core" not in missing_tokens:
            raise AssertionError(
                "Expected missing-kernels payload to include measured-pH kernel."
            )

        _BackendStub.measured_ph_uptake_calibration_core = staticmethod(_kernel_stub)
        ready_payload = _evaluate_rust_backend_capability(_BackendStub())
        if str(ready_payload.get("state") or "") != "ready":
            raise AssertionError(
                "Expected measured-pH kernel export to restore ready capability state."
            )
        if list(ready_payload.get("missing_kernels") or ()):
            raise AssertionError(
                "Expected no missing kernels once measured-pH callable is exported."
            )
    finally:
        if original_toolchain_diag is not None:
            globals()["_resolve_runtime_rust_toolchain_diagnostics"] = (
                original_toolchain_diag
            )
        else:
            globals().pop("_resolve_runtime_rust_toolchain_diagnostics", None)


def _resolve_rust_backend_capability_probe_module(
    backend: Any,
) -> Tuple[Any, str]:
    """Resolve the module object used for Rust capability contract checks.

    Purpose:
        Prefer capability validation against the compiled extension module object.
    Why:
        Package-level `__init__` exports can lag behind rebuilt extension exports,
        which produces false missing-kernel deprecations after successful builds.
    Inputs:
        backend: Imported Rust backend package/module candidate.
    Outputs:
        Tuple `(probe_module, probe_source)` where `probe_source` indicates the
        selected path (`"extension"`, `"package_fallback"`, or `"missing"`).
    Side Effects:
        May import `gl260_rust_ext.gl260_rust_ext`.
    Exceptions:
        Extension import failures are handled by falling back to `backend`.
    """
    if backend is None:
        return None, "missing"
    try:
        extension_backend = importlib.import_module(_RUST_BACKEND_EXTENSION_MODULE_NAME)
    except Exception:
        return backend, "package_fallback"
    if extension_backend is None:
        return backend, "package_fallback"
    return extension_backend, "extension"


class _PatchedInstallHarness:
    def _install_and_build_rust_backend_interactive(
        self,
        *,
        status_var: Optional[tk.StringVar] = None,
    ) -> bool:
        """Install missing Rust prerequisites and build the extension module.

        Purpose:
            Execute the first-use Rust setup pipeline from the UI.
        Why:
            Rust acceleration is optional; this flow enables in-app bootstrapping
            without forcing manual terminal setup.
        Inputs:
            status_var: Optional status variable for progress/error messaging.
        Outputs:
            True when toolchain + extension are ready, otherwise False.
        Side Effects:
            Runs system installers/commands and updates runtime PATH/module cache.
        Exceptions:
            Command failures are reported and converted to False.
        """
        project_root = os.path.dirname(os.path.abspath(__file__))
        manifest_path = os.path.join(project_root, "rust_ext", "Cargo.toml")
        if not os.path.isfile(manifest_path):
            if status_var is not None:
                status_var.set("Rust extension manifest missing; using Python backend.")
            self._report_rust_backend_install_failure(
                "Rust extension manifest is missing; manual setup cannot continue.",
                manifest_path,
            )
            return False

        def _set_status(message: str) -> None:
            """Update setup status text shown in the active workflow context.

            Purpose:
                Mirror install/build progress to the caller's status field.
            Why:
                Long-running setup steps should remain transparent in the UI.
            Inputs:
                message: Human-readable progress or fallback message.
            Outputs:
                None.
            Side Effects:
                Mutates `status_var` when one is provided.
            Exceptions:
                None.
            """
            if status_var is not None:
                status_var.set(message)

        state = _detect_rust_runtime_requirements()
        rustup_cmd = str(state.get("rustup_cmd") or "rustup")
        if not state.get("rustup_ok"):
            _set_status("Installing Rustup via winget...")
            ok, details = _run_command_for_status(
                [
                    "winget",
                    "install",
                    "--id",
                    "Rustlang.Rustup",
                    "--exact",
                    "--scope",
                    "user",
                    "--interactive",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                interactive=True,
            )
            if not ok:
                _set_status("Rustup install failed; continuing with Python backend.")
                self._report_rust_backend_install_failure(
                    "Rustup install failed; continuing with Python backend.",
                    details,
                )
                return False

        _ensure_user_cargo_bin_on_path()
        state = _detect_rust_runtime_requirements()
        rustup_cmd = str(state.get("rustup_cmd") or rustup_cmd)

        if state.get("rustup_ok") and (
            not state.get("rustc_ok") or not state.get("cargo_ok")
        ):
            _set_status("Configuring Rust stable toolchain...")
            ok, details = _run_command_for_status([rustup_cmd, "default", "stable"])
            if not ok:
                _set_status(
                    "Rust toolchain configuration failed; using Python backend."
                )
                self._report_rust_backend_install_failure(
                    "Rust toolchain configuration failed; using Python backend.",
                    details,
                )
                return False
            _ensure_user_cargo_bin_on_path()
            state = _detect_rust_runtime_requirements()
            if not state.get("rustc_ok") or not state.get("cargo_ok"):
                _set_status(
                    "Rust compiler tools still unavailable; using Python backend."
                )
                self._report_rust_backend_install_failure(
                    "Rust compiler tools are still unavailable after rustup setup.",
                    "rustc="
                    + str(state.get("rustc_msg") or "")
                    + " cargo="
                    + str(state.get("cargo_msg") or ""),
                )
                return False

        if not state.get("maturin_ok"):
            _set_status("Installing maturin for Python extension builds...")
            ok, details = _run_command_for_status(
                [sys.executable, "-m", "pip", "install", "maturin>=1.12,<2.0"]
            )
            if not ok:
                _set_status("maturin install failed; using Python backend.")
                self._report_rust_backend_install_failure(
                    "maturin install failed; using Python backend.",
                    details,
                )
                return False

        state = _detect_rust_runtime_requirements()
        build_strategy = str(state.get("selected_build_strategy") or "unavailable")
        build_toolchain = MSVC_TOOLCHAIN
        build_target: Optional[str] = None
        mingw_bin_dir = ""
        # Select one explicit strategy before build so diagnostics and retries are deterministic.
        if build_strategy == "msvc":
            _set_status("Building Rust extension with maturin (MSVC strategy)...")
        elif build_strategy == "gnu":
            mingw_bin_dir = str(state.get("mingw_bin_dir") or "").strip()
            if not mingw_bin_dir:
                _set_status(
                    "MinGW linker fallback unavailable (gcc/ld not found); using Python backend."
                )
                self._report_rust_backend_install_failure(
                    "GNU fallback selected but MinGW bin directory is unresolved.",
                    "mingw_bin_dir missing",
                )
                return False
            if not state.get("gnu_toolchain_installed"):
                _set_status("Installing Rust GNU host toolchain for MinGW fallback...")
                ok, details = _run_command_for_status(
                    [rustup_cmd, "toolchain", "install", GNU_TOOLCHAIN]
                )
                if not ok:
                    _set_status(
                        "Rust GNU host toolchain install failed; using Python backend."
                    )
                    self._report_rust_backend_install_failure(
                        f"Rust GNU host toolchain install failed ({GNU_TOOLCHAIN}).",
                        details,
                    )
                    return False
            if not state.get("gnu_target_installed"):
                _set_status("Installing Rust GNU target for MinGW fallback...")
                ok, details = _run_command_for_status(
                    [
                        rustup_cmd,
                        "target",
                        "add",
                        GNU_TARGET,
                        "--toolchain",
                        GNU_TOOLCHAIN,
                    ]
                )
                if not ok:
                    _set_status("Rust GNU target install failed; using Python backend.")
                    self._report_rust_backend_install_failure(
                        f"Rust GNU target install failed ({GNU_TARGET} on {GNU_TOOLCHAIN}).",
                        details,
                    )
                    return False
            _ensure_user_cargo_bin_on_path()
            state = _detect_rust_runtime_requirements()
            mingw_bin_dir = str(state.get("mingw_bin_dir") or mingw_bin_dir).strip()
            if (
                not mingw_bin_dir
                or not state.get("gnu_toolchain_installed")
                or not state.get("gnu_target_installed")
            ):
                _set_status(
                    "Rust GNU fallback prerequisites unresolved after install; using Python backend."
                )
                self._report_rust_backend_install_failure(
                    "Rust GNU fallback prerequisites remain unresolved after install.",
                    "mingw="
                    + str(bool(mingw_bin_dir))
                    + " toolchain="
                    + str(bool(state.get("gnu_toolchain_installed")))
                    + " target="
                    + str(bool(state.get("gnu_target_installed"))),
                )
                return False
            build_toolchain = GNU_TOOLCHAIN
            build_target = GNU_TARGET
            _set_status("Building Rust extension with maturin (GNU/MinGW fallback)...")
        else:
            _set_status(
                "Rust build unavailable: neither MSVC linker nor MinGW linker was detected; using Python backend."
            )
            self._report_rust_backend_install_failure(
                "Rust build strategy unavailable: neither MSVC nor MinGW linker was detected.",
                "msvc_linker="
                + str(bool(state.get("msvc_linker_ok")))
                + " mingw="
                + str(bool(state.get("mingw_ok"))),
            )
            return False

        self._dbg(
            "rust.backend",
            "Rust build invocation strategy=%s toolchain=%s target=%s mingw_bin=%s",
            build_strategy,
            build_toolchain,
            str(build_target or "(default)"),
            str(mingw_bin_dir or "(none)"),
        )
        ok, details = _run_maturin_develop_build(
            manifest_path,
            cwd=project_root,
            toolchain=build_toolchain,
            target_triple=build_target,
            mingw_bin_dir=(mingw_bin_dir or None),
        )
        if not ok:
            details_lc = str(details or "").lower()
            fail_reason = "Rust extension build failed; using Python backend."
            if build_strategy == "msvc" and "link.exe not found" in details_lc:
                fail_reason = "Rust build tools missing (MSVC linker). Install Visual Studio Build Tools C++ workload."
            elif (
                build_strategy == "gnu" and "can't find crate for `core`" in details_lc
            ):
                fail_reason = "Rust GNU target still unavailable after setup; using Python backend."
            elif "crypt_e_no_revocation_check" in details_lc:
                fail_reason = "Rust crate download failed due TLS/certificate policy; using Python backend."
            _set_status(fail_reason)
            self._report_rust_backend_install_failure(
                f"{fail_reason} (strategy={build_strategy})",
                details,
            )
            return False

        purged_module_names = _purge_rust_backend_module_import_cache()
        if purged_module_names:
            self._dbg(
                "rust.backend",
                "Purged Rust module import cache entries after build: %s",
                ", ".join(purged_module_names),
            )
        _invalidate_rust_backend_cache()
        loaded_backend = _load_rust_backend(force_reload=True, enforce_identity=False)
        ready = loaded_backend is not None
        if not ready:
            capability_payload = _snapshot_rust_backend_capability_status()
            active_pip_path = _resolve_active_interpreter_pip_path() or "(unresolved)"
            base_prefix = getattr(sys, "base_prefix", sys.prefix)
            in_virtual_env = bool(getattr(sys, "real_prefix", "")) or (
                sys.prefix != base_prefix
            )
            expected_virtual_env = sys.prefix if in_virtual_env else "(none)"
            import_error_text = (
                str(_RUST_BACKEND_IMPORT_ERROR)
                if _RUST_BACKEND_IMPORT_ERROR
                else "(none)"
            )
            manifest_map = (
                dict(capability_payload.get("manifest") or {})
                if isinstance(capability_payload, Mapping)
                else {}
            )
            exported_raw = manifest_map.get("exported_kernels", ())
            manifest_kernel_names: List[str] = []
            if isinstance(exported_raw, Sequence) and not isinstance(
                exported_raw, (str, bytes, bytearray)
            ):
                manifest_kernel_names = [
                    str(token or "").strip()
                    for token in exported_raw
                    if str(token or "").strip()
                ]
            missing_kernels = (
                list(capability_payload.get("missing_kernels") or ())
                if isinstance(capability_payload, Mapping)
                else []
            )
            capability_module_path = (
                str(capability_payload.get("module_path") or "").strip()
                if isinstance(capability_payload, Mapping)
                else ""
            )
            capability_reason = (
                str(capability_payload.get("reason") or "").strip()
                if isinstance(capability_payload, Mapping)
                else ""
            )
            # Include interpreter-target details so import failures can be tied to
            # environment drift quickly when troubleshooting build/install paths.
            # Include capability metadata so stale import surfaces are distinguishable
            # from genuine missing-kernel build artifacts.
            import_failure_details = (
                f"import_error={import_error_text}; "
                f"sys.executable={sys.executable}; "
                f"sys.prefix={sys.prefix}; "
                f"expected_VIRTUAL_ENV={expected_virtual_env}; "
                f"os.VIRTUAL_ENV={os.environ.get('VIRTUAL_ENV') or '(unset)'}; "
                f"pip_path={active_pip_path}; "
                f"capability_reason={capability_reason or '(unknown)'}; "
                f"module_path={capability_module_path or '(unknown)'}; "
                f"manifest_kernel_count={len(manifest_kernel_names)}; "
                f"missing_kernels={','.join(str(item or '').strip() for item in missing_kernels if str(item or '').strip()) or '(none)'}"
            )
            _set_status(
                "Rust extension import failed after build; using Python backend."
            )
            self._report_rust_backend_install_failure(
                "Rust extension import failed after successful build.",
                import_failure_details,
            )
            return False
        capability_payload = _evaluate_rust_backend_capability(loaded_backend)
        _set_rust_backend_capability_status(capability_payload)
        if str(capability_payload.get("state") or "").strip().lower() != "ready":
            capability_details = str(capability_payload.get("details") or "").strip()
            _set_status(
                "Rust backend interface is deprecated after build; using Python backend."
            )
            self._report_rust_backend_install_failure(
                "Rust backend interface check failed after successful build.",
                capability_details
                or str(capability_payload.get("reason") or "deprecated"),
            )
            return False
        _set_rust_backend_expected_identity(
            capability_payload,
            source="install_and_build_interactive",
        )
        capability_payload = _evaluate_rust_backend_capability(loaded_backend)
        _set_rust_backend_capability_status(capability_payload)
        if str(capability_payload.get("state") or "").strip().lower() != "ready":
            _set_status(
                "Rust backend identity check failed after build; using Python backend."
            )
            self._report_rust_backend_install_failure(
                "Rust backend identity check failed after successful build.",
                str(capability_payload.get("details") or "identity mismatch"),
            )
            return False
        verify_ok, verify_details = _run_command_for_status(
            [
                sys.executable,
                "-c",
                "import gl260_rust_ext as m; print(m.__file__)",
            ]
        )
        if not verify_ok:
            fingerprint_payload = _runtime_rust_install_fingerprint_payload()
            verify_failure_details = (
                f"verification={verify_details}; "
                f"sys.executable={fingerprint_payload.get('executable', '')}; "
                f"abi_tag={fingerprint_payload.get('abi_tag', '')}; "
                f"soabi={fingerprint_payload.get('soabi', '')}; "
                f"pip_path={_resolve_active_interpreter_pip_path() or '(unresolved)'}"
            )
            _set_status(
                "Rust import verification failed after build; using Python backend."
            )
            self._report_rust_backend_install_failure(
                "Rust extension verification failed after successful build.",
                verify_failure_details,
            )
            return False
        _record_rust_backend_ready_for_current_runtime(persist=True)
        _set_status("Rust backend ready.")
        self._dbg(
            "rust.backend",
            "Rust backend install/repair completed successfully (strategy=%s).",
            build_strategy,
        )
        return True
