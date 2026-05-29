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
GNU_TARGET = "x86_64-pc-windows-gnu"
GNU_TOOLCHAIN = "stable-x86_64-pc-windows-gnu"
MINGW_FALLBACK_BIN_DIR = Path.home() / "mingw64" / "bin"
RUNTIME_IMPORT_PROBES = [
    ("tkinter", "tkinter", "tk", True),
    ("matplotlib", "matplotlib", "matplotlib", True),
    (
        "matplotlib Tk backend",
        "matplotlib.backends.backend_tkagg",
        "matplotlib",
        True,
    ),
    ("numpy", "numpy", "numpy", True),
    ("openpyxl", "openpyxl", "openpyxl", True),
    ("pandas", "pandas", "pandas", True),
    ("scipy", "scipy", "scipy", True),
    ("markdown", "markdown", "markdown", False),
    ("latex2mathml", "latex2mathml.converter", "latex2mathml", False),
    ("mplcursors", "mplcursors", "mplcursors", False),
    ("pypdf", "pypdf", "pypdf", False),
    ("PyPDF2", "PyPDF2", "PyPDF2", False),
    ("great_tables", "great_tables", "great_tables", False),
    ("customtkinter", "customtkinter", "customtkinter", False),
    ("chempy", "chempy", "chempy", False),
]


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
    skipped: bool = False
    error: str = ""
    warnings: list[str] = field(default_factory=list)
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
            encoding="utf-8",
            errors="replace",
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


def _summarize_command_failure(result: CommandResult, *, limit: int = 1800) -> str:
    """Return a concise command failure diagnostic.

    Purpose:
        Trim noisy tool output to the most actionable failure text.
    Why:
        Pip and build tools can emit hundreds of warning lines, which makes the
        setup summary hard to use when a repair command is needed.
    Inputs:
        result: Command result to summarize.
        limit: Maximum number of trailing characters to return.
    Outputs:
        Trimmed stdout/stderr diagnostic text.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    text = str(result.stderr or result.stdout or "").strip()
    if not text:
        return f"Command exited with status {result.returncode}."
    if len(text) <= limit:
        return text
    return "... " + text[-limit:]


def _run_pip_install(
    *,
    python_path: Path,
    pip_args: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    dry_run: bool,
    description: str,
) -> CommandResult:
    """Run a pip install command with a resilient no-cache retry.

    Purpose:
        Install packages while recovering from corrupt pip cache entries and
        transient network resets.
    Why:
        Fresh VS Code setup should be as painless as possible, and a single
        interrupted wheel download should not permanently fail the installer.
    Inputs:
        python_path: Interpreter whose pip module should be used.
        pip_args: Arguments after `python -m pip install`.
        cwd: Command working directory.
        env: Optional subprocess environment.
        dry_run: True to print commands without executing.
        description: User-facing setup step label.
    Outputs:
        CommandResult from the successful first attempt or the retry attempt.
    Side Effects:
        May install or upgrade packages in the target interpreter.
    Exceptions:
        Process startup failures are captured in CommandResult.
    """

    first = _run_command(
        [str(python_path), "-m", "pip", "install", *pip_args],
        cwd=cwd,
        env=env,
        dry_run=dry_run,
        description=description,
    )
    if first.ok or dry_run:
        return first

    retry = _run_command(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--retries",
            "10",
            "--timeout",
            "60",
            *pip_args,
        ],
        cwd=cwd,
        env=env,
        dry_run=dry_run,
        description=f"Retry {description} without pip cache",
    )
    return retry if retry.ok else retry


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


def _runtime_import_probe_script() -> str:
    """Build the interpreter-side runtime dependency probe script.

    Purpose:
        Generate a compact Python command that checks the modules needed by
        interactive GL-260 runtime workflows.
    Why:
        Fresh installs should fail before launch with clear missing-package
        diagnostics instead of surfacing import errors inside the GUI startup.
    Inputs:
        None.
    Outputs:
        Python source string passed to the target environment interpreter.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    probe_pairs = repr(RUNTIME_IMPORT_PROBES)
    return (
        "import importlib.util, sys\n"
        f"required = {probe_pairs}\n"
        "missing_required = []\n"
        "missing_optional = []\n"
        "missing_required_packages = []\n"
        "missing_optional_packages = []\n"
        "for label, module_name, package_name, is_required in required:\n"
        "    try:\n"
        "        spec = importlib.util.find_spec(module_name)\n"
        "    except (ImportError, AttributeError, ValueError):\n"
        "        spec = None\n"
        "    if spec is None:\n"
        "        target = missing_required if is_required else missing_optional\n"
        "        package_target = (\n"
        "            missing_required_packages\n"
        "            if is_required\n"
        "            else missing_optional_packages\n"
        "        )\n"
        "        target.append(f'{label} ({module_name})')\n"
        "        package_target.append(package_name)\n"
        "if missing_optional:\n"
        "    print(\n"
        "        'Optional runtime modules missing: '\n"
        "        + ', '.join(missing_optional)\n"
        "    )\n"
        "    print(\n"
        "        'GL260_MISSING_OPTIONAL_PIP_PACKAGES='\n"
        "        + ','.join(sorted(set(missing_optional_packages)))\n"
        "    )\n"
        "if missing_required:\n"
        "    print(\n"
        "        'Missing required runtime modules: '\n"
        "        + ', '.join(missing_required)\n"
        "    )\n"
        "    print(\n"
        "        'GL260_MISSING_REQUIRED_PIP_PACKAGES='\n"
        "        + ','.join(sorted(set(missing_required_packages)))\n"
        "    )\n"
        "    raise SystemExit(2)\n"
        "print(f'Runtime module probe OK: {len(required)} modules available')\n"
    )


