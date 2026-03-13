"""Validate the Rust backend build against the free-threaded Python environment.

Purpose:
    Provide one repo-local command that rebuilds `gl260_rust_ext` using the
    pinned `.venv-314t\\Scripts\\python.exe` interpreter and rustup-managed
    toolchain paths.
Why:
    Windows PATH resolution can pick incompatible `cargo.exe` shims from Python
    or other tool directories, which makes manual rebuilds fail inconsistently.
Inputs:
    Optional `--toolchain` and `--target` CLI arguments.
Outputs:
    Prints interpreter, toolchain, build, and import-smoke-test status lines.
Side Effects:
    Runs `maturin develop`, which rebuilds and reinstalls the Rust extension
    into the active `.venv-314t` environment.
Exceptions:
    Raises `RuntimeError` when required tools, interpreter paths, or commands
    cannot be resolved or when build/import validation fails.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_INTERPRETER = REPO_ROOT / ".venv-314t" / "Scripts" / "python.exe"
MANIFEST_PATH = REPO_ROOT / "rust_ext" / "Cargo.toml"
GNU_TARGET = "x86_64-pc-windows-gnu"
GNU_TOOLCHAIN = "stable-x86_64-pc-windows-gnu"
MSVC_TOOLCHAIN = "stable"
MINGW_FALLBACK_BIN_DIR = Path.home() / "mingw64" / "bin"


def _run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and capture stdout/stderr for explicit diagnostics.

    Purpose:
        Execute validation commands with consistent text capture.
    Why:
        Build failures need to surface the exact stderr/stdout details instead of
        depending on terminal state or shell-specific behavior.
    Inputs:
        command: Tokenized command to execute.
        cwd: Optional working directory for the subprocess.
        env: Optional environment override dictionary.
    Outputs:
        Completed subprocess result with captured text output.
    Side Effects:
        Launches external processes.
    Exceptions:
        Raises `RuntimeError` when command startup fails.
    """
    try:
        return subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        joined = subprocess.list2cmdline(command)
        raise RuntimeError(f"Failed to start command: {joined}\n{exc}") from exc


def _require_expected_interpreter() -> Path:
    """Require the validator to run from the pinned free-threaded interpreter.

    Purpose:
        Prevent validation from accidentally rebuilding into the wrong virtual
        environment.
    Why:
        `maturin develop` installs into the interpreter that launches it, so a
        mismatched runtime can report success while leaving `.venv-314t` stale.
    Inputs:
        None.
    Outputs:
        Resolved expected interpreter path.
    Side Effects:
        None.
    Exceptions:
        Raises `RuntimeError` if the running interpreter does not match the
        pinned `.venv-314t\\Scripts\\python.exe` path.
    """
    expected = EXPECTED_INTERPRETER.resolve()
    active = Path(sys.executable).resolve()
    if active != expected:
        raise RuntimeError(
            "This validator must be launched with the pinned free-threaded "
            f"interpreter.\nExpected: {expected}\nActive:   {active}"
        )
    return expected


def _resolve_rustup_tool(tool_name: str, *, toolchain: str) -> Path:
    """Resolve a rustup-managed tool path for deterministic validation.

    Purpose:
        Find the concrete `rustc` or `cargo` binary rustup will launch.
    Why:
        PATH-visible shims can be stale or incompatible even when rustup itself
        is installed and healthy.
    Inputs:
        tool_name: Rust tool to resolve, such as `cargo` or `rustc`.
        toolchain: Rustup toolchain token used for resolution.
    Outputs:
        Absolute path to the requested rustup-managed executable.
    Side Effects:
        Executes `rustup which`.
    Exceptions:
        Raises `RuntimeError` when rustup cannot resolve the requested tool.
    """
    rustup_path = shutil.which("rustup")
    if not rustup_path:
        raise RuntimeError("`rustup` is not available on PATH.")
    completed = _run_command(
        [rustup_path, "which", "--toolchain", toolchain, tool_name],
        cwd=REPO_ROOT,
    )
    candidate = (completed.stdout or completed.stderr or "").strip().splitlines()
    resolved = (
        Path(candidate[-1].strip()) if completed.returncode == 0 and candidate else None
    )
    if completed.returncode != 0 or not resolved or not resolved.is_file():
        raise RuntimeError(
            f"Unable to resolve rustup-managed `{tool_name}` for toolchain "
            f"`{toolchain}`.\n{completed.stderr or completed.stdout}".rstrip()
        )
    return resolved.resolve()


