"""Cross-platform bootstrap installer for the GL-260 application.

Purpose:
    Provision local virtual environments, install Python dependencies, attempt
    Rust backend setup, and print a single terminal-ready run command.
Why:
    New workstations often have only VS Code plus a base Python runtime, and
    users need a deterministic setup flow that works without admin rights.
Inputs:
    CLI flags:
    - --python-std: Optional explicit path to the standard Python interpreter.
    - --python-ft: Optional explicit path to the free-threaded interpreter.
    - --dry-run: Print planned commands without mutating the repository.
Outputs:
    Console setup summary and a final `RUN COMMAND: ...` line.
Side Effects:
    May create `.venv` / `.venv-314t`, install packages, install rustup in user
    scope, and run `maturin develop`.
Exceptions:
    Command failures are reported as status entries; process exits non-zero only
    when no runnable environment is available.
"""

from __future__ import annotations

import argparse
import os
import platform
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

APP_ENTRY_SCRIPT = "GL-260 Data Analysis and Plotter.py"
STD_ENV_DIRNAME = ".venv"
FT_ENV_DIRNAME = ".venv-314t"


@dataclass
class CommandResult:
    """Container for command execution diagnostics.

    Purpose:
        Normalize subprocess outcomes for success checks and user-facing logs.
    Why:
        Setup flow is branch-heavy and needs one common result type so failures
        can be reported consistently without duplicating parsing logic.
    Inputs:
        returncode: Command exit status.
        stdout: Captured standard output text.
        stderr: Captured standard error text.
        command: Tokenized command that was executed or planned.
        dry_run: Whether command execution was skipped intentionally.
    Outputs:
        Dataclass instance used by setup orchestration helpers.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    dry_run: bool = False

    @property
    def ok(self) -> bool:
        """Return success state for this command result.

        Purpose:
            Provide compact boolean success checks for setup branches.
        Why:
            Setup code evaluates many command outcomes and should avoid repeated
            `returncode == 0` boilerplate.
        Inputs:
            None.
        Outputs:
            bool: True when the command exit code is zero.
        Side Effects:
            None.
        Exceptions:
            None.
        """

        return self.returncode == 0


@dataclass
class EnvironmentProvisionResult:
    """Track setup state for one virtual environment target.

    Purpose:
        Capture discovery, provisioning, and remediation details for `.venv` or
        `.venv-314t` in one immutable summary object.
    Why:
        Final status and run-command selection depend on multiple intermediate
        outcomes and should not rely on implicit globals.
    Inputs:
        label: Human-readable environment label.
        env_dir: Filesystem path to the target virtual environment directory.
    Outputs:
        Dataclass instance used throughout setup and reporting.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    label: str
    env_dir: Path
    interpreter: str = ""
    resolved: bool = False
    ready: bool = False
    error: str = ""
    remediation_commands: list[str] = field(default_factory=list)

    @property
    def python_path(self) -> Path:
        """Return environment-local Python executable path.

        Purpose:
            Resolve platform-appropriate venv interpreter location.
        Why:
            Setup and run command generation must avoid activation scripts and
            invoke venv-local Python directly for no-admin compatibility.
        Inputs:
            None.
        Outputs:
            Path to the expected virtual environment Python executable.
        Side Effects:
            None.
        Exceptions:
            None.
        """

        if os.name == "nt":
            return self.env_dir / "Scripts" / "python.exe"
        return self.env_dir / "bin" / "python"


