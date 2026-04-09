"""Regression tests for docs HTML math-render runtime shell behavior."""

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
        ("build_user_manual.py", "build_user_manual_render_test"),
        ("build_equilibrium_walkthrough.py", "build_equilibrium_render_test"),
    ],
)
def test_mathjax_source_priority_order(script_name: str, module_name: str) -> None:
    """Verify MathJax source list exists and preserves required priority order.

    Purpose:
    - Ensure docs shells attempt local paths before CDN fallbacks consistently.
    Why:
    - Source-order regressions can break offline and relative-path workflows.
    Inputs:
    - ``script_name`` and ``module_name`` from parametrized test cases.
    Outputs:
    - None.
    Side effects:
    - Reads source markdown via script ``build_once()``.
    Exceptions:
    - Raises assertions when required source entries are missing or reordered.
    """

    html = build_docs_html(script_name, module_name)
    expected_sources = [
        "mathjax/es5/tex-mml-chtml.js",
        "../mathjax/es5/tex-mml-chtml.js",
        "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js",
    ]
    indices = [html.find(source) for source in expected_sources]
    assert all(index >= 0 for index in indices)
    assert indices == sorted(indices)


@pytest.mark.parametrize(
    ("script_name", "module_name"),
    [
        ("build_user_manual.py", "build_user_manual_typeset_test"),
        ("build_equilibrium_walkthrough.py", "build_equilibrium_typeset_test"),
    ],
)
def test_per_block_typeset_contract(script_name: str, module_name: str) -> None:
    """Ensure fenced-LaTeX rendering is per-block rather than batch all-or-nothing.

    Purpose:
    - Lock in block-level MathJax typesetting behavior for resiliency.
    Why:
    - One invalid fenced block must not prevent other valid blocks from rendering.
    Inputs:
    - ``script_name`` and ``module_name`` from parametrized test cases.
    Outputs:
    - None.
    Side effects:
    - Reads source markdown via script ``build_once()``.
    Exceptions:
    - Raises assertions when batch-only typesetting contract reappears.
    """

    html = build_docs_html(script_name, module_name)
    assert "window.MathJax.typesetPromise([entry.displayNode])" in html
    assert "window.MathJax.typesetPromise(displayNodes)" not in html


@pytest.mark.parametrize(
    ("script_name", "module_name"),
    [
        ("build_user_manual.py", "build_user_manual_warning_test"),
        ("build_equilibrium_walkthrough.py", "build_equilibrium_warning_test"),
    ],
)
def test_failure_warning_contract(script_name: str, module_name: str) -> None:
    """Validate per-block failure warning and fallback status annotations exist.

    Purpose:
    - Enforce explicit user-visible fallback behavior on math-render failures.
    Why:
    - Operators need clear diagnostics when one LaTeX block cannot be typeset.
    Inputs:
    - ``script_name`` and ``module_name`` from parametrized test cases.
    Outputs:
    - None.
    Side effects:
    - Reads source markdown via script ``build_once()``.
    Exceptions:
    - Raises assertions when failure-warning contract markers are missing.
    """

    html = build_docs_html(script_name, module_name)
    assert 'data-math-render-status="failed"' in html
    assert "math-render-warning" in html
    assert "Math rendering failed for this block. Showing raw LaTeX." in html
    assert "MathJax could not be loaded. Showing raw LaTeX." in html


@pytest.mark.parametrize(
    ("script_name", "module_name"),
    [
        ("build_user_manual.py", "build_user_manual_single_bootstrap_test"),
        (
            "build_equilibrium_walkthrough.py",
            "build_equilibrium_single_bootstrap_test",
        ),
    ],
)
def test_single_math_bootstrap_pipeline(script_name: str, module_name: str) -> None:
    """Ensure each generated shell emits one canonical math bootstrap pipeline.

    Purpose:
    - Guard against duplicated MathJax bootstrap blocks in generated docs shells.
    Why:
    - Duplicate bootstrap paths can race each other and cause unstable LaTeX output.
    Inputs:
    - ``script_name`` and ``module_name`` from parametrized test cases.
    Outputs:
    - None.
    Side effects:
    - Reads source markdown via script ``build_once()``.
    Exceptions:
    - Raises assertions when canonical math helper functions are duplicated.
    """

    html = build_docs_html(script_name, module_name)
    assert html.count("function prepareLatexDisplayBlocks()") == 1
    assert html.count("function setMathRenderFailure(entry, reason)") == 1
    assert html.count("function loadScript(src)") == 1
    assert html.count("function loadMathJaxDualMode()") == 1
    assert html.count("function initializeMathRendering()") == 1