def _validate_runtime_imports(
    *,
    label: str,
    python_path: Path,
    repo_root: Path,
    dry_run: bool,
) -> CommandResult:
    """Validate that a provisioned environment can resolve runtime modules.

    Purpose:
        Confirm installed packages cover the import surface GL-260 needs at
        startup and for optional user-facing workflows.
    Why:
        `pip install -r requirements.txt` can report success while an expected
        package is unavailable in the target interpreter, especially after PATH
        or interpreter mismatches.
    Inputs:
        label: Human-readable environment label for command output.
        python_path: Environment-local interpreter path to validate.
        repo_root: Repository root for subprocess execution.
        dry_run: True to print the probe without executing it.
    Outputs:
        CommandResult for the dependency probe.
    Side Effects:
        Launches the environment interpreter when not in dry-run mode.
    Exceptions:
        Process startup failures are captured in CommandResult.
    """

    return _run_command(
        [str(python_path), "-c", _runtime_import_probe_script()],
        cwd=repo_root,
        dry_run=dry_run,
        description=f"Validate runtime imports in {label} environment",
    )


def _extract_missing_runtime_packages(probe_result: CommandResult) -> list[str]:
    """Extract pip package names from a failed runtime dependency probe.

    Purpose:
        Convert structured probe output into a targeted package install list.
    Why:
        If a bulk requirements install is interrupted, retrying only missing
        runtime packages can salvage an otherwise usable environment faster.
    Inputs:
        probe_result: Result returned by `_validate_runtime_imports`.
    Outputs:
        Ordered package names that should be installed, with duplicates removed.
    Side Effects:
        None.
    Exceptions:
        Malformed probe output is ignored and returns an empty list.
    """

    marker = "GL260_MISSING_REQUIRED_PIP_PACKAGES="
    packages: list[str] = []
    seen: set[str] = set()
    output = "\n".join([probe_result.stdout or "", probe_result.stderr or ""])
    for line in output.splitlines():
        if not line.startswith(marker):
            continue
        raw_packages = line.removeprefix(marker).split(",")
        for raw_package in raw_packages:
            package = raw_package.strip()
            normalized = package.lower()
            if not package or normalized in seen:
                continue
            packages.append(package)
            seen.add(normalized)
    return packages


