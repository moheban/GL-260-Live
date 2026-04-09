#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and validate the equilibrium walkthrough HTML artifact.

Purpose:
    Convert ``docs/equilibrium-walkthrough.md`` into a styled, presentation-ready
    HTML page with deterministic output.
Why:
    The repository keeps Markdown as source-of-truth while publishing an HTML
    companion for presentations and browser sharing.
Inputs:
    Command-line flags controlling write/check behavior.
Outputs:
    Writes or validates ``docs/equilibrium-walkthrough.html``.
Side Effects:
    Reads and writes files under the repository ``docs/`` subtree.
Exceptions:
    Exits non-zero on build/check failures with actionable messages.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import markdown

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SOURCE_MD_PATH = REPO_ROOT / "docs" / "equilibrium-walkthrough.md"
OUTPUT_HTML_PATH = REPO_ROOT / "docs" / "equilibrium-walkthrough.html"
INLINE_MATH_SENTINELS = (
    (r"\(", "GL260EQMATHOPENPARENZXCV"),
    (r"\)", "GL260EQMATHCLOSEPARENZXCV"),
    (r"\[", "GL260EQMATHOPENBRACKETZXCV"),
    (r"\]", "GL260EQMATHCLOSEBRACKETZXCV"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI flags for equilibrium walkthrough build/check flows.

    Purpose:
        Define deterministic command-line behavior for generation and validation.
    Why:
        Local and CI workflows need one shared contract for build parity checks.
    Inputs:
        argv: Optional explicit argument vector for tests; defaults to ``sys.argv``.
    Outputs:
        Parsed namespace with ``--check`` mode.
    Side Effects:
        None.
    Exceptions:
        ``argparse`` exits with status code 2 when arguments are invalid.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Build or validate docs/equilibrium-walkthrough.html from "
            "docs/equilibrium-walkthrough.md."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the generated HTML is missing or out of date.",
    )
    return parser.parse_args(argv)


def read_utf8(path: Path) -> str:
    """Read one UTF-8 text file.

    Purpose:
        Centralize text reads for source and generated artifacts.
    Why:
        Shared file-read behavior keeps diagnostics and encoding handling
        consistent across build/check paths.
    Inputs:
        path: Absolute file path to read.
    Outputs:
        Decoded UTF-8 text.
    Side Effects:
        Reads file bytes from disk.
    Exceptions:
        Propagates ``OSError`` for missing/unreadable files and ``UnicodeError``
        for invalid UTF-8 payloads.
    """

    return path.read_text(encoding="utf-8")


def write_utf8(path: Path, content: str) -> None:
    """Write one UTF-8 text file with normalized newlines.

    Purpose:
        Persist generated HTML deterministically.
    Why:
        Stable newline handling is required for exact ``--check`` parity.
    Inputs:
        path: Output file path.
        content: HTML payload to write.
    Outputs:
        None.
    Side Effects:
        Creates parent directories and writes file content to disk.
    Exceptions:
        Propagates ``OSError`` on write failures.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def source_sha256(text: str) -> str:
    """Return SHA-256 fingerprint for source tracking metadata.

    Purpose:
        Stamp generated HTML with deterministic provenance metadata.
    Why:
        Source hashing enables exact out-of-date detection in check mode.
    Inputs:
        text: Source Markdown payload.
    Outputs:
        Hex digest string.
    Side Effects:
        None.
    Exceptions:
        None under normal usage.
    """

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _protect_inline_math_delimiters(markdown_text: str) -> str:
    """Protect escaped LaTeX delimiters before Markdown conversion.

    Purpose:
        Preserve escaped math delimiters that Python-Markdown may unescape.
    Why:
        LaTeX delimiters must survive conversion for runtime MathJax rendering.
    Inputs:
        markdown_text: Source Markdown payload.
    Outputs:
        Markdown text with temporary sentinel substitutions.
    Side Effects:
        None.
    Exceptions:
        None under normal usage.
    """

    protected_text = markdown_text
    for source, sentinel in INLINE_MATH_SENTINELS:
        protected_text = protected_text.replace(source, sentinel)
    return protected_text


def _restore_inline_math_delimiters(rendered_text: str) -> str:
    """Restore canonical LaTeX delimiters after conversion.

    Purpose:
        Replace temporary sentinel tokens with original math delimiters.
    Why:
        Final HTML requires canonical delimiters for MathJax parsing.
    Inputs:
        rendered_text: Converted HTML fragment.
    Outputs:
        HTML fragment with restored LaTeX delimiters.
    Side Effects:
        None.
    Exceptions:
        None under normal usage.
    """

    restored_text = rendered_text
    for source, sentinel in INLINE_MATH_SENTINELS:
        restored_text = restored_text.replace(sentinel, source)
    return restored_text


def render_markdown(markdown_text: str) -> tuple[str, str]:
    """Render source Markdown into body and TOC HTML.

    Purpose:
        Convert source Markdown into semantic HTML plus table of contents.
    Why:
        The walkthrough needs both structured content and quick navigation.
    Inputs:
        markdown_text: Source Markdown text.
    Outputs:
        Tuple ``(body_html, toc_html)``.
    Side Effects:
        None.
    Exceptions:
        Propagates Markdown rendering errors.
    """

    protected = _protect_inline_math_delimiters(markdown_text)
    md = markdown.Markdown(
        extensions=[
            "toc",
            "tables",
            "fenced_code",
            "sane_lists",
            "attr_list",
            "admonition",
            "nl2br",
        ],
        extension_configs={"toc": {"permalink": False, "toc_depth": "2-4"}},
        output_format="html5",
    )
    body_html = _restore_inline_math_delimiters(md.convert(protected))
    toc_html = _restore_inline_math_delimiters(
        md.toc or "<ul><li>No headings detected</li></ul>"
    )
    return body_html, toc_html


def build_html_document(*, body_html: str, toc_html: str, source_hash: str) -> str:
    """Wrap rendered content in a standalone interactive HTML shell.

    Purpose:
        Apply layout, styling, TOC filtering, and LaTeX rendering bootstrap.
    Why:
        Presentation use needs an immediately readable artifact with reliable
        math rendering and graceful fallback behavior.
    Inputs:
        body_html: Rendered content fragment.
        toc_html: Table-of-contents fragment.
        source_hash: SHA-256 digest of source markdown.
    Outputs:
        Full HTML document string.
    Side Effects:
        None.
    Exceptions:
        None under normal usage.
    """

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <meta name=\"equilibrium-walkthrough-source-sha256\" content=\"{source_hash}\">
  <title>GL-260 Equilibrium Walkthrough</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-0: #07131d;
      --bg-1: #0d2231;
      --bg-2: #173246;
      --surface: rgba(9, 22, 32, 0.82);
      --surface-soft: rgba(11, 29, 42, 0.66);
      --paper: #f7fbff;
      --ink: #d9e8f3;
      --ink-muted: #9eb8cb;
      --ink-body: #1a3344;
      --edge: rgba(152, 186, 207, 0.40);
      --accent: #35d0d7;
      --accent-soft: rgba(53, 208, 215, 0.16);
      --heading-font: "Space Grotesk", "Segoe UI", sans-serif;
      --body-font: "Source Sans 3", "Segoe UI", sans-serif;
      --mono-font: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; }}
    body {{
      font-family: var(--body-font);
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 8%, rgba(42, 162, 175, 0.31), transparent 42%),
        radial-gradient(circle at 88% -2%, rgba(36, 82, 145, 0.43), transparent 46%),
        linear-gradient(165deg, var(--bg-0) 0%, var(--bg-1) 46%, var(--bg-2) 100%);
      line-height: 1.56;
      min-height: 100vh;
      overflow-x: hidden;
    }}
    .hero {{
      padding: clamp(56px, 8vw, 108px) clamp(18px, 5vw, 84px) clamp(34px, 4vw, 62px);
    }}
    .hero-inner {{
      max-width: 1030px;
      margin: 0 auto;
      opacity: 0;
      transform: translateY(16px);
      transition: opacity 650ms ease, transform 650ms ease;
    }}
    body.is-ready .hero-inner {{ opacity: 1; transform: translateY(0); }}
    .hero-eyebrow {{
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.13em;
      font-weight: 700;
      font-size: 0.78rem;
      color: var(--accent);
    }}
    .hero h1 {{
      margin: 0;
      max-width: 840px;
      font-family: var(--heading-font);
      font-size: clamp(2rem, 5vw, 3.52rem);
      line-height: 1.04;
      letter-spacing: -0.025em;
    }}
    .hero p {{
      margin: 14px 0 0;
      max-width: 730px;
      color: var(--ink-muted);
      font-size: clamp(1.05rem, 1.8vw, 1.24rem);
    }}
    .hero-metrics {{
      margin-top: 24px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .hero-metric {{
      border: 1px solid var(--edge);
      background: var(--surface-soft);
      border-radius: 12px;
      padding: 9px 11px;
    }}
    .hero-metric .label {{
      display: block;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      font-size: 0.72rem;
      color: var(--ink-muted);
    }}
    .hero-metric .value {{
      display: block;
      margin-top: 2px;
      font-family: var(--heading-font);
      font-size: 1.08rem;
      color: #f4fbff;
    }}
    .hero-cta {{
      display: inline-block;
      margin-top: 22px;
      text-decoration: none;
      font-family: var(--heading-font);
      font-weight: 700;
      color: #06232b;
      background: linear-gradient(135deg, #4be5ea, #95f3f7);
      border-radius: 999px;
      padding: 10px 18px;
      box-shadow: 0 8px 24px rgba(12, 181, 194, 0.35);
    }}
    .headerlink {{ display: none !important; }}
    .control-bar {{
      position: sticky;
      top: 8px;
      z-index: 30;
      width: min(1480px, calc(100vw - 24px));
      margin: 0 auto 12px;
      border: 1px solid var(--edge);
      border-radius: 14px;
      background: var(--surface);
      backdrop-filter: blur(8px);
      padding: 10px 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .control-bar .label {{
      color: var(--ink-muted);
      text-transform: uppercase;
      letter-spacing: 0.07em;
      font-size: 0.72rem;
      font-weight: 700;
      margin-right: 4px;
    }}
    .control-bar button,
    .control-bar select {{
      border: 1px solid rgba(162, 196, 215, 0.44);
      background: rgba(8, 23, 34, 0.8);
      color: var(--ink);
      border-radius: 8px;
      font-family: var(--body-font);
      font-size: 0.86rem;
      padding: 6px 9px;
      min-height: 32px;
      cursor: pointer;
    }}
    .control-bar button[aria-pressed="true"] {{
      background: var(--accent-soft);
      color: #dffcff;
      border-color: rgba(78, 223, 230, 0.74);
    }}
    .control-bar select {{
      min-width: 88px;
      cursor: default;
    }}
    .floating-nav {{
      position: fixed;
      right: 14px;
      bottom: 14px;
      z-index: 35;
      display: flex;
      gap: 8px;
      align-items: center;
      border: 1px solid var(--edge);
      background: rgba(8, 24, 35, 0.92);
      border-radius: 12px;
      padding: 8px;
      box-shadow: 0 10px 26px rgba(4, 15, 29, 0.35);
      backdrop-filter: blur(6px);
    }}
    .floating-nav button,
    .floating-nav select {{
      border: 1px solid rgba(162, 196, 215, 0.44);
      background: rgba(8, 23, 34, 0.9);
      color: var(--ink);
      border-radius: 8px;
      font-family: var(--body-font);
      font-size: 0.84rem;
      min-height: 30px;
      padding: 5px 9px;
    }}
    .floating-nav select {{
      min-width: 190px;
    }}
    .control-bar button:disabled,
    .floating-nav button:disabled {{
      opacity: 0.48;
      cursor: not-allowed;
    }}
    body.motion-disabled .reveal-node {{
      opacity: 1 !important;
      transform: none !important;
      transition: none !important;
    }}
    body.motion-disabled .hero-inner {{
      opacity: 1 !important;
      transform: none !important;
      transition: none !important;
    }}
    body.presentation-mode .hero {{
      padding-top: clamp(26px, 4vw, 44px);
      padding-bottom: clamp(20px, 3vw, 34px);
      min-height: min(74svh, 720px);
      display: flex;
      align-items: flex-end;
    }}
    body.presentation-mode .shell {{
      width: min(1600px, calc(100vw - 18px));
      margin-bottom: 16px;
      gap: 10px;
    }}
    body.presentation-mode .rail {{
      top: 64px;
      max-height: calc(100vh - 78px);
    }}
    body.presentation-mode .surface {{
      border-radius: 12px;
    }}
    body.presentation-mode .content {{
      font-size: 1.08rem;
      padding: clamp(14px, 2.4vw, 24px);
      min-height: clamp(460px, 70vh, 820px);
    }}
    body.presentation-mode .chart-panel {{
      min-height: clamp(460px, 70vh, 820px);
    }}
    body.presentation-mode .chart-viewport {{
      height: clamp(240px, 32vh, 360px);
      min-height: 240px;
      max-height: 360px;
    }}
    body.presentation-mode .content h2 {{
      margin-top: 1.3rem;
    }}
    .shell {{
      width: min(1480px, calc(100vw - 24px));
      margin: 0 auto 24px;
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      gap: 15px;
      align-items: start;
    }}
    .rail {{
      position: sticky;
      top: 12px;
      max-height: calc(100vh - 20px);
      overflow: hidden;
      border: 1px solid var(--edge);
      border-radius: 16px;
      background: var(--surface);
      backdrop-filter: blur(6px);
    }}
    .rail-head {{ padding: 13px 14px 10px; border-bottom: 1px solid var(--edge); }}
    .rail-head h2 {{ margin: 0; font-family: var(--heading-font); font-size: 1rem; }}
    .rail-head p {{ margin: 5px 0 0; color: var(--ink-muted); font-size: 0.84rem; }}
    .progress-track {{ margin-top: 10px; height: 5px; border-radius: 999px; background: rgba(162, 198, 219, 0.22); overflow: hidden; }}
    .progress-bar {{ height: 100%; width: 100%; transform-origin: left center; transform: scaleX(0); background: linear-gradient(90deg, #4adce4, #9ef9fc); transition: transform 120ms linear; }}
    .rail-tools {{ padding: 10px 14px; border-bottom: 1px solid var(--edge); }}
    .rail-tools label {{ display: block; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.07em; font-size: 0.78rem; color: var(--ink-muted); }}
    .rail-tools input {{ width: 100%; border: 1px solid rgba(162, 196, 215, 0.44); border-radius: 10px; padding: 8px 10px; color: var(--ink); background: rgba(8, 23, 34, 0.72); font-family: var(--body-font); }}
    .toc-scroll {{ max-height: calc(100vh - 220px); overflow: auto; padding: 10px 14px 14px; }}
    #toc-nav ul {{ list-style: none; margin: 0; padding-left: 0.9rem; }}
    #toc-nav > .toc > ul {{ padding-left: 0; }}
    #toc-nav li {{ margin: 2px 0; }}
    #toc-nav a {{ display: block; border-radius: 8px; padding: 3px 7px; text-decoration: none; color: #abc2d1; transition: 120ms ease; }}
    #toc-nav a:hover {{ color: #edfaff; background: rgba(94, 212, 228, 0.16); transform: translateX(2px); }}
    #toc-nav a.is-active {{ color: #0d2733; background: linear-gradient(90deg, rgba(95, 225, 233, 0.94), rgba(166, 250, 252, 0.90)); font-weight: 700; }}
    .stage {{ display: grid; gap: 13px; }}
    .surface {{ border: 1px solid rgba(188, 214, 230, 0.50); border-radius: 16px; background: var(--paper); box-shadow: 0 14px 34px rgba(4, 15, 29, 0.30); }}
    .chart-panel {{ padding: 15px 17px 17px; }}
    .chart-panel h2 {{ margin: 0; font-family: var(--heading-font); color: #102839; }}
    .chart-panel p {{ margin: 6px 0 0; color: #345468; }}
    .chart-module {{ margin-top: 12px; border: 1px solid #d6e8f2; border-radius: 12px; background: #fcfeff; padding: 10px; min-width: 0; overflow: hidden; }}
    .chart-tabs {{ display: inline-flex; gap: 6px; border: 1px solid #d0e3ed; border-radius: 999px; padding: 4px; background: #eef7fb; }}
    .chart-tab {{ border: 0; border-radius: 999px; background: transparent; color: #2b4a5d; padding: 7px 12px; font-family: var(--heading-font); font-size: 0.83rem; cursor: pointer; }}
    .chart-tab[aria-selected="true"] {{ background: #1fb8cb; color: #f6feff; }}
    .chart-stack {{ position: relative; margin-top: 10px; min-width: 0; width: 100%; height: clamp(220px, 30vw, 320px); min-height: 220px; max-height: 320px; overflow: hidden; }}
    .chart-view {{ position: absolute; inset: 0; opacity: 0; pointer-events: none; transition: opacity 160ms ease; }}
    .chart-view.is-active {{ opacity: 1; pointer-events: auto; }}
    .chart-view h3 {{ margin: 0 0 8px; color: #19384a; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.88rem; font-family: var(--heading-font); }}
    .chart-viewport {{ position: relative; width: 100%; height: 100%; min-height: 100%; max-height: 100%; overflow: hidden; }}
    .chart-viewport canvas {{ display: block; width: 100% !important; height: 100% !important; }}
    .chart-fallback {{ margin-top: 10px; border: 1px dashed #c5dce9; border-radius: 10px; background: #f7fbfd; color: #4f6a7d; padding: 8px 10px; display: none; }}
    .chart-fallback.visible {{ display: block; }}
    .content {{ padding: clamp(18px, 3vw, 34px); color: var(--ink-body); }}
    .content h1, .content h2, .content h3, .content h4 {{ font-family: var(--heading-font); color: #102638; scroll-margin-top: 72px; }}
    .content h1 {{ margin-top: 0; font-size: clamp(1.84rem, 3.4vw, 2.48rem); letter-spacing: -0.02em; }}
    .content h2 {{ margin-top: 2rem; border-top: 1px solid #deebf3; padding-top: 1rem; font-size: clamp(1.32rem, 2.2vw, 1.64rem); }}
    .content p, .content li {{ color: #21384a; font-size: 1.03rem; }}
    .content blockquote {{ margin: 0.8rem 0 1rem; border-left: 4px solid #18b1c0; background: #eef9fc; color: #143448; border-radius: 8px; padding: 0.75rem 0.95rem; font-weight: 600; }}
    .content code {{ background: #e8f5fb; border: 1px solid #cee5f1; border-radius: 6px; padding: 0.06rem 0.26rem; font-family: var(--mono-font); color: #0f3648; }}
    .content pre {{ margin: 0.68rem 0; background: #08131d; color: #e3f0fa; border-radius: 12px; padding: 14px; overflow-x: auto; border: 1px solid #1f3545; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03); }}
    .content pre code {{ background: transparent; border: 0; color: inherit; padding: 0; font-size: 0.92rem; }}
    .content table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 1.2rem; font-size: 0.94rem; }}
    .content th, .content td {{ border: 1px solid #d6e6f0; padding: 0.55rem; text-align: left; }}
    .content th {{ background: #edf7fc; color: #163547; font-family: var(--heading-font); text-transform: uppercase; letter-spacing: 0.04em; font-size: 0.85rem; }}
    .content tr:nth-child(even) td {{ background: #f9fdff; }}
    .math-display-block {{ border: 1px solid #d5e5ef; border-radius: 10px; background: #f8fcff; margin: 0.2rem 0; overflow-x: auto; padding: 0.6rem 0.7rem; }}
    .content pre.latex-fallback {{ margin-top: 0.5rem; }}
    .content pre.latex-fallback.math-fallback-hidden {{ display: none; }}
    .math-render-warning {{ border: 1px solid #d8a652; background: #fff4e3; color: #7a4f00; border-radius: 8px; padding: 0.42rem 0.62rem; margin-top: 0.38rem; font-size: 0.85rem; font-weight: 700; }}
    .content pre.latex-fallback[data-math-render-status="failed"] {{ display: block; border-color: #8d3a3a; box-shadow: inset 0 0 0 1px rgba(198, 86, 86, 0.25); }}
    .pco2-sweep-chart-mount {{ margin: 0.9rem 0 1.2rem; border: 1px solid #d6e8f2; border-radius: 12px; background: #fcfeff; padding: 10px; height: clamp(220px, 28vw, 320px); min-height: 220px; max-height: 320px; }}
    .pco2-sweep-chart-mount canvas {{ width: 100% !important; height: 100% !important; display: block; }}
    .reveal-node {{ opacity: 0; transform: translateY(12px); transition: opacity 360ms ease, transform 360ms ease; }}
    .reveal-node.is-visible {{ opacity: 1; transform: translateY(0); }}
    .footer {{ font-size: 0.85rem; color: #496578; margin-top: 1.8rem; border-top: 1px solid #d9e9f3; padding-top: 0.75rem; }}
    @media (max-width: 1180px) {{
      .hero-metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .shell {{ grid-template-columns: 1fr; }}
      .control-bar {{ width: min(1480px, calc(100vw - 16px)); }}
      .rail {{ position: static; max-height: none; }}
      .toc-scroll {{ max-height: 340px; }}
      .floating-nav {{
        left: 8px;
        right: 8px;
        bottom: 8px;
        justify-content: space-between;
      }}
      .floating-nav select {{ flex: 1 1 auto; min-width: 120px; }}
    }}
    @media (max-width: 760px) {{
      .hero-metrics {{ grid-template-columns: 1fr; }}
      .chart-stack {{ height: clamp(200px, 52vw, 260px); min-height: 200px; max-height: 260px; }}
      .pco2-sweep-chart-mount {{ height: clamp(200px, 52vw, 260px); min-height: 200px; max-height: 260px; }}
      .control-bar {{ padding: 8px; gap: 6px; }}
      .control-bar .label {{ width: 100%; }}
      .control-bar button,
      .control-bar select {{ flex: 1 1 calc(50% - 6px); }}
      .floating-nav {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
      }}
      .floating-nav select {{ grid-column: 1 / -1; width: 100%; }}
    }}
    @media print {{
      body {{
        background: #ffffff !important;
        color: #000000 !important;
      }}
      .hero,
      .control-bar,
      .rail,
      .floating-nav,
      .progress-track,
      .math-render-warning {{
        display: none !important;
      }}
      .shell {{
        display: block !important;
        width: auto !important;
        margin: 0 !important;
      }}
      .surface,
      .content,
      .chart-panel {{
        box-shadow: none !important;
        border: 1px solid #ccd5dc !important;
        break-inside: avoid-page;
      }}
      .chart-viewport {{
        height: 240px !important;
        min-height: 240px !important;
        max-height: 240px !important;
      }}
      #walkthrough-content h2 {{
        break-before: page;
      }}
      #walkthrough-content h2:first-of-type {{
        break-before: auto;
      }}
      .content {{
        color: #1b2f3c !important;
      }}
    }}
  </style>
</head>
<body>
  <header class="hero" role="banner" aria-label="Walkthrough overview">
    <div class="hero-inner">
      <p class="hero-eyebrow">GL-260 Technical Presentation</p>
      <h1>Equilibrium and Simulation Walkthrough</h1>
      <p>A guided flow from NaOH basis setup to calibrated Analysis-mode outputs, with equation-level transparency and trend visuals for live explanation.</p>
      <div class="hero-metrics" aria-label="Scenario summary">
        <div class="hero-metric"><span class="label">NaOH Charge</span><span class="value">700 g</span></div>
        <div class="hero-metric"><span class="label">Water Basis</span><span class="value">2,200 mL</span></div>
        <div class="hero-metric"><span class="label">Temperature</span><span class="value">25 C</span></div>
        <div class="hero-metric"><span class="label">Cumulative CO2</span><span class="value">900 g</span></div>
      </div>
      <a class="hero-cta" id="start-walkthrough" href="#2-equilibrium-half-reactions-constants-and-activities">Start Walkthrough</a>
    </div>
  </header>

  <section class="control-bar" id="presenter-controls" aria-label="Presentation controls">
    <span class="label">Presentation Controls</span>
    <button id="motion" type="button" aria-pressed="true">Motion: On</button>
    <button id="auto-advance" type="button" aria-pressed="false">Auto-Advance: Off</button>
    <label for="speed" class="label">Speed</label>
    <select id="speed" aria-label="Auto-advance speed">
      <option value="3">3s</option>
      <option value="5" selected>5s</option>
      <option value="8">8s</option>
      <option value="12">12s</option>
    </select>
    <button id="slide-mode" type="button" aria-pressed="false">Slide Mode: Off</button>
    <button id="reset" type="button">Reset View</button>
    <button id="print-export" type="button">Print/PDF</button>
  </section>

  <div class=\"shell\">
    <aside class="rail" aria-label="Walkthrough navigation">
      <div class="rail-head">
        <h2>Presentation Rail</h2>
        <p>Track progress and jump by section.</p>
        <div class="progress-track" aria-hidden="true"><div id="scroll-progress" class="progress-bar"></div></div>
      </div>
      <div class="rail-tools">
        <label for="toc-filter">Filter Sections</label>
        <input id="toc-filter" type="search" placeholder="Type to narrow headings..." aria-label="Filter table of contents">
      </div>
      <div class="toc-scroll">
        <nav id="toc-nav">{toc_html}</nav>
      </div>
    </aside>

    <main class="stage" aria-label="Walkthrough content">
      <article class="surface content" id="walkthrough-content">
        {body_html}
        <div class="footer">Source fingerprint: <code>{source_hash}</code></div>
      </article>
      <section class="surface chart-panel" aria-label="Cycle trend highlights">
        <h2>Cycle Trend Highlights</h2>
        <p>After equilibrium and pCO2 framing, use these tabs for cycle-level pH and fraction trends from the worked simulation table in Section 8.</p>
        <div class="chart-module" id="cycle-chart-module">
          <div class="chart-tabs" role="tablist" aria-label="Cycle trend chart views">
            <button id="cycle-tab-ph" class="chart-tab" type="button" role="tab" aria-selected="true" aria-controls="cycle-chart-view-ph">pH vs Cycle</button>
            <button id="cycle-tab-fraction" class="chart-tab" type="button" role="tab" aria-selected="false" aria-controls="cycle-chart-view-fraction">Carbonate Fractions</button>
          </div>
          <div class="chart-stack">
            <section id="cycle-chart-view-ph" class="chart-view is-active" role="tabpanel" aria-labelledby="cycle-tab-ph">
              <h3>pH by Cycle</h3>
              <div class="chart-viewport">
                <canvas id="ph-trend-chart" aria-label="pH by cycle chart"></canvas>
              </div>
            </section>
            <section id="cycle-chart-view-fraction" class="chart-view" role="tabpanel" aria-labelledby="cycle-tab-fraction">
              <h3>Carbonate Fractions by Cycle</h3>
              <div class="chart-viewport">
                <canvas id="fraction-trend-chart" aria-label="Carbonate fraction by cycle chart"></canvas>
              </div>
            </section>
          </div>
        </div>
        <div id="chart-fallback" class="chart-fallback" role="status" aria-live="polite"></div>
      </section>
    </main>
  </div>

  <div class="floating-nav" aria-label="Section navigation">
    <button id="prev" type="button" aria-label="Previous section">Previous</button>
    <select id="section-selector" aria-label="Jump to section"></select>
    <button id="next" type="button" aria-label="Next section">Next</button>
  </div>

  <script>
    (function () {{
      const tocNav = document.getElementById("toc-nav");
      const filterInput = document.getElementById("toc-filter");
      const content = document.getElementById("walkthrough-content");
      const progressBar = document.getElementById("scroll-progress");
      const chartFallback = document.getElementById("chart-fallback");
      const startWalkthrough = document.getElementById("start-walkthrough");
      const motionToggle = document.getElementById("motion");
      const autoAdvanceToggle = document.getElementById("auto-advance");
      const speedSelect = document.getElementById("speed");
      const slideModeToggle = document.getElementById("slide-mode");
      const resetButton = document.getElementById("reset");
      const printExportButton = document.getElementById("print-export");
      const prevButton = document.getElementById("prev");
      const nextButton = document.getElementById("next");
      const sectionSelector = document.getElementById("section-selector");
      const cycleTabPh = document.getElementById("cycle-tab-ph");
      const cycleTabFraction = document.getElementById("cycle-tab-fraction");
      const cycleViewPh = document.getElementById("cycle-chart-view-ph");
      const cycleViewFraction = document.getElementById("cycle-chart-view-fraction");
      let phChart = null;
      let fractionChart = null;
      let pco2Chart = null;
      let chartsInitialized = false;
      let autoAdvanceTimer = null;
      let revealObserver = null;
      let sectionHeadings = [];
      let currentSectionIndex = 0;
      const supportsPromises = typeof Promise === "function";
      const supportsIntersectionObserver = "IntersectionObserver" in window;
      const supportsRaf = typeof window.requestAnimationFrame === "function";
      const supportsSmoothScroll = "scrollBehavior" in document.documentElement.style;
      const supportsScrollIntoView =
        typeof Element !== "undefined" &&
        Element.prototype &&
        typeof Element.prototype.scrollIntoView === "function";
      if (!content) {{
        return;
      }}
      document.body.setAttribute("data-presentation-mode", "disabled");
      document.body.setAttribute("data-motion-enabled", "enabled");
      document.body.setAttribute("data-auto-advance-enabled", "disabled");

      const tocLinks = tocNav
        ? Array.from(tocNav.querySelectorAll("a[href^='#']"))
        : [];
      const headingMap = new Map();
      const headingNodes = Array.from(
        document.querySelectorAll("#walkthrough-content h2, #walkthrough-content h3, #walkthrough-content h4")
      );
      for (const heading of headingNodes) {{
        if (heading.id) {{
          headingMap.set("#" + heading.id, heading);
        }}
      }}

      function runPhase(name, fn) {{
        try {{
          fn();
        }} catch (error) {{
          console.error("[walkthrough-phase:" + name + "]", error);
        }}
      }}

      function closestByClass(node, className) {{
        let cursor = node;
        while (cursor && cursor !== document.body) {{
          if (cursor.classList && cursor.classList.contains(className)) {{
            return cursor;
          }}
          cursor = cursor.parentNode;
        }}
        return null;
      }}

      function closestByTagName(node, tagName) {{
        let cursor = node;
        const normalizedTag = String(tagName || "").toUpperCase();
        while (cursor && cursor !== document.body) {{
          if (String(cursor.tagName || "").toUpperCase() === normalizedTag) {{
            return cursor;
          }}
          cursor = cursor.parentNode;
        }}
        return null;
      }}

      function setActiveCycleTab(tabKey) {{
        const showingPh = tabKey !== "fraction";
        if (cycleTabPh) {{
          cycleTabPh.setAttribute("aria-selected", String(showingPh));
        }}
        if (cycleTabFraction) {{
          cycleTabFraction.setAttribute("aria-selected", String(!showingPh));
        }}
        if (cycleViewPh) {{
          cycleViewPh.classList.toggle("is-active", showingPh);
        }}
        if (cycleViewFraction) {{
          cycleViewFraction.classList.toggle("is-active", !showingPh);
        }}
      }}

      function initializeChartTabs() {{
        if (cycleTabPh) {{
          cycleTabPh.addEventListener("click", function () {{
            setActiveCycleTab("ph");
          }});
        }}
        if (cycleTabFraction) {{
          cycleTabFraction.addEventListener("click", function () {{
            setActiveCycleTab("fraction");
          }});
        }}
        setActiveCycleTab("ph");
      }}

      function applyFilter() {{
        const needle = String((filterInput && filterInput.value) || "").trim().toLowerCase();
        for (const link of tocLinks) {{
          const href = link.getAttribute("href");
          const linkText = (link.textContent || "").toLowerCase();
          const heading = headingMap.get(href);
          const headingText = heading ? (heading.textContent || "").toLowerCase() : "";
          const show = !needle || linkText.includes(needle) || headingText.includes(needle);
          const row = closestByTagName(link, "LI");
          if (row) {{
            row.style.display = show ? "" : "none";
          }}
        }}
      }}

      function setActiveTocLink(activeHash) {{
        for (const link of tocLinks) {{
          const active = link.getAttribute("href") === activeHash;
          link.classList.toggle("is-active", active);
          if (active) {{
            link.setAttribute("aria-current", "true");
          }} else {{
            link.removeAttribute("aria-current");
          }}
        }}
      }}

      function initializeActiveSectionTracking() {{
        if (!headingNodes.length) {{
          return;
        }}
        if (!supportsIntersectionObserver) {{
          const updateActiveFromScroll = function () {{
            let activeHeading = null;
            for (const heading of headingNodes) {{
              if (!heading.id) {{
                continue;
              }}
              const distanceFromTop = heading.getBoundingClientRect().top;
              if (distanceFromTop <= 150) {{
                activeHeading = heading;
              }} else {{
                break;
              }}
            }}
            if (!(activeHeading && activeHeading.id)) {{
              activeHeading = headingNodes[0];
            }}
            if (activeHeading && activeHeading.id) {{
              setActiveTocLink("#" + activeHeading.id);
              const sectionIndex = resolveSectionIndexByHeading(activeHeading);
              if (sectionIndex !== null) {{
                setCurrentSectionIndex(sectionIndex);
              }}
            }}
          }};
          window.addEventListener("scroll", updateActiveFromScroll, {{ passive: true }});
          updateActiveFromScroll();
          return;
        }}
        const observer = new IntersectionObserver(
          function (entries) {{
            const visibleEntries = entries
              .filter(function (entry) {{
                return entry.isIntersecting && entry.target.id;
              }})
              .sort(function (left, right) {{
                return left.boundingClientRect.top - right.boundingClientRect.top;
              }});
            if (!visibleEntries.length) {{
              return;
            }}
            const activeHeading = visibleEntries[0].target;
            setActiveTocLink("#" + activeHeading.id);
            const sectionIndex = resolveSectionIndexByHeading(activeHeading);
            if (sectionIndex !== null) {{
              setCurrentSectionIndex(sectionIndex);
            }}
          }},
          {{ rootMargin: "-24% 0px -58% 0px", threshold: 0.02 }}
        );
        for (const heading of headingNodes) {{
          observer.observe(heading);
        }}
      }}

      function updateScrollProgress() {{
        if (!progressBar) {{
          return;
        }}
        // Read-only progress calculation; never writes scroll position.
        const scrollable = document.documentElement.scrollHeight - window.innerHeight;
        const ratio = scrollable > 0 ? Math.min(Math.max(window.scrollY / scrollable, 0), 1) : 0;
        progressBar.style.transform = "scaleX(" + ratio.toFixed(4) + ")";
      }}

      function initializeLayoutPhase() {{
        if (filterInput) {{
          filterInput.addEventListener("input", applyFilter);
        }}
        applyFilter();
        initializeChartTabs();
        window.addEventListener("scroll", updateScrollProgress, {{ passive: true }});
        window.addEventListener("resize", updateScrollProgress);
        initializeActiveSectionTracking();
        updateScrollProgress();
      }}

      function markRevealNodes() {{
        const revealNodes = Array.from(
          content.querySelectorAll("h2, h3, p, ul, ol, blockquote, table, pre, .math-display-block")
        );
        for (const node of revealNodes) {{
          node.classList.add("reveal-node");
        }}
        if (revealObserver) {{
          revealObserver.disconnect();
          revealObserver = null;
        }}
        if (document.body.classList.contains("motion-disabled")) {{
          for (const node of revealNodes) {{
            node.classList.add("is-visible");
          }}
          return;
        }}
        if (!supportsIntersectionObserver) {{
          for (const node of revealNodes) {{
            node.classList.add("is-visible");
          }}
          return;
        }}
        revealObserver = new IntersectionObserver(
          function (entries) {{
            for (const entry of entries) {{
              if (entry.isIntersecting) {{
                entry.target.classList.add("is-visible");
                if (revealObserver) {{
                  revealObserver.unobserve(entry.target);
                }}
              }}
            }}
          }},
          {{ rootMargin: "0px 0px -10% 0px", threshold: 0.18 }}
        );
        for (const node of revealNodes) {{
          if (!node.classList.contains("is-visible")) {{
            revealObserver.observe(node);
          }}
        }}
      }}

      function prepareLatexDisplayBlocks() {{
        const latexCodeNodes = Array.from(
          content.querySelectorAll("pre > code.language-latex")
        );
        const prepared = [];
        for (const codeNode of latexCodeNodes) {{
          const preNode = closestByTagName(codeNode, "PRE");
          if (!preNode || !preNode.parentNode) {{
            continue;
          }}
          if (preNode.getAttribute("data-math-prepared") === "true") {{
            continue;
          }}
          const latexRaw = String(codeNode.textContent || "").trim();
          if (!latexRaw) {{
            continue;
          }}
          const displayNode = document.createElement("div");
          displayNode.className = "math-display-block";
          displayNode.textContent = "\\\\[\\n" + latexRaw + "\\n\\\\]";
          preNode.parentNode.insertBefore(displayNode, preNode);
          preNode.setAttribute("data-math-prepared", "true");
          preNode.classList.add("latex-fallback");
          preNode.classList.add("math-fallback-hidden");
          preNode.removeAttribute("data-math-render-status");
          prepared.push({{ displayNode, fallbackNode: preNode, warningNode: null }});
        }}
        return prepared;
      }}

      function setMathRenderFailure(entry, reason) {{
        if (entry.displayNode && entry.displayNode.parentNode) {{
          entry.displayNode.parentNode.removeChild(entry.displayNode);
        }}
        if (!entry.warningNode && entry.fallbackNode.parentNode) {{
          const warningNode = document.createElement("div");
          warningNode.className = "math-render-warning";
          entry.fallbackNode.parentNode.insertBefore(warningNode, entry.fallbackNode);
          entry.warningNode = warningNode;
        }}
        if (entry.warningNode) {{
          entry.warningNode.textContent = reason;
        }}
        entry.fallbackNode.classList.remove("math-fallback-hidden");
        entry.fallbackNode.setAttribute("data-math-render-status", "failed");
      }}

      function loadScript(src) {{
        return new Promise(function (resolve, reject) {{
          const script = document.createElement("script");
          script.src = src;
          script.async = true;
          script.onload = function () {{
            resolve(src);
          }};
          script.onerror = function () {{
            reject(new Error("Failed to load " + src));
          }};
          document.head.appendChild(script);
        }});
      }}

      function loadMathJaxDualMode() {{
        if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {{
          return Promise.resolve("existing");
        }}
        window.MathJax = {{
          tex: {{
            inlineMath: [["\\\\(", "\\\\)"], ["$", "$"]],
            displayMath: [["\\\\[", "\\\\]"]],
            processEscapes: true
          }},
          options: {{
            skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"]
          }}
        }};
        const mathJaxSources = [
          "mathjax/es5/tex-mml-chtml.js",
          "../mathjax/es5/tex-mml-chtml.js",
          "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
          "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js"
        ];
        let index = 0;
        function tryLoadNextSource() {{
          if (index >= mathJaxSources.length) {{
            return Promise.reject(new Error("No MathJax source could be loaded."));
          }}
          const source = mathJaxSources[index];
          index += 1;
          return loadScript(source).catch(function () {{
            return tryLoadNextSource();
          }});
        }}
        return tryLoadNextSource();
      }}

      function initializeMathRendering() {{
        const prepared = prepareLatexDisplayBlocks();
        if (!prepared.length) {{
          return;
        }}
        loadMathJaxDualMode()
          .then(function () {{
            if (!(window.MathJax && typeof window.MathJax.typesetPromise === "function")) {{
              throw new Error("MathJax unavailable after script load.");
            }}
            const renderTasks = prepared.map(function (entry) {{
              return window.MathJax.typesetPromise([entry.displayNode])
                .then(function () {{
                  if (entry.warningNode && entry.warningNode.parentNode) {{
                    entry.warningNode.parentNode.removeChild(entry.warningNode);
                  }}
                  entry.warningNode = null;
                  entry.fallbackNode.removeAttribute("data-math-render-status");
                  entry.fallbackNode.classList.add("math-fallback-hidden");
                }})
                .catch(function () {{
                  setMathRenderFailure(
                    entry,
                    "Math rendering failed for this block. Showing raw LaTeX."
                  );
                }});
            }});
            return Promise.all(renderTasks);
          }})
          .catch(function () {{
            for (const entry of prepared) {{
              setMathRenderFailure(
                entry,
                "MathJax could not be loaded. Showing raw LaTeX."
              );
            }}
          }});
      }}

      function parseNumericCell(value) {{
        const cleaned = String(value || "").replace(/[^0-9eE+\\.\\-]/g, "");
        if (!cleaned) {{
          return null;
        }}
        const parsed = Number(cleaned);
        return Number.isFinite(parsed) ? parsed : null;
      }}

      function extractSimulationSeries() {{
        const tables = Array.from(content.querySelectorAll("table"));
        const targetTable = tables.find(function (tableNode) {{
          const headers = Array.from(tableNode.querySelectorAll("th")).map(function (header) {{
            return String(header.textContent || "").trim().toLowerCase();
          }});
          return headers.includes("cycle") && headers.includes("ph");
        }});
        if (!targetTable) {{
          return null;
        }}
        const rows = Array.from(targetTable.querySelectorAll("tr")).slice(1);
        const series = {{
          cycle: [],
          ph: [],
          h2co3: [],
          hco3: [],
          co3: [],
        }};
        for (const row of rows) {{
          const cells = Array.from(row.querySelectorAll("td"));
          if (cells.length < 9) {{
            continue;
          }}
          const cycleValue = parseNumericCell(cells[0].textContent);
          const phValue = parseNumericCell(cells[4].textContent);
          const h2co3Value = parseNumericCell(cells[6].textContent);
          const hco3Value = parseNumericCell(cells[7].textContent);
          const co3Value = parseNumericCell(cells[8].textContent);
          if (
            cycleValue === null ||
            phValue === null ||
            h2co3Value === null ||
            hco3Value === null ||
            co3Value === null
          ) {{
            continue;
          }}
          series.cycle.push(cycleValue);
          series.ph.push(phValue);
          series.h2co3.push(h2co3Value);
          series.hco3.push(hco3Value);
          series.co3.push(co3Value);
        }}
        return series.cycle.length ? series : null;
      }}

      function extractPco2SensitivitySeries() {{
        const tables = Array.from(content.querySelectorAll("table"));
        const targetTable = tables.find(function (tableNode) {{
          const headers = Array.from(tableNode.querySelectorAll("th")).map(function (header) {{
            return String(header.textContent || "").trim().toLowerCase();
          }});
          return (
            headers.includes("pco2 (atm)") &&
            headers.includes("hco3- frac") &&
            headers.includes("co3^2- frac")
          );
        }});
        if (!targetTable) {{
          return null;
        }}
        const rows = Array.from(targetTable.querySelectorAll("tr")).slice(1);
        const series = {{
          pco2: [],
          h2co3: [],
          hco3: [],
          co3: [],
        }};
        for (const row of rows) {{
          const cells = Array.from(row.querySelectorAll("td"));
          if (cells.length < 5) {{
            continue;
          }}
          const pco2Value = parseNumericCell(cells[0].textContent);
          const h2co3Value = parseNumericCell(cells[2].textContent);
          const hco3Value = parseNumericCell(cells[3].textContent);
          const co3Value = parseNumericCell(cells[4].textContent);
          if (
            pco2Value === null ||
            h2co3Value === null ||
            hco3Value === null ||
            co3Value === null
          ) {{
            continue;
          }}
          series.pco2.push(pco2Value);
          series.h2co3.push(h2co3Value);
          series.hco3.push(hco3Value);
          series.co3.push(co3Value);
        }}
        return series.pco2.length ? series : null;
      }}

      function showChartFallback(message) {{
        if (!chartFallback) {{
          return;
        }}
        chartFallback.textContent = message;
        chartFallback.classList.add("visible");
      }}

      function loadChartLibrary() {{
        if (window.Chart) {{
          return Promise.resolve("existing");
        }}
        const sources = [
          "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js",
          "https://unpkg.com/chart.js@4.4.4/dist/chart.umd.min.js",
          "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"
        ];
        let index = 0;
        function tryLoad() {{
          if (index >= sources.length) {{
            return Promise.reject(new Error("No chart source could be loaded."));
          }}
          const source = sources[index];
          index += 1;
          return loadScript(source).catch(function () {{
            return tryLoad();
          }});
        }}
        return tryLoad();
      }}

      function renderCharts(series, pco2Series) {{
        if (!(window.Chart && series)) {{
          return;
        }}
        const phCanvas = document.getElementById("ph-trend-chart");
        const fractionCanvas = document.getElementById("fraction-trend-chart");
        if (!(phCanvas && fractionCanvas)) {{
          return;
        }}
        const phViewport = closestByClass(phCanvas, "chart-viewport");
        const fractionViewport = closestByClass(fractionCanvas, "chart-viewport");
        const pco2Canvas = document.getElementById("pco2-sweep-chart");
        const pco2Viewport = pco2Canvas ? closestByClass(pco2Canvas, "pco2-sweep-chart-mount") : null;
        if (!(phViewport && fractionViewport)) {{
          throw new Error("Chart viewport containers are missing.");
        }}
        if (
          phViewport.clientWidth <= 0 ||
          phViewport.clientHeight <= 0 ||
          fractionViewport.clientWidth <= 0 ||
          fractionViewport.clientHeight <= 0
        ) {{
          throw new Error("Chart viewport has invalid dimensions.");
        }}
        if (pco2Canvas && pco2Viewport) {{
          if (pco2Viewport.clientWidth <= 0 || pco2Viewport.clientHeight <= 0) {{
            throw new Error("pCO2 chart viewport has invalid dimensions.");
          }}
        }}
        if (phChart) {{
          phChart.destroy();
          phChart = null;
        }}
        if (fractionChart) {{
          fractionChart.destroy();
          fractionChart = null;
        }}
        if (pco2Chart) {{
          pco2Chart.destroy();
          pco2Chart = null;
        }}
        function buildChartOptions(yTitle) {{
          return {{
            responsive: true,
            maintainAspectRatio: false,
            resizeDelay: 140,
            animation: {{
              duration: 260,
              easing: "easeOutCubic"
            }},
            interaction: {{ mode: "index", intersect: false }},
            plugins: {{
              legend: {{
                labels: {{
                  boxWidth: 10,
                  usePointStyle: true,
                  color: "#17384c",
                  font: {{ family: "Source Sans 3", size: 12 }}
                }}
              }}
            }},
            scales: {{
              x: {{
                title: {{
                  display: true,
                  text: "Cycle",
                  color: "#2c4d61",
                  font: {{ family: "Space Grotesk", size: 12 }}
                }},
                ticks: {{ color: "#32556a" }},
                grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
              }},
              y: {{
                title: {{
                  display: true,
                  text: yTitle,
                  color: "#2c4d61",
                  font: {{ family: "Space Grotesk", size: 12 }}
                }},
                ticks: {{ color: "#32556a" }},
                grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
              }}
            }}
          }};
        }}
        phChart = new Chart(phCanvas.getContext("2d"), {{
          type: "line",
          data: {{
            labels: series.cycle,
            datasets: [{{
              label: "pH",
              data: series.ph,
              borderColor: "#0daec0",
              backgroundColor: "rgba(13, 174, 192, 0.18)",
              borderWidth: 2.3,
              pointRadius: 3,
              pointHoverRadius: 4,
              tension: 0.28,
              fill: true
            }}]
          }},
          options: buildChartOptions("pH")
        }});
        fractionChart = new Chart(fractionCanvas.getContext("2d"), {{
          type: "line",
          data: {{
            labels: series.cycle,
            datasets: [
              {{
                label: "H2CO3* frac",
                data: series.h2co3,
                borderColor: "#3fa2ff",
                backgroundColor: "rgba(63, 162, 255, 0.14)",
                borderWidth: 2,
                tension: 0.25,
                pointRadius: 2.4
              }},
              {{
                label: "HCO3- frac",
                data: series.hco3,
                borderColor: "#1eb46e",
                backgroundColor: "rgba(30, 180, 110, 0.14)",
                borderWidth: 2,
                tension: 0.25,
                pointRadius: 2.4
              }},
              {{
                label: "CO3^2- frac",
                data: series.co3,
                borderColor: "#5568ff",
                backgroundColor: "rgba(85, 104, 255, 0.14)",
                borderWidth: 2,
                tension: 0.25,
                pointRadius: 2.4
              }}
            ]
          }},
          options: buildChartOptions("Fraction")
        }});
        if (pco2Canvas && pco2Series) {{
          pco2Chart = new Chart(pco2Canvas.getContext("2d"), {{
            type: "line",
            data: {{
              labels: pco2Series.pco2,
              datasets: [
                {{
                  label: "H2CO3* frac",
                  data: pco2Series.h2co3,
                  borderColor: "#3fa2ff",
                  backgroundColor: "rgba(63, 162, 255, 0.14)",
                  borderWidth: 2,
                  tension: 0.25,
                  pointRadius: 2.4
                }},
                {{
                  label: "HCO3- frac",
                  data: pco2Series.hco3,
                  borderColor: "#1eb46e",
                  backgroundColor: "rgba(30, 180, 110, 0.14)",
                  borderWidth: 2,
                  tension: 0.25,
                  pointRadius: 2.4
                }},
                {{
                  label: "CO3^2- frac",
                  data: pco2Series.co3,
                  borderColor: "#5568ff",
                  backgroundColor: "rgba(85, 104, 255, 0.14)",
                  borderWidth: 2,
                  tension: 0.25,
                  pointRadius: 2.4
                }}
              ]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              resizeDelay: 140,
              animation: {{
                duration: 260,
                easing: "easeOutCubic"
              }},
              interaction: {{ mode: "index", intersect: false }},
              plugins: {{
                legend: {{
                  labels: {{
                    boxWidth: 10,
                    usePointStyle: true,
                    color: "#17384c",
                    font: {{ family: "Source Sans 3", size: 12 }}
                  }}
                }}
              }},
              scales: {{
                x: {{
                  title: {{
                    display: true,
                    text: "pCO2 (atm)",
                    color: "#2c4d61",
                    font: {{ family: "Space Grotesk", size: 12 }}
                  }},
                  ticks: {{ color: "#32556a" }},
                  grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
                }},
                y: {{
                  title: {{
                    display: true,
                    text: "Fraction",
                    color: "#2c4d61",
                    font: {{ family: "Space Grotesk", size: 12 }}
                  }},
                  min: 0,
                  max: 1,
                  ticks: {{ color: "#32556a" }},
                  grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
                }}
              }}
            }}
          }});
        }}
        if (
          !Number.isFinite(phChart.width) ||
          !Number.isFinite(phChart.height) ||
          phChart.width <= 0 ||
          phChart.height <= 0 ||
          !Number.isFinite(fractionChart.width) ||
          !Number.isFinite(fractionChart.height) ||
          fractionChart.width <= 0 ||
          fractionChart.height <= 0 ||
          (pco2Chart &&
            (!Number.isFinite(pco2Chart.width) ||
              !Number.isFinite(pco2Chart.height) ||
              pco2Chart.width <= 0 ||
              pco2Chart.height <= 0))
        ) {{
          throw new Error("Chart instances reported invalid render dimensions.");
        }}
      }}

      function initializeCharts() {{
        if (chartsInitialized) {{
          return;
        }}
        if (!supportsPromises) {{
          showChartFallback(
            "Chart rendering requires Promise support. The walkthrough table remains available."
          );
          return;
        }}
        const series = extractSimulationSeries();
        const pco2Series = extractPco2SensitivitySeries();
        if (!series) {{
          showChartFallback("Simulation table data was not detected, so chart rendering was skipped.");
          return;
        }}
        loadChartLibrary()
          .then(function () {{
            if (!window.Chart) {{
              throw new Error("Chart library unavailable after script load.");
            }}
            renderCharts(series, pco2Series);
            chartsInitialized = true;
          }})
          .catch(function (error) {{
            if (phChart) {{
              phChart.destroy();
              phChart = null;
            }}
            if (fractionChart) {{
              fractionChart.destroy();
              fractionChart = null;
            }}
            if (pco2Chart) {{
              pco2Chart.destroy();
              pco2Chart = null;
            }}
            showChartFallback(
              "Chart rendering is disabled for stability (" +
                (error && error.message ? error.message : "unknown error") +
                "). The walkthrough table remains available."
            );
          }});
      }}

      function collectSectionHeadings() {{
        const majorHeadings = headingNodes.filter(function (node) {{
          return String(node.tagName || "").toUpperCase() === "H2" && node.id;
        }});
        if (majorHeadings.length) {{
          return majorHeadings;
        }}
        return headingNodes.filter(function (node) {{
          return Boolean(node.id);
        }});
      }}

      function syncSectionControls() {{
        const hasSections = sectionHeadings.length > 0;
        if (prevButton) {{
          prevButton.disabled = !hasSections || currentSectionIndex <= 0;
        }}
        if (nextButton) {{
          nextButton.disabled =
            !hasSections || currentSectionIndex >= sectionHeadings.length - 1;
        }}
        if (sectionSelector && hasSections) {{
          sectionSelector.value = String(currentSectionIndex);
        }}
      }}

      function setCurrentSectionIndex(index) {{
        if (!sectionHeadings.length) {{
          currentSectionIndex = 0;
          syncSectionControls();
          return 0;
        }}
        const boundedIndex = Math.min(
          Math.max(Number(index) || 0, 0),
          sectionHeadings.length - 1
        );
        currentSectionIndex = boundedIndex;
        const activeHeading = sectionHeadings[boundedIndex];
        if (activeHeading && activeHeading.id) {{
          setActiveTocLink("#" + activeHeading.id);
        }}
        syncSectionControls();
        return boundedIndex;
      }}

      function navigateToSection(index, smoothScroll) {{
        if (!sectionHeadings.length) {{
          return;
        }}
        const boundedIndex = setCurrentSectionIndex(index);
        const targetHeading = sectionHeadings[boundedIndex];
        if (!targetHeading) {{
          return;
        }}
        if (supportsScrollIntoView) {{
          targetHeading.scrollIntoView({{
            behavior: smoothScroll && supportsSmoothScroll ? "smooth" : "auto",
            block: "start"
          }});
          return;
        }}
        if (targetHeading.id) {{
          window.location.hash = "#" + targetHeading.id;
        }}
      }}

      function resolveSectionIndexByHeading(headingNode) {{
        if (!(headingNode && headingNode.id) || !sectionHeadings.length) {{
          return null;
        }}
        const targetHash = "#" + headingNode.id;
        for (let idx = 0; idx < sectionHeadings.length; idx += 1) {{
          if ("#" + sectionHeadings[idx].id === targetHash) {{
            return idx;
          }}
        }}
        return null;
      }}

      function resolveSectionIndexById(headingId) {{
        const requestedId = String(headingId || "");
        if (!requestedId || !sectionHeadings.length) {{
          return null;
        }}
        for (let idx = 0; idx < sectionHeadings.length; idx += 1) {{
          if (String(sectionHeadings[idx].id || "") === requestedId) {{
            return idx;
          }}
        }}
        return null;
      }}

      function setAutoAdvanceEnabled(enabled) {{
        const isEnabled = Boolean(enabled);
        document.body.setAttribute(
          "data-auto-advance-enabled",
          isEnabled ? "enabled" : "disabled"
        );
        if (autoAdvanceToggle) {{
          autoAdvanceToggle.setAttribute("aria-pressed", String(isEnabled));
          autoAdvanceToggle.textContent = "Auto-Advance: " + (isEnabled ? "On" : "Off");
        }}
        if (autoAdvanceTimer) {{
          window.clearInterval(autoAdvanceTimer);
          autoAdvanceTimer = null;
        }}
        if (!isEnabled || sectionHeadings.length < 2) {{
          return;
        }}
        const intervalSeconds = Number(speedSelect && speedSelect.value) || 5;
        const intervalMs = Math.max(1000, Math.round(intervalSeconds * 1000));
        autoAdvanceTimer = window.setInterval(function () {{
          if (currentSectionIndex >= sectionHeadings.length - 1) {{
            setAutoAdvanceEnabled(false);
            return;
          }}
          navigateToSection(currentSectionIndex + 1, true);
        }}, intervalMs);
      }}

      function setMotionEnabled(enabled) {{
        const isEnabled = Boolean(enabled);
        document.body.classList.toggle("motion-disabled", !isEnabled);
        document.body.setAttribute(
          "data-motion-enabled",
          isEnabled ? "enabled" : "disabled"
        );
        if (motionToggle) {{
          motionToggle.setAttribute("aria-pressed", String(isEnabled));
          motionToggle.textContent = "Motion: " + (isEnabled ? "On" : "Off");
        }}
        markRevealNodes();
      }}

      function setPresentationMode(enabled) {{
        const isEnabled = Boolean(enabled);
        document.body.classList.toggle("presentation-mode", isEnabled);
        document.body.setAttribute(
          "data-presentation-mode",
          isEnabled ? "enabled" : "disabled"
        );
        if (slideModeToggle) {{
          slideModeToggle.setAttribute("aria-pressed", String(isEnabled));
          slideModeToggle.textContent = "Slide Mode: " + (isEnabled ? "On" : "Off");
        }}
      }}

      function initializeSectionNavigation() {{
        sectionHeadings = collectSectionHeadings();
        for (const tocLink of tocLinks) {{
          tocLink.addEventListener("click", function (event) {{
            const href = tocLink.getAttribute("href");
            const heading = href ? headingMap.get(href) : null;
            if (!(heading && heading.id)) {{
              return;
            }}
            event.preventDefault();
            const sectionIndex = resolveSectionIndexByHeading(heading);
            if (sectionIndex !== null) {{
              navigateToSection(sectionIndex, true);
              return;
            }}
            if (supportsScrollIntoView) {{
              heading.scrollIntoView({{
                behavior: supportsSmoothScroll ? "smooth" : "auto",
                block: "start"
              }});
              return;
            }}
            window.location.hash = "#" + heading.id;
          }});
        }}
        if (sectionSelector) {{
          sectionSelector.innerHTML = "";
          sectionHeadings.forEach(function (heading, index) {{
            const option = document.createElement("option");
            option.value = String(index);
            const labelText = (heading.textContent || "").trim() || "Section " + (index + 1);
            option.textContent = String(index + 1) + ". " + labelText;
            sectionSelector.appendChild(option);
          }});
          sectionSelector.addEventListener("change", function () {{
            const requestedIndex = Number(sectionSelector.value);
            navigateToSection(requestedIndex, true);
          }});
        }}
        if (prevButton) {{
          prevButton.addEventListener("click", function () {{
            navigateToSection(currentSectionIndex - 1, true);
          }});
        }}
        if (nextButton) {{
          nextButton.addEventListener("click", function () {{
            navigateToSection(currentSectionIndex + 1, true);
          }});
        }}
        if (startWalkthrough) {{
          startWalkthrough.addEventListener("click", function (event) {{
            event.preventDefault();
            if (sectionHeadings.length) {{
              const deepDiveIndex = resolveSectionIndexById(
                "2-equilibrium-half-reactions-constants-and-activities"
              );
              navigateToSection(deepDiveIndex === null ? 0 : deepDiveIndex, true);
              return;
            }}
            if (supportsScrollIntoView) {{
              content.scrollIntoView({{
                behavior: supportsSmoothScroll ? "smooth" : "auto",
                block: "start"
              }});
            }}
          }});
        }}
        document.addEventListener("keydown", function (event) {{
          const key = String(event.key || "");
          const targetTag = String((event.target && event.target.tagName) || "").toUpperCase();
          const inTypingControl =
            targetTag === "INPUT" || targetTag === "TEXTAREA" || targetTag === "SELECT";
          if (inTypingControl || event.defaultPrevented) {{
            return;
          }}
          if (key === "ArrowRight" || key === "ArrowDown" || key === "PageDown") {{
            event.preventDefault();
            navigateToSection(currentSectionIndex + 1, true);
          }} else if (
            key === "ArrowLeft" ||
            key === "ArrowUp" ||
            key === "PageUp"
          ) {{
            event.preventDefault();
            navigateToSection(currentSectionIndex - 1, true);
          }} else if (key === "Home") {{
            event.preventDefault();
            navigateToSection(0, true);
          }} else if (key === "End") {{
            event.preventDefault();
            navigateToSection(sectionHeadings.length - 1, true);
          }}
        }});
        setCurrentSectionIndex(0);
      }}

      function initializePresentationControls() {{
        if (motionToggle) {{
          motionToggle.addEventListener("click", function () {{
            const enableMotion = motionToggle.getAttribute("aria-pressed") !== "true";
            setMotionEnabled(enableMotion);
          }});
        }}
        if (autoAdvanceToggle) {{
          autoAdvanceToggle.addEventListener("click", function () {{
            const enableAuto = autoAdvanceToggle.getAttribute("aria-pressed") !== "true";
            setAutoAdvanceEnabled(enableAuto);
          }});
        }}
        if (speedSelect) {{
          speedSelect.addEventListener("change", function () {{
            if (autoAdvanceToggle && autoAdvanceToggle.getAttribute("aria-pressed") === "true") {{
              setAutoAdvanceEnabled(true);
            }}
          }});
        }}
        if (slideModeToggle) {{
          slideModeToggle.addEventListener("click", function () {{
            const enableSlideMode = slideModeToggle.getAttribute("aria-pressed") !== "true";
            setPresentationMode(enableSlideMode);
          }});
        }}
        if (resetButton) {{
          resetButton.addEventListener("click", function () {{
            setAutoAdvanceEnabled(false);
            setPresentationMode(false);
            setMotionEnabled(true);
            if (filterInput) {{
              filterInput.value = "";
              applyFilter();
            }}
            if (supportsSmoothScroll && typeof window.scrollTo === "function") {{
              window.scrollTo({{ top: 0, behavior: "smooth" }});
            }} else if (typeof window.scrollTo === "function") {{
              window.scrollTo(0, 0);
            }}
            setCurrentSectionIndex(0);
          }});
        }}
        if (printExportButton && typeof window.print === "function") {{
          printExportButton.addEventListener("click", function () {{
            window.print();
          }});
        }}
      }}

      function initializePresentationPhase() {{
        initializeSectionNavigation();
        initializePresentationControls();
      }}

      runPhase("math", initializeMathRendering);
      runPhase("layout", initializeLayoutPhase);
      runPhase("charts", initializeCharts);
      runPhase("presentation-controls", initializePresentationPhase);
      runPhase("motion-reveals", markRevealNodes);

      const readyCallback = function () {{
        document.body.classList.add("is-ready");
      }};
      if (supportsRaf) {{
        window.requestAnimationFrame(readyCallback);
      }} else {{
        window.setTimeout(readyCallback, 0);
      }}
    }})();
  </script>
  <script>
    (function () {{
      const walkthroughContent = document.getElementById("walkthrough-content");
      if (!walkthroughContent) {{
        return;
      }}

      function prepareLatexDisplayBlocks() {{
        const latexCodeNodes = Array.from(
          walkthroughContent.querySelectorAll("pre > code.language-latex")
        );
        const prepared = [];
        for (const codeNode of latexCodeNodes) {{
          const preNode = codeNode.parentNode;
          if (!(preNode && preNode.tagName === "PRE" && preNode.parentNode)) {{
            continue;
          }}
          if (preNode.getAttribute("data-math-prepared") === "true") {{
            continue;
          }}
          const latexRaw = String(codeNode.textContent || "").trim();
          if (!latexRaw) {{
            continue;
          }}
          const displayNode = document.createElement("div");
          displayNode.className = "math-display-block";
          displayNode.textContent = "\\\\[\\n" + latexRaw + "\\n\\\\]";
          preNode.parentNode.insertBefore(displayNode, preNode);
          preNode.setAttribute("data-math-prepared", "true");
          preNode.classList.add("latex-fallback");
          preNode.classList.add("math-fallback-hidden");
          preNode.removeAttribute("data-math-render-status");
          prepared.push({{ displayNode: displayNode, fallbackNode: preNode, warningNode: null }});
        }}
        return prepared;
      }}

      function setMathRenderFailure(entry, reason) {{
        if (entry.displayNode && entry.displayNode.parentNode) {{
          entry.displayNode.parentNode.removeChild(entry.displayNode);
        }}
        if (!entry.warningNode && entry.fallbackNode.parentNode) {{
          const warningNode = document.createElement("div");
          warningNode.className = "math-render-warning";
          entry.fallbackNode.parentNode.insertBefore(warningNode, entry.fallbackNode);
          entry.warningNode = warningNode;
        }}
        if (entry.warningNode) {{
          entry.warningNode.textContent = reason;
        }}
        entry.fallbackNode.classList.remove("math-fallback-hidden");
        entry.fallbackNode.setAttribute("data-math-render-status", "failed");
      }}

      function loadScript(src) {{
        return new Promise(function (resolve, reject) {{
          const existingScript = Array.from(document.querySelectorAll("script[src]")).find(
            function (node) {{
              return node.getAttribute("src") === src;
            }}
          );
          if (existingScript) {{
            if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {{
              resolve(src);
              return;
            }}
            existingScript.addEventListener("load", function () {{
              resolve(src);
            }}, {{ once: true }});
            existingScript.addEventListener("error", function () {{
              reject(new Error("Failed to load " + src));
            }}, {{ once: true }});
            return;
          }}
          const script = document.createElement("script");
          script.src = src;
          script.async = true;
          script.onload = function () {{
            resolve(src);
          }};
          script.onerror = function () {{
            reject(new Error("Failed to load " + src));
          }};
          document.head.appendChild(script);
        }});
      }}

      function loadMathJaxDualMode() {{
        if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {{
          return Promise.resolve("existing");
        }}
        window.MathJax = {{
          tex: {{
            inlineMath: [["\\\\(", "\\\\)"], ["$", "$"]],
            displayMath: [["\\\\[", "\\\\]"]],
            processEscapes: true
          }},
          options: {{
            skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"]
          }}
        }};
        const mathJaxSources = [
          "mathjax/es5/tex-mml-chtml.js",
          "../mathjax/es5/tex-mml-chtml.js",
          "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
          "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js"
        ];
        let index = 0;
        function tryLoadNextSource() {{
          if (index >= mathJaxSources.length) {{
            return Promise.reject(new Error("No MathJax source could be loaded."));
          }}
          const source = mathJaxSources[index];
          index += 1;
          return loadScript(source).catch(function () {{
            return tryLoadNextSource();
          }});
        }}
        return tryLoadNextSource();
      }}

      function initializeMathRendering() {{
        const prepared = prepareLatexDisplayBlocks();
        if (!prepared.length) {{
          return;
        }}
        loadMathJaxDualMode()
          .then(function () {{
            if (!(window.MathJax && typeof window.MathJax.typesetPromise === "function")) {{
              throw new Error("MathJax unavailable after script load.");
            }}
            const renderTasks = prepared.map(function (entry) {{
              return window.MathJax.typesetPromise([entry.displayNode])
                .then(function () {{
                  if (entry.warningNode && entry.warningNode.parentNode) {{
                    entry.warningNode.parentNode.removeChild(entry.warningNode);
                  }}
                  entry.warningNode = null;
                  entry.fallbackNode.removeAttribute("data-math-render-status");
                  entry.fallbackNode.classList.add("math-fallback-hidden");
                }})
                .catch(function () {{
                  setMathRenderFailure(
                    entry,
                    "Math rendering failed for this block. Showing raw LaTeX."
                  );
                }});
            }});
            return Promise.all(renderTasks);
          }})
          .catch(function () {{
            for (const entry of prepared) {{
              setMathRenderFailure(
                entry,
                "MathJax could not be loaded. Showing raw LaTeX."
              );
            }}
          }});
      }}

      initializeMathRendering();
    }})();
  </script>
</body>
</html>
"""


def build_once() -> str:
    """Build one HTML payload from the walkthrough Markdown source.

    Purpose:
        Execute one full render pipeline from Markdown to final HTML string.
    Why:
        Build and check modes both need one canonical generation path.
    Inputs:
        None.
    Outputs:
        Generated HTML document string.
    Side Effects:
        Reads source markdown from disk.
    Exceptions:
        Raises ``FileNotFoundError`` if source markdown is missing.
    """

    if not SOURCE_MD_PATH.exists():
        raise FileNotFoundError(f"Source Markdown is missing: {SOURCE_MD_PATH}")
    source_md = read_utf8(SOURCE_MD_PATH)
    body_html, toc_html = render_markdown(source_md)
    digest = source_sha256(source_md)
    return build_html_document(
        body_html=body_html,
        toc_html=toc_html,
        source_hash=digest,
    )


def main(argv: list[str] | None = None) -> int:
    """Run CLI entrypoint for walkthrough build/check workflow.

    Purpose:
        Dispatch write/check behavior and emit deterministic status messages.
    Why:
        A single command must support both generation and parity validation.
    Inputs:
        argv: Optional explicit argument vector.
    Outputs:
        Process exit code (0 success, non-zero failure).
    Side Effects:
        May write generated HTML when not in ``--check`` mode.
    Exceptions:
        Converts runtime failures into non-zero exit status with stderr output.
    """

    args = parse_args(argv)
    try:
        generated = build_once()
    except Exception as exc:
        print(f"[ERROR] Failed to build walkthrough HTML: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if not OUTPUT_HTML_PATH.exists():
            print(
                "[FAIL] Missing generated artifact: "
                f"{OUTPUT_HTML_PATH.relative_to(REPO_ROOT)}",
                file=sys.stderr,
            )
            return 1
        existing = read_utf8(OUTPUT_HTML_PATH)
        if existing != generated:
            print(
                "[FAIL] HTML out of date. Run: "
                "python scripts/build_equilibrium_walkthrough.py",
                file=sys.stderr,
            )
            return 1
        print(
            "[OK] docs/equilibrium-walkthrough.html is up to date.",
            file=sys.stdout,
        )
        return 0

    write_utf8(OUTPUT_HTML_PATH, generated)
    print(
        "[OK] Wrote docs/equilibrium-walkthrough.html",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