@dataclass
class RustSetupResult:
    """Track Rust backend setup/build status.

    Purpose:
        Preserve one authoritative summary of Rust tooling and extension build
        readiness for final reporting.
    Why:
        Rust setup is non-blocking for app readiness, so user output must state
        exactly what failed and how to repair it.
    Inputs:
        None.
    Outputs:
        Dataclass instance for status reporting.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    attempted: bool = False
    ready: bool = False
    error: str = ""
    remediation_commands: list[str] = field(default_factory=list)


def _quote_command(command: list[str]) -> str:
    """Render a tokenized command as a shell-visible command line.

    Purpose:
        Produce readable, copyable command text for logs and dry-run output.
    Why:
        Users need exact command visibility when setup steps fail or are skipped.
    Inputs:
        command: Tokenized command sequence.
    Outputs:
        str: Shell-escaped command text.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
    description: str = "",
) -> CommandResult:
    """Execute or plan a command with consistent diagnostics.

    Purpose:
        Centralize subprocess execution, dry-run behavior, and failure capture.
    Why:
        Setup steps should share one execution path to ensure consistent output,
        robust error handling, and deterministic logging.
    Inputs:
        command: Tokenized command to run.
        cwd: Working directory for subprocess execution.
        env: Optional environment dictionary for subprocess overrides.
        dry_run: True to print plan without executing.
        description: Optional step label printed before execution.
    Outputs:
        CommandResult containing exit code and captured output.
    Side Effects:
        Launches subprocesses when `dry_run` is False.
    Exceptions:
        OS/process spawn failures are captured into the result rather than raised.
    """

    prefix = "[DRY-RUN]" if dry_run else "[RUN]"
    if description:
        print(f"{prefix} {description}")
    print(f"{prefix} {_quote_command(command)}")
    if dry_run:
        return CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=command,
            dry_run=True,
        )
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return CommandResult(
            returncode=1,
            stdout="",
            stderr=str(exc),
            command=command,
            dry_run=False,
        )
    return CommandResult(
        returncode=int(completed.returncode),
        stdout=str(completed.stdout or ""),
        stderr=str(completed.stderr or ""),
        command=command,
        dry_run=False,
    )


def _resolve_repo_root() -> Path:
    """Resolve repository root directory from this installer location.

    Purpose:
        Pin setup operations to the repository root regardless of caller CWD.
    Why:
        Relative paths like `requirements.txt` and `rust_ext/Cargo.toml` must
        be stable when users launch setup from VS Code terminals in any folder.
    Inputs:
        None.
    Outputs:
        Path to repository root (`scripts/..`).
    Side Effects:
        None.
    Exceptions:
        Raises `RuntimeError` when expected repo sentinel files are missing.
    """

    repo_root = Path(__file__).resolve().parents[1]
    sentinels = [
        repo_root / "requirements.txt",
        repo_root / APP_ENTRY_SCRIPT,
        repo_root / "rust_ext" / "Cargo.toml",
    ]
    missing = [str(item) for item in sentinels if not item.exists()]
    if missing:
        raise RuntimeError(
            "Repository layout validation failed. Missing required paths: "
            + ", ".join(missing)
        )
    return repo_root


def _detect_windows_py_launcher(version_flag: str, *, cwd: Path) -> str:
    """Resolve interpreter path via Windows `py` launcher.

    Purpose:
        Find concrete interpreter executables for version-specific launcher tokens.
    Why:
        `py -3.14` and `py -3.14t` are the most reliable no-admin discovery path
        on Windows machines with user-scope Python installs.
    Inputs:
        version_flag: Launcher selector (for example `-3.14` or `-3.14t`).
        cwd: Command working directory.
    Outputs:
        Resolved interpreter executable path, or empty string when unavailable.
    Side Effects:
        Executes one read-only interpreter probe command.
    Exceptions:
        None; probe failures return empty string.
    """

    result = _run_command(
        [
            "py",
            version_flag,
            "-c",
            "import sys; print(sys.executable)",
        ],
        cwd=cwd,
        dry_run=False,
    )
    if not result.ok:
        return ""
    first_line = str(result.stdout or "").strip().splitlines()
    return str(first_line[-1]).strip() if first_line else ""


def _resolve_interpreter_from_candidates(
    candidates: list[str],
    *,
    cwd: Path,
) -> str:
    """Resolve first runnable interpreter from executable candidates.

    Purpose:
        Validate interpreter executables before virtualenv provisioning.
    Why:
        PATH entries can include stale shims; explicit runtime probes reduce
        false positives before setup starts mutating state.
    Inputs:
        candidates: Candidate executable tokens or absolute paths.
        cwd: Probe command working directory.
    Outputs:
        Resolved interpreter path string, or empty string when no candidate works.
    Side Effects:
        Executes lightweight `python -c` probes.
    Exceptions:
        None; invalid candidates are skipped.
    """

    for candidate in candidates:
        token = str(candidate or "").strip()
        if not token:
            continue
        if os.path.sep in token or (os.name == "nt" and ":" in token):
            if not Path(token).exists():
                continue
            probe_cmd = [token, "-c", "import sys; print(sys.executable)"]
        else:
            if shutil.which(token) is None:
                continue
            probe_cmd = [token, "-c", "import sys; print(sys.executable)"]
        result = _run_command(probe_cmd, cwd=cwd, dry_run=False)
        if not result.ok:
            continue
        lines = str(result.stdout or "").strip().splitlines()
        if lines:
            return str(lines[-1]).strip()
    return ""