def _extract_optional_runtime_warnings(probe_result: CommandResult) -> list[str]:
    """Extract optional-package warning lines from a runtime probe.

    Purpose:
        Preserve optional dependency visibility without failing a runnable app
        environment.
    Why:
        Optional workflow packages such as `chempy` should be reported clearly
        when unavailable, but a transient optional download failure should not
        block basic GL-260 startup.
    Inputs:
        probe_result: Result returned by `_validate_runtime_imports`.
    Outputs:
        User-facing warning strings for final environment status output.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    warnings: list[str] = []
    output = "\n".join([probe_result.stdout or "", probe_result.stderr or ""])
    for line in output.splitlines():
        if line.startswith("Optional runtime modules missing: "):
            warnings.append(line.strip())
    return warnings


def _install_missing_runtime_packages(
    *,
    label: str,
    python_path: Path,
    packages: list[str],
    repo_root: Path,
    dry_run: bool,
) -> CommandResult:
    """Install runtime packages individually after a bulk install failure.

    Purpose:
        Recover from interrupted batch downloads by installing only packages
        still missing from the target environment.
    Why:
        Individual installs reduce repeated network work and make the installer
        more resilient on unstable connections.
    Inputs:
        label: Human-readable environment label for command output.
        python_path: Environment-local interpreter path.
        packages: Pip package names to install.
        repo_root: Repository root for subprocess execution.
        dry_run: True to print commands without executing.
    Outputs:
        CommandResult for the first failed install or the final successful one.
    Side Effects:
        May install packages into the target environment.
    Exceptions:
        Process startup failures are captured in CommandResult.
    """

    last_result = CommandResult(
        returncode=0,
        stdout="",
        stderr="",
        command=[],
        dry_run=dry_run,
    )
    for package in packages:
        last_result = _run_pip_install(
            python_path=python_path,
            pip_args=[package],
            cwd=repo_root,
            dry_run=dry_run,
            description=f"Install missing runtime package {package} in {label}",
        )
        if not last_result.ok:
            return last_result
    return last_result


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

    pip_upgrade = _run_pip_install(
        python_path=python_path,
        pip_args=["--upgrade", "pip"],
        cwd=repo_root,
        dry_run=dry_run,
        description=f"Upgrade pip in {label} environment",
    )
    if not pip_upgrade.ok:
        result.error = (
            f"Failed to upgrade pip in {label} environment: "
            f"{_summarize_command_failure(pip_upgrade)}"
        )
        return result

    install_requirements = _run_pip_install(
        python_path=python_path,
        pip_args=["-r", "requirements.txt"],
        cwd=repo_root,
        dry_run=dry_run,
        description=f"Install requirements in {label} environment",
    )
    if not install_requirements.ok:
        import_probe_after_failure = _validate_runtime_imports(
            label=label,
            python_path=python_path,
            repo_root=repo_root,
            dry_run=dry_run,
        )
        if import_probe_after_failure.ok:
            result.warnings.extend(
                _extract_optional_runtime_warnings(import_probe_after_failure)
            )
            result.ready = True
            return result

        missing_packages = _extract_missing_runtime_packages(import_probe_after_failure)
        if missing_packages:
            targeted_install = _install_missing_runtime_packages(
                label=label,
                python_path=python_path,
                packages=missing_packages,
                repo_root=repo_root,
                dry_run=dry_run,
            )
            if targeted_install.ok:
                final_probe = _validate_runtime_imports(
                    label=label,
                    python_path=python_path,
                    repo_root=repo_root,
                    dry_run=dry_run,
                )
                if final_probe.ok:
                    result.warnings.extend(
                        _extract_optional_runtime_warnings(final_probe)
                    )
                    result.ready = True
                    return result
                result.error = (
                    "Runtime dependency validation failed after targeted "
                    f"installs in {label} environment: "
                    f"{_summarize_command_failure(final_probe)}"
                )
                return result
            result.error = (
                "Failed to install missing runtime packages in "
                f"{label} environment: {_summarize_command_failure(targeted_install)}"
            )
            return result

        result.error = (
            "Failed to install requirements in "
            f"{label} environment: {_summarize_command_failure(install_requirements)}"
        )
        return result

    import_probe = _validate_runtime_imports(
        label=label,
        python_path=python_path,
        repo_root=repo_root,
        dry_run=dry_run,
    )
    if not import_probe.ok:
        result.error = (
            "Runtime dependency validation failed in "
            f"{label} environment: "
            f"{_summarize_command_failure(import_probe)}"
        )
        result.remediation_commands.append(
            f"{python_path} -m pip install -r requirements.txt"
        )
        return result

    result.warnings.extend(_extract_optional_runtime_warnings(import_probe))
    result.ready = True
    return result


def _skipped_environment_result(
    *,
    label: str,
    env_dir: Path,
    reason: str,
) -> EnvironmentProvisionResult:
    """Create a status object for an intentionally skipped environment.

    Purpose:
        Report optimization decisions in the final installer summary.
    Why:
        Hybrid setup should avoid redundant package installs when `.venv-314t`
        is ready, but users still need to know that `.venv` was skipped by
        design instead of silently omitted.
    Inputs:
        label: Human-readable environment label.
        env_dir: Target virtualenv directory path.
        reason: User-facing explanation for skipping provisioning.
    Outputs:
        EnvironmentProvisionResult marked as skipped.
    Side Effects:
        None.
    Exceptions:
        None.
    """

    result = EnvironmentProvisionResult(label=label, env_dir=env_dir)
    result.skipped = True
    result.error = reason
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


def _prepend_unique_path_entries(
    base_path: str,
    entries: list[Path],
) -> str:
    """Prepend existing path entries while preserving uniqueness.

    Purpose:
        Make known-good tool directories win executable resolution.
    Why:
        Fresh Windows shells can resolve Python package shims named `cargo.exe`
        or `rustc.exe` before rustup-managed compiler tools.
    Inputs:
        base_path: Original PATH value.
        entries: Candidate directories to prepend when they exist.
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
        if not entry.is_dir():
            continue
        resolved = str(entry)
        normalized = os.path.normcase(resolved)
        if normalized in seen:
            continue
        prefix.append(resolved)
        seen.add(normalized)
    return os.pathsep.join(prefix + existing)


