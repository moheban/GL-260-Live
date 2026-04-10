"""Regression tests for deterministic docs MathML build contracts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def load_script_module(script_name: str, module_name: str) -> ModuleType:
    """Load one docs build script as an importable module object.

    Purpose:
    - Import standalone scripts under ``scripts/`` for direct function-level checks.
    Why:
    - The docs builders are script files, not installable package modules.
    Inputs:
    - ``script_name``: Script filename under ``scripts/``.
    - ``module_name``: Synthetic module name used for isolated imports.
    Outputs:
    - Loaded module object exposing the script's functions/constants.
    Side effects:
    - Executes top-level script module code once for each unique module name.
    Exceptions:
    - ``RuntimeError`` when import specification/loader resolution fails.
    """

    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {module_path}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_docs_html(script_name: str, module_name: str) -> str:
    """Build generated docs HTML text from one builder script.

    Purpose:
    - Reuse the script's canonical generation path for assertion targets.
    Why:
    - Tests should inspect emitted shell content exactly as runtime will consume it.
    Inputs:
    - ``script_name``: Builder filename under ``scripts/``.
    - ``module_name``: Synthetic module namespace for import isolation.
    Outputs:
    - Generated HTML document text from ``build_once()``.
    Side effects:
    - Reads markdown source files referenced by the target script.
    Exceptions:
    - ``AssertionError`` when the loaded script does not expose ``build_once``.
    """

    module = load_script_module(script_name, module_name)
    build_once = getattr(module, "build_once", None)
    if callable(build_once):
        return build_once()
    build_expected_html = getattr(module, "build_expected_html", None)
    markdown_path = getattr(module, "MANUAL_MD_PATH", None)
    assert callable(build_expected_html)
    assert isinstance(markdown_path, Path)
    return build_expected_html(markdown_path)


@pytest.mark.parametrize(
    ("script_name", "module_name"),
    [
        ("build_user_manual.py", "build_user_manual_mathml_contract_test"),
        (
            "build_equilibrium_walkthrough.py",
            "build_equilibrium_mathml_contract_test",
        ),
    ],
)
def test_mathml_contract_no_runtime_mathjax(
    script_name: str,
    module_name: str,
) -> None:
    """Ensure generated docs shells contain MathML and no runtime MathJax hooks.

    Purpose:
    - Lock in deterministic build-time math rendering contract.
    Why:
    - Runtime MathJax loaders can fail on offline/restricted environments.
    Inputs:
    - ``script_name`` and ``module_name`` from parametrized test cases.
    Outputs:
    - None.
    Side effects:
    - Reads source markdown via script ``build_once()``.
    Exceptions:
    - Raises assertions when runtime MathJax bootstrap paths reappear.
    """

    html = build_docs_html(script_name, module_name)
    assert "<math" in html
    assert "window.MathJax" not in html
    assert "loadMathJaxDualMode" not in html
    assert "typesetPromise" not in html


@pytest.mark.parametrize(
    ("script_name", "module_name"),
    [
        ("build_user_manual.py", "build_user_manual_no_fenced_latex_test"),
        (
            "build_equilibrium_walkthrough.py",
            "build_equilibrium_no_fenced_latex_test",
        ),
    ],
)
def test_no_fenced_latex_code_blocks_in_output(
    script_name: str,
    module_name: str,
) -> None:
    """Ensure generated output contains no raw fenced-LaTeX code blocks.

    Purpose:
    - Confirm fenced `````latex```` payloads are converted to MathML at build time.
    Why:
    - Shipping raw LaTeX blocks would indicate conversion regressions.
    Inputs:
    - ``script_name`` and ``module_name`` from parametrized test cases.
    Outputs:
    - None.
    Side effects:
    - Reads source markdown via script ``build_once()``.
    Exceptions:
    - Raises assertions when fenced-LaTeX code blocks remain in output.
    """

    html = build_docs_html(script_name, module_name)
    assert 'class="language-latex"' not in html
    assert "<code class=\"language-latex\">" not in html
    assert 'data-math-origin="latex-fence"' in html


@pytest.mark.parametrize(
    ("script_name", "module_name"),
    [
        ("build_user_manual.py", "build_user_manual_fail_fast_test"),
        ("build_equilibrium_walkthrough.py", "build_equilibrium_fail_fast_test"),
    ],
)
def test_mathml_conversion_fail_fast_contract(
    script_name: str,
    module_name: str,
) -> None:
    """Ensure conversion failures raise immediately with actionable diagnostics.

    Purpose:
    - Lock strict fail-fast behavior for docs math conversion.
    Why:
    - Broken equations must fail builds instead of shipping stale/raw math.
    Inputs:
    - ``script_name`` and ``module_name`` from parametrized test cases.
    Outputs:
    - None.
    Side effects:
    - Temporarily patches conversion callable inside loaded script module.
    Exceptions:
    - Raises assertions when conversion failures are swallowed.
    """

    module = load_script_module(script_name, module_name)
    render_mathml_html = module.render_mathml_html
    assert callable(render_mathml_html)

    original_converter = module.latex_to_mathml

    def fail_converter(*_args, **_kwargs) -> str:
        """Force converter failure to validate build failure behavior."""

        raise RuntimeError("forced conversion failure")

    module.latex_to_mathml = fail_converter
    try:
        with pytest.raises(ValueError, match="failed to convert LaTeX"):
            render_mathml_html(
                '<pre><code class="language-latex">x^2</code></pre>',
                source_label=f"{script_name} forced failure",
            )
    finally:
        module.latex_to_mathml = original_converter
