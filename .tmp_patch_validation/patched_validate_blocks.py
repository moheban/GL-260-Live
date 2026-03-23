# ruff: noqa: F821
from __future__ import annotations
import argparse
import sys


def main() -> int:
    """Run the pinned Rust backend rebuild and import smoke test.

    Purpose:
        Rebuild `gl260_rust_ext` deterministically and confirm it imports from
        the free-threaded `.venv-314t` environment.
    Why:
        One command reduces human error while exposing the exact interpreter and
        toolchain paths used by the rebuild.
    Inputs:
        Optional CLI arguments parsed from `sys.argv`.
    Outputs:
        Process exit status code.
    Side Effects:
        Builds and reinstalls the Rust extension in `.venv-314t`.
    Exceptions:
        Returns non-zero on validation failure after printing diagnostics.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--toolchain",
        default="",
        help="Rustup toolchain token to use.",
    )
    parser.add_argument(
        "--target",
        default=GNU_TARGET,
        help="Cargo target triple to use for the maturin build.",
    )
    args = parser.parse_args()
    toolchain = str(args.toolchain or "").strip() or _default_toolchain_for_target(
        args.target
    )

    try:
        interpreter_path = _require_expected_interpreter()
        rustc_path = _resolve_rustup_tool("rustc", toolchain=toolchain)
        cargo_path = _resolve_rustup_tool("cargo", toolchain=toolchain)
        _warn_on_path_cargo_mismatch(cargo_path)

        rustc_version = _run_command([str(rustc_path), "--version"], cwd=REPO_ROOT)
        cargo_version = _run_command([str(cargo_path), "--version"], cwd=REPO_ROOT)
        print(f"Interpreter: {interpreter_path}")
        print(f"Rustup toolchain: {toolchain}")
        print(f"rustc: {_format_command_output(rustc_version)}")
        print(f"cargo: {_format_command_output(cargo_version)}")

        build_env = _build_validation_env(
            toolchain=toolchain,
            target=args.target,
            rustc_path=rustc_path,
            cargo_path=cargo_path,
        )
        build_command = [
            str(interpreter_path),
            "-m",
            "maturin",
            "develop",
            "--manifest-path",
            str(MANIFEST_PATH),
            "--target",
            args.target,
        ]
        build_result = _run_command(build_command, cwd=REPO_ROOT, env=build_env)
        _print_console_safe(_format_command_output(build_result))
        if build_result.returncode != 0:
            raise RuntimeError("Rust backend build validation failed.")

        smoke_command = [
            str(interpreter_path),
            "-c",
            (
                "import gl260_rust_ext as pkg; "
                "import gl260_rust_ext.gl260_rust_ext as mod; "
                "pkg_has = hasattr(pkg, 'measured_ph_uptake_calibration_core'); "
                "mod_has = hasattr(mod, 'measured_ph_uptake_calibration_core'); "
                "print(mod.__file__); "
                "print(f'measured_ph_uptake_calibration_core package={pkg_has} extension={mod_has}'); "
                "raise SystemExit(0 if (pkg_has and mod_has) else 2)"
            ),
        ]
        smoke_result = _run_command(smoke_command, cwd=REPO_ROOT, env=build_env)
        smoke_output = _format_command_output(smoke_result)
        print(f"Import smoke test: {smoke_output}")
        if smoke_result.returncode != 0:
            raise RuntimeError("Rust backend import smoke test failed.")
        return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