def _resolve_standard_interpreter(explicit: str, *, cwd: Path) -> str:
    """Resolve interpreter used for standard `.venv` provisioning.

    Purpose:
        Determine best available standard CPython interpreter for setup.
    Why:
        Installer should prefer pinned versions but still remain functional on
        machines that only provide broader `python3` or current interpreter.
    Inputs:
        explicit: Optional explicit user-supplied interpreter path.
        cwd: Probe command working directory.
    Outputs:
        Interpreter path string, or empty string when unresolved.
    Side Effects:
        Executes read-only interpreter probe commands.
    Exceptions:
        None.
    """

    explicit_token = str(explicit or "").strip()
    if explicit_token:
        return _resolve_interpreter_from_candidates([explicit_token], cwd=cwd)
    if os.name == "nt":
        launcher_path = _detect_windows_py_launcher("-3.14", cwd=cwd)
        if launcher_path:
            return launcher_path
    return _resolve_interpreter_from_candidates(
        [
            "python3.14",
            "python3",
            "python",
            sys.executable,
        ],
        cwd=cwd,
    )


def _resolve_free_threaded_interpreter(explicit: str, *, cwd: Path) -> str:
    """Resolve interpreter used for free-threaded `.venv-314t` provisioning.

    Purpose:
        Determine whether a free-threaded interpreter is available for preferred
        runtime provisioning.
    Why:
        Rust backend and no-GIL workflows should prefer the free-threaded path
        when available, but setup must continue when it is not present.
    Inputs:
        explicit: Optional explicit user-supplied free-threaded interpreter path.
        cwd: Probe command working directory.
    Outputs:
        Interpreter path string, or empty string when unresolved.
    Side Effects:
        Executes read-only interpreter probe commands.
    Exceptions:
        None.
    """

    explicit_token = str(explicit or "").strip()
    if explicit_token:
        return _resolve_interpreter_from_candidates([explicit_token], cwd=cwd)
    if os.name == "nt":
        launcher_path = _detect_windows_py_launcher("-3.14t", cwd=cwd)
        if launcher_path:
            return launcher_path
    return _resolve_interpreter_from_candidates(["python3.14t"], cwd=cwd)


