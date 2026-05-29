"""Repository-root launcher for the GL-260 bootstrap installer.

Purpose:
    Delegate `python install_gl260.py` to the maintained installer under
    `scripts/install_gl260.py`.
Why:
    First-time users working in VS Code should not need to know the internal
    scripts directory before the environment exists.
Inputs:
    CLI arguments are preserved and forwarded through `sys.argv`.
Outputs:
    Returns the delegated installer's process exit status.
Side Effects:
    Executes the installer module, which may create virtual environments,
    install packages, install Rust tooling, and build the Rust extension.
Exceptions:
    Any installer exceptions follow the existing script behavior.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    """Run the maintained installer script from the repository root.

    Purpose:
        Provide a stable, discoverable entrypoint for fresh VS Code workflows.
    Why:
        Keeping the real implementation in `scripts/install_gl260.py` avoids
        duplicated setup logic while making root-level invocation painless.
    Inputs:
        None directly; existing process arguments remain in `sys.argv`.
    Outputs:
        Integer process exit status from the delegated installer.
    Side Effects:
        Executes `scripts/install_gl260.py` as `__main__`.
    Exceptions:
        Propagates unexpected delegation errors; converts `SystemExit` codes
        from the installer into an integer return value.
    """

    installer_path = Path(__file__).resolve().parent / "scripts" / "install_gl260.py"
    try:
        runpy.run_path(str(installer_path), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        if code is None:
            return 0
        print(code)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