def _resolve_rustup_tool_path(
    *,
    tool_name: str,
    toolchain: str,
    repo_root: Path,
    env: dict[str, str],
    dry_run: bool,
) -> Path | None:
    """Resolve a rustup-managed compiler tool path.

    Purpose:
        Locate the concrete `rustc` or `cargo` executable managed by rustup.
    Why:
        PATH can contain stale Python-side shims, so Rust setup should prefer
        rustup's authoritative tool resolution before building the extension.
    Inputs:
        tool_name: Rust tool to resolve, such as `rustc` or `cargo`.
        toolchain: Rustup toolchain token.
        repo_root: Repository root for command execution.
        env: Subprocess environment used for rustup resolution.
        dry_run: True to skip filesystem-dependent resolution.
    Outputs:
        Resolved tool path, or None when unavailable.
    Side Effects:
        Executes `rustup which` when not in dry-run mode.
    Exceptions:
        None; resolution failures return None.
    """

    if dry_run:
        return None
    resolved = _run_command(
        ["rustup", "which", "--toolchain", toolchain, tool_name],
        cwd=repo_root,
        env=env,
        dry_run=False,
        description=f"Resolve rustup-managed {tool_name}",
    )
    if not resolved.ok:
        return None
    lines = str(resolved.stdout or resolved.stderr or "").strip().splitlines()
    if not lines:
        return None
    candidate = Path(lines[-1].strip())
    return candidate if candidate.is_file() else None