def _build_run_command(env_dir_name: str) -> str:
    """Build final VS Code terminal command for launching the application.

    Purpose:
        Produce one deterministic run command string users can paste directly.
    Why:
        Setup contract requires explicit launch guidance independent of shell
        activation scripts and admin policy.
    Inputs:
        env_dir_name: Environment directory name (`.venv` or `.venv-314t`).
    Outputs:
        Command string using platform-native virtualenv Python path.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    if os.name == "nt":
        python_path = f".\\{env_dir_name}\\Scripts\\python.exe"
    else:
        python_path = f"./{env_dir_name}/bin/python"
    return f'{python_path} "{APP_ENTRY_SCRIPT}"'


def _provision_environment(
    *,
    label: str,
    env_dir: Path,
    interpreter: str,
    repo_root: Path,
    dry_run: bool,
) -> EnvironmentProvisionResult:
    """Create and populate one virtual environment target.

    Purpose:
        Build a virtual environment and install Python requirements.
    Why:
        The app must run reproducibly without relying on global site-packages.
    Inputs:
        label: Human-readable environment label for status output.
        env_dir: Target virtualenv directory path.
        interpreter: Interpreter executable path used to create the venv.
        repo_root: Repository root for command execution.
        dry_run: True to print planned steps without mutating state.
    Outputs:
        EnvironmentProvisionResult summarizing readiness and remediation hints.
    Side Effects:
        May create/upgrade virtualenv and install packages.
    Exceptions:
        Subprocess failures are captured into result state.
    """

    result = EnvironmentProvisionResult(label=label, env_dir=env_dir)
    result.interpreter = str(interpreter or "").strip()
    result.resolved = bool(result.interpreter)
    if not result.resolved:
        if label == "free-threaded":
            result.error = (
                "Free-threaded interpreter not found. "
                "Setup continued with standard env."
            )
            if os.name == "nt":
                result.remediation_commands.extend(
                    [
                        "py -3.14t -m venv .venv-314t",
                        (
                            ".\\.venv-314t\\Scripts\\python.exe "
                            "-m pip install --upgrade pip"
                        ),
                        (
                            ".\\.venv-314t\\Scripts\\python.exe "
                            "-m pip install -r requirements.txt"
                        ),
                    ]
                )
            else:
                result.remediation_commands.extend(
                    [
                        "python3.14t -m venv .venv-314t",
                        "./.venv-314t/bin/python -m pip install --upgrade pip",
                        "./.venv-314t/bin/python -m pip install -r requirements.txt",
                    ]
                )
        else:
            result.error = "Standard interpreter not found."
            if os.name == "nt":
                result.remediation_commands.extend(
                    [
                        "py -3.14 -m venv .venv",
                        ".\\.venv\\Scripts\\python.exe -m pip install --upgrade pip",
                        (
                            ".\\.venv\\Scripts\\python.exe "
                            "-m pip install -r requirements.txt"
                        ),
                    ]
                )
            else:
                result.remediation_commands.extend(
                    [
                        "python3.14 -m venv .venv",
                        "./.venv/bin/python -m pip install --upgrade pip",
                        "./.venv/bin/python -m pip install -r requirements.txt",
                    ]
                )
        return result

    create = _run_command(
        [result.interpreter, "-m", "venv", str(env_dir)],
        cwd=repo_root,
        dry_run=dry_run,
        description=f"Create {label} environment",
    )
    if not create.ok:
        result.error = f"Failed to create {label} environment: {create.stderr.strip()}"
        return result

    python_path = result.python_path
    if not dry_run and not python_path.exists():
        result.error = (
            f"Environment created but Python executable not found at {python_path}."
        )
        return result

    pip_upgrade = _run_command(
        [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
        cwd=repo_root,
        dry_run=dry_run,
        description=f"Upgrade pip in {label} environment",
    )
    if not pip_upgrade.ok:
        result.error = (
            f"Failed to upgrade pip in {label} environment: "
            f"{pip_upgrade.stderr.strip()}"
        )
        return result

    install_requirements = _run_command(
        [str(python_path), "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=repo_root,
        dry_run=dry_run,
        description=f"Install requirements in {label} environment",
    )
    if not install_requirements.ok:
        result.error = (
            "Failed to install requirements in "
            f"{label} environment: {install_requirements.stderr.strip()}"
        )
        return result

    result.ready = True
    return result


def _ensure_cargo_bin_on_path(base_env: dict[str, str]) -> dict[str, str]:
    """Return environment with user cargo binary path prepended when available.

    Purpose:
        Ensure `rustup`, `cargo`, and `rustc` are discoverable in current process.
    Why:
        Fresh rustup installs typically require shell restart before PATH updates;
        installer must work in the current terminal session.
    Inputs:
        base_env: Source environment dictionary.
    Outputs:
        Updated environment dictionary with cargo bin path prepended when present.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    env = dict(base_env)
    cargo_bin = Path.home() / ".cargo" / "bin"
    if cargo_bin.is_dir():
        current_path = str(env.get("PATH", "") or "")
        prepend = str(cargo_bin)
        parts = [item for item in current_path.split(os.pathsep) if item]
        normalized = {os.path.normcase(p) for p in parts}
        if os.path.normcase(prepend) not in normalized:
            env["PATH"] = prepend + (os.pathsep + current_path if current_path else "")
    return env