def _format_command_output(completed: subprocess.CompletedProcess[str]) -> str:
    """Collapse subprocess output into one trimmed diagnostic string.

    Purpose:
        Produce short, stable command output for logs and failure messages.
    Why:
        Validation output should be easy to scan while still surfacing the
        command text that matters.
    Inputs:
        completed: Captured subprocess result.
    Outputs:
        Single trimmed output string.
    Side Effects:
        None.
    Exceptions:
        None.
    """
    return (completed.stdout or completed.stderr or "").strip()


def _print_console_safe(message: str) -> None:
    """Print text while tolerating Windows console encoding limitations.

    Purpose:
        Emit command output without crashing on Unicode glyphs from build tools.
    Why:
        `maturin` can include status icons that are valid UTF-8 but not encodable
        by the active cp1252 console, which would otherwise abort validation.
    Inputs:
        message: Text to write to stdout.
    Outputs:
        None.
    Side Effects:
        Writes to stdout.
    Exceptions:
        None.
    """
    text = str(message)
    encoding = sys.stdout.encoding or "utf-8"
    safe_text = text.encode(encoding, errors="replace").decode(encoding)
    sys.stdout.write(safe_text)
    sys.stdout.write("\n")


def _resolve_mingw_bin_dir() -> Path | None:
    """Locate a usable MinGW bin directory for GNU fallback builds.

    Purpose:
        Discover the GCC/LD pair needed for `x86_64-pc-windows-gnu` builds.
    Why:
        GNU Rust builds can fail late if the linker is only partially installed
        or present in a non-standard location.
    Inputs:
        None.
    Outputs:
        Path to a directory containing both `gcc.exe` and `ld.exe`, or `None`.
    Side Effects:
        Reads PATH and filesystem metadata.
    Exceptions:
        None.
    """
    candidates: list[Path] = []
    for raw_entry in str(os.environ.get("PATH", "") or "").split(os.pathsep):
        cleaned = str(raw_entry or "").strip().strip('"')
        if cleaned:
            candidates.append(Path(cleaned))
    candidates.append(MINGW_FALLBACK_BIN_DIR)
    seen: set[str] = set()
    for candidate_dir in candidates:
        try:
            resolved = candidate_dir.resolve()
        except OSError:
            continue
        normalized = os.path.normcase(str(resolved))
        if normalized in seen or not resolved.is_dir():
            continue
        seen.add(normalized)
        if (resolved / "gcc.exe").is_file() and (resolved / "ld.exe").is_file():
            return resolved
    return None


def _prepend_unique_path_entries(
    base_path: str,
    entries: Iterable[Path],
) -> str:
    """Prepend path entries while preserving deterministic uniqueness.

    Purpose:
        Make rustup-managed tools and interpreter scripts win PATH resolution.
    Why:
        Validation should not depend on which stale shim directory happens to
        appear first in the caller's environment.
    Inputs:
        base_path: Original PATH string.
        entries: Ordered path entries to prepend.
    Outputs:
        Updated PATH string.
    Side Effects:
        None.
    Exceptions:
        None.
    """
    existing = [chunk for chunk in str(base_path or "").split(os.pathsep) if chunk]
    seen = {os.path.normcase(item.strip()) for item in existing if item.strip()}
    prefix: list[str] = []
    for entry in entries:
        resolved = str(entry)
        normalized = os.path.normcase(resolved)
        if normalized in seen or not entry.is_dir():
            continue
        prefix.append(resolved)
        seen.add(normalized)
    return os.pathsep.join(prefix + existing)


