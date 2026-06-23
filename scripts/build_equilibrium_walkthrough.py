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
import html
import json
import re
import sys
from pathlib import Path

import markdown
from latex2mathml.converter import convert as latex_to_mathml

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
LATEX_CODE_BLOCK_PATTERN = re.compile(
    r"(?is)<pre[^>]*>\s*<code(?P<attrs>[^>]*)>(?P<latex>.*?)</code>\s*</pre>"
)
LANGUAGE_LATEX_CLASS_PATTERN = re.compile(
    r"""class\s*=\s*(["'])[^"']*\blanguage-latex\b[^"']*\1""",
    re.IGNORECASE,
)
PROTECTED_HTML_BLOCK_PATTERN = re.compile(
    r"(?is)<pre\b.*?</pre>|<code\b.*?</code>|<script\b.*?</script>|<style\b.*?</style>"
)
INLINE_PAREN_MATH_PATTERN = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
INLINE_BRACKET_MATH_PATTERN = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
CONCENTRATION_BRACKET_PATTERN = re.compile(
    r"(?<!\\left)\[(\s*(?:\\mathrm\{[^{}\n]+\}|[A-Za-z0-9\\^_+\-{}]+)\s*)\](?!\s*\\right)"
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
        LaTeX delimiters must survive conversion for build-time MathML rendering.
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
        Final HTML requires canonical delimiters for MathML conversion.
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


def _convert_latex_fragment(
    *,
    latex_source: str,
    display_mode: str,
    context_label: str,
) -> str:
    """Convert one LaTeX fragment to MathML with fail-fast diagnostics.

    Purpose:
        Produce deterministic MathML output from one raw LaTeX expression.
    Why:
        Build-time conversion removes runtime MathJax/CDN dependencies and keeps
        rendered walkthrough output stable across environments.
    Inputs:
        latex_source: Raw LaTeX expression text.
        display_mode: Target layout mode (`inline` or `block`).
        context_label: Source context used in conversion error messages.
    Outputs:
        MathML fragment string emitted by ``latex2mathml``.
    Side Effects:
        None.
    Exceptions:
        Raises ``ValueError`` when conversion fails or source is empty.
    """

    normalized_latex = str(latex_source or "").strip()
    if not normalized_latex:
        raise ValueError(f"{context_label}: empty LaTeX expression.")
    # latex2mathml is strict about concentration bracket notation like `[H^+]`.
    normalized_latex = CONCENTRATION_BRACKET_PATTERN.sub(
        r"\\left[\1\\right]",
        normalized_latex,
    )
    try:
        return latex_to_mathml(normalized_latex, display=display_mode)
    except TypeError as exc:
        # Keep compatibility with converter builds that do not expose `display`.
        if "display" not in str(exc):
            preview = normalized_latex.replace("\n", " ")[:120]
            raise ValueError(
                f"{context_label}: failed to convert LaTeX `{preview}` ({exc})."
            ) from exc
        try:
            converted = latex_to_mathml(normalized_latex)
        except Exception as fallback_exc:  # pragma: no cover - safety path
            preview = normalized_latex.replace("\n", " ")[:120]
            raise ValueError(
                f"{context_label}: failed to convert LaTeX `{preview}` ({fallback_exc})."
            ) from fallback_exc
        if display_mode == "block" and "display=" not in converted:
            converted = converted.replace("<math", '<math display="block"', 1)
        return converted
    except Exception as exc:
        preview = normalized_latex.replace("\n", " ")[:120]
        raise ValueError(
            f"{context_label}: failed to convert LaTeX `{preview}` ({exc})."
        ) from exc


def _replace_latex_fence_blocks(rendered_html: str, *, source_label: str) -> str:
    """Replace fenced LaTeX code blocks with build-time MathML wrappers.

    Purpose:
        Convert `````latex```` fence output from Markdown into rendered MathML.
    Why:
        Fenced equations are the primary math payload in this walkthrough and must
        not rely on runtime JavaScript typesetting.
    Inputs:
        rendered_html: HTML emitted by Markdown conversion.
        source_label: Source file label for conversion diagnostics.
    Outputs:
        HTML string with fenced LaTeX blocks replaced by MathML containers.
    Side Effects:
        None.
    Exceptions:
        Raises ``ValueError`` when any fenced LaTeX block fails conversion.
    """

    block_index = 0

    def replace_match(match: re.Match[str]) -> str:
        nonlocal block_index
        block_index += 1
        attrs = str(match.group("attrs") or "")
        if LANGUAGE_LATEX_CLASS_PATTERN.search(attrs) is None:
            return str(match.group(0))
        latex_raw = html.unescape(str(match.group("latex") or ""))
        mathml = _convert_latex_fragment(
            latex_source=latex_raw,
            display_mode="block",
            context_label=f"{source_label} fenced block #{block_index}",
        )
        return (
            '<div class="math-display-block" data-math-origin="latex-fence">'
            f"{mathml}"
            "</div>"
        )

    return LATEX_CODE_BLOCK_PATTERN.sub(replace_match, rendered_html)


def _replace_inline_latex_in_segment(segment_text: str, *, source_label: str) -> str:
    """Convert inline LaTeX delimiters within one HTML text segment.

    Purpose:
        Render ``\\(...\\)`` and ``\\[...\\]`` expressions into MathML wrappers.
    Why:
        Inline equations appear in walkthrough prose and need deterministic output
        without runtime MathJax dependency.
    Inputs:
        segment_text: HTML text that does not include protected code/script tags.
        source_label: Source file label for conversion diagnostics.
    Outputs:
        Updated segment text with inline LaTeX replaced by MathML wrappers.
    Side Effects:
        None.
    Exceptions:
        Raises ``ValueError`` when any inline LaTeX expression fails conversion.
    """

    inline_index = 0
    display_index = 0

    def replace_bracket(match: re.Match[str]) -> str:
        nonlocal display_index
        display_index += 1
        latex_raw = html.unescape(str(match.group(1) or ""))
        mathml = _convert_latex_fragment(
            latex_source=latex_raw,
            display_mode="block",
            context_label=f"{source_label} inline-display #{display_index}",
        )
        return (
            '<span class="math-inline math-inline-display" '
            'data-math-origin="inline-display">'
            f"{mathml}"
            "</span>"
        )

    converted = INLINE_BRACKET_MATH_PATTERN.sub(replace_bracket, segment_text)

    def replace_paren(match: re.Match[str]) -> str:
        nonlocal inline_index
        inline_index += 1
        latex_raw = html.unescape(str(match.group(1) or ""))
        mathml = _convert_latex_fragment(
            latex_source=latex_raw,
            display_mode="inline",
            context_label=f"{source_label} inline #{inline_index}",
        )
        return (
            '<span class="math-inline" data-math-origin="inline">'
            f"{mathml}"
            "</span>"
        )

    return INLINE_PAREN_MATH_PATTERN.sub(replace_paren, converted)


def _replace_inline_latex_blocks(rendered_html: str, *, source_label: str) -> str:
    """Convert inline LaTeX delimiters outside protected code/script blocks.

    Purpose:
        Apply inline LaTeX conversion only where prose text is rendered.
    Why:
        Code snippets and scripts may contain backslash patterns that should never
        be treated as math expressions.
    Inputs:
        rendered_html: HTML containing prose and structured nodes.
        source_label: Source file label for conversion diagnostics.
    Outputs:
        HTML with inline LaTeX delimiters replaced by MathML wrappers.
    Side Effects:
        None.
    Exceptions:
        Raises ``ValueError`` when inline conversion fails.
    """

    output_parts: list[str] = []
    cursor = 0
    # Process only gaps between protected blocks so code/script text is untouched.
    for match in PROTECTED_HTML_BLOCK_PATTERN.finditer(rendered_html):
        segment = rendered_html[cursor : match.start()]
        output_parts.append(
            _replace_inline_latex_in_segment(segment, source_label=source_label)
        )
        output_parts.append(str(match.group(0)))
        cursor = match.end()
    output_parts.append(
        _replace_inline_latex_in_segment(rendered_html[cursor:], source_label=source_label)
    )
    return "".join(output_parts)


def render_mathml_html(rendered_html: str, *, source_label: str) -> str:
    """Render fenced and inline LaTeX in one HTML fragment to MathML.

    Purpose:
        Run the full deterministic build-time math conversion pass.
    Why:
        Walkthrough output must render equations without any runtime script fetch.
    Inputs:
        rendered_html: HTML fragment produced by Markdown conversion.
        source_label: Source file label for conversion diagnostics.
    Outputs:
        HTML fragment with LaTeX expressions replaced by MathML wrappers.
    Side Effects:
        None.
    Exceptions:
        Raises ``ValueError`` when any LaTeX expression fails conversion.
    """

    with_fences_converted = _replace_latex_fence_blocks(
        rendered_html,
        source_label=source_label,
    )
    return _replace_inline_latex_blocks(
        with_fences_converted,
        source_label=source_label,
    )


def render_markdown(markdown_text: str) -> tuple[str, str]:
    """Render source Markdown into body and TOC HTML.

    Purpose:
        Convert source Markdown into semantic HTML, table of contents, and MathML.
    Why:
        The walkthrough needs deterministic math rendering without runtime scripts.
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
    restored_body_html = _restore_inline_math_delimiters(md.convert(protected))
    restored_toc_html = _restore_inline_math_delimiters(
        md.toc or "<ul><li>No headings detected</li></ul>"
    )
    body_html = render_mathml_html(
        restored_body_html,
        source_label="docs/equilibrium-walkthrough.md body",
    )
    toc_html = render_mathml_html(
        restored_toc_html,
        source_label="docs/equilibrium-walkthrough.md toc",
    )
    return body_html, toc_html


def build_derivation_stepper_steps_json() -> str:
    """Build JSON payload for the live derivation slider.

    Purpose:
        Convert the stepper's curated LaTeX equations and inline callout math
        into MathML-backed HTML.
    Why:
        The slider content is inserted at runtime, so it cannot pass through the
        normal Markdown conversion path; pre-rendering keeps the presentation
        self-contained and visually consistent with the rest of the walkthrough.
    Inputs:
        None.
    Outputs:
        JSON string containing titles, prose, rendered callout HTML, and
        rendered equation HTML fragments for the derivation stepper.
    Side Effects:
        None.
    Exceptions:
        Propagates ``ValueError`` from LaTeX conversion if a curated expression
        or callout cannot be rendered, causing the build to fail before writing
        bad HTML.
    """

    raw_steps = [
        {
            "title": "1. Establish the material basis",
            "purpose": (
                "Start with the charged NaOH and convert it into the sodium "
                "basis used by every later equation."
            ),
            "equations": [
                r"n_{\mathrm{NaOH}} = \frac{m_{\mathrm{NaOH}}}{MW_{\mathrm{NaOH}}}",
                r"m_{\mathrm{NaT}} = \frac{n_{\mathrm{NaOH}}}{kg_{\mathrm{water}}}",
                r"m_{\mathrm{NaT}} = \frac{700\ \mathrm{g} / 40.00\ \mathrm{g\ mol^{-1}}}{2.2\ \mathrm{kg}} = 7.9545\ \mathrm{mol\ kg^{-1}}",
            ],
            "callout": (
                "This fixes the positive-charge inventory that the pH solver "
                "must balance."
            ),
        },
        {
            "title": "2. Write the carbonate half-reactions",
            "purpose": (
                "Expose the three reversible constraints that govern carbonic "
                "acid, bicarbonate, carbonate, hydroxide, and pH."
            ),
            "equations": [
                r"\mathrm{CO_2^*} \rightleftharpoons \mathrm{H^+} + \mathrm{HCO_3^-}",
                r"\mathrm{HCO_3^-} \rightleftharpoons \mathrm{H^+} + \mathrm{CO_3^{2-}}",
                r"\mathrm{H_2O} \rightleftharpoons \mathrm{H^+} + \mathrm{OH^-}",
            ],
            "callout": (
                "These are the local equilibrium rules the solver must satisfy "
                "at the same time."
            ),
        },
        {
            "title": "3. Convert reactions into constants",
            "purpose": (
                "Turn the reaction statements into algebraic constraints using "
                "activities or concentration fallback terms."
            ),
            "equations": [
                r"K_{a1} = \frac{a_{\mathrm{H^+}} \times a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}}}",
                r"K_{a2} = \frac{a_{\mathrm{H^+}} \times a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}}",
                r"K_w = a_{\mathrm{H^+}} \times a_{\mathrm{OH^-}}",
                r"a_i = \gamma_i \times m_i",
            ],
            "callout": (
                "In the Pitzer path, activities replace raw molality through "
                r"\(a_i = \gamma_i \times m_i\)."
            ),
        },
        {
            "title": "4. Combine the base-consumption path",
            "purpose": (
                "Show why bicarbonate is the intermediate and why carbonate "
                "over-conversion is controlled by hydroxide."
            ),
            "equations": [
                r"K_{b1} = \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}} = \frac{K_{a1}}{K_w}",
                r"K_{b2} = \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}} = \frac{K_{a2}}{K_w}",
                r"K_{eq,\mathrm{overall}} = K_{b1} \times K_{b2}",
                r"K_{eq,\mathrm{overall}} = \frac{a_{\mathrm{HCO_3^-}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}} \times \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{HCO_3^-}} \times a_{\mathrm{OH^-}}}",
                r"K_{eq,\mathrm{overall}} = \frac{a_{\mathrm{CO_3^{2-}}} \times a_{\mathrm{H_2O}}}{a_{\mathrm{CO_2^*}} \times a_{\mathrm{OH^-}}^2} = \frac{K_{a1} \times K_{a2}}{K_w^2}",
            ],
            "callout": (
                "The HCO3- term cancels algebraically, which is why residual "
                "alkalinity can push the pathway past bicarbonate."
            ),
        },
        {
            "title": "5. Build alpha fractions from H+",
            "purpose": (
                "Use one trial hydrogen value to distribute total inorganic "
                "carbon among the three carbonate-family species."
            ),
            "equations": [
                r"C_T = [\mathrm{CO_2^*}] + [\mathrm{HCO_3^-}] + [\mathrm{CO_3^{2-}}]",
                r"[\mathrm{HCO_3^-}] = \frac{K_{a1}}{[H^+]}[\mathrm{CO_2^*}]",
                r"[\mathrm{CO_3^{2-}}] = \frac{K_{a1}K_{a2}}{[H^+]^2}[\mathrm{CO_2^*}]",
                r"D = [H^+]^2 + K_{a1}[H^+] + K_{a1}K_{a2}",
                r"\alpha_0 = \frac{[H^+]^2}{D},\quad \alpha_1 = \frac{K_{a1}[H^+]}{D},\quad \alpha_2 = \frac{K_{a1}K_{a2}}{D}",
            ],
            "callout": (
                "Once [H+] is chosen, the species fractions are no longer "
                "independent knobs."
            ),
        },
        {
            "title": "6. Reconstruct species and hydroxide",
            "purpose": (
                "Convert fractions into concentration or molality outputs that "
                "can be checked against charge balance."
            ),
            "equations": [
                r"[\mathrm{CO_2^*}] = \frac{[H^+]^2}{[H^+]^2 + K_{a1}[H^+] + K_{a1}K_{a2}} \times C_T",
                r"[\mathrm{HCO_3^-}] = \frac{K_{a1}[H^+]}{[H^+]^2 + K_{a1}[H^+] + K_{a1}K_{a2}} \times C_T",
                r"[\mathrm{CO_3^{2-}}] = \frac{K_{a1}K_{a2}}{[H^+]^2 + K_{a1}[H^+] + K_{a1}K_{a2}} \times C_T",
                r"[\mathrm{OH^-}] = \frac{K_w}{[H^+]}",
            ],
            "callout": (
                "This is the point where pH, hydroxide, and speciation become "
                "one coupled state."
            ),
        },
        {
            "title": "7. Close charge balance and report pH",
            "purpose": (
                "Accept the pH only when the positive and negative charge pools "
                "agree within tolerance."
            ),
            "equations": [
                r"R_q = [\mathrm{Na^+}] + [H^+] - \frac{K_w}{[H^+]} - \left(\frac{K_{a1}[H^+]}{D} \times C_T\right) - 2\left(\frac{K_{a1}K_{a2}}{D} \times C_T\right)",
                r"D = [H^+]^2 + K_{a1}[H^+] + K_{a1}K_{a2}",
                r"R_q = 0",
                r"\mathrm{pH} = -\log_{10}([H^+])",
            ],
            "callout": (
                "The displayed pH is useful because it belongs to a "
                "charge-consistent species distribution."
            ),
        },
        {
            "title": "8. Apply the same solve per cycle",
            "purpose": (
                "Feed each accepted uptake event into cumulative loading, then "
                "repeat the equilibrium solve for that cycle."
            ),
            "equations": [
                r"\Delta P_{\mathrm{atm},k} = \frac{\Delta P_{\mathrm{psi},k}}{14.6959}",
                r"n_{\mathrm{CO_2},k} = \frac{\Delta P_{\mathrm{atm},k} \times V_{\mathrm{headspace}}}{R \times T_k}",
                r"\Delta m_{\mathrm{CO_2},k} = n_{\mathrm{CO_2},k} \times MW_{\mathrm{CO_2}}",
                r"m_{\mathrm{CO_2,cum},k} = \sum_{i=1}^{k} \Delta m_{\mathrm{CO_2},i}",
                r"m_{CT,k} = \frac{m_{\mathrm{CO_2,cum},k} / MW_{\mathrm{CO_2}}}{kg_{\mathrm{water}}}",
                r"k \rightarrow \{\mathrm{pH}_k,\ m_{\mathrm{OH^-},k},\ [\mathrm{CO_2^*}]_k,\ [\mathrm{HCO_3^-}]_k,\ [\mathrm{CO_3^{2-}}]_k\}",
            ],
            "callout": (
                "This is how the derivation becomes the cycle-by-cycle "
                "predicted pH and speciation timeline."
            ),
        },
    ]

    rendered_steps = []
    for step in raw_steps:
        rendered_steps.append(
            {
                "title": step["title"],
                "purpose": step["purpose"],
                "equationsHtml": [
                    (
                        '<div class="math-display-block" '
                        'data-math-origin="derivation-stepper">'
                        f"{_convert_latex_fragment(latex_source=equation, display_mode='block', context_label='derivation stepper')}"
                        "</div>"
                    )
                    for equation in step["equations"]
                ],
                "calloutHtml": _replace_inline_latex_in_segment(
                    html.escape(step["callout"]),
                    source_label="derivation stepper callout",
                ),
            }
        )

    return json.dumps(rendered_steps, ensure_ascii=True)


def build_html_document(*, body_html: str, toc_html: str, source_hash: str) -> str:
    """Wrap rendered content in a standalone interactive HTML shell.

    Purpose:
        Apply layout, styling, TOC filtering, and deterministic math presentation.
    Why:
        Presentation use needs an immediately readable artifact with reliable
        build-time MathML rendering and no runtime script dependency.
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

    derivation_steps_json = build_derivation_stepper_steps_json()

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
    @font-face {{
      font-family: "XITS Math";
      src: url("assets/fonts/XITSMath-Regular.otf") format("opentype");
      font-weight: 400;
      font-style: normal;
      font-display: swap;
    }}
    @font-face {{
      font-family: "XITS Math";
      src: url("assets/fonts/XITSMath-Bold.otf") format("opentype");
      font-weight: 700;
      font-style: normal;
      font-display: swap;
    }}
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
      --math-font: "XITS Math", "STIX Two Math", "Cambria Math", "Latin Modern Math", serif;
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
    .headerlink,
    .content .headerlink,
    .content a.anchor-link,
    .content a.permalink {{
      display: none !important;
    }}
    .sr-only {{
      position: absolute !important;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}
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
      display: grid;
      gap: 8px;
      min-width: 0;
    }}
    .control-primary,
    .control-secondary {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      min-width: 0;
    }}
    .control-secondary[hidden] {{
      display: none;
    }}
    .section-organizer {{
      border-top: 1px solid rgba(162, 196, 215, 0.26);
      padding-top: 8px;
      display: grid;
      gap: 8px;
      width: 100%;
    }}
    .section-organizer[hidden] {{
      display: none;
    }}
    .section-organizer-header {{
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
    }}
    .section-organizer-title {{
      color: var(--ink-muted);
      text-transform: uppercase;
      letter-spacing: 0.07em;
      font-size: 0.72rem;
      font-weight: 700;
    }}
    .section-organizer-list {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 8px;
      width: 100%;
    }}
    .section-organizer-item {{
      border: 1px solid rgba(162, 196, 215, 0.30);
      border-radius: 9px;
      background: rgba(8, 23, 34, 0.58);
      padding: 8px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 7px;
      align-items: center;
      min-width: 0;
    }}
    .section-organizer-item.is-hidden {{
      opacity: 0.56;
    }}
    .section-organizer-toggle {{
      display: flex;
      align-items: center;
      gap: 7px;
      min-width: 0;
      color: var(--ink);
      font-size: 0.84rem;
    }}
    .section-organizer-toggle input {{
      accent-color: var(--accent);
      flex: 0 0 auto;
    }}
    .section-organizer-toggle span {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .section-organizer-actions {{
      display: flex;
      gap: 4px;
    }}
    .section-organizer-actions button {{
      min-width: 32px;
      padding-inline: 8px;
    }}
    .slide-studio[hidden] {{ display: none; }}
    .slide-studio {{ position: fixed; inset: 0; z-index: 1000; background: rgba(3,15,24,0.88); backdrop-filter: blur(8px); padding: 18px; display: grid; place-items: center; }}
    .slide-studio-shell {{ width: min(1500px, 100%); height: min(940px, calc(100vh - 36px)); border: 1px solid #31596b; border-radius: 14px; background: #0b1f2b; color: #eaf8fb; display: grid; grid-template-rows: auto minmax(0,1fr) auto; overflow: hidden; box-shadow: 0 24px 70px rgba(0,0,0,0.42); }}
    .slide-studio-header, .slide-studio-footer {{ padding: 10px 12px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; background: #102b38; }}
    .slide-studio-header {{ border-bottom: 1px solid #31596b; }}
    .slide-studio-footer {{ border-top: 1px solid #31596b; justify-content: space-between; }}
    .slide-studio-title {{ margin-right: auto; font-family: var(--heading-font); font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: #8eeaf0; }}
    .slide-studio button, .slide-studio select, .slide-studio input {{ min-height: 34px; border: 1px solid #466b79; border-radius: 7px; background: #173746; color: #eefcff; padding: 6px 9px; }}
    .slide-studio button {{ cursor: pointer; }}
    .slide-studio button:hover {{ border-color: #69d8e2; background: #1d4656; }}
    .slide-studio-body {{ min-height: 0; display: grid; grid-template-columns: 220px minmax(0,1fr) 240px; }}
    .slide-studio-sidebar, .slide-studio-properties {{ padding: 12px; overflow: auto; background: #0e2632; }}
    .slide-studio-sidebar {{ border-right: 1px solid #31596b; }}
    .slide-studio-properties {{ border-left: 1px solid #31596b; }}
    .slide-studio-label {{ display: block; margin: 0 0 6px; color: #9fc4cc; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em; }}
    .slide-studio-list {{ display: grid; gap: 7px; }}
    .slide-studio-list button {{ width: 100%; text-align: left; }}
    .slide-studio-list button.is-active {{ border-color: #66deb0; box-shadow: inset 3px 0 #66deb0; }}
    .slide-studio-workspace {{ min-width: 0; overflow: auto; padding: 14px; display: grid; place-items: start center; background: radial-gradient(circle at center, #294554 0, #172f3c 46%, #0b202c 100%); }}
    .slide-studio-canvas, .studio-slide-runtime {{ position: relative; width: 100%; aspect-ratio: 16/9; overflow: hidden; border-radius: 8px; background: linear-gradient(135deg,#fbfeff,#eff8fb); color: #102839; }}
    .slide-studio-canvas {{ width: min(100%, 1050px); box-shadow: 0 16px 44px rgba(0,0,0,0.32); }}
    .studio-slide-runtime {{ margin: 0 0 1.2rem; border: 1px solid #cfe3ec; }}
    .studio-element {{ position: absolute; min-width: 70px; min-height: 42px; border: 1px solid transparent; padding: 8px; overflow: auto; resize: both; background: rgba(255,255,255,0.78); }}
    .slide-studio-canvas .studio-element {{ cursor: move; }}
    .slide-studio-canvas .studio-element.is-selected {{ border-color: #1fb8cb; box-shadow: 0 0 0 2px rgba(31,184,203,0.2); }}
    .studio-element[data-type="title"] {{ font-family: var(--heading-font); font-size: clamp(22px,3vw,42px); font-weight: 800; background: transparent; }}
    .studio-element[data-type="text"], .studio-element[data-type="bullets"] {{ font-size: clamp(14px,1.5vw,22px); line-height: 1.35; }}
    .studio-element img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
    .studio-element table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    .studio-element th, .studio-element td {{ border: 1px solid #b9d2dc; padding: 5px; }}
    .studio-chart-svg {{ width: 100%; height: 100%; display: block; }}
    .slide-studio-toolbar {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }}
    .slide-studio-field {{ display: grid; gap: 5px; margin-bottom: 10px; }}
    .slide-studio-field input, .slide-studio-field select {{ width: 100%; }}
    .slide-studio-help {{ color: #9fc4cc; font-size: 0.78rem; line-height: 1.45; }}
    .slide-studio-status {{ color: #a9d5dc; font-size: 0.78rem; }}
    .slide-studio-import {{ display: none; }}
    [data-section-hidden="true"] {{
      display: none !important;
    }}
    body.tile-reveal-enabled .calculation-map-step {{
      cursor: pointer;
    }}
    body.tile-reveal-enabled .calculation-map-step:focus-within,
    body.tile-reveal-enabled .calculation-map-step:hover {{
      border-color: rgba(31, 184, 203, 0.58);
      box-shadow: 0 10px 22px rgba(13, 81, 95, 0.08);
    }}
    body.tile-reveal-enabled .tile-build-fragment {{
      max-height: 0;
      margin-top: 0;
      opacity: 0;
      overflow: hidden;
      transform: translateY(8px);
      transition:
        max-height 220ms ease,
        margin-top 180ms ease,
        opacity 180ms ease,
        transform 180ms ease;
    }}
    body.tile-reveal-enabled .tile-build-fragment.is-revealed {{
      max-height: 420px;
      margin-top: 4px;
      opacity: 1;
      transform: translateY(0);
    }}
    body.tile-reveal-enabled .calculation-map-step.is-build-complete {{
      border-color: rgba(30, 180, 110, 0.36);
    }}
    .control-bar .label {{
      color: var(--ink-muted);
      text-transform: uppercase;
      letter-spacing: 0.07em;
      font-size: 0.72rem;
      font-weight: 700;
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
    .control-bar select {{
      min-width: 88px;
      cursor: default;
      max-width: min(100%, 560px);
    }}
    .control-bar button[aria-pressed="true"] {{
      background: var(--accent-soft);
      color: #dffcff;
      border-color: rgba(78, 223, 230, 0.74);
    }}
    .control-bar button:disabled {{
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
    body.presentation-mode {{
      min-height: 100svh;
      background:
        radial-gradient(circle at 8% 12%, rgba(53, 208, 215, 0.18), transparent 32%),
        radial-gradient(circle at 92% 82%, rgba(217, 146, 33, 0.13), transparent 30%),
        #07131d;
    }}
    body.presentation-mode .hero {{ display: none; }}
    body.presentation-mode .control-bar {{
      top: 6px;
      width: min(1600px, calc(100vw - 24px));
      margin-bottom: 12px;
      padding: 8px 10px;
      border-radius: 10px;
    }}
    body.presentation-mode .shell {{
      display: block;
      width: min(
        1600px,
        calc(100vw - 32px),
        calc((100svh - 104px) * 16 / 9)
      );
      margin: 0 auto 16px;
    }}
    body.presentation-mode .rail,
    body.presentation-mode .chart-panel {{ display: none; }}
    body.presentation-mode .stage {{ width: 100%; }}
    body.presentation-mode .surface {{
      border-radius: 8px;
    }}
    body.presentation-mode .content {{
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      min-height: 0;
      max-height: calc(100svh - 104px);
      padding: clamp(24px, 3vw, 52px) clamp(28px, 4vw, 68px);
      overflow-x: hidden;
      overflow-y: auto;
      border: 1px solid rgba(53, 208, 215, 0.42);
      border-top: 6px solid var(--accent);
      background:
        linear-gradient(90deg, rgba(53, 208, 215, 0.08), transparent 18%),
        var(--paper);
      box-shadow: 0 30px 80px rgba(0, 0, 0, 0.42);
      font-size: clamp(0.9rem, 1.08vw, 1.12rem);
      scrollbar-color: rgba(31, 184, 203, 0.62) rgba(7, 19, 29, 0.08);
    }}
    body.presentation-mode .chart-viewport {{
      height: clamp(220px, 28vh, 340px);
      min-height: 220px;
      max-height: 340px;
    }}
    body.presentation-mode .content h2 {{
      margin: 0 0 1.1rem;
      padding: 0 0 0.72rem;
      border-top: 0;
      border-bottom: 1px solid #cfe3ec;
      font-size: clamp(1.5rem, 2.4vw, 2.3rem);
      line-height: 1.08;
      letter-spacing: -0.025em;
    }}
    body.presentation-mode .content > :not([data-slide-node="true"]) {{
      display: none !important;
    }}
    body.presentation-mode .content > [data-slide-active="false"] {{
      display: none !important;
    }}
    body.presentation-mode .content > [data-slide-active="true"] {{
      animation: slide-content-enter 360ms ease both;
    }}
    body.presentation-mode .slide-format {{ display: inline-flex; }}
    .slide-format {{
      display: none;
      align-items: center;
      margin-left: auto;
      color: #8eeaf0;
      font-family: var(--heading-font);
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    @keyframes slide-content-enter {{
      from {{ opacity: 0; transform: translateY(10px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .shell {{
      width: min(1480px, calc(100vw - 24px));
      margin: 0 auto 24px;
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      gap: 15px;
      align-items: start;
      min-width: 0;
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
      min-width: 0;
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
    .stage {{ display: grid; gap: 13px; min-width: 0; }}
    .surface {{ border: 1px solid rgba(188, 214, 230, 0.50); border-radius: 16px; background: var(--paper); box-shadow: 0 14px 34px rgba(4, 15, 29, 0.30); min-width: 0; }}
    .chart-panel {{ padding: 15px 17px 17px; min-width: 0; }}
    .chart-panel h2 {{ margin: 0; font-family: var(--heading-font); color: #102839; }}
    .chart-panel p {{ margin: 6px 0 0; color: #345468; }}
    .content .chart-panel.chart-panel-inline {{
      margin: 1rem 0 1.3rem;
      border: 1px solid #d6e8f2;
      border-radius: 12px;
      background: #fcfeff;
      box-shadow: none;
      padding: 12px;
    }}
    .content .chart-panel.chart-panel-inline h2 {{
      margin: 0;
      border-top: 0;
      padding-top: 0;
      font-size: 1.05rem;
      color: #16384a;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
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
    .content {{ padding: clamp(18px, 3vw, 34px); color: var(--ink-body); min-width: 0; overflow-x: hidden; }}
    .content h1, .content h2, .content h3, .content h4 {{ font-family: var(--heading-font); color: #102638; scroll-margin-top: 72px; }}
    .content h1 {{ margin-top: 0; font-size: clamp(1.84rem, 3.4vw, 2.48rem); letter-spacing: -0.02em; }}
    .content h2 {{ margin-top: 2rem; border-top: 1px solid #deebf3; padding-top: 1rem; font-size: clamp(1.32rem, 2.2vw, 1.64rem); }}
    .content p, .content li {{ color: #21384a; font-size: 1.03rem; }}
    .content blockquote {{ margin: 0.8rem 0 1rem; border-left: 4px solid #18b1c0; background: #eef9fc; color: #143448; border-radius: 8px; padding: 0.75rem 0.95rem; font-weight: 600; }}
    .content code {{ background: #e8f5fb; border: 1px solid #cee5f1; border-radius: 6px; padding: 0.06rem 0.26rem; font-family: var(--mono-font); color: #0f3648; }}
    .content pre {{ margin: 0.68rem 0; background: #08131d; color: #e3f0fa; border-radius: 12px; padding: 14px; overflow-x: auto; max-width: 100%; border: 1px solid #1f3545; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03); }}
    .content pre code {{ background: transparent; border: 0; color: inherit; padding: 0; font-size: 0.92rem; }}
    .content img {{
      display: block;
      width: 100%;
      max-width: 100%;
      height: auto;
      margin: 0.9rem 0 1.2rem;
      border: 1px solid #cfe1ec;
      border-radius: 12px;
      background: #ffffff;
      box-shadow: 0 10px 24px rgba(24, 52, 70, 0.14);
    }}
    .content table {{ display: block; width: 100%; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 1rem 0 1.2rem; font-size: 0.94rem; }}
    .content th, .content td {{ border: 1px solid #d6e6f0; padding: 0.55rem; text-align: left; }}
    .content th {{ background: #edf7fc; color: #163547; font-family: var(--heading-font); text-transform: uppercase; letter-spacing: 0.04em; font-size: 0.85rem; }}
    .content tr:nth-child(even) td {{ background: #f9fdff; }}
    .content table.reaction-map {{
      display: table;
      table-layout: fixed;
      width: 100%;
      max-width: 100%;
      overflow-x: visible;
      border-collapse: separate;
      border-spacing: 0;
      margin: 0.8rem 0 1.2rem;
      border: 1px solid #cfe2ee;
      border-radius: 12px;
    }}
    .content table.reaction-map th,
    .content table.reaction-map td {{
      width: 50%;
      vertical-align: top;
      padding: 0.65rem 0.7rem;
      background: #fafdff;
    }}
    .content table.reaction-map tbody tr:nth-child(even) td {{
      background: #f2f9ff;
    }}
    .content table.reaction-map td .math-inline-display {{
      margin: 0;
    }}
    .content table.reaction-map td br + .math-inline-display {{
      margin-top: 0.32rem;
    }}
    .math-display-block {{ border: 1px solid #d5e5ef; border-radius: 10px; background: #f8fcff; margin: 0.2rem 0; overflow-x: auto; padding: 0.6rem 0.7rem; }}
    .content .math-inline {{ display: inline-block; max-width: 100%; vertical-align: middle; }}
    .content .math-inline-display {{ display: block; margin: 0.2rem 0; overflow-x: auto; }}
    .content .math-display-block math,
    .content .math-inline math {{
      max-width: 100%;
      font-family: var(--math-font);
      font-style: normal;
    }}
    .content .admonition {{
      margin: 0.9rem 0 1rem;
      border: 1px solid #c9ddec;
      border-radius: 12px;
      background: linear-gradient(180deg, #f5fbff 0%, #eef7fe 100%);
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.5);
      padding: 0.75rem 0.9rem 0.8rem;
    }}
    .content .admonition .admonition-title {{
      margin: 0 0 0.35rem;
      font-family: var(--heading-font);
      font-size: 0.84rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #0f4a62;
    }}
    .content .admonition ul,
    .content .admonition ol {{ margin: 0.3rem 0 0.2rem 1.05rem; }}
    .content .admonition p {{ margin: 0.25rem 0; }}
    .content .admonition li code {{
      border-radius: 999px;
      padding: 0.05rem 0.42rem;
      background: #ddf2ff;
      border-color: #badcf1;
      font-size: 0.84rem;
    }}
    .content .admonition.info {{
      border-left: 5px solid #22adc0;
      background: linear-gradient(180deg, #f2fdff 0%, #ebf9fe 100%);
    }}
    .content .admonition.note {{
      border-left: 5px solid #2f85c9;
      background: linear-gradient(180deg, #f3f8ff 0%, #eef5fe 100%);
    }}
    .content .admonition.tip {{
      border-left: 5px solid #2b9f69;
      background: linear-gradient(180deg, #f2fff9 0%, #ebfbf3 100%);
    }}
    .inline-chart-anchor {{ display: block; margin: 0; }}
    .inline-module-anchor {{ display: block; margin: 0; }}
    .inline-chart-mount {{
      margin: 0.9rem 0 1.2rem;
      border: 1px solid #d6e8f2;
      border-radius: 12px;
      background: #fcfeff;
      padding: 10px;
      min-width: 0;
      display: grid;
      gap: 8px;
      overflow: hidden;
    }}
    .inline-chart-mount .inline-chart-title {{
      margin: 0;
      color: #19384a;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.84rem;
      font-family: var(--heading-font);
    }}
    .inline-chart-mount .inline-chart-copy {{
      margin: 0;
      color: #375a6e;
      font-size: 0.94rem;
    }}
    .equilibrium-interplay-module {{ margin: 1rem 0 1.25rem; border: 1px solid #245765; border-radius: 14px; background: radial-gradient(circle at 85% 10%, rgba(52,211,153,0.14), transparent 34%), linear-gradient(145deg, #0a2631 0%, #103945 58%, #0d2d39 100%); color: #eafcff; padding: 16px; display: grid; gap: 16px; overflow: hidden; box-shadow: 0 16px 36px rgba(7,38,49,0.16); }}
    .equilibrium-interplay-header {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 16px; align-items: start; }}
    .equilibrium-interplay-title {{ margin: 0; color: #8eeaf0; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.82rem; font-family: var(--heading-font); }}
    .equilibrium-interplay-copy {{ margin: 5px 0 0; color: #d5edf1; max-width: 780px; }}
    .pco2-pressure-readout {{ min-width: 118px; border: 1px solid rgba(142,234,240,0.28); border-radius: 11px; background: rgba(255,255,255,0.08); padding: 9px 12px; text-align: right; }}
    .pco2-pressure-readout span {{ display: block; color: #a8cbd2; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em; }}
    .pco2-pressure-readout strong {{ display: block; color: #ffffff; font-size: 1.55rem; font-family: var(--heading-font); line-height: 1.05; }}
    .pco2-batch-anchor {{ border: 1px solid rgba(98,221,169,0.4); border-radius: 11px; background: rgba(4,25,32,0.48); padding: 11px 13px; display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr); gap: 12px; align-items: center; }}
    .pco2-anchor-step {{ display: grid; gap: 2px; }}
    .pco2-anchor-step span {{ color: #91b8c0; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.07em; }}
    .pco2-anchor-step strong {{ color: #f3feff; font-family: var(--heading-font); font-size: 1.2rem; }}
    .pco2-anchor-step small {{ color: #b8d8dd; font-size: 0.7rem; }}
    .pco2-anchor-step:last-child strong {{ color: #72e5ad; font-size: 1.45rem; }}
    .pco2-anchor-arrow {{ color: #62dda9; font-family: var(--heading-font); font-size: 1.25rem; }}
    .pco2-purity-grid {{ display: grid; grid-template-columns: minmax(260px, 0.92fr) minmax(340px, 1.08fr); gap: 14px; align-items: stretch; }}
    .pco2-control-panel, .pco2-product-panel {{ border: 1px solid rgba(174,224,231,0.2); border-radius: 11px; background: rgba(255,255,255,0.07); padding: 13px; display: grid; gap: 13px; }}
    .pco2-slider-row {{ display: grid; gap: 7px; }}
    .pco2-slider-row label {{ color: #d8f1f4; font-family: var(--heading-font); font-size: 0.84rem; }}
    .pco2-slider-row input[type="range"] {{ width: 100%; accent-color: #62dda9; }}
    .pco2-slider-scale {{ display: flex; justify-content: space-between; color: #8fb6be; font-size: 0.68rem; }}
    .pco2-process-path {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }}
    .pco2-process-stage {{ position: relative; min-height: 82px; border: 1px solid rgba(174,224,231,0.16); border-radius: 9px; background: rgba(5,28,36,0.38); padding: 9px; display: grid; gap: 5px; align-content: center; }}
    .pco2-process-stage:not(:last-child)::after {{ content: ""; position: absolute; top: 50%; right: -8px; width: 8px; height: 2px; background: #62dda9; }}
    .pco2-process-stage span {{ color: #91b8c0; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.06em; }}
    .pco2-process-stage strong {{ color: #f3feff; font-family: var(--heading-font); font-size: 0.84rem; }}
    .pco2-status {{ min-height: 54px; border-left: 3px solid #62dda9; border-radius: 8px; background: rgba(6,31,40,0.46); padding: 8px 10px; color: #d8f1f4; }}
    .pco2-product-heading {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: end; }}
    .pco2-product-heading span {{ color: #a8cbd2; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em; }}
    .pco2-product-heading strong {{ color: #72e5ad; font-family: var(--heading-font); font-size: 2.15rem; line-height: 1; }}
    .pco2-purity-gauge {{ height: 16px; border: 1px solid rgba(174,224,231,0.2); border-radius: 999px; background: linear-gradient(90deg, rgba(217,146,33,0.35), rgba(255,255,255,0.08)); overflow: hidden; }}
    .pco2-purity-gauge span {{ display: block; height: 100%; width: 0%; border-radius: inherit; background: linear-gradient(90deg, #31b779, #72e5ad); transition: width 220ms ease; }}
    .pco2-species-labels {{ display: flex; justify-content: space-between; gap: 8px; color: #b7d7dc; font-size: 0.72rem; }}
    .pco2-species-stack {{ display: flex; height: 30px; border: 1px solid rgba(174,224,231,0.2); border-radius: 8px; overflow: hidden; background: rgba(255,255,255,0.06); }}
    .pco2-species-stack span {{ display: block; height: 100%; min-width: 0; transition: width 220ms ease; }}
    .pco2-species-carbonic {{ background: #3fa2ff; }}
    .pco2-species-bicarbonate {{ background: #34d399; }}
    .pco2-species-carbonate {{ background: #d99221; }}
    .pco2-kpis {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }}
    .pco2-kpi {{ border-top: 1px solid rgba(174,224,231,0.18); padding-top: 8px; display: grid; gap: 2px; }}
    .pco2-kpi span {{ color: #91b8c0; font-size: 0.67rem; text-transform: uppercase; letter-spacing: 0.06em; }}
    .pco2-kpi strong {{ color: #f3feff; font-family: var(--heading-font); font-size: 1.05rem; }}
    .pco2-source-note {{ margin: 0; color: #93b9c1; font-size: 0.72rem; }}
    .calculation-visual-module {{ margin: 1rem 0 1.25rem; border: 1px solid #cfe3ec; border-radius: 12px; background: #fcfeff; padding: 14px; display: grid; gap: 14px; overflow: hidden; }}
    .calculation-visual-title {{ margin: 0; color: #19384a; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.86rem; font-family: var(--heading-font); }}
    .calculation-visual-copy {{ margin: 4px 0 0; color: #345468; }}
    .cycle-flow-controls, .cycle-flow-stage {{ border: 1px solid #d8e8ee; border-radius: 10px; background: rgba(255,255,255,0.76); padding: 12px; }}
    .cycle-flow-controls label {{ color: #2c4d61; font-size: 0.82rem; font-family: var(--heading-font); }}
    .cycle-flow-controls input[type="range"] {{ width: 100%; accent-color: #1fb8cb; }}
    .cycle-flow-grid {{ display: grid; gap: 12px; }}
    .cycle-flow-controls {{ display: grid; grid-template-columns: minmax(180px, 0.6fr) minmax(220px, 1fr); gap: 12px; align-items: center; }}
    .cycle-flow-stages {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; }}
    .cycle-flow-stage {{ min-height: 104px; display: grid; align-content: start; gap: 6px; position: relative; }}
    .cycle-flow-stage::after {{ content: ""; position: absolute; right: -8px; top: 50%; width: 8px; height: 2px; background: #bdd7e2; }}
    .cycle-flow-stage:last-child::after {{ display: none; }}
    .cycle-flow-stage span {{ color: #5f7888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }}
    .cycle-flow-stage strong {{ color: #102839; font-family: var(--heading-font); font-size: 1.05rem; }}
    .cycle-flow-stage p {{ margin: 0; color: #345468; font-size: 0.86rem; }}
    .cycle-flow-stage.is-active {{ border-color: #58b9b7; box-shadow: 0 10px 22px rgba(13, 81, 95, 0.1); }}
    .cycle-flow-summary {{ border-left: 3px solid #1fb8cb; border-radius: 8px; background: rgba(239,248,250,0.74); padding: 8px 10px; color: #345468; }}
    .derivation-stepper-module {{ margin: 1rem 0 1.25rem; border: 1px solid #cfe3ec; border-radius: 12px; background: linear-gradient(135deg, #fcfeff 0%, #f6fbff 58%, #fffaf2 100%); padding: 14px; display: grid; gap: 14px; overflow: hidden; }}
    .derivation-stepper-header {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: start; }}
    .derivation-stepper-title {{ margin: 0; color: #19384a; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.86rem; font-family: var(--heading-font); }}
    .derivation-stepper-copy {{ margin: 4px 0 0; color: #345468; }}
    .derivation-step-count {{ border: 1px solid #d7e8ec; border-radius: 10px; background: rgba(255,255,255,0.78); padding: 8px 10px; color: #5f7888; min-width: 94px; text-align: right; }}
    .derivation-step-count strong {{ display: block; color: #102839; font-size: 1.35rem; font-family: var(--heading-font); line-height: 1; }}
    .derivation-stepper-grid {{ display: grid; grid-template-columns: minmax(230px, 0.82fr) minmax(300px, 1.18fr); gap: 14px; align-items: stretch; }}
    .derivation-controls, .derivation-board {{ border: 1px solid #d8e8ee; border-radius: 10px; background: rgba(255,255,255,0.76); padding: 12px; }}
    .derivation-controls {{ display: grid; gap: 12px; align-content: start; }}
    .derivation-slider-row {{ display: grid; gap: 6px; }}
    .derivation-slider-row label {{ color: #2c4d61; font-size: 0.82rem; font-family: var(--heading-font); }}
    .derivation-slider-row input[type="range"] {{ width: 100%; accent-color: #1fb8cb; }}
    .derivation-step-list {{ display: grid; gap: 6px; }}
    .derivation-step-button {{ width: 100%; min-height: 36px; border: 1px solid #c8dde6; border-radius: 8px; background: #f8fcfd; color: #25485d; cursor: pointer; font-family: var(--heading-font); font-size: 0.8rem; text-align: left; padding: 7px 9px; }}
    .derivation-step-button[aria-current="step"] {{ color: #062b35; border-color: #58b9b7; background: #dff7f1; box-shadow: inset 0 0 0 1px rgba(31,184,203,0.28); }}
    .derivation-board {{ display: grid; gap: 12px; min-width: 0; }}
    .derivation-stage-label {{ margin: 0; color: #19384a; font-family: var(--heading-font); font-size: 1.05rem; }}
    .derivation-stage-purpose {{ margin: 0; color: #345468; }}
    .derivation-equation-stack {{ display: grid; gap: 8px; }}
    .derivation-equation {{ border: 1px solid #d9e9f3; border-radius: 10px; background: #ffffff; padding: 10px; color: #102839; font-size: 0.95rem; line-height: 1.45; overflow-x: auto; transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease; }}
    .derivation-equation .math-display-block {{ margin: 0; overflow-x: auto; }}
    .derivation-equation.is-active {{ border-color: #58b9b7; box-shadow: 0 10px 22px rgba(13, 81, 95, 0.1); transform: translateY(-2px); }}
    .derivation-callout {{ border-left: 3px solid #1fb8cb; border-radius: 8px; background: rgba(239,248,250,0.74); padding: 8px 10px; color: #345468; min-height: 50px; }}
    .reveal-node {{ opacity: 0; transform: translateY(12px); transition: opacity 360ms ease, transform 360ms ease; }}
    .reveal-node.is-visible {{ opacity: 1; transform: translateY(0); }}
    .footer {{ font-size: 0.85rem; color: #496578; margin-top: 1.8rem; border-top: 1px solid #d9e9f3; padding-top: 0.75rem; }}
    @media (max-width: 1180px) {{
      .hero-metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .shell {{ grid-template-columns: 1fr; }}
      .control-bar {{ width: min(1480px, calc(100vw - 16px)); }}
      .rail {{ position: static; max-height: none; }}
      .toc-scroll {{ max-height: 340px; }}
      .control-primary,
      .control-secondary {{ gap: 6px; }}
      .control-primary select {{ flex: 1 1 240px; }}
    }}
    @media (max-width: 760px) {{
      .hero-metrics {{ grid-template-columns: 1fr; }}
      .chart-stack {{ height: clamp(200px, 52vw, 260px); min-height: 200px; max-height: 260px; }}
      .equilibrium-interplay-header {{ grid-template-columns: 1fr; }}
      .pco2-pressure-readout {{ text-align: left; }}
      .pco2-batch-anchor {{ grid-template-columns: 1fr; }}
      .pco2-anchor-arrow {{ display: none; }}
      .pco2-purity-grid {{ grid-template-columns: 1fr; }}
      .pco2-process-path {{ grid-template-columns: 1fr 1fr; }}
      .pco2-process-stage::after {{ display: none; }}
      .pco2-kpis {{ grid-template-columns: 1fr; }}
      .cycle-flow-controls {{ grid-template-columns: 1fr; }}
      .cycle-flow-stages {{ grid-template-columns: 1fr; }}
      .cycle-flow-stage::after {{ display: none; }}
      .derivation-stepper-header, .derivation-stepper-grid {{ grid-template-columns: 1fr; }}
      .derivation-step-count {{ text-align: left; }}
      .content table.reaction-map {{
        display: block;
        border: 0;
        border-radius: 0;
      }}
      .content table.reaction-map thead {{
        display: none;
      }}
      .content table.reaction-map tbody,
      .content table.reaction-map tr,
      .content table.reaction-map td {{
        display: block;
        width: 100%;
      }}
      .content table.reaction-map tr {{
        margin: 0 0 0.85rem;
        border: 1px solid #cfe2ee;
        border-radius: 11px;
        overflow: hidden;
      }}
      .content table.reaction-map td + td {{
        border-top: 1px solid #dceaf3;
      }}
      .control-bar {{ padding: 8px; gap: 6px; }}
      .control-primary,
      .control-secondary {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        width: 100%;
      }}
      .control-primary select,
      .control-secondary select {{
        grid-column: 1 / -1;
        width: 100%;
      }}
      .slide-studio {{ padding: 0; }}
      .slide-studio-shell {{ height: 100vh; border-radius: 0; }}
      .slide-studio-body {{ grid-template-columns: 1fr; overflow: auto; }}
      .slide-studio-sidebar, .slide-studio-properties {{ border: 0; border-bottom: 1px solid #31596b; max-height: 180px; }}
      .slide-studio-workspace {{ min-height: 420px; }}
      body.presentation-mode .shell {{
        width: calc(100vw - 16px);
      }}
      body.presentation-mode .content {{
        aspect-ratio: 16 / 9;
        padding: 18px 20px;
      }}
      body.presentation-mode .slide-format {{ display: none; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      body.presentation-mode .content > [data-slide-active="true"] {{
        animation: none;
      }}
    }}
    @media print {{
      body {{
        background: #ffffff !important;
        color: #000000 !important;
      }}
      .hero,
      .control-bar,
      .rail,
      .progress-track,
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
      <a class="hero-cta" id="start-walkthrough" href="#1-basis-setup-700-g-naoh-in-2200-ml-water">Start Walkthrough</a>
    </div>
  </header>

  <section class="control-bar" id="presenter-controls" aria-label="Presentation controls">
    <div class="control-primary">
      <button id="prev" type="button" aria-label="Previous section">Previous</button>
      <button id="next" type="button" aria-label="Next section">Next</button>
      <label for="section-selector" class="sr-only">Jump to section</label>
      <select id="section-selector" aria-label="Jump to section"></select>
      <button id="real-data-jump" type="button">Real Data</button>
      <button id="slide-mode" type="button" aria-pressed="false">Slide Mode: Off</button>
      <button id="controls-more" type="button" aria-expanded="false" aria-controls="secondary-controls">More Controls</button>
      <span class="slide-format" id="slide-format" aria-live="polite">
        16:9 Widescreen
      </span>
    </div>
    <div class="control-secondary" id="secondary-controls" hidden>
      <button id="motion" type="button" aria-pressed="true">Motion: On</button>
      <button id="auto-advance" type="button" aria-pressed="false">Auto-Advance: Off</button>
      <button id="section-organizer-toggle" type="button" aria-expanded="false" aria-controls="section-organizer">Sections</button>
      <button id="tile-reveal-toggle" type="button" aria-pressed="false">Tile Reveal: Off</button>
      <button id="tile-reveal-next" type="button" disabled>Reveal Next Tile</button>
      <button id="tile-reveal-reset" type="button" disabled>Reset Reveals</button>
      <label for="speed" class="label">Speed</label>
      <select id="speed" aria-label="Auto-advance speed">
        <option value="3">3s</option>
        <option value="5" selected>5s</option>
        <option value="8">8s</option>
        <option value="12">12s</option>
      </select>
      <button id="reset" type="button">Reset View</button>
      <button id="print-export" type="button">Print/PDF</button>
      <button id="slide-studio-open" type="button">Slide Studio</button>
      <div class="section-organizer" id="section-organizer" hidden>
        <div class="section-organizer-header">
          <span class="section-organizer-title">Section Organizer</span>
          <button id="section-layout-reset" type="button">Reset Sections</button>
        </div>
        <div class="section-organizer-list" id="section-organizer-list" aria-label="Reorder and hide walkthrough sections"></div>
      </div>
    </div>
  </section>

  <div class="shell">
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
      <section id="cycle-trend-panel" class="surface chart-panel" aria-label="Cycle trend highlights">
        <h2>Cycle Trend Highlights</h2>
        <p>Use these tabs to inspect how loading, hydroxide depletion, and fraction crossover control bicarbonate formation through the Section 9 worked table.</p>
        <div class="chart-module" id="cycle-chart-module">
          <div class="chart-tabs" role="tablist" aria-label="Cycle trend chart views">
            <button id="cycle-tab-ph" class="chart-tab" type="button" role="tab" aria-selected="true" aria-controls="cycle-chart-view-ph">pH + m_OH</button>
            <button id="cycle-tab-fraction" class="chart-tab" type="button" role="tab" aria-selected="false" aria-controls="cycle-chart-view-fraction">Carbonate Fractions</button>
            <button id="cycle-tab-loading" class="chart-tab" type="button" role="tab" aria-selected="false" aria-controls="cycle-chart-view-loading">Loading + CT</button>
          </div>
          <div class="chart-stack">
            <section id="cycle-chart-view-ph" class="chart-view is-active" role="tabpanel" aria-labelledby="cycle-tab-ph">
              <h3>pH and Hydroxide by Cycle</h3>
              <div class="chart-viewport">
                <canvas id="ph-trend-chart" aria-label="pH and hydroxide by cycle chart"></canvas>
              </div>
            </section>
            <section id="cycle-chart-view-fraction" class="chart-view" role="tabpanel" aria-labelledby="cycle-tab-fraction">
              <h3>Carbonate Fractions by Cycle</h3>
              <div class="chart-viewport">
                <canvas id="fraction-trend-chart" aria-label="Carbonate fraction by cycle chart"></canvas>
              </div>
            </section>
            <section id="cycle-chart-view-loading" class="chart-view" role="tabpanel" aria-labelledby="cycle-tab-loading">
              <h3>Cycle Loading and CT</h3>
              <div class="chart-viewport">
                <canvas id="cycle-loading-chart" aria-label="Cycle loading and CT chart"></canvas>
              </div>
            </section>
          </div>
        </div>
        <div id="chart-fallback" class="chart-fallback" role="status" aria-live="polite"></div>
      </section>
    </main>
  </div>

  <section class="slide-studio" id="slide-studio" role="dialog" aria-modal="true" aria-labelledby="slide-studio-heading" hidden>
    <div class="slide-studio-shell">
      <header class="slide-studio-header">
        <span class="slide-studio-title" id="slide-studio-heading">GL-260 Slide Studio</span>
        <button id="slide-studio-new" type="button">New Slide</button>
        <button id="slide-studio-edit-current" type="button">Edit Current Slide</button>
        <button id="slide-studio-duplicate" type="button">Duplicate</button>
        <button id="slide-studio-delete" type="button">Delete</button>
        <button id="slide-studio-export" type="button">Export JSON</button>
        <button id="slide-studio-import" type="button">Import JSON</button>
        <input class="slide-studio-import" id="slide-studio-import-file" type="file" accept="application/json,.json">
        <button id="slide-studio-close" type="button">Close</button>
      </header>
      <div class="slide-studio-body">
        <aside class="slide-studio-sidebar">
          <span class="slide-studio-label">Custom slides</span>
          <div class="slide-studio-list" id="slide-studio-list"></div>
        </aside>
        <main class="slide-studio-workspace">
          <div>
            <div class="slide-studio-toolbar" aria-label="Add slide elements">
              <button type="button" data-studio-add="title">Title</button>
              <button type="button" data-studio-add="text">Text</button>
              <button type="button" data-studio-add="bullets">Bullets</button>
              <button type="button" data-studio-add="image">Image</button>
              <button type="button" data-studio-add="table">Table</button>
              <button type="button" data-studio-add="chart">Chart</button>
              <button type="button" data-studio-format="bold"><strong>B</strong></button>
              <button type="button" data-studio-format="italic"><em>I</em></button>
              <button type="button" data-studio-format="underline"><u>U</u></button>
            </div>
            <div class="slide-studio-canvas" id="slide-studio-canvas" aria-label="Editable 16 by 9 slide canvas"></div>
          </div>
        </main>
        <aside class="slide-studio-properties">
          <label class="slide-studio-field"><span class="slide-studio-label">Slide title</span><input id="slide-studio-slide-title" type="text"></label>
          <label class="slide-studio-field"><span class="slide-studio-label">Element fill</span><input id="slide-studio-fill" type="color" value="#ffffff"></label>
          <label class="slide-studio-field"><span class="slide-studio-label">Text color</span><input id="slide-studio-color" type="color" value="#102839"></label>
          <label class="slide-studio-field"><span class="slide-studio-label">Font size</span><input id="slide-studio-font-size" type="number" min="10" max="72" value="22"></label>
          <button id="slide-studio-remove-element" type="button">Remove Selected Element</button>
          <p class="slide-studio-help">Drag elements to position them. Resize from the lower-right corner. Double-click text, bullets, or table cells to edit. Images are embedded into the saved slide. Use Export JSON for backups because browser storage is local to this browser profile.</p>
        </aside>
      </div>
      <footer class="slide-studio-footer">
        <span class="slide-studio-status" id="slide-studio-status" role="status" aria-live="polite">Custom slides save automatically.</span>
        <button id="slide-studio-present" type="button">Save &amp; Present</button>
      </footer>
    </div>
  </section>

  <script>
    (function () {{
      const tocNav = document.getElementById("toc-nav");
      const filterInput = document.getElementById("toc-filter");
      const content = document.getElementById("walkthrough-content");
      const progressBar = document.getElementById("scroll-progress");
      const cycleTrendPanel = document.getElementById("cycle-trend-panel");
      const chartFallback = document.getElementById("chart-fallback");
      const startWalkthrough = document.getElementById("start-walkthrough");
      const realDataJump = document.getElementById("real-data-jump");
      const motionToggle = document.getElementById("motion");
      const autoAdvanceToggle = document.getElementById("auto-advance");
      const speedSelect = document.getElementById("speed");
      const slideModeToggle = document.getElementById("slide-mode");
      const controlsMoreButton = document.getElementById("controls-more");
      const secondaryControlsPanel = document.getElementById("secondary-controls");
      const sectionOrganizerToggle = document.getElementById("section-organizer-toggle");
      const sectionOrganizerPanel = document.getElementById("section-organizer");
      const sectionOrganizerList = document.getElementById("section-organizer-list");
      const sectionLayoutReset = document.getElementById("section-layout-reset");
      const tileRevealToggle = document.getElementById("tile-reveal-toggle");
      const tileRevealNext = document.getElementById("tile-reveal-next");
      const tileRevealReset = document.getElementById("tile-reveal-reset");
      const resetButton = document.getElementById("reset");
      const printExportButton = document.getElementById("print-export");
      const slideStudioOpen = document.getElementById("slide-studio-open");
      const slideStudio = document.getElementById("slide-studio");
      const slideStudioCanvas = document.getElementById("slide-studio-canvas");
      const slideStudioList = document.getElementById("slide-studio-list");
      const slideStudioStatus = document.getElementById("slide-studio-status");
      const slideStudioTitleInput = document.getElementById("slide-studio-slide-title");
      const slideStudioFill = document.getElementById("slide-studio-fill");
      const slideStudioColor = document.getElementById("slide-studio-color");
      const slideStudioFontSize = document.getElementById("slide-studio-font-size");
      const prevButton = document.getElementById("prev");
      const nextButton = document.getElementById("next");
      const sectionSelector = document.getElementById("section-selector");
      const cycleTabPh = document.getElementById("cycle-tab-ph");
      const cycleTabFraction = document.getElementById("cycle-tab-fraction");
      const cycleTabLoading = document.getElementById("cycle-tab-loading");
      const cycleViewPh = document.getElementById("cycle-chart-view-ph");
      const cycleViewFraction = document.getElementById("cycle-chart-view-fraction");
      const cycleViewLoading = document.getElementById("cycle-chart-view-loading");
      const presentationShell = document.querySelector(".shell");
      const slideFormat = document.getElementById("slide-format");
      let phChart = null;
      let fractionChart = null;
      let cycleLoadingChart = null;
      let pco2Chart = null;
      let stoichChart = null;
      let uptakeLoadingChart = null;
      let anchorResidualChart = null;
      let chartsInitialized = false;
      let autoAdvanceTimer = null;
      let revealObserver = null;
      let sectionHeadings = [];
      let sectionBlocks = [];
      let sectionLayoutState = {{ order: [], hidden: {{}} }};
      let tileRevealTiles = [];
      let tileRevealEnabled = false;
      let currentSectionIndex = 0;
      const sectionLayoutStorageKey = "gl260-equilibrium-section-layout-v1";
      const slideStudioStorageKey = "gl260-equilibrium-slide-studio-v1";
      let studioSlides = [];
      let activeStudioSlideId = "";
      let activeStudioElementId = "";
      let studioSourceSectionId = "";
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

      let tocLinks = tocNav
        ? Array.from(tocNav.querySelectorAll("a[href^='#']"))
        : [];
      const headingMap = new Map();
      let headingNodes = Array.from(
        document.querySelectorAll("#walkthrough-content h2, #walkthrough-content h3, #walkthrough-content h4")
      );
      for (const heading of headingNodes) {{
        if (heading.id) {{
          headingMap.set("#" + heading.id, heading);
        }}
      }}

      /** Create a collision-resistant local identifier for a slide or element.
       * Why: author-created nodes need stable storage and DOM keys.
       * Inputs: prefix, a short identifier category. Returns: string id.
       * Side effects: none. Errors: falls back to time/random entropy.
       */
      function studioId(prefix) {{
        return prefix + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
      }}

      /** Sanitize formatted author text before it enters the slide DOM.
       * Why: imported JSON must not execute scripts or event handlers.
       * Inputs: html, locally edited or imported markup. Returns: safe HTML.
       * Side effects: creates a detached template. Errors: invalid input becomes text.
       */
      function sanitizeStudioHtml(html) {{
        const template = document.createElement("template");
        template.innerHTML = String(html || "");
        template.content.querySelectorAll("script,style,iframe,object,embed,link,meta").forEach(function (node) {{ node.remove(); }});
        template.content.querySelectorAll("*").forEach(function (node) {{
          Array.from(node.attributes).forEach(function (attribute) {{
            if (attribute.name.toLowerCase().startsWith("on")) {{ node.removeAttribute(attribute.name); }}
          }});
        }});
        return template.innerHTML;
      }}

      /** Read saved custom slides from browser storage.
       * Why: generated HTML cannot write Markdown, so local persistence preserves work.
       * Inputs: none. Returns: validated slide array.
       * Side effects: reads localStorage. Errors: corrupt/unavailable storage returns [].
       */
      function readStudioSlides() {{
        try {{
          const parsed = JSON.parse(window.localStorage.getItem(slideStudioStorageKey) || "[]");
          return Array.isArray(parsed) ? parsed.filter(function (slide) {{ return slide && slide.id; }}) : [];
        }} catch (error) {{
          return [];
        }}
      }}

      /** Persist the complete custom slide deck.
       * Why: every edit should survive refreshes without server access.
       * Inputs: none; reads studioSlides. Returns: boolean success.
       * Side effects: writes localStorage and status copy. Errors: quota failures are reported.
       */
      function writeStudioSlides() {{
        try {{
          window.localStorage.setItem(slideStudioStorageKey, JSON.stringify(studioSlides));
          if (slideStudioStatus) {{ slideStudioStatus.textContent = "Saved locally. Use Export JSON for a portable backup."; }}
          return true;
        }} catch (error) {{
          if (slideStudioStatus) {{ slideStudioStatus.textContent = "Save failed: browser storage may be full. Export JSON and reduce image size."; }}
          return false;
        }}
      }}

      /** Return the currently edited slide model.
       * Why: editor actions share one authoritative selection lookup.
       * Inputs: none. Returns: slide object or null. Side effects: none.
       * Errors: missing selection returns null.
       */
      function activeStudioSlide() {{
        return studioSlides.find(function (slide) {{ return slide.id === activeStudioSlideId; }}) || null;
      }}

      /** Build an accessible inline SVG bar chart from a chart element model.
       * Why: custom charts must remain self-contained without external libraries.
       * Inputs: element with labels and numeric values. Returns: SVG markup.
       * Side effects: none. Errors: invalid values are normalized to zero.
       */
      function studioChartSvg(element) {{
        const labels = Array.isArray(element.labels) ? element.labels.slice(0, 8) : ["A", "B", "C"];
        const values = Array.isArray(element.values) ? element.values.slice(0, 8).map(Number) : [3, 6, 4];
        const maximum = Math.max.apply(null, values.concat([1]));
        const width = 720;
        const height = 360;
        const slot = width / Math.max(values.length, 1);
        const bars = values.map(function (value, index) {{
          const safeValue = Number.isFinite(value) ? Math.max(value, 0) : 0;
          const barHeight = (safeValue / maximum) * 250;
          const x = (index * slot) + (slot * 0.2);
          const y = 300 - barHeight;
          const label = String(labels[index] || "Item " + (index + 1)).replace(/[<>&]/g, "");
          return '<rect x="' + x + '" y="' + y + '" width="' + (slot * 0.6) + '" height="' + barHeight + '" rx="6" fill="#1fb8cb"/><text x="' + (x + slot * 0.3) + '" y="325" text-anchor="middle" font-size="18" fill="#345468">' + label + '</text><text x="' + (x + slot * 0.3) + '" y="' + Math.max(y - 8, 18) + '" text-anchor="middle" font-size="17" fill="#102839">' + safeValue + '</text>';
        }}).join("");
        return '<svg class="studio-chart-svg" viewBox="0 0 720 360" role="img" aria-label="Custom bar chart"><line x1="20" y1="300" x2="700" y2="300" stroke="#9cbac6" stroke-width="2"/>' + bars + '</svg>';
      }}

      /** Create one editable or presentation-ready slide element node.
       * Why: editor and runtime slides must render from the same model.
       * Inputs: element model and editable flag. Returns: positioned HTMLElement.
       * Side effects: none beyond detached node construction. Errors: unknown types render text.
       */
      function buildStudioElementNode(element, editable) {{
        const node = document.createElement("div");
        node.className = "studio-element";
        node.dataset.elementId = element.id;
        node.dataset.type = element.type;
        node.style.left = Number(element.x || 5) + "%";
        node.style.top = Number(element.y || 8) + "%";
        node.style.width = Number(element.w || 40) + "%";
        node.style.height = Number(element.h || 18) + "%";
        node.style.color = element.color || "#102839";
        node.style.backgroundColor = element.fill || "rgba(255,255,255,0.78)";
        node.style.fontSize = Number(element.fontSize || 22) + "px";
        if (element.type === "image") {{
          const imageNode = document.createElement("img");
          imageNode.src = String(element.src || "");
          imageNode.alt = String(element.alt || "Custom slide image");
          node.appendChild(imageNode);
        }} else if (element.type === "chart") {{
          node.innerHTML = studioChartSvg(element);
        }} else {{
          node.innerHTML = sanitizeStudioHtml(element.html || (element.type === "bullets" ? "<ul><li>First point</li><li>Second point</li></ul>" : "Double-click to edit"));
        }}
        return node;
      }}

      /** Copy canvas geometry/content back into the active slide model.
       * Why: drag, resize, and rich-text edits occur directly in the preview DOM.
       * Inputs: none. Returns: undefined.
       * Side effects: mutates model and localStorage. Errors: missing canvas/slide is a no-op.
       */
      function syncStudioCanvasToModel() {{
        const slide = activeStudioSlide();
        if (!(slide && slideStudioCanvas)) {{ return; }}
        const canvasRect = slideStudioCanvas.getBoundingClientRect();
        slide.elements.forEach(function (element) {{
          const node = slideStudioCanvas.querySelector('[data-element-id="' + element.id + '"]');
          if (!node) {{ return; }}
          const rect = node.getBoundingClientRect();
          element.x = ((rect.left - canvasRect.left) / canvasRect.width) * 100;
          element.y = ((rect.top - canvasRect.top) / canvasRect.height) * 100;
          element.w = (rect.width / canvasRect.width) * 100;
          element.h = (rect.height / canvasRect.height) * 100;
          element.color = node.style.color || element.color;
          element.fill = node.style.backgroundColor || element.fill;
          element.fontSize = parseFloat(node.style.fontSize) || element.fontSize;
          if (element.type !== "image" && element.type !== "chart") {{ element.html = sanitizeStudioHtml(node.innerHTML); }}
        }});
        writeStudioSlides();
      }}

      /** Render all saved slides into the walkthrough before navigation initializes.
       * Why: custom slides must behave like ordinary H2 presentation sections.
       * Inputs: none. Returns: undefined.
       * Side effects: replaces runtime custom slide DOM. Errors: invalid slides are skipped.
       */
      function renderStudioRuntimeSlides() {{
        content.querySelectorAll('[data-studio-runtime="true"]').forEach(function (node) {{ node.remove(); }});
        studioSlides.filter(function (slide) {{ return Boolean(slide.sourceId); }}).forEach(function (slide) {{
          const heading = document.getElementById(slide.sourceId);
          if (!heading) {{ return; }}
          let sibling = heading.nextElementSibling;
          while (sibling && String(sibling.tagName || "").toUpperCase() !== "H2") {{
            const nextSibling = sibling.nextElementSibling;
            sibling.remove();
            sibling = nextSibling;
          }}
          heading.textContent = slide.title || heading.textContent;
          const canvas = document.createElement("section");
          canvas.className = "studio-slide-runtime";
          canvas.dataset.studioRuntime = "true";
          canvas.setAttribute("aria-label", slide.title || "Edited walkthrough slide");
          (slide.elements || []).forEach(function (element) {{ canvas.appendChild(buildStudioElementNode(element, false)); }});
          heading.insertAdjacentElement("afterend", canvas);
        }});
        studioSlides.filter(function (slide) {{ return !slide.sourceId; }}).forEach(function (slide, index) {{
          const heading = document.createElement("h2");
          heading.id = "studio-slide-" + slide.id;
          heading.dataset.studioRuntime = "true";
          heading.textContent = "Custom " + (index + 1) + ") " + (slide.title || "Untitled Slide");
          const canvas = document.createElement("section");
          canvas.className = "studio-slide-runtime";
          canvas.dataset.studioRuntime = "true";
          canvas.setAttribute("aria-label", slide.title || "Custom slide");
          (slide.elements || []).forEach(function (element) {{ canvas.appendChild(buildStudioElementNode(element, false)); }});
          content.appendChild(heading);
          content.appendChild(canvas);
        }});
      }}

      /** Refresh heading and TOC registries after custom slides are inserted.
       * Why: presentation navigation captures headings once during startup.
       * Inputs: none. Returns: undefined.
       * Side effects: rebuilds custom TOC links and heading maps. Errors: absent TOC is tolerated.
       */
      function refreshStudioHeadingRegistry() {{
        if (tocNav) {{
          tocNav.querySelectorAll('[data-studio-toc="true"]').forEach(function (node) {{ node.remove(); }});
          const list = tocNav.querySelector(".toc > ul");
          if (list) {{
            studioSlides.filter(function (slide) {{ return !slide.sourceId; }}).forEach(function (slide, index) {{
              const item = document.createElement("li");
              item.dataset.studioToc = "true";
              const link = document.createElement("a");
              link.href = "#studio-slide-" + slide.id;
              link.textContent = "Custom " + (index + 1) + ") " + (slide.title || "Untitled Slide");
              item.appendChild(link);
              list.appendChild(item);
            }});
          }}
          studioSlides.filter(function (slide) {{ return Boolean(slide.sourceId); }}).forEach(function (slide) {{
            const link = tocNav.querySelector('a[href="#' + slide.sourceId + '"]');
            if (link) {{ link.textContent = slide.title || link.textContent; }}
          }});
        }}
        tocLinks = tocNav ? Array.from(tocNav.querySelectorAll("a[href^='#']")) : [];
        headingNodes = Array.from(content.querySelectorAll("h2, h3, h4"));
        headingMap.clear();
        headingNodes.forEach(function (heading) {{ if (heading.id) {{ headingMap.set("#" + heading.id, heading); }} }});
      }}

      /** Render the editor canvas and custom-slide list for the active model.
       * Why: all authoring actions need one consistent visual refresh.
       * Inputs: none. Returns: undefined.
       * Side effects: rebuilds editor DOM and wires drag/select behavior. Errors: empty deck shows guidance.
       */
      function renderSlideStudioEditor() {{
        if (!(slideStudioCanvas && slideStudioList)) {{ return; }}
        slideStudioList.innerHTML = "";
        studioSlides.forEach(function (slide) {{
          const button = document.createElement("button");
          button.type = "button";
          button.textContent = (slide.sourceId ? "Override · " : "Custom · ") + (slide.title || "Untitled Slide");
          button.classList.toggle("is-active", slide.id === activeStudioSlideId);
          button.addEventListener("click", function () {{ activeStudioSlideId = slide.id; activeStudioElementId = ""; renderSlideStudioEditor(); }});
          slideStudioList.appendChild(button);
        }});
        const slide = activeStudioSlide();
        slideStudioCanvas.innerHTML = "";
        if (!slide) {{
          slideStudioCanvas.innerHTML = '<div style="padding:8%;font-size:24px">Choose New Slide to begin.</div>';
          return;
        }}
        if (slideStudioTitleInput) {{ slideStudioTitleInput.value = slide.title || ""; }}
        (slide.elements || []).forEach(function (element) {{
          const node = buildStudioElementNode(element, true);
          node.classList.toggle("is-selected", element.id === activeStudioElementId);
          if (element.type !== "image" && element.type !== "chart") {{
            node.addEventListener("dblclick", function () {{ node.setAttribute("contenteditable", "true"); node.focus(); }});
            node.addEventListener("blur", function () {{ node.removeAttribute("contenteditable"); syncStudioCanvasToModel(); }});
          }}
          node.addEventListener("pointerdown", function (event) {{
            activeStudioElementId = element.id;
            renderSlideStudioEditor();
            const selected = slideStudioCanvas.querySelector('[data-element-id="' + element.id + '"]');
            if (!selected || selected.getAttribute("contenteditable") === "true") {{ return; }}
            const startX = event.clientX;
            const startY = event.clientY;
            const startLeft = selected.offsetLeft;
            const startTop = selected.offsetTop;
            const move = function (moveEvent) {{
              selected.style.left = Math.max(0, startLeft + moveEvent.clientX - startX) + "px";
              selected.style.top = Math.max(0, startTop + moveEvent.clientY - startY) + "px";
            }};
            const stop = function () {{ document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", stop); syncStudioCanvasToModel(); }};
            document.addEventListener("pointermove", move);
            document.addEventListener("pointerup", stop);
          }});
          node.addEventListener("input", syncStudioCanvasToModel);
          node.addEventListener("pointerup", syncStudioCanvasToModel);
          slideStudioCanvas.appendChild(node);
        }});
      }}

      /** Add one supported element type to the active custom slide.
       * Why: toolbar actions need consistent defaults and storage behavior.
       * Inputs: type, one of title/text/bullets/image/table/chart. Returns: undefined.
       * Side effects: may open prompts/file picker, mutates deck, rerenders editor.
       * Errors: cancelled prompts/uploads leave the slide unchanged.
       */
      function addStudioElement(type) {{
        const slide = activeStudioSlide();
        if (!slide) {{ return; }}
        const contentIndex = slide.elements.filter(function (candidate) {{ return candidate.type !== "title"; }}).length;
        const element = {{ id: studioId("element"), type: type, x: type === "title" ? 7 : 7 + ((contentIndex % 2) * 45), y: type === "title" ? 6 : 25 + (Math.floor(contentIndex / 2) * 30), w: type === "title" ? 86 : 40, h: type === "title" ? 16 : 24, color: "#102839", fill: type === "title" ? "rgba(255,255,255,0)" : "rgba(255,255,255,0.78)", fontSize: type === "title" ? 40 : 22, html: "" }};
        if (type === "title") {{ element.html = "Slide title"; }}
        if (type === "text") {{ element.html = "Double-click to edit formatted text."; }}
        if (type === "bullets") {{ element.html = "<ul><li>First point</li><li>Second point</li></ul>"; }}
        if (type === "table") {{
          const rows = Math.max(1, Math.min(10, Number(window.prompt("Table rows", "3")) || 0));
          const columns = Math.max(1, Math.min(8, Number(window.prompt("Table columns", "3")) || 0));
          if (!rows || !columns) {{ return; }}
          element.w = 72; element.h = 36;
          element.html = "<table><tbody>" + Array.from({{ length: rows }}, function (_, row) {{ return "<tr>" + Array.from({{ length: columns }}, function (_, column) {{ return "<td>" + (row === 0 ? "Header " + (column + 1) : "Value") + "</td>"; }}).join("") + "</tr>"; }}).join("") + "</tbody></table>";
        }}
        if (type === "chart") {{
          const labels = window.prompt("Comma-separated chart labels", "Cycle 1,Cycle 2,Cycle 3");
          const values = window.prompt("Comma-separated chart values", "20,55,82");
          if (labels === null || values === null) {{ return; }}
          element.labels = labels.split(",").map(function (value) {{ return value.trim(); }});
          element.values = values.split(",").map(Number);
          element.w = 62; element.h = 42;
        }}
        if (type === "image") {{
          const picker = document.createElement("input");
          picker.type = "file";
          picker.accept = "image/*";
          picker.addEventListener("change", function () {{
            const file = picker.files && picker.files[0];
            if (!file) {{ return; }}
            const reader = new FileReader();
            reader.addEventListener("load", function () {{ element.src = String(reader.result || ""); element.alt = file.name; element.w = 55; element.h = 48; slide.elements.push(element); activeStudioElementId = element.id; writeStudioSlides(); renderSlideStudioEditor(); }});
            reader.readAsDataURL(file);
          }});
          picker.click();
          return;
        }}
        slide.elements.push(element);
        activeStudioElementId = element.id;
        writeStudioSlides();
        renderSlideStudioEditor();
      }}

      /** Import the active generated walkthrough section as an editable override.
       * Why: authors need to modify existing slides without changing Markdown.
       * Inputs: none; reads currentSectionIndex and sectionBlocks. Returns: undefined.
       * Side effects: creates an override model, persists it, and opens the editor.
       * Errors: missing/custom sections are reported without changing stored slides.
       */
      function importCurrentStudioSlide() {{
        const activeHeading = studioSourceSectionId
          ? document.getElementById(studioSourceSectionId)
          : sectionHeadings[currentSectionIndex];
        const block = sectionBlocks.find(function (candidate) {{ return candidate.heading === activeHeading; }});
        if (!(activeHeading && block && activeHeading.id)) {{
          if (slideStudioStatus) {{ slideStudioStatus.textContent = "The current slide could not be imported."; }}
          return;
        }}
        if (activeHeading.id.startsWith("studio-slide-")) {{
          const customId = activeHeading.id.slice("studio-slide-".length);
          if (studioSlides.some(function (slide) {{ return slide.id === customId; }})) {{
            activeStudioSlideId = customId;
            activeStudioElementId = "";
            if (slideStudio) {{ slideStudio.hidden = false; }}
            renderSlideStudioEditor();
            return;
          }}
        }}
        let override = studioSlides.find(function (slide) {{ return slide.sourceId === activeHeading.id; }});
        if (!override) {{
          const sourceNodes = block.nodes.filter(function (node) {{ return node !== activeHeading; }});
          const slotHeight = Math.max(7, Math.min(22, 84 / Math.max(sourceNodes.length, 1)));
          override = {{
            id: studioId("override"),
            sourceId: activeHeading.id,
            title: String(activeHeading.textContent || "Edited Slide").trim(),
            elements: sourceNodes.map(function (node, index) {{
              return {{
                id: studioId("element"),
                type: "text",
                x: 4,
                y: 5 + (index * slotHeight),
                w: 92,
                h: Math.max(slotHeight - 1, 6),
                color: "#102839",
                fill: "rgba(255,255,255,0.82)",
                fontSize: 15,
                html: sanitizeStudioHtml(node.outerHTML)
              }};
            }})
          }};
          studioSlides.push(override);
          writeStudioSlides();
        }}
        activeStudioSlideId = override.id;
        activeStudioElementId = "";
        if (slideStudio) {{ slideStudio.hidden = false; }}
        renderSlideStudioEditor();
        if (slideStudioStatus) {{ slideStudioStatus.textContent = "Imported built-in slide as a local override. Delete this override and reload to restore the generated original."; }}
      }}

      /** Initialize Slide Studio, load saved slides, and wire authoring controls.
       * Why: custom slides must exist before section navigation captures headings.
       * Inputs: none. Returns: undefined.
       * Side effects: reads storage, inserts runtime slides, and registers UI events.
       * Errors: unavailable controls/storage degrade to the original walkthrough.
       */
      function initializeSlideStudio() {{
        studioSlides = readStudioSlides();
        activeStudioSlideId = studioSlides.length ? studioSlides[0].id : "";
        renderStudioRuntimeSlides();
        refreshStudioHeadingRegistry();
        if (!(slideStudio && slideStudioOpen)) {{ return; }}
        slideStudioOpen.addEventListener("click", function () {{
          const selectedIndex = Number(sectionSelector && sectionSelector.value);
          const sourceHeading = sectionHeadings[Number.isFinite(selectedIndex) ? selectedIndex : currentSectionIndex];
          studioSourceSectionId = sourceHeading && sourceHeading.id ? sourceHeading.id : "";
          slideStudio.hidden = false;
          renderSlideStudioEditor();
        }});
        document.getElementById("slide-studio-close").addEventListener("click", function () {{ syncStudioCanvasToModel(); slideStudio.hidden = true; }});
        document.getElementById("slide-studio-new").addEventListener("click", function () {{
          const slide = {{ id: studioId("slide"), title: "New Custom Slide", elements: [] }};
          studioSlides.push(slide); activeStudioSlideId = slide.id; activeStudioElementId = ""; writeStudioSlides(); renderSlideStudioEditor();
        }});
        document.getElementById("slide-studio-edit-current").addEventListener("click", importCurrentStudioSlide);
        document.getElementById("slide-studio-duplicate").addEventListener("click", function () {{
          const slide = activeStudioSlide(); if (!slide) {{ return; }}
          const copy = JSON.parse(JSON.stringify(slide)); copy.id = studioId("slide"); delete copy.sourceId; copy.title += " Copy"; copy.elements.forEach(function (element) {{ element.id = studioId("element"); }}); studioSlides.push(copy); activeStudioSlideId = copy.id; writeStudioSlides(); renderSlideStudioEditor();
        }});
        document.getElementById("slide-studio-delete").addEventListener("click", function () {{
          if (!activeStudioSlideId || !window.confirm("Delete this custom slide?")) {{ return; }}
          studioSlides = studioSlides.filter(function (slide) {{ return slide.id !== activeStudioSlideId; }}); activeStudioSlideId = studioSlides.length ? studioSlides[0].id : ""; activeStudioElementId = ""; writeStudioSlides(); renderSlideStudioEditor();
        }});
        document.querySelectorAll("[data-studio-add]").forEach(function (button) {{ button.addEventListener("click", function () {{ addStudioElement(button.dataset.studioAdd); }}); }});
        document.querySelectorAll("[data-studio-format]").forEach(function (button) {{ button.addEventListener("click", function () {{ document.execCommand(button.dataset.studioFormat, false); syncStudioCanvasToModel(); }}); }});
        if (slideStudioTitleInput) {{ slideStudioTitleInput.addEventListener("input", function () {{ const slide = activeStudioSlide(); if (slide) {{ slide.title = slideStudioTitleInput.value; writeStudioSlides(); }} }}); }}
        [slideStudioFill, slideStudioColor, slideStudioFontSize].forEach(function (control) {{ if (control) {{ control.addEventListener("input", function () {{ const element = activeStudioSlide() && activeStudioSlide().elements.find(function (candidate) {{ return candidate.id === activeStudioElementId; }}); if (!element) {{ return; }} element.fill = slideStudioFill.value; element.color = slideStudioColor.value; element.fontSize = Number(slideStudioFontSize.value); renderSlideStudioEditor(); writeStudioSlides(); }}); }} }});
        document.getElementById("slide-studio-remove-element").addEventListener("click", function () {{ const slide = activeStudioSlide(); if (!slide) {{ return; }} slide.elements = slide.elements.filter(function (element) {{ return element.id !== activeStudioElementId; }}); activeStudioElementId = ""; writeStudioSlides(); renderSlideStudioEditor(); }});
        document.getElementById("slide-studio-present").addEventListener("click", function () {{ syncStudioCanvasToModel(); window.location.reload(); }});
        document.getElementById("slide-studio-export").addEventListener("click", function () {{
          syncStudioCanvasToModel(); const blob = new Blob([JSON.stringify({{ schema: 1, slides: studioSlides }}, null, 2)], {{ type: "application/json" }}); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "gl260-custom-slides.json"; link.click(); URL.revokeObjectURL(link.href);
        }});
        const importFile = document.getElementById("slide-studio-import-file");
        document.getElementById("slide-studio-import").addEventListener("click", function () {{ importFile.click(); }});
        importFile.addEventListener("change", function () {{ const file = importFile.files && importFile.files[0]; if (!file) {{ return; }} const reader = new FileReader(); reader.addEventListener("load", function () {{ try {{ const payload = JSON.parse(String(reader.result || "")); if (!payload || !Array.isArray(payload.slides)) {{ throw new Error("Invalid slide deck"); }} studioSlides = payload.slides; activeStudioSlideId = studioSlides.length ? studioSlides[0].id : ""; writeStudioSlides(); renderSlideStudioEditor(); }} catch (error) {{ slideStudioStatus.textContent = "Import failed: invalid Slide Studio JSON."; }} }}); reader.readAsText(file); }});
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

      function findInlineChartAnchor(name) {{
        return content.querySelector('[data-inline-chart="' + String(name || "") + '"]');
      }}

      function findInlineModuleAnchor(name) {{
        return content.querySelector('[data-inline-module="' + String(name || "") + '"]');
      }}

      /** Resolve or create one inline chart canvas.
       * Purpose: provide a stable canvas for generated and Slide Studio-rendered charts.
       * Why: saved slide overrides can retain the mounted canvas after replacing the
       * original data-inline-chart anchor, so existing canvases must be reusable.
       * Inputs: config containing the optional anchor, required canvasId, title, copy,
       * and accessibility labels. Returns: the existing or newly created canvas, or null.
       * Side effects: creates and mounts chart DOM only when no reusable canvas exists.
       * Errors: missing identifiers or invalid/missing anchors fail closed with null.
       */
      function buildInlineChartMount(config) {{
        const canvasId = config && config.canvasId ? String(config.canvasId) : "";
        if (!canvasId) {{
          return null;
        }}
        const existingCanvas = document.getElementById(canvasId);
        if (existingCanvas) {{
          return existingCanvas;
        }}
        const anchor = config && config.anchor ? config.anchor : null;
        if (!anchor || String(anchor.tagName || "").toUpperCase() !== "DIV") {{
          return null;
        }}
        const mount = document.createElement("section");
        mount.className = "inline-chart-mount";
        mount.setAttribute("aria-label", config.ariaLabel || "Inline chart");
        const title = document.createElement("p");
        title.className = "inline-chart-title";
        title.textContent = config.title || "Trend View";
        mount.appendChild(title);
        if (config.copy) {{
          const copy = document.createElement("p");
          copy.className = "inline-chart-copy";
          copy.textContent = config.copy;
          mount.appendChild(copy);
        }}
        const viewport = document.createElement("div");
        viewport.className = "chart-viewport";
        const canvas = document.createElement("canvas");
        canvas.id = canvasId;
        canvas.setAttribute("aria-label", config.canvasAria || (config.title || "Inline chart"));
        viewport.appendChild(canvas);
        mount.appendChild(viewport);
        anchor.replaceWith(mount);
        return canvas;
      }}

      /**
       * Build the pCO2-to-NaHCO3 purity-potential presentation module.
       * The module replaces the compact sensitivity table with one operational
       * story: increasing headspace pCO2 lowers pH, suppresses carbonate, and
       * raises the equilibrium bicarbonate share.
       * Inputs: none; reads the equilibrium-interplay inline anchor.
       * Returns: undefined.
       * Side effects: replaces the anchor and wires one pressure slider.
       * Errors: missing anchors or optional output nodes are handled as no-ops.
       */
      function ensureEquilibriumInterplayModule() {{
        if (document.getElementById("equilibrium-interplay-module")) {{
          return;
        }}
        const anchor = findInlineModuleAnchor("equilibrium-interplay");
        if (!(anchor && anchor.parentNode)) {{
          return;
        }}
        const module = document.createElement("section");
        module.id = "equilibrium-interplay-module";
        module.className = "equilibrium-interplay-module";
        module.setAttribute("aria-label", "pCO2 to sodium bicarbonate purity visual");
        module.innerHTML = `
          <div class="equilibrium-interplay-header">
            <div>
              <div class="equilibrium-interplay-title">pCO2 → NaHCO3 Purity Path</div>
              <div class="equilibrium-interplay-copy">Raise headspace CO2 pressure and follow the same chemistry through dissolved CO2, hydroxide consumption, carbonate suppression, and bicarbonate-selective product potential.</div>
            </div>
            <div class="pco2-pressure-readout">
              <span>Headspace pCO2</span>
              <strong><output data-pco2-pressure>1.00</output> atm</strong>
            </div>
          </div>
          <div class="pco2-batch-anchor" aria-label="775 gram carbon dioxide uptake target and predicted pH">
            <div class="pco2-anchor-step">
              <span>Absorbed CO2 target</span>
              <strong>775 g</strong>
              <small>17.61 mol CO2</small>
            </div>
            <div class="pco2-anchor-arrow" aria-hidden="true">→</div>
            <div class="pco2-anchor-step">
              <span>700 g NaOH basis</span>
              <strong>17.50 mol</strong>
              <small>Near the 1:1 bicarbonate endpoint</small>
            </div>
            <div class="pco2-anchor-arrow" aria-hidden="true">→</div>
            <div class="pco2-anchor-step">
              <span>Predicted batch state</span>
              <strong>pH ≈ 8.1</strong>
              <small>Bicarbonate-dominant target</small>
            </div>
          </div>
          <div class="pco2-purity-grid">
            <div class="pco2-control-panel">
              <div class="pco2-slider-row">
                <label for="pco2-purity-slider">Move the operating pCO2</label>
                <input id="pco2-purity-slider" type="range" min="10" max="400" value="100" step="10">
                <div class="pco2-slider-scale"><span>0.10 atm</span><span>2.00 atm</span><span>4.00 atm</span></div>
              </div>
              <div class="pco2-process-path" aria-label="pCO2 process consequence path">
                <div class="pco2-process-stage"><span>Headspace</span><strong data-path-pressure>1.00 atm CO2</strong></div>
                <div class="pco2-process-stage"><span>Liquid boundary</span><strong>Dissolved CO2 rises</strong></div>
                <div class="pco2-process-stage"><span>Alkalinity</span><strong data-path-hydroxide>OH- is consumed</strong></div>
                <div class="pco2-process-stage"><span>Carbonate impurity</span><strong data-path-carbonate>30.5% CO3</strong></div>
              </div>
              <div class="pco2-status" data-pco2-status></div>
            </div>
            <div class="pco2-product-panel">
              <div class="pco2-product-heading">
                <div>
                  <span>NaHCO3-form purity potential</span>
                  <div class="pco2-source-note">Equilibrium bicarbonate share, not a final solid assay</div>
                </div>
                <strong data-purity-potential>69.3%</strong>
              </div>
              <div class="pco2-purity-gauge" aria-label="Bicarbonate purity potential">
                <span data-purity-fill></span>
              </div>
              <div class="pco2-species-labels"><span>CO2*</span><span>HCO3-</span><span>CO3^2-</span></div>
              <div class="pco2-species-stack" aria-label="Reactive carbon species distribution">
                <span class="pco2-species-carbonic" data-species-fill="carbonic"></span>
                <span class="pco2-species-bicarbonate" data-species-fill="bicarbonate"></span>
                <span class="pco2-species-carbonate" data-species-fill="carbonate"></span>
              </div>
              <div class="pco2-kpis">
                <div class="pco2-kpi"><span>Sensitivity-state pH</span><strong data-pco2-ph>9.45</strong></div>
                <div class="pco2-kpi"><span>Bicarbonate</span><strong data-pco2-bicarbonate>69.3%</strong></div>
                <div class="pco2-kpi"><span>Carbonate</span><strong data-pco2-carbonate>30.5%</strong></div>
              </div>
              <div class="pco2-source-note">Interpolated from the locked 25 C, 700 g NaOH, and 2,200 mL water sensitivity points formerly shown as the compact sweep.</div>
            </div>
          </div>
        `;
        anchor.replaceWith(module);

        const slider = module.querySelector("#pco2-purity-slider");
        const pressureOutput = module.querySelector("[data-pco2-pressure]");
        const pathPressure = module.querySelector("[data-path-pressure]");
        const pathHydroxide = module.querySelector("[data-path-hydroxide]");
        const pathCarbonate = module.querySelector("[data-path-carbonate]");
        const status = module.querySelector("[data-pco2-status]");
        const purityPotential = module.querySelector("[data-purity-potential]");
        const purityFill = module.querySelector("[data-purity-fill]");
        const phOutput = module.querySelector("[data-pco2-ph]");
        const bicarbonateOutput = module.querySelector("[data-pco2-bicarbonate]");
        const carbonateOutput = module.querySelector("[data-pco2-carbonate]");
        const speciesFills = {{
          carbonic: module.querySelector('[data-species-fill="carbonic"]'),
          bicarbonate: module.querySelector('[data-species-fill="bicarbonate"]'),
          carbonate: module.querySelector('[data-species-fill="carbonate"]')
        }};
        const sensitivityPoints = [
          {{ pco2: 0.10, pH: 10.25, carbonic: 0.0002, bicarbonate: 0.1820, carbonate: 0.8178 }},
          {{ pco2: 0.50, pH: 9.85, carbonic: 0.0008, bicarbonate: 0.4107, carbonate: 0.5885 }},
          {{ pco2: 1.00, pH: 9.45, carbonic: 0.0025, bicarbonate: 0.6928, carbonate: 0.3047 }},
          {{ pco2: 2.00, pH: 9.05, carbonic: 0.0086, bicarbonate: 0.8409, carbonate: 0.1505 }},
          {{ pco2: 4.00, pH: 8.65, carbonic: 0.0272, bicarbonate: 0.8952, carbonate: 0.0776 }}
        ];

        /**
         * Interpolate one display state from the locked pCO2 sensitivity points.
         * The interpolation exists to preserve the documented calculations while
         * giving the presentation a continuous pressure control.
         * Inputs: pressure, headspace pCO2 in atmospheres.
         * Returns: pH and normalized carbon-species fractions.
         * Side effects: none.
         * Errors: non-finite values are clamped to the first point.
         */
        function interpolateSensitivityState(pressure) {{
          const boundedPressure = Number.isFinite(pressure)
            ? Math.min(Math.max(pressure, sensitivityPoints[0].pco2), sensitivityPoints[sensitivityPoints.length - 1].pco2)
            : sensitivityPoints[0].pco2;
          let upperIndex = sensitivityPoints.findIndex(function (point) {{
            return point.pco2 >= boundedPressure;
          }});
          if (upperIndex <= 0) {{
            return {{ ...sensitivityPoints[0] }};
          }}
          if (upperIndex < 0) {{
            return {{ ...sensitivityPoints[sensitivityPoints.length - 1] }};
          }}
          const lower = sensitivityPoints[upperIndex - 1];
          const upper = sensitivityPoints[upperIndex];
          const ratio = (boundedPressure - lower.pco2) / (upper.pco2 - lower.pco2);
          return {{
            pco2: boundedPressure,
            pH: lower.pH + ((upper.pH - lower.pH) * ratio),
            carbonic: lower.carbonic + ((upper.carbonic - lower.carbonic) * ratio),
            bicarbonate: lower.bicarbonate + ((upper.bicarbonate - lower.bicarbonate) * ratio),
            carbonate: lower.carbonate + ((upper.carbonate - lower.carbonate) * ratio)
          }};
        }}

        /**
         * Render the pCO2 consequence path and NaHCO3-form purity potential.
         * It exists so pressure, pH, carbonate impurity, and bicarbonate
         * selectivity update as one chemically linked presentation state.
         * Inputs: none; reads the pressure slider value in hundredths of an atm.
         * Returns: undefined.
         * Side effects: updates text, ARIA copy, gauge width, and species widths.
         * Errors: missing optional output nodes are handled as no-ops.
         */
        function updatePco2PurityModule() {{
          const pressure = Number(slider ? slider.value : 100) / 100;
          const state = interpolateSensitivityState(pressure);
          const carbonicPercent = state.carbonic * 100;
          const bicarbonatePercent = state.bicarbonate * 100;
          const carbonatePercent = state.carbonate * 100;
          const pressureText = state.pco2.toFixed(2);
          const bicarbonateText = bicarbonatePercent.toFixed(1) + "%";
          const carbonateText = carbonatePercent.toFixed(1) + "%";
          if (pressureOutput) {{ pressureOutput.textContent = pressureText; }}
          if (pathPressure) {{ pathPressure.textContent = pressureText + " atm CO2"; }}
          if (pathHydroxide) {{
            pathHydroxide.textContent = state.pco2 < 0.75
              ? "High OH- remains"
              : state.pco2 < 2.0 ? "OH- is consumed" : "Low free OH-";
          }}
          if (pathCarbonate) {{ pathCarbonate.textContent = carbonateText + " CO3"; }}
          if (purityPotential) {{ purityPotential.textContent = bicarbonateText; }}
          if (purityFill) {{ purityFill.style.width = bicarbonatePercent.toFixed(2) + "%"; }}
          if (phOutput) {{ phOutput.textContent = state.pH.toFixed(2); }}
          if (bicarbonateOutput) {{ bicarbonateOutput.textContent = bicarbonateText; }}
          if (carbonateOutput) {{ carbonateOutput.textContent = carbonateText; }}
          if (speciesFills.carbonic) {{ speciesFills.carbonic.style.width = carbonicPercent.toFixed(2) + "%"; }}
          if (speciesFills.bicarbonate) {{ speciesFills.bicarbonate.style.width = bicarbonatePercent.toFixed(2) + "%"; }}
          if (speciesFills.carbonate) {{ speciesFills.carbonate.style.width = carbonatePercent.toFixed(2) + "%"; }}
          if (slider) {{
            slider.setAttribute(
              "aria-valuetext",
              pressureText + " atm; " + bicarbonateText + " bicarbonate-form purity potential"
            );
          }}
          if (status) {{
            status.textContent = bicarbonatePercent < 50
              ? "Carbonate-rich region: insufficient pCO2 leaves most reactive carbon as carbonate impurity."
              : bicarbonatePercent < 80
                ? "Transition region: higher pCO2 is suppressing carbonate, but bicarbonate selectivity is not yet strong."
                : "Bicarbonate-dominant region: higher pCO2 lowers carbonate impurity and raises NaHCO3-form product potential.";
          }}
        }}

        if (slider) {{
          slider.addEventListener("input", updatePco2PurityModule);
        }}
        updatePco2PurityModule();
      }}

      function ensureCycleFlowVisualModule() {{
        if (document.getElementById("cycle-flow-visual-module")) {{
          return;
        }}
        const anchor = findInlineModuleAnchor("cycle-flow-visual");
        if (!(anchor && anchor.parentNode)) {{
          return;
        }}
        const module = document.createElement("section");
        module.id = "cycle-flow-visual-module";
        module.className = "calculation-visual-module";
        module.setAttribute("aria-label", "Cycle calculation flow visual module");
        module.innerHTML = `
          <div>
            <p class="calculation-visual-title">Cycle Calculation Flow</p>
            <p class="calculation-visual-copy">Select a synthetic cycle to see how one accepted uptake event becomes loading, pH, speciation, and dashboard outputs.</p>
          </div>
          <div class="cycle-flow-grid">
            <div class="cycle-flow-controls">
              <label for="cycle-flow-slider">Cycle index</label>
              <input id="cycle-flow-slider" type="range" min="0" max="8" value="5" step="1">
            </div>
            <div class="cycle-flow-stages">
              <div class="cycle-flow-stage" data-cycle-stage="delta"><span>Accepted uptake</span><strong data-cycle-value="delta">0 g</strong><p>cycle event</p></div>
              <div class="cycle-flow-stage" data-cycle-stage="cum"><span>Cumulative uptake</span><strong data-cycle-value="cum">0 g</strong><p>total carbon added</p></div>
              <div class="cycle-flow-stage" data-cycle-stage="ct"><span>Carbon basis</span><strong data-cycle-value="ct">0.0000</strong><p>mol/kg CT</p></div>
              <div class="cycle-flow-stage" data-cycle-stage="ph"><span>Equilibrium solve</span><strong data-cycle-value="ph">0.00 pH</strong><p>charge closure</p></div>
              <div class="cycle-flow-stage" data-cycle-stage="species"><span>Dominant species</span><strong data-cycle-value="species">-</strong><p>displayed fraction</p></div>
            </div>
            <div class="cycle-flow-summary" data-cycle-flow-summary></div>
          </div>
        `;
        anchor.replaceWith(module);

        const slider = module.querySelector("#cycle-flow-slider");
        const values = {{
          delta: module.querySelector('[data-cycle-value="delta"]'),
          cum: module.querySelector('[data-cycle-value="cum"]'),
          ct: module.querySelector('[data-cycle-value="ct"]'),
          ph: module.querySelector('[data-cycle-value="ph"]'),
          species: module.querySelector('[data-cycle-value="species"]')
        }};
        const summary = module.querySelector("[data-cycle-flow-summary]");
        const stages = Array.from(module.querySelectorAll("[data-cycle-stage]"));
        const data = [
          {{ cycle: 0, delta: 0, cum: 0, ct: 0.0000, ph: 15.2672, species: "OH-", frac: 1.0 }},
          {{ cycle: 1, delta: 80, cum: 80, ct: 0.8263, ph: 15.1608, species: "CO3^2-", frac: 1.0 }},
          {{ cycle: 2, delta: 90, cum: 170, ct: 1.7558, ph: 15.0093, species: "CO3^2-", frac: 1.0 }},
          {{ cycle: 3, delta: 100, cum: 270, ct: 2.7886, ph: 14.7436, species: "CO3^2-", frac: 1.0 }},
          {{ cycle: 4, delta: 110, cum: 380, ct: 3.9247, ph: 13.4003, species: "CO3^2-", frac: 1.0 }},
          {{ cycle: 5, delta: 120, cum: 500, ct: 5.1641, ph: 9.6257, species: "CO3^2-", frac: 0.5404 }},
          {{ cycle: 6, delta: 130, cum: 630, ct: 6.5068, ph: 9.2061, species: "HCO3-", frac: 0.7771 }},
          {{ cycle: 7, delta: 130, cum: 760, ct: 7.8495, ph: 8.2255, species: "HCO3-", frac: 0.9810 }},
          {{ cycle: 8, delta: 140, cum: 900, ct: 9.2954, ph: 7.8538, species: "HCO3-", frac: 0.9867 }}
        ];

        function updateCycleFlow() {{
          const index = Math.max(0, Math.min(data.length - 1, Number(slider ? slider.value : 5)));
          const row = data[index];
          if (values.delta) {{ values.delta.textContent = row.delta + " g"; }}
          if (values.cum) {{ values.cum.textContent = row.cum + " g"; }}
          if (values.ct) {{ values.ct.textContent = row.ct.toFixed(4); }}
          if (values.ph) {{ values.ph.textContent = row.ph.toFixed(2) + " pH"; }}
          if (values.species) {{ values.species.textContent = row.species; }}
          stages.forEach(function (stage, stageIndex) {{
            stage.classList.toggle("is-active", stageIndex <= Math.min(index, 4));
          }});
          if (summary) {{
            summary.textContent =
              "Cycle " + row.cycle + " carries " + row.cum + " g cumulative CO2 into the equilibrium solve; the model reports " +
              row.ph.toFixed(2) + " pH with " + row.species + " as the dominant state (" + Math.round(row.frac * 100) + "%).";
          }}
        }}
        if (slider) {{
          slider.addEventListener("input", updateCycleFlow);
        }}
        updateCycleFlow();
      }}

      function ensureDerivationStepperModule() {{
        if (document.getElementById("derivation-stepper-module")) {{
          return;
        }}
        const anchor = findInlineModuleAnchor("derivation-stepper");
        if (!(anchor && anchor.parentNode)) {{
          return;
        }}
        const module = document.createElement("section");
        module.id = "derivation-stepper-module";
        module.className = "derivation-stepper-module";
        module.setAttribute("aria-label", "Interactive equation derivation stepper");
        module.innerHTML = `
          <div class="derivation-stepper-header">
            <div>
              <p class="derivation-stepper-title">Live Derivation Slider</p>
            </div>
            <div class="derivation-step-count">
              <span>Step</span>
              <strong data-derivation-count>1 / 8</strong>
            </div>
          </div>
          <div class="derivation-stepper-grid">
            <div class="derivation-controls">
              <div class="derivation-slider-row">
                <label for="derivation-step-slider">Derivation progress</label>
                <input id="derivation-step-slider" type="range" min="0" max="7" value="0" step="1">
              </div>
              <div class="derivation-step-list" data-derivation-step-list></div>
            </div>
            <div class="derivation-board">
              <p class="derivation-stage-label" data-derivation-title></p>
              <p class="derivation-stage-purpose" data-derivation-purpose></p>
              <div class="derivation-equation-stack" data-derivation-equations></div>
              <div class="derivation-callout" data-derivation-callout></div>
            </div>
          </div>
        `;
        anchor.replaceWith(module);

        const steps = {derivation_steps_json};

        const slider = module.querySelector("#derivation-step-slider");
        const count = module.querySelector("[data-derivation-count]");
        const title = module.querySelector("[data-derivation-title]");
        const purpose = module.querySelector("[data-derivation-purpose]");
        const equations = module.querySelector("[data-derivation-equations]");
        const callout = module.querySelector("[data-derivation-callout]");
        const stepList = module.querySelector("[data-derivation-step-list]");

        function renderStepButtons(activeIndex) {{
          if (!stepList) {{
            return;
          }}
          stepList.innerHTML = "";
          steps.forEach(function (step, index) {{
            const button = document.createElement("button");
            button.type = "button";
            button.className = "derivation-step-button";
            button.textContent = step.title;
            if (index === activeIndex) {{
              button.setAttribute("aria-current", "step");
            }}
            button.addEventListener("click", function () {{
              if (slider) {{
                slider.value = String(index);
              }}
              renderDerivationStep(index);
            }});
            stepList.appendChild(button);
          }});
        }}

        function renderDerivationStep(index) {{
          const boundedIndex = Math.max(0, Math.min(steps.length - 1, Number(index) || 0));
          const step = steps[boundedIndex];
          if (count) {{
            count.textContent = String(boundedIndex + 1) + " / " + String(steps.length);
          }}
          if (title) {{
            title.textContent = step.title;
          }}
          if (purpose) {{
            purpose.textContent = step.purpose;
          }}
          if (equations) {{
            equations.innerHTML = "";
            step.equationsHtml.forEach(function (equationHtml, equationIndex) {{
              const block = document.createElement("div");
              block.className = "derivation-equation";
              block.classList.toggle("is-active", equationIndex === step.equationsHtml.length - 1);
              block.innerHTML = equationHtml;
              equations.appendChild(block);
            }});
          }}
          if (callout) {{
            callout.innerHTML = step.calloutHtml || "";
          }}
          renderStepButtons(boundedIndex);
        }}

        if (slider) {{
          slider.max = String(steps.length - 1);
          slider.addEventListener("input", function () {{
            renderDerivationStep(Number(slider.value));
          }});
        }}
        renderDerivationStep(0);
      }}

      function ensureCycleTrendPanelInline() {{
        if (!cycleTrendPanel) {{
          return;
        }}
        const anchor = findInlineChartAnchor("cycle-trend-highlights");
        if (!(anchor && anchor.parentNode)) {{
          return;
        }}
        cycleTrendPanel.classList.add("chart-panel-inline");
        anchor.replaceWith(cycleTrendPanel);
      }}

      function ensureStoichChartMount() {{
        const anchor = findInlineChartAnchor("stoich-impact");
        return buildInlineChartMount({{
          anchor: anchor,
            canvasId: "stoich-impact-chart",
            title: "Stoichiometric Endpoint Impact",
            copy: "These landmarks show how quickly required CO2 mass rises from carbonate endpoint to bicarbonate endpoint.",
            ariaLabel: "Stoichiometric endpoint impact chart",
            canvasAria: "Stoichiometric endpoint impact chart",
        }});
      }}

      function ensureUptakeLoadingChartMount() {{
        const anchor = findInlineChartAnchor("uptake-loading");
        return buildInlineChartMount({{
          anchor: anchor,
            canvasId: "uptake-loading-chart",
            title: "Cycle Uptake and Cumulative Loading",
            copy: "Per-cycle uptake events are converted to cumulative loading, which drives the state update each cycle.",
            ariaLabel: "Cycle uptake and cumulative loading chart",
            canvasAria: "Cycle uptake and cumulative loading chart",
        }});
      }}

      function ensureAnchorResidualChartMount() {{
        const anchor = findInlineChartAnchor("anchor-residuals");
        return buildInlineChartMount({{
          anchor: anchor,
            canvasId: "anchor-residual-chart",
            title: "Anchor Residual Impact",
            copy: "Measured-vs-baseline anchor gaps define the direction and magnitude of correction before ML residual smoothing.",
            ariaLabel: "Anchor residual impact chart",
            canvasAria: "Anchor residual impact chart",
        }});
      }}

      function setActiveCycleTab(tabKey) {{
        const activeTabKey =
          tabKey === "fraction" || tabKey === "loading" ? tabKey : "ph";
        const showingPh = activeTabKey === "ph";
        const showingFraction = activeTabKey === "fraction";
        const showingLoading = activeTabKey === "loading";
        if (cycleTabPh) {{
          cycleTabPh.setAttribute("aria-selected", String(showingPh));
        }}
        if (cycleTabFraction) {{
          cycleTabFraction.setAttribute("aria-selected", String(showingFraction));
        }}
        if (cycleTabLoading) {{
          cycleTabLoading.setAttribute("aria-selected", String(showingLoading));
        }}
        if (cycleViewPh) {{
          cycleViewPh.classList.toggle("is-active", showingPh);
        }}
        if (cycleViewFraction) {{
          cycleViewFraction.classList.toggle("is-active", showingFraction);
        }}
        if (cycleViewLoading) {{
          cycleViewLoading.classList.toggle("is-active", showingLoading);
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
        if (cycleTabLoading) {{
          cycleTabLoading.addEventListener("click", function () {{
            setActiveCycleTab("loading");
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
          const sectionVisible = !heading || !heading.hidden;
          const show =
            sectionVisible && (!needle || linkText.includes(needle) || headingText.includes(needle));
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

      function tileIsVisible(tile) {{
        if (!tile || tile.hidden || tile.closest("[hidden], [data-section-hidden='true']")) {{
          return false;
        }}
        const rect = tile.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      }}

      function tileRevealFragments(tile) {{
        if (!tile) {{
          return [];
        }}
        return Array.from(tile.querySelectorAll(":scope > .tile-build-fragment"));
      }}

      function tileHasHiddenFragments(tile) {{
        return tileRevealFragments(tile).some(function (fragment) {{
          return !fragment.classList.contains("is-revealed");
        }});
      }}

      function updateTileRevealCompletion(tile) {{
        const fragments = tileRevealFragments(tile);
        const isComplete =
          fragments.length > 0 &&
          fragments.every(function (fragment) {{
            return fragment.classList.contains("is-revealed");
          }});
        tile.classList.toggle("is-build-complete", isComplete);
      }}

      function updateTileRevealControls() {{
        const hasHiddenVisibleFragments = tileRevealTiles.some(function (tile) {{
          return tileIsVisible(tile) && tileHasHiddenFragments(tile);
        }});
        document.body.classList.toggle("tile-reveal-enabled", tileRevealEnabled);
        if (tileRevealToggle) {{
          tileRevealToggle.setAttribute("aria-pressed", String(tileRevealEnabled));
          tileRevealToggle.textContent = "Tile Reveal: " + (tileRevealEnabled ? "On" : "Off");
        }}
        if (tileRevealNext) {{
          tileRevealNext.disabled = !tileRevealEnabled || !hasHiddenVisibleFragments;
        }}
        if (tileRevealReset) {{
          tileRevealReset.disabled = !tileRevealEnabled || !tileRevealTiles.length;
        }}
      }}

      function resetTileRevealFragments() {{
        for (const tile of tileRevealTiles) {{
          tile.classList.remove("is-build-complete");
          for (const fragment of tileRevealFragments(tile)) {{
            fragment.classList.remove("is-revealed");
          }}
        }}
        updateTileRevealControls();
      }}

      function revealTile(tile) {{
        if (!tileRevealEnabled || !tile) {{
          return false;
        }}
        const hiddenFragments = tileRevealFragments(tile).filter(function (fragment) {{
          return !fragment.classList.contains("is-revealed");
        }});
        if (!hiddenFragments.length) {{
          updateTileRevealCompletion(tile);
          updateTileRevealControls();
          return false;
        }}
        for (const fragment of hiddenFragments) {{
          fragment.classList.add("is-revealed");
        }}
        updateTileRevealCompletion(tile);
        updateTileRevealControls();
        return true;
      }}

      function tileRevealViewportScore(tile) {{
        const rect = tile.getBoundingClientRect();
        const viewportCenter = window.innerHeight / 2;
        const tileCenter = rect.top + rect.height / 2;
        const intersectsViewport = rect.bottom >= 0 && rect.top <= window.innerHeight;
        return (intersectsViewport ? 0 : 100000) + Math.abs(tileCenter - viewportCenter);
      }}

      function revealNextVisibleTileFragment() {{
        const candidates = tileRevealTiles
          .filter(function (tile) {{
            return tileIsVisible(tile) && tileHasHiddenFragments(tile);
          }})
          .sort(function (firstTile, secondTile) {{
            return tileRevealViewportScore(firstTile) - tileRevealViewportScore(secondTile);
          }});
        if (!candidates.length) {{
          updateTileRevealControls();
          return false;
        }}
        return revealTile(candidates[0]);
      }}

      function setTileRevealEnabled(enabled) {{
        tileRevealEnabled = Boolean(enabled);
        if (tileRevealEnabled) {{
          resetTileRevealFragments();
        }}
        updateTileRevealControls();
      }}

      function initializeTileRevealTiles() {{
        tileRevealTiles = Array.from(content.querySelectorAll(".calculation-map-step")).filter(
          function (tile) {{
            const childElements = Array.from(tile.children);
            if (childElements.length < 2) {{
              return false;
            }}
            childElements.forEach(function (child, index) {{
              if (index > 0) {{
                child.classList.add("tile-build-fragment");
              }}
            }});
            tile.setAttribute("tabindex", "0");
            tile.addEventListener("click", function (event) {{
              const interactiveTarget = event.target.closest(
                "a, button, input, select, textarea, label"
              );
              if (interactiveTarget) {{
                return;
              }}
              revealTile(tile);
            }});
            tile.addEventListener("keydown", function (event) {{
              if (event.key !== "Enter" && event.key !== " ") {{
                return;
              }}
              if (!tileRevealEnabled) {{
                return;
              }}
              event.preventDefault();
              revealTile(tile);
            }});
            return true;
          }}
        );
        updateTileRevealControls();
      }}

      function initializeLayoutPhase() {{
        initializeSlideStudio();
        ensureDerivationStepperModule();
        ensureEquilibriumInterplayModule();
        ensureCycleFlowVisualModule();
        ensureCycleTrendPanelInline();
        if (filterInput) {{
          filterInput.addEventListener("input", applyFilter);
        }}
        applyFilter();
        initializeChartTabs();
        initializeTileRevealTiles();
        window.addEventListener("scroll", updateScrollProgress, {{ passive: true }});
        window.addEventListener("resize", updateScrollProgress);
        initializeActiveSectionTracking();
        updateScrollProgress();
      }}

      function markRevealNodes() {{
        const revealNodes = Array.from(
          content.querySelectorAll(
            "h2, h3, p, ul, ol, blockquote, table, pre, img, .admonition, .math-display-block, .math-inline-display, .inline-chart-mount, .equilibrium-interplay-module, .calculation-visual-module, .derivation-stepper-module, .chart-panel-inline"
          )
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
          delta: [],
          cumulative: [],
          ct: [],
          ph: [],
          moh: [],
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
          const deltaValue = parseNumericCell(cells[1].textContent);
          const cumulativeValue = parseNumericCell(cells[2].textContent);
          const ctValue = parseNumericCell(cells[3].textContent);
          const phValue = parseNumericCell(cells[4].textContent);
          const mohValue = parseNumericCell(cells[5].textContent);
          const h2co3Value = parseNumericCell(cells[6].textContent);
          const hco3Value = parseNumericCell(cells[7].textContent);
          const co3Value = parseNumericCell(cells[8].textContent);
          if (
            cycleValue === null ||
            deltaValue === null ||
            cumulativeValue === null ||
            ctValue === null ||
            phValue === null ||
            mohValue === null ||
            h2co3Value === null ||
            hco3Value === null ||
            co3Value === null
          ) {{
            continue;
          }}
          series.cycle.push(cycleValue);
          series.delta.push(deltaValue);
          series.cumulative.push(cumulativeValue);
          series.ct.push(ctValue);
          series.ph.push(phValue);
          series.moh.push(mohValue);
          series.h2co3.push(h2co3Value);
          series.hco3.push(hco3Value);
          series.co3.push(co3Value);
        }}
        return series.cycle.length ? series : null;
      }}

      function extractPco2SensitivitySeries() {{
        const tables = Array.from(content.querySelectorAll("table"));
        const inlineAnchor = findInlineChartAnchor("pco2-sensitivity");
        let targetTable = null;
        if (inlineAnchor) {{
          let cursor = inlineAnchor.previousElementSibling;
          while (cursor && !targetTable) {{
            if (String(cursor.tagName || "").toUpperCase() === "TABLE") {{
              targetTable = cursor;
              break;
            }}
            cursor = cursor.previousElementSibling;
          }}
        }}
        if (!targetTable) {{
          targetTable = tables.find(function (tableNode) {{
            const headers = Array.from(tableNode.querySelectorAll("th")).map(function (header) {{
              return String(header.textContent || "").trim().toLowerCase();
            }});
            const compactHeaders = headers.map(function (header) {{
              return header.replace(/[^a-z0-9]+/g, "");
            }});
            // MathML-rendered carbonate headers lose the Markdown text shape, so
            // identify the pCO2 sweep table by stable neighboring columns too.
            return (
              headers.includes("pco2 (atm)") &&
              headers.includes("ph") &&
              compactHeaders.some(function (header) {{ return header.includes("h2co3"); }}) &&
              tableNode.querySelectorAll("th").length >= 5
            );
          }});
        }}
        if (!targetTable) {{
          return null;
        }}
        const rows = Array.from(targetTable.querySelectorAll("tr")).slice(1);
        const series = {{
          pco2: [],
          ph: [],
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
          const phValue = parseNumericCell(cells[1].textContent);
          const h2co3Value = parseNumericCell(cells[2].textContent);
          const hco3Value = parseNumericCell(cells[3].textContent);
          const co3Value = parseNumericCell(cells[4].textContent);
          if (
            pco2Value === null ||
            phValue === null ||
            h2co3Value === null ||
            hco3Value === null ||
            co3Value === null
          ) {{
            continue;
          }}
          series.pco2.push(pco2Value);
          series.ph.push(phValue);
          series.h2co3.push(h2co3Value);
          series.hco3.push(hco3Value);
          series.co3.push(co3Value);
        }}
        return series.pco2.length ? series : null;
      }}

      function ensurePco2ChartMount() {{
        const existingCanvas = document.getElementById("pco2-sweep-chart");
        if (existingCanvas) {{
          return existingCanvas;
        }}
        const inlineAnchor = findInlineChartAnchor("pco2-sensitivity");
        if (inlineAnchor) {{
          return buildInlineChartMount({{
            anchor: inlineAnchor,
            canvasId: "pco2-sweep-chart",
            title: "pCO2 Sensitivity Trend",
            copy: "Higher pCO2 shifts chemistry toward bicarbonate while suppressing carbonate over-conversion, improving NaHCO3 purity control.",
            ariaLabel: "pCO2 sensitivity chart",
            canvasAria: "pCO2 sensitivity chart",
          }});
        }}
        const tables = Array.from(content.querySelectorAll("table"));
        const targetTable = tables.find(function (tableNode) {{
          const headers = Array.from(tableNode.querySelectorAll("th")).map(function (header) {{
            return String(header.textContent || "").trim().toLowerCase();
          }});
          const compactHeaders = headers.map(function (header) {{
            return header.replace(/[^a-z0-9]+/g, "");
          }});
          // Keep this fallback tolerant of MathML-rendered species labels.
          return (
            headers.includes("pco2 (atm)") &&
            headers.includes("ph") &&
            compactHeaders.some(function (header) {{ return header.includes("h2co3"); }}) &&
            tableNode.querySelectorAll("th").length >= 5
          );
        }});
        if (!(targetTable && targetTable.parentNode)) {{
          return null;
        }}
        const mount = document.createElement("div");
        mount.id = "pco2-sweep-chart-mount";
        mount.className = "inline-chart-mount pco2-sweep-chart-mount";
        mount.setAttribute("aria-label", "pCO2 sensitivity chart");
        const title = document.createElement("p");
        title.className = "inline-chart-title";
        title.textContent = "pCO2 Sensitivity Trend";
        const copy = document.createElement("p");
        copy.className = "inline-chart-copy";
        copy.textContent =
          "Higher pCO2 shifts chemistry toward bicarbonate while suppressing carbonate over-conversion, improving NaHCO3 purity control.";
        const viewport = document.createElement("div");
        viewport.className = "chart-viewport";
        const canvas = document.createElement("canvas");
        canvas.id = "pco2-sweep-chart";
        canvas.setAttribute("aria-label", "pCO2 sensitivity chart");
        viewport.appendChild(canvas);
        mount.appendChild(title);
        mount.appendChild(copy);
        mount.appendChild(viewport);
        targetTable.insertAdjacentElement("afterend", mount);
        return canvas;
      }}

      function showChartFallback(message) {{
        if (!chartFallback) {{
          return;
        }}
        chartFallback.textContent = message;
        chartFallback.classList.add("visible");
      }}

      function loadScript(source) {{
        const url = String(source || "").trim();
        return new Promise(function (resolve, reject) {{
          if (!url) {{
            reject(new Error("Chart source URL is empty."));
            return;
          }}
          const existingScript = document.querySelector(
            'script[data-chart-lib="' + url + '"]'
          );
          if (existingScript) {{
            if (window.Chart) {{
              resolve("existing");
              return;
            }}
            existingScript.addEventListener(
              "load",
              function () {{
                resolve("loaded-existing");
              }},
              {{ once: true }}
            );
            existingScript.addEventListener(
              "error",
              function () {{
                reject(new Error("Failed to load chart source: " + url));
              }},
              {{ once: true }}
            );
            return;
          }}
          const script = document.createElement("script");
          script.src = url;
          script.async = true;
          script.defer = true;
          script.setAttribute("data-chart-lib", url);
          script.onload = function () {{
            resolve(url);
          }};
          script.onerror = function () {{
            script.remove();
            reject(new Error("Failed to load chart source: " + url));
          }};
          document.head.appendChild(script);
        }});
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
        const stoichCanvas = ensureStoichChartMount();
        const uptakeCanvas = ensureUptakeLoadingChartMount();
        const anchorCanvas = ensureAnchorResidualChartMount();
        const phCanvas = document.getElementById("ph-trend-chart");
        const fractionCanvas = document.getElementById("fraction-trend-chart");
        const loadingCanvas = document.getElementById("cycle-loading-chart");
        if (!(phCanvas && fractionCanvas && loadingCanvas)) {{
          throw new Error("Cycle trend chart canvases are missing.");
        }}
        const phViewport = closestByClass(phCanvas, "chart-viewport");
        const fractionViewport = closestByClass(fractionCanvas, "chart-viewport");
        const loadingViewport = closestByClass(loadingCanvas, "chart-viewport");
        const pco2Canvas = ensurePco2ChartMount();
        const pco2Viewport = pco2Canvas ? closestByClass(pco2Canvas, "chart-viewport") : null;
        const stoichViewport = stoichCanvas ? closestByClass(stoichCanvas, "chart-viewport") : null;
        const uptakeViewport = uptakeCanvas ? closestByClass(uptakeCanvas, "chart-viewport") : null;
        const anchorViewport = anchorCanvas ? closestByClass(anchorCanvas, "chart-viewport") : null;
        if (!(phViewport && fractionViewport && loadingViewport)) {{
          throw new Error("Chart viewport containers are missing.");
        }}
        if (
          phViewport.clientWidth <= 0 ||
          phViewport.clientHeight <= 0 ||
          fractionViewport.clientWidth <= 0 ||
          fractionViewport.clientHeight <= 0 ||
          loadingViewport.clientWidth <= 0 ||
          loadingViewport.clientHeight <= 0
        ) {{
          throw new Error("Chart viewport has invalid dimensions.");
        }}
        if (pco2Canvas && pco2Viewport) {{
          if (pco2Viewport.clientWidth <= 0 || pco2Viewport.clientHeight <= 0) {{
            throw new Error("pCO2 chart viewport has invalid dimensions.");
          }}
        }}
        if (stoichCanvas && stoichViewport) {{
          if (stoichViewport.clientWidth <= 0 || stoichViewport.clientHeight <= 0) {{
            throw new Error("Stoichiometric chart viewport has invalid dimensions.");
          }}
        }}
        if (uptakeCanvas && uptakeViewport) {{
          if (uptakeViewport.clientWidth <= 0 || uptakeViewport.clientHeight <= 0) {{
            throw new Error("Uptake chart viewport has invalid dimensions.");
          }}
        }}
        if (anchorCanvas && anchorViewport) {{
          if (anchorViewport.clientWidth <= 0 || anchorViewport.clientHeight <= 0) {{
            throw new Error("Anchor residual chart viewport has invalid dimensions.");
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
        if (cycleLoadingChart) {{
          cycleLoadingChart.destroy();
          cycleLoadingChart = null;
        }}
        if (pco2Chart) {{
          pco2Chart.destroy();
          pco2Chart = null;
        }}
        if (stoichChart) {{
          stoichChart.destroy();
          stoichChart = null;
        }}
        if (uptakeLoadingChart) {{
          uptakeLoadingChart.destroy();
          uptakeLoadingChart = null;
        }}
        if (anchorResidualChart) {{
          anchorResidualChart.destroy();
          anchorResidualChart = null;
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
        function buildDualAxisOptions(primaryTitle, secondaryTitle, xTitle) {{
          return {{
            responsive: true,
            maintainAspectRatio: false,
            resizeDelay: 140,
            animation: {{ duration: 260, easing: "easeOutCubic" }},
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
                  text: xTitle || "Cycle",
                  color: "#2c4d61",
                  font: {{ family: "Space Grotesk", size: 12 }}
                }},
                ticks: {{ color: "#32556a" }},
                grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
              }},
              y: {{
                title: {{
                  display: true,
                  text: primaryTitle,
                  color: "#2c4d61",
                  font: {{ family: "Space Grotesk", size: 12 }}
                }},
                ticks: {{ color: "#32556a" }},
                grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
              }},
              y2: {{
                position: "right",
                title: {{
                  display: true,
                  text: secondaryTitle,
                  color: "#2c4d61",
                  font: {{ family: "Space Grotesk", size: 12 }}
                }},
                ticks: {{ color: "#32556a" }},
                grid: {{ drawOnChartArea: false }}
              }}
            }}
          }};
        }}
        phChart = new Chart(phCanvas.getContext("2d"), {{
          type: "line",
          data: {{
            labels: series.cycle,
            datasets: [
              {{
                label: "pH",
                data: series.ph,
                yAxisID: "y",
                borderColor: "#0daec0",
                backgroundColor: "rgba(13, 174, 192, 0.18)",
                borderWidth: 2.3,
                pointRadius: 3,
                pointHoverRadius: 4,
                tension: 0.28,
                fill: true
              }},
              {{
                label: "m_OH (mol/kg)",
                data: series.moh,
                yAxisID: "y2",
                borderColor: "#5568ff",
                backgroundColor: "rgba(85, 104, 255, 0.14)",
                borderWidth: 2.1,
                pointRadius: 2.8,
                tension: 0.2,
                fill: false
              }},
            ]
          }},
          options: buildDualAxisOptions("pH", "m_OH (mol/kg)", "Cycle")
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
        cycleLoadingChart = new Chart(loadingCanvas.getContext("2d"), {{
          data: {{
            labels: series.cycle,
            datasets: [
              {{
                type: "bar",
                label: "Delta CO2 (g)",
                data: series.delta,
                yAxisID: "y",
                borderColor: "#3fa2ff",
                backgroundColor: "rgba(63, 162, 255, 0.22)",
                borderWidth: 1.2,
              }},
              {{
                type: "line",
                label: "Cumulative CO2 (g)",
                data: series.cumulative,
                yAxisID: "y",
                borderColor: "#1eb46e",
                backgroundColor: "rgba(30, 180, 110, 0.14)",
                borderWidth: 2.2,
                pointRadius: 2.5,
                tension: 0.22,
              }},
              {{
                type: "line",
                label: "CT (mol/kg)",
                data: series.ct,
                yAxisID: "y2",
                borderColor: "#5568ff",
                backgroundColor: "rgba(85, 104, 255, 0.14)",
                borderWidth: 2.0,
                pointRadius: 2.4,
                tension: 0.22,
              }},
            ]
          }},
          options: buildDualAxisOptions("CO2 Mass (g)", "CT (mol/kg)", "Cycle")
        }});
        if (pco2Canvas && pco2Series) {{
          const pco2Options = buildDualAxisOptions("Fraction", "pH", "pCO2 (atm)");
          pco2Options.scales.y.min = 0;
          pco2Options.scales.y.max = 1;
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
                }},
                {{
                  label: "pH",
                  data: pco2Series.ph,
                  yAxisID: "y2",
                  borderColor: "#0daec0",
                  backgroundColor: "rgba(13, 174, 192, 0.16)",
                  borderWidth: 2.2,
                  tension: 0.2,
                  pointRadius: 2.8
                }}
              ]
            }},
            options: pco2Options
          }});
        }}
        if (stoichCanvas) {{
          stoichChart = new Chart(stoichCanvas.getContext("2d"), {{
            type: "bar",
            data: {{
              labels: ["Stage 1 endpoint", "Stage 2 endpoint", "Worked total"],
              datasets: [
                {{
                  label: "CO2 mass (g)",
                  data: [385.1, 770.2, 900.0],
                  borderColor: ["#3fa2ff", "#1eb46e", "#5568ff"],
                  backgroundColor: [
                    "rgba(63, 162, 255, 0.22)",
                    "rgba(30, 180, 110, 0.22)",
                    "rgba(85, 104, 255, 0.22)",
                  ],
                  borderWidth: 1.6,
                }}
              ]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              resizeDelay: 140,
              animation: {{ duration: 260, easing: "easeOutCubic" }},
              plugins: {{
                legend: {{ display: false }}
              }},
              scales: {{
                x: {{
                  ticks: {{ color: "#32556a" }},
                  grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
                }},
                y: {{
                  title: {{
                    display: true,
                    text: "CO2 Mass (g)",
                    color: "#2c4d61",
                    font: {{ family: "Space Grotesk", size: 12 }}
                  }},
                  ticks: {{ color: "#32556a" }},
                  grid: {{ color: "rgba(87, 123, 146, 0.16)" }}
                }}
              }}
            }}
          }});
        }}
        if (uptakeCanvas) {{
          uptakeLoadingChart = new Chart(uptakeCanvas.getContext("2d"), {{
            data: {{
              labels: series.cycle,
              datasets: [
                {{
                  type: "bar",
                  label: "Delta CO2 (g)",
                  data: series.delta,
                  yAxisID: "y",
                  borderColor: "#3fa2ff",
                  backgroundColor: "rgba(63, 162, 255, 0.22)",
                  borderWidth: 1.2,
                }},
                {{
                  type: "line",
                  label: "Cumulative CO2 (g)",
                  data: series.cumulative,
                  yAxisID: "y",
                  borderColor: "#1eb46e",
                  backgroundColor: "rgba(30, 180, 110, 0.14)",
                  borderWidth: 2.2,
                  pointRadius: 2.5,
                  tension: 0.22,
                }},
                {{
                  type: "line",
                  label: "CT (mol/kg)",
                  data: series.ct,
                  yAxisID: "y2",
                  borderColor: "#5568ff",
                  backgroundColor: "rgba(85, 104, 255, 0.14)",
                  borderWidth: 2.0,
                  pointRadius: 2.4,
                  tension: 0.22,
                }},
              ]
            }},
            options: buildDualAxisOptions("CO2 Mass (g)", "CT (mol/kg)")
          }});
        }}
        if (anchorCanvas) {{
          anchorResidualChart = new Chart(anchorCanvas.getContext("2d"), {{
            data: {{
              labels: [5, 9],
              datasets: [
                {{
                  type: "line",
                  label: "Baseline pH",
                  data: [9.1483, 8.7016],
                  yAxisID: "y",
                  borderColor: "#5568ff",
                  backgroundColor: "rgba(85, 104, 255, 0.14)",
                  borderWidth: 2.1,
                  pointRadius: 3,
                  tension: 0.2,
                }},
                {{
                  type: "line",
                  label: "Measured pH",
                  data: [9.74, 9.34],
                  yAxisID: "y",
                  borderColor: "#1eb46e",
                  backgroundColor: "rgba(30, 180, 110, 0.14)",
                  borderWidth: 2.1,
                  pointRadius: 3,
                  tension: 0.2,
                }},
                {{
                  type: "bar",
                  label: "Residual (pH)",
                  data: [0.5917, 0.6384],
                  yAxisID: "y2",
                  borderColor: "#0daec0",
                  backgroundColor: "rgba(13, 174, 192, 0.22)",
                  borderWidth: 1.2,
                }},
              ]
            }},
            options: buildDualAxisOptions("pH", "Residual (pH)")
          }});
        }}
        const instances = [phChart, fractionChart, cycleLoadingChart, pco2Chart, stoichChart, uptakeLoadingChart, anchorResidualChart].filter(Boolean);
        for (const chartInstance of instances) {{
          if (
            !Number.isFinite(chartInstance.width) ||
            !Number.isFinite(chartInstance.height) ||
            chartInstance.width <= 0 ||
            chartInstance.height <= 0
          ) {{
            throw new Error("Chart instances reported invalid render dimensions.");
          }}
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
        let chartLoadPromise = null;
        try {{
          chartLoadPromise = loadChartLibrary();
        }} catch (error) {{
          showChartFallback(
            "Chart rendering is disabled for stability (" +
              (error && error.message ? error.message : "unknown error") +
              "). The walkthrough table remains available."
          );
          return;
        }}
        chartLoadPromise
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
            if (cycleLoadingChart) {{
              cycleLoadingChart.destroy();
              cycleLoadingChart = null;
            }}
            if (pco2Chart) {{
              pco2Chart.destroy();
              pco2Chart = null;
            }}
            if (stoichChart) {{
              stoichChart.destroy();
              stoichChart = null;
            }}
            if (uptakeLoadingChart) {{
              uptakeLoadingChart.destroy();
              uptakeLoadingChart = null;
            }}
            if (anchorResidualChart) {{
              anchorResidualChart.destroy();
              anchorResidualChart = null;
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
          return String(node.tagName || "").toUpperCase() === "H2" && node.id && !node.hidden;
        }});
        if (majorHeadings.length) {{
          return majorHeadings;
        }}
        return headingNodes.filter(function (node) {{
          return Boolean(node.id) && !node.hidden;
        }});
      }}

      /**
       * Group each major heading and its siblings into one presentation slide.
       * This mapping keeps document order authoritative while adding slide metadata.
       * Inputs: none; reads the rendered headingNodes collection.
       * Returns: section descriptors containing ids, titles, headings, and DOM nodes.
       * Side effects: adds slide index/state attributes to walkthrough content nodes.
       * Errors: DOM failures propagate to the guarded presentation
       * initialization phase.
       */
      function createSectionBlocks() {{
        const majorHeadings = headingNodes.filter(function (node) {{
          return String(node.tagName || "").toUpperCase() === "H2" && node.id;
        }});
        return majorHeadings.map(function (heading, index) {{
          const nodes = [heading];
          let sibling = heading.nextElementSibling;
          while (sibling) {{
            if (String(sibling.tagName || "").toUpperCase() === "H2" && sibling.id) {{
              break;
            }}
            nodes.push(sibling);
            sibling = sibling.nextElementSibling;
          }}
          for (const node of nodes) {{
            node.setAttribute("data-slide-node", "true");
            node.setAttribute("data-slide-index", String(index));
          }}
          return {{
            id: heading.id,
            title: (heading.textContent || "").trim() || "Section " + (index + 1),
            heading: heading,
            nodes: nodes,
          }};
        }});
      }}

      function readStoredSectionLayout() {{
        try {{
          const rawLayout = window.localStorage
            ? window.localStorage.getItem(sectionLayoutStorageKey)
            : "";
          if (!rawLayout) {{
            return {{ order: [], hidden: {{}} }};
          }}
          const parsedLayout = JSON.parse(rawLayout);
          return {{
            order: Array.isArray(parsedLayout.order) ? parsedLayout.order : [],
            hidden:
              parsedLayout.hidden && typeof parsedLayout.hidden === "object"
                ? parsedLayout.hidden
                : {{}},
          }};
        }} catch (error) {{
          return {{ order: [], hidden: {{}} }};
        }}
      }}

      function writeStoredSectionLayout() {{
        try {{
          if (window.localStorage) {{
            window.localStorage.setItem(
              sectionLayoutStorageKey,
              JSON.stringify(sectionLayoutState)
            );
          }}
        }} catch (error) {{
          // Storage can be unavailable in locked-down browsers; the page still updates live.
        }}
      }}

      function normalizeSectionLayout() {{
        const knownIds = sectionBlocks.map(function (block) {{ return block.id; }});
        const knownSet = new Set(knownIds);
        const orderedKnownIds = [];
        for (const sectionId of sectionLayoutState.order || []) {{
          if (knownSet.has(sectionId) && orderedKnownIds.indexOf(sectionId) === -1) {{
            orderedKnownIds.push(sectionId);
          }}
        }}
        for (const sectionId of knownIds) {{
          if (orderedKnownIds.indexOf(sectionId) === -1) {{
            orderedKnownIds.push(sectionId);
          }}
        }}
        const hidden = {{}};
        for (const sectionId of knownIds) {{
          hidden[sectionId] = Boolean(sectionLayoutState.hidden[sectionId]);
        }}
        sectionLayoutState = {{ order: orderedKnownIds, hidden: hidden }};
      }}

      function sectionBlockById(sectionId) {{
        for (const block of sectionBlocks) {{
          if (block.id === sectionId) {{
            return block;
          }}
        }}
        return null;
      }}

      function applySectionLayoutToContent() {{
        for (const sectionId of sectionLayoutState.order) {{
          const block = sectionBlockById(sectionId);
          if (!block) {{
            continue;
          }}
          for (const node of block.nodes) {{
            node.hidden = Boolean(sectionLayoutState.hidden[block.id]);
            node.setAttribute(
              "data-section-hidden",
              sectionLayoutState.hidden[block.id] ? "true" : "false"
            );
            content.appendChild(node);
          }}
        }}
      }}

      function updateTocLayout() {{
        if (!tocNav) {{
          return;
        }}
        let topLevelParent = null;
        for (const sectionId of sectionLayoutState.order) {{
          const tocLink = tocNav.querySelector("a[href='#" + CSS.escape(sectionId) + "']");
          const tocItem = tocLink ? tocLink.closest("li") : null;
          if (tocItem && !topLevelParent) {{
            topLevelParent = tocItem.parentElement;
          }}
          if (tocItem) {{
            tocItem.hidden = Boolean(sectionLayoutState.hidden[sectionId]);
          }}
        }}
        if (!topLevelParent) {{
          return;
        }}
        for (const sectionId of sectionLayoutState.order) {{
          const tocLink = tocNav.querySelector("a[href='#" + CSS.escape(sectionId) + "']");
          const tocItem = tocLink ? tocLink.closest("li") : null;
          if (tocItem && tocItem.parentElement === topLevelParent) {{
            topLevelParent.appendChild(tocItem);
          }}
        }}
      }}

      function updateSectionSelector() {{
        if (!sectionSelector) {{
          return;
        }}
        sectionSelector.innerHTML = "";
        sectionHeadings.forEach(function (heading, index) {{
          const option = document.createElement("option");
          option.value = String(index);
          const labelText = (heading.textContent || "").trim() || "Section " + (index + 1);
          option.textContent = String(index + 1) + ". " + labelText;
          sectionSelector.appendChild(option);
        }});
      }}

      function refreshSectionNavigationState() {{
        sectionHeadings = collectSectionHeadings();
        updateSectionSelector();
        currentSectionIndex = Math.min(currentSectionIndex, Math.max(sectionHeadings.length - 1, 0));
        syncSectionControls();
        applyFilter();
      }}

      function renderSectionOrganizer() {{
        if (!sectionOrganizerList) {{
          return;
        }}
        sectionOrganizerList.innerHTML = "";
        sectionLayoutState.order.forEach(function (sectionId, index) {{
          const block = sectionBlockById(sectionId);
          if (!block) {{
            return;
          }}
          const item = document.createElement("div");
          item.className = "section-organizer-item";
          item.classList.toggle("is-hidden", Boolean(sectionLayoutState.hidden[sectionId]));
          const label = document.createElement("label");
          label.className = "section-organizer-toggle";
          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.checked = !sectionLayoutState.hidden[sectionId];
          checkbox.addEventListener("change", function () {{
            setSectionHidden(sectionId, !checkbox.checked);
          }});
          const labelText = document.createElement("span");
          labelText.textContent = block.title;
          label.appendChild(checkbox);
          label.appendChild(labelText);
          const actions = document.createElement("div");
          actions.className = "section-organizer-actions";
          const upButton = document.createElement("button");
          upButton.type = "button";
          upButton.textContent = "Up";
          upButton.disabled = index === 0;
          upButton.addEventListener("click", function () {{ moveSection(sectionId, -1); }});
          const downButton = document.createElement("button");
          downButton.type = "button";
          downButton.textContent = "Down";
          downButton.disabled = index === sectionLayoutState.order.length - 1;
          downButton.addEventListener("click", function () {{ moveSection(sectionId, 1); }});
          actions.appendChild(upButton);
          actions.appendChild(downButton);
          item.appendChild(label);
          item.appendChild(actions);
          sectionOrganizerList.appendChild(item);
        }});
      }}

      function setSectionHidden(sectionId, hidden) {{
        sectionLayoutState.hidden[sectionId] = Boolean(hidden);
        applySectionLayoutToContent();
        updateTocLayout();
        refreshSectionNavigationState();
        renderSectionOrganizer();
        updateTileRevealControls();
        writeStoredSectionLayout();
      }}

      function moveSection(sectionId, direction) {{
        const currentIndex = sectionLayoutState.order.indexOf(sectionId);
        const targetIndex = currentIndex + direction;
        if (currentIndex < 0 || targetIndex < 0 || targetIndex >= sectionLayoutState.order.length) {{
          return;
        }}
        const movedSection = sectionLayoutState.order.splice(currentIndex, 1)[0];
        sectionLayoutState.order.splice(targetIndex, 0, movedSection);
        applySectionLayoutToContent();
        updateTocLayout();
        refreshSectionNavigationState();
        renderSectionOrganizer();
        updateTileRevealControls();
        writeStoredSectionLayout();
      }}

      function resetSectionLayout() {{
        sectionLayoutState = {{
          order: sectionBlocks.map(function (block) {{ return block.id; }}),
          hidden: {{}},
        }};
        normalizeSectionLayout();
        applySectionLayoutToContent();
        updateTocLayout();
        refreshSectionNavigationState();
        renderSectionOrganizer();
        updateTileRevealControls();
        try {{
          if (window.localStorage) {{
            window.localStorage.removeItem(sectionLayoutStorageKey);
          }}
        }} catch (error) {{
          // The in-page reset is complete even if persisted storage cannot be cleared.
        }}
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

      /**
       * Select one bounded walkthrough section as the current slide.
       * Centralizing selection keeps controls, TOC state, and slide visibility aligned.
       * Inputs: index, a numeric or numeric-like zero-based section index.
       * Returns: the bounded zero-based index selected for presentation.
       * Side effects: updates navigation state, slide attributes, and control values.
       * Errors: invalid numeric inputs safely resolve to the first available section.
       */
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
        syncPresentationSlide();
        syncSectionControls();
        return boundedIndex;
      }}

      /**
       * Apply active-slide attributes and update the visible widescreen counter.
       * The attributes let CSS show one major section without changing document mode.
       * Inputs: none; reads currentSectionIndex, sectionHeadings, and sectionBlocks.
       * Returns: undefined.
       * Side effects: mutates DOM attributes, counter text, presentation scroll
       * state, and tile-reveal control availability.
       * Errors: missing optional counter/content state is handled without throwing.
       */
      function syncPresentationSlide() {{
        sectionBlocks.forEach(function (block) {{
          const isActive = block.heading === sectionHeadings[currentSectionIndex];
          for (const node of block.nodes) {{
            node.setAttribute("data-slide-active", isActive ? "true" : "false");
          }}
        }});
        if (slideFormat) {{
          const slideNumber = sectionHeadings.length ? currentSectionIndex + 1 : 0;
          slideFormat.textContent =
            "16:9 Widescreen · " + slideNumber + " / " + sectionHeadings.length;
        }}
        if (document.body.classList.contains("presentation-mode")) {{
          content.scrollTop = 0;
        }}
        // Slide visibility changed, so refresh reveal availability for the active slide.
        updateTileRevealControls();
      }}

      /**
       * Navigate to a section using slide replacement or document scrolling as needed.
       * This preserves one control path for both widescreen and normal reading modes.
       * Inputs: index (zero-based section index) and smoothScroll (boolean preference).
       * Returns: undefined.
       * Side effects: changes the current slide and may scroll the shell or document.
       * Errors: missing sections or headings cause a safe no-op.
       */
      function navigateToSection(index, smoothScroll) {{
        if (!sectionHeadings.length) {{
          return;
        }}
        const boundedIndex = setCurrentSectionIndex(index);
        const targetHeading = sectionHeadings[boundedIndex];
        if (!targetHeading) {{
          return;
        }}
        if (document.body.classList.contains("presentation-mode")) {{
          content.scrollTop = 0;
          if (presentationShell && supportsScrollIntoView) {{
            presentationShell.scrollIntoView({{ behavior: "auto", block: "start" }});
          }}
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

      /**
       * Enable or disable the section-based 16:9 presentation surface.
       * The mode exists so the browser walkthrough aligns with a PowerPoint deck.
       * Inputs: enabled, a value normalized to boolean presentation state.
       * Returns: undefined.
       * Side effects: updates body state, toggle copy, active slide, and shell scroll.
       * Errors: absent optional controls or shell elements are handled as no-ops.
       */
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
        syncPresentationSlide();
        if (isEnabled && presentationShell && supportsScrollIntoView) {{
          presentationShell.scrollIntoView({{ behavior: "auto", block: "start" }});
        }}
      }}

      function setSecondaryControlsVisible(visible) {{
        const isVisible = Boolean(visible);
        if (secondaryControlsPanel) {{
          secondaryControlsPanel.hidden = !isVisible;
        }}
        if (controlsMoreButton) {{
          controlsMoreButton.setAttribute("aria-expanded", String(isVisible));
          controlsMoreButton.textContent = isVisible ? "Hide Controls" : "More Controls";
        }}
      }}

      function initializeSectionNavigation() {{
        sectionBlocks = createSectionBlocks();
        sectionLayoutState = readStoredSectionLayout();
        normalizeSectionLayout();
        applySectionLayoutToContent();
        updateTocLayout();
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
          updateSectionSelector();
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
                "1-basis-setup-700-g-naoh-in-2200-ml-water"
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
        if (realDataJump) {{
          realDataJump.addEventListener("click", function () {{
            const realDataIndex = resolveSectionIndexById(
              "10-worked-real-world-example-pr-24304-sodium-bicarbonate-batch-1"
            );
            navigateToSection(realDataIndex === null ? currentSectionIndex : realDataIndex, true);
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
        renderSectionOrganizer();
        setCurrentSectionIndex(0);
      }}

      function initializePresentationControls() {{
        if (controlsMoreButton) {{
          controlsMoreButton.addEventListener("click", function () {{
            const currentlyExpanded =
              controlsMoreButton.getAttribute("aria-expanded") === "true";
            setSecondaryControlsVisible(!currentlyExpanded);
          }});
        }}
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
        if (sectionOrganizerToggle) {{
          sectionOrganizerToggle.addEventListener("click", function () {{
            const isExpanded = sectionOrganizerToggle.getAttribute("aria-expanded") === "true";
            sectionOrganizerToggle.setAttribute("aria-expanded", String(!isExpanded));
            if (sectionOrganizerPanel) {{
              sectionOrganizerPanel.hidden = isExpanded;
            }}
          }});
        }}
        if (sectionLayoutReset) {{
          sectionLayoutReset.addEventListener("click", resetSectionLayout);
        }}
        if (tileRevealToggle) {{
          tileRevealToggle.addEventListener("click", function () {{
            const enableTileReveal = tileRevealToggle.getAttribute("aria-pressed") !== "true";
            setTileRevealEnabled(enableTileReveal);
          }});
        }}
        if (tileRevealNext) {{
          tileRevealNext.addEventListener("click", revealNextVisibleTileFragment);
        }}
        if (tileRevealReset) {{
          tileRevealReset.addEventListener("click", resetTileRevealFragments);
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
            setTileRevealEnabled(false);
            resetTileRevealFragments();
            resetSectionLayout();
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
        setSecondaryControlsVisible(false);
      }}

      function initializePresentationPhase() {{
        initializeSectionNavigation();
        initializePresentationControls();
      }}

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