def _ensure_rust_backend(
    *,
    repo_root: Path,
    python_exe: Path,
    dry_run: bool,
) -> RustSetupResult:
    """Install/validate Rust toolchain and build the extension module.

    Purpose:
        Attempt user-scope Rust tooling setup and extension build in the primary
        runtime selected by Python environment provisioning.
    Why:
        Rust acceleration should be enabled automatically when possible without
        blocking app readiness when setup fails.
    Inputs:
        repo_root: Repository root for command execution.
        python_exe: Interpreter path from the primary virtual environment.
        dry_run: True to print planned commands without mutating state.
    Outputs:
        RustSetupResult containing readiness and remediation commands.
    Side Effects:
        May install rustup, install maturin, build extension artifacts.
    Exceptions:
        Failures are captured as status/error text without raising.
    """

    rust = RustSetupResult(attempted=True)
    base_env = _ensure_cargo_bin_on_path(dict(os.environ))

    rustup_check = _run_command(
        ["rustup", "--version"],
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Check rustup availability",
    )
    if not rustup_check.ok:
        if os.name == "nt":
            winget_available = shutil.which("winget") is not None
            install_cmd = [
                "winget",
                "install",
                "--id",
                "Rustlang.Rustup",
                "--exact",
                "--scope",
                "user",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]
            if winget_available:
                install = _run_command(
                    install_cmd,
                    cwd=repo_root,
                    env=base_env,
                    dry_run=dry_run,
                    description="Install rustup (user scope)",
                )
                if not install.ok:
                    rust.error = (
                        "rustup installation failed; continuing with Python fallback."
                    )
            else:
                rust.error = (
                    "rustup not found and winget is unavailable; "
                    "continuing with Python fallback."
                )
            rust.remediation_commands.extend(
                [
                    _quote_command(install_cmd),
                    "rustup default stable",
                ]
            )
        else:
            install_cmd = ["sh", "-c", "curl https://sh.rustup.rs -sSf | sh -s -- -y"]
            install = _run_command(
                install_cmd,
                cwd=repo_root,
                env=base_env,
                dry_run=dry_run,
                description="Install rustup in user space",
            )
            if not install.ok:
                rust.error = (
                    "rustup installation failed; continuing with Python fallback."
                )
            rust.remediation_commands.extend(
                [
                    "curl https://sh.rustup.rs -sSf | sh -s -- -y",
                    'source "$HOME/.cargo/env"',
                    "rustup default stable",
                ]
            )
        base_env = _ensure_cargo_bin_on_path(base_env)

    stable = _run_command(
        ["rustup", "default", "stable"],
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Ensure stable Rust toolchain",
    )
    if not stable.ok and not rust.error:
        rust.error = "Failed to configure stable Rust toolchain."

    rustc_ok = _run_command(
        ["rustc", "--version"],
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Check rustc availability",
    )
    cargo_ok = _run_command(
        ["cargo", "--version"],
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Check cargo availability",
    )
    if not rustc_ok.ok or not cargo_ok.ok:
        if not rust.error:
            rust.error = (
                "Rust compiler tools are unavailable; continuing with Python fallback."
            )
        rust.remediation_commands.extend(
            [
                "rustup default stable",
                "rustc --version",
                "cargo --version",
            ]
        )
        return rust

    maturin_install = _run_command(
        [str(python_exe), "-m", "pip", "install", "maturin>=1.12,<2.0"],
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Install maturin in primary runtime",
    )
    if not maturin_install.ok:
        rust.error = "Failed to install maturin; continuing with Python fallback."
        rust.remediation_commands.append(
            f'{python_exe} -m pip install "maturin>=1.12,<2.0"'
        )
        return rust

    build = _run_command(
        [
            str(python_exe),
            "-m",
            "maturin",
            "develop",
            "--manifest-path",
            "rust_ext/Cargo.toml",
        ],
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Build Rust backend with maturin",
    )
    if not build.ok:
        rust.error = "Rust backend build failed; continuing with Python fallback."
        rust.remediation_commands.extend(
            [
                f"{python_exe} -m maturin develop --manifest-path rust_ext/Cargo.toml",
                f'{python_exe} -c "import gl260_rust_ext as m; print(m.__file__)"',
            ]
        )
        return rust

    verify = _run_command(
        [str(python_exe), "-c", "import gl260_rust_ext as m; print(m.__file__)"],
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Verify Rust backend import in primary runtime",
    )
    if not verify.ok:
        rust.error = (
            "Rust backend import verification failed; continuing with Python fallback."
        )
        rust.remediation_commands.extend(
            [
                f"{python_exe} -m maturin develop --manifest-path rust_ext/Cargo.toml",
                f'{python_exe} -c "import gl260_rust_ext as m; print(m.__file__)"',
            ]
        )
        return rust

    rust.ready = True
    return rust


def _print_environment_status(result: EnvironmentProvisionResult) -> None:
    """Print setup status for one environment target.

    Purpose:
        Emit concise, consistent status lines for environment provisioning.
    Why:
        Users need quick visibility into which runtime is ready and what failed.
    Inputs:
        result: Environment provisioning summary.
    Outputs:
        None.
    Side Effects:
        Writes status text to stdout.
    Exceptions:
        None.
    """

    status = "READY" if result.ready else "NOT READY"
    print(f"[ENV] {result.label}: {status}")
    if result.interpreter:
        print(f"      interpreter: {result.interpreter}")
    if result.error:
        print(f"      reason: {result.error}")
    for command in result.remediation_commands:
        print(f"      repair: {command}")