def _build_validation_env(
    *,
    toolchain: str,
    target: str,
    rustc_path: Path,
    cargo_path: Path,
) -> dict[str, str]:
    """Build the environment used for the pinned maturin validation run.

    Purpose:
        Force the rebuild to use the same Python interpreter and rustup-resolved
        Rust tools every time.
    Why:
        Maturin can otherwise discover a mismatched interpreter or PATH shim and
        report a misleadingly successful build.
    Inputs:
        toolchain: Rustup toolchain token used for the validation.
        target: Cargo target triple for the build.
        rustc_path: Resolved rustup-managed `rustc` path.
        cargo_path: Resolved rustup-managed `cargo` path.
    Outputs:
        Environment dictionary for the build subprocess.
    Side Effects:
        None.
    Exceptions:
        None.
    """
    env = dict(os.environ)
    scripts_dir = EXPECTED_INTERPRETER.parent
    prepend_entries = [scripts_dir, rustc_path.parent, cargo_path.parent]
    env["PYO3_PYTHON"] = str(EXPECTED_INTERPRETER)
    env["VIRTUAL_ENV"] = str(EXPECTED_INTERPRETER.parents[1])
    env["RUSTUP_TOOLCHAIN"] = toolchain
    env["RUSTC"] = str(rustc_path)
    env["CARGO"] = str(cargo_path)
    env["CARGO_BUILD_TARGET"] = target
    if target == GNU_TARGET:
        mingw_bin_dir = _resolve_mingw_bin_dir()
        if mingw_bin_dir:
            target_upper = target.upper().replace("-", "_")
            prepend_entries.append(mingw_bin_dir)
            env[f"CARGO_TARGET_{target_upper}_LINKER"] = str(mingw_bin_dir / "gcc.exe")
            env["CC_x86_64_pc_windows_gnu"] = str(mingw_bin_dir / "gcc.exe")
            env["CXX_x86_64_pc_windows_gnu"] = str(mingw_bin_dir / "g++.exe")
            env["AR_x86_64_pc_windows_gnu"] = str(mingw_bin_dir / "ar.exe")
    env["PATH"] = _prepend_unique_path_entries(env.get("PATH", ""), prepend_entries)
    env.setdefault("CARGO_HTTP_CHECK_REVOKE", "false")
    return env


def _default_toolchain_for_target(target: str) -> str:
    """Choose the rustup host toolchain that matches the requested target.

    Purpose:
        Keep validator defaults aligned with the app's MSVC-first, GNU-fallback
        build strategy.
    Why:
        GNU target builds launched from the MSVC host toolchain try to compile
        host build scripts with `link.exe`, which fails on machines that only
        have the MinGW fallback path available.
    Inputs:
        target: Cargo target triple requested for validation.
    Outputs:
        Rustup toolchain token to use for the build.
    Side Effects:
        None.
    Exceptions:
        None.
    """
    return GNU_TOOLCHAIN if target == GNU_TARGET else MSVC_TOOLCHAIN


def _warn_on_path_cargo_mismatch(expected_cargo: Path) -> None:
    """Warn when the shell resolves `cargo` to a non-rustup executable.

    Purpose:
        Surface the exact PATH drift that causes manual rebuild confusion.
    Why:
        This workspace currently resolves bare `cargo` to a Python-side shim, so
        the validator should call that out before using rustup-managed tools.
    Inputs:
        expected_cargo: Rustup-managed `cargo` path used for the actual build.
    Outputs:
        None.
    Side Effects:
        Writes a warning to stderr when PATH points at a different executable.
    Exceptions:
        None.
    """
    direct_cargo = shutil.which("cargo")
    if not direct_cargo:
        return
    direct_path = Path(direct_cargo).resolve()
    expected_path = expected_cargo.resolve()
    if direct_path != expected_path:
        print(
            "Warning: bare `cargo` resolves to a different executable than the "
            "rustup-managed path used for validation.\n"
            f"PATH cargo:   {direct_path}\n"
            f"rustup cargo: {expected_path}\n"
            "Use this validator or `rustup run stable cargo ...` for manual "
            "Rust extension troubleshooting.",
            file=sys.stderr,
        )


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
            "import gl260_rust_ext.gl260_rust_ext as m; print(m.__file__)",
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


if __name__ == "__main__":
    raise SystemExit(main())
