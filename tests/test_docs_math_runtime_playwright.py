"""Browser runtime smoke tests for generated docs MathML output."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


def load_script_module(script_name: str, module_name: str) -> ModuleType:
    """Load one docs build script as an importable module object.

    Purpose:
    - Import standalone scripts under ``scripts/`` for browser smoke checks.
    Why:
    - The docs builders are script files, not package modules.
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
    - Reuse canonical builder output for runtime browser assertions.
    Why:
    - Smoke checks must verify exactly what generated artifacts contain.
    Inputs:
    - ``script_name``: Builder filename under ``scripts/``.
    - ``module_name``: Synthetic module namespace for import isolation.
    Outputs:
    - Generated HTML document text from ``build_once()``.
    Side effects:
    - Reads markdown source files referenced by the target script.
    Exceptions:
    - ``AssertionError`` when expected builder functions are unavailable.
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


def resolve_browser_executable_path() -> Path | None:
    """Resolve a local Chromium-family executable for runtime smoke tests.

    Purpose:
    - Select one browser binary path without requiring Playwright downloads.
    Why:
    - Some environments block browser package downloads behind TLS inspection.
    Inputs:
    - None.
    Outputs:
    - Browser executable path when available; otherwise ``None``.
    Side effects:
    - Reads environment variable and checks filesystem paths.
    Exceptions:
    - None.
    """

    candidate_paths: list[Path] = []
    env_browser_path = str(os.environ.get("PLAYWRIGHT_BROWSER_EXECUTABLE", "")).strip()
    if env_browser_path:
        env_path = Path(env_browser_path)
        candidate_paths.append(env_path)
    candidate_paths.extend(
        [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ]
    )
    for candidate in candidate_paths:
        if candidate and candidate.exists():
            return candidate
    return None


def open_browser_page(playwright: Playwright) -> tuple[Browser, BrowserContext, Page]:
    """Launch one browser page for smoke rendering checks.

    Purpose:
    - Create an isolated page using a locally available browser binary.
    Why:
    - Runtime smoke tests should run even when Playwright-managed browser
      downloads are blocked by network policy.
    Inputs:
    - ``playwright``: Active Playwright session object.
    Outputs:
    - Tuple of ``(browser, context, page)`` handles.
    Side effects:
    - Launches headless Chromium-family browser process.
    Exceptions:
    - Calls ``pytest.skip`` when no local executable is available.
    """

    executable_path = resolve_browser_executable_path()
    if executable_path is None:
        pytest.skip(
            "No local Chromium-family browser executable found. "
            "Set PLAYWRIGHT_BROWSER_EXECUTABLE or install Chromium.",
        )
    browser = playwright.chromium.launch(
        headless=True,
        executable_path=str(executable_path),
    )
    context = browser.new_context()
    page = context.new_page()
    return browser, context, page


@pytest.mark.parametrize(
    ("script_name", "module_name"),
    [
        ("build_user_manual.py", "build_user_manual_playwright_smoke_test"),
        (
            "build_equilibrium_walkthrough.py",
            "build_equilibrium_playwright_smoke_test",
        ),
    ],
)
def test_mathml_runtime_smoke(script_name: str, module_name: str) -> None:
    """Validate rendered docs expose visible MathML and hide raw fenced LaTeX.

    Purpose:
    - Run a true browser-level gate for generated docs math rendering.
    Why:
    - Static HTML assertions alone cannot prove runtime DOM visibility behavior.
    Inputs:
    - ``script_name`` / ``module_name`` from parametrized cases.
    Outputs:
    - None.
    Side effects:
    - Launches a headless local Chromium-family browser process.
    Exceptions:
    - Raises assertions when math nodes are missing or not visibly rendered.
    """

    html = build_docs_html(script_name, module_name)
    with sync_playwright() as playwright:
        browser, context, page = open_browser_page(playwright)
        try:
            page.set_content(html, wait_until="domcontentloaded")

            math_count = page.locator("math").count()
            assert math_count > 0
            assert page.locator("pre code.language-latex").count() == 0

            visible_sizes = page.evaluate(
                """() => {
                    return Array.from(document.querySelectorAll("math"))
                        .slice(0, 12)
                        .map((node) => {
                            const rect = node.getBoundingClientRect();
                            return { width: rect.width, height: rect.height };
                        });
                }"""
            )
            assert any(
                entry["width"] > 0 and entry["height"] > 0 for entry in visible_sizes
            )
        finally:
            context.close()
            browser.close()