def _print_rust_status(result: RustSetupResult) -> None:
    """Print setup status for Rust backend provisioning.

    Purpose:
        Emit one summary block for Rust toolchain/build readiness.
    Why:
        Rust setup is optional for app startup but still requires transparent
        diagnostics and exact repair commands when unavailable.
    Inputs:
        result: Rust setup summary.
    Outputs:
        None.
    Side Effects:
        Writes status text to stdout.
    Exceptions:
        None.
    """

    if not result.attempted:
        print("[RUST] SKIPPED")
        return
    status = "READY" if result.ready else "FALLBACK TO PYTHON"
    print(f"[RUST] {status}")
    if result.error:
        print(f"       reason: {result.error}")
    for command in result.remediation_commands:
        print(f"       repair: {command}")


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser for bootstrap installer options.

    Purpose:
        Define user-facing installer flags and help text.
    Why:
        Deterministic setup requires explicit override hooks for interpreter
        selection and a no-mutation planning mode.
    Inputs:
        None.
    Outputs:
        Configured argparse parser instance.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    parser = argparse.ArgumentParser(
        description="Bootstrap installer for GL-260 local development runtime."
    )
    parser.add_argument(
        "--python-std",
        default="",
        help="Optional explicit path to standard Python interpreter for .venv.",
    )
    parser.add_argument(
        "--python-ft",
        default="",
        help=(
            "Optional explicit path to free-threaded Python interpreter for .venv-314t."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned setup commands without applying changes.",
    )
    return parser


def main() -> int:
    """Run the end-to-end bootstrap installer workflow.

    Purpose:
        Orchestrate interpreter discovery, environment provisioning, optional
        Rust backend build, and final launch command output.
    Why:
        End users need one reliable setup command that works across supported
        operating systems and privilege levels.
    Inputs:
        CLI flags parsed from process arguments.
    Outputs:
        Process exit code: 0 when at least one runnable environment is ready,
        1 when no runnable environment is available.
    Side Effects:
        May create environments, install dependencies/tooling, build Rust module.
    Exceptions:
        Repository validation errors are printed and converted to exit code 1.
    """

    args = _build_arg_parser().parse_args()
    try:
        repo_root = _resolve_repo_root()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        print(f"RUN COMMAND: {_build_run_command(STD_ENV_DIRNAME)}")
        return 1

    print("GL-260 Bootstrap Installer")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Repository root: {repo_root}")
    if Path.cwd().resolve() != repo_root:
        print(
            f"[INFO] Current directory is {Path.cwd().resolve()}, "
            f"commands will run from {repo_root}."
        )
    if args.dry_run:
        print("[INFO] Dry-run enabled. No setup changes will be applied.")

    std_interpreter = _resolve_standard_interpreter(args.python_std, cwd=repo_root)
    ft_interpreter = _resolve_free_threaded_interpreter(args.python_ft, cwd=repo_root)

    std_result = _provision_environment(
        label="standard",
        env_dir=repo_root / STD_ENV_DIRNAME,
        interpreter=std_interpreter,
        repo_root=repo_root,
        dry_run=args.dry_run,
    )
    ft_result = _provision_environment(
        label="free-threaded",
        env_dir=repo_root / FT_ENV_DIRNAME,
        interpreter=ft_interpreter,
        repo_root=repo_root,
        dry_run=args.dry_run,
    )

    primary_env = ft_result if ft_result.ready else std_result
    rust_result = RustSetupResult(attempted=False, ready=False)
    if primary_env.ready:
        rust_result = _ensure_rust_backend(
            repo_root=repo_root,
            python_exe=primary_env.python_path,
            dry_run=args.dry_run,
        )

    # Keep the run command deterministic and free-threaded-first for copy/paste output.
    preferred_env_name = FT_ENV_DIRNAME if ft_result.ready else STD_ENV_DIRNAME
    run_command = _build_run_command(preferred_env_name)

    print("")
    print("Setup Summary")
    print("-------------")
    _print_environment_status(std_result)
    _print_environment_status(ft_result)
    _print_rust_status(rust_result)
    print(f"RUN COMMAND: {run_command}")

    if not primary_env.ready:
        print("[ERROR] No runnable Python environment was provisioned.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