def _resolve_mingw_bin_dir() -> Path | None:
    """Locate a MinGW bin directory usable for GNU Rust builds.

    Purpose:
        Find `gcc.exe` and related linker tools for the Windows GNU fallback.
    Why:
        Fresh VS Code installations do not include MSVC `link.exe`, so the
        installer needs a non-MSVC backend build route when MinGW is present.
    Inputs:
        None.
    Outputs:
        Path to a MinGW bin directory, or None when unavailable.
    Side Effects:
        Reads PATH and the user-home fallback directory.
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


def _build_gnu_rust_env(
    *,
    base_env: dict[str, str],
    repo_root: Path,
    python_exe: Path,
    dry_run: bool,
) -> dict[str, str] | None:
    """Build environment overrides for the Windows GNU Rust fallback.

    Purpose:
        Configure maturin/cargo to use rustup's GNU toolchain and MinGW linker.
    Why:
        This keeps Rust backend setup viable on machines with VS Code and MinGW
        but without Visual Studio C++ Build Tools.
    Inputs:
        base_env: Source environment from the primary Rust setup attempt.
        repo_root: Repository root for rustup tool resolution.
        python_exe: Target virtualenv interpreter.
        dry_run: True to skip filesystem-dependent resolution.
    Outputs:
        Environment dictionary for GNU build, or None when prerequisites are
        unavailable.
    Side Effects:
        Executes rustup resolution probes when not in dry-run mode.
    Exceptions:
        None.
    """

    if os.name != "nt":
        return None
    mingw_bin = _resolve_mingw_bin_dir()
    if not dry_run and mingw_bin is None:
        return None

    env = dict(base_env)
    rustc_path = _resolve_rustup_tool_path(
        tool_name="rustc",
        toolchain=GNU_TOOLCHAIN,
        repo_root=repo_root,
        env=env,
        dry_run=dry_run,
    )
    cargo_path = _resolve_rustup_tool_path(
        tool_name="cargo",
        toolchain=GNU_TOOLCHAIN,
        repo_root=repo_root,
        env=env,
        dry_run=dry_run,
    )
    if not dry_run and (rustc_path is None or cargo_path is None):
        return None

    target_upper = GNU_TARGET.upper().replace("-", "_")
    env["PYO3_PYTHON"] = str(python_exe)
    env["VIRTUAL_ENV"] = str(python_exe.parents[1])
    env["RUSTUP_TOOLCHAIN"] = GNU_TOOLCHAIN
    env["CARGO_BUILD_TARGET"] = GNU_TARGET
    if rustc_path:
        env["RUSTC"] = str(rustc_path)
    if cargo_path:
        env["CARGO"] = str(cargo_path)
    if mingw_bin:
        env[f"CARGO_TARGET_{target_upper}_LINKER"] = str(mingw_bin / "gcc.exe")
        env["CC_x86_64_pc_windows_gnu"] = str(mingw_bin / "gcc.exe")
        env["CXX_x86_64_pc_windows_gnu"] = str(mingw_bin / "g++.exe")
        env["AR_x86_64_pc_windows_gnu"] = str(mingw_bin / "ar.exe")

    path_entries = [python_exe.parent]
    if rustc_path:
        path_entries.append(rustc_path.parent)
    if cargo_path:
        path_entries.append(cargo_path.parent)
    if mingw_bin:
        path_entries.append(mingw_bin)
    env["PATH"] = _prepend_unique_path_entries(env.get("PATH", ""), path_entries)
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

    rustc_path = _resolve_rustup_tool_path(
        tool_name="rustc",
        toolchain="stable",
        repo_root=repo_root,
        env=base_env,
        dry_run=dry_run,
    )
    cargo_path = _resolve_rustup_tool_path(
        tool_name="cargo",
        toolchain="stable",
        repo_root=repo_root,
        env=base_env,
        dry_run=dry_run,
    )
    if rustc_path and cargo_path:
        base_env["RUSTC"] = str(rustc_path)
        base_env["CARGO"] = str(cargo_path)
        base_env["PYO3_PYTHON"] = str(python_exe)
        base_env["VIRTUAL_ENV"] = str(python_exe.parents[1])
        base_env["PATH"] = _prepend_unique_path_entries(
            base_env.get("PATH", ""),
            [python_exe.parent, rustc_path.parent, cargo_path.parent],
        )

    rustc_command = (
        [str(rustc_path), "--version"] if rustc_path else ["rustc", "--version"]
    )
    cargo_command = (
        [str(cargo_path), "--version"] if cargo_path else ["cargo", "--version"]
    )
    rustc_ok = _run_command(
        rustc_command,
        cwd=repo_root,
        env=base_env,
        dry_run=dry_run,
        description="Check rustc availability",
    )
    cargo_ok = _run_command(
        cargo_command,
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

    maturin_install = _run_pip_install(
        python_path=python_exe,
        pip_args=["maturin>=1.12,<2.0"],
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
        gnu_env = _build_gnu_rust_env(
            base_env=base_env,
            repo_root=repo_root,
            python_exe=python_exe,
            dry_run=dry_run,
        )
        if gnu_env is not None:
            gnu_build = _run_command(
                [
                    str(python_exe),
                    "-m",
                    "maturin",
                    "develop",
                    "--manifest-path",
                    "rust_ext/Cargo.toml",
                    "--target",
                    GNU_TARGET,
                ],
                cwd=repo_root,
                env=gnu_env,
                dry_run=dry_run,
                description="Build Rust backend with GNU/MinGW fallback",
            )
            if gnu_build.ok:
                gnu_verify = _run_command(
                    [
                        str(python_exe),
                        "-c",
                        (
                            "import gl260_rust_ext as pkg; "
                            "import gl260_rust_ext.gl260_rust_ext as ext; "
                            "print(getattr(ext, '__file__', "
                            "getattr(pkg, '__file__', '')))"
                        ),
                    ],
                    cwd=repo_root,
                    env=gnu_env,
                    dry_run=dry_run,
                    description="Verify Rust backend import after GNU fallback",
                )
                if gnu_verify.ok:
                    rust.ready = True
                    return rust
                rust.error = (
                    "Rust GNU fallback import verification failed; continuing "
                    f"with Python fallback. {_summarize_command_failure(gnu_verify)}"
                )
                return rust

        rust.error = "Rust backend build failed; continuing with Python fallback."
        rust.remediation_commands.extend(
            [
                f"{python_exe} -m maturin develop --manifest-path rust_ext/Cargo.toml",
                (
                    f"{python_exe} -m maturin develop --manifest-path "
                    f"rust_ext/Cargo.toml --target {GNU_TARGET}"
                ),
                (
                    f'{python_exe} -c "import gl260_rust_ext as pkg; '
                    "import gl260_rust_ext.gl260_rust_ext as ext; "
                    "print(ext.__file__)\""
                ),
            ]
        )
        return rust

    verify = _run_command(
        [
            str(python_exe),
            "-c",
            (
                "import gl260_rust_ext as pkg; "
                "import gl260_rust_ext.gl260_rust_ext as ext; "
                "print(getattr(ext, '__file__', getattr(pkg, '__file__', '')))"
            ),
        ],
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
                (
                    f'{python_exe} -c "import gl260_rust_ext as pkg; '
                    "import gl260_rust_ext.gl260_rust_ext as ext; "
                    "print(ext.__file__)\""
                ),
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

    status = (
        "SKIPPED" if result.skipped else ("READY" if result.ready else "NOT READY")
    )
    print(f"[ENV] {result.label}: {status}")
    if result.interpreter:
        print(f"      interpreter: {result.interpreter}")
    if result.error:
        print(f"      reason: {result.error}")
    for warning in result.warnings:
        print(f"      warning: {warning}")
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
    parser.add_argument(
        "--with-standard-env",
        action="store_true",
        help=(
            "Provision .venv even when the preferred .venv-314t environment "
            "is ready."
        ),
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

    ft_interpreter = _resolve_free_threaded_interpreter(args.python_ft, cwd=repo_root)

    ft_result = _provision_environment(
        label="free-threaded",
        env_dir=repo_root / FT_ENV_DIRNAME,
        interpreter=ft_interpreter,
        repo_root=repo_root,
        dry_run=args.dry_run,
    )

    std_result: EnvironmentProvisionResult
    if ft_result.ready and not args.with_standard_env:
        std_result = _skipped_environment_result(
            label="standard",
            env_dir=repo_root / STD_ENV_DIRNAME,
            reason=(
                "Preferred free-threaded environment is ready; standard "
                "fallback provisioning was skipped for faster setup. Re-run "
                "with --with-standard-env to create it too."
            ),
        )
    else:
        std_interpreter = _resolve_standard_interpreter(args.python_std, cwd=repo_root)
        std_result = _provision_environment(
            label="standard",
            env_dir=repo_root / STD_ENV_DIRNAME,
            interpreter=std_interpreter,
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
