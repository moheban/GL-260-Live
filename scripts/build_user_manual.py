#!/usr/bin/env python3
# ruff: noqa: E501
"""Build and validate the repository user-manual HTML artifact.

Purpose:
    Convert ``docs/user-manual.md`` into a styled, searchable, single-page HTML manual.
Why:
    The repository keeps Markdown as the editable source-of-truth while publishing
    ``docs/user-manual.html`` for browser-friendly consumption.
Inputs:
    Command-line flags controlling write/check behavior.
Outputs:
    Writes or validates ``docs/user-manual.html``.
Side Effects:
    Reads from and writes to files in the repository ``docs/`` subtree.
Exceptions:
    Exits non-zero on validation/build failures and reports actionable messages.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import markdown

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MANUAL_MD_PATH = REPO_ROOT / "docs" / "user-manual.md"
MANUAL_HTML_PATH = REPO_ROOT / "docs" / "user-manual.html"
INLINE_MATH_SENTINELS = (
    (r"\(", "GL260INLINEMATHOPENPARENZXCV"),
    (r"\)", "GL260INLINEMATHCLOSEPARENZXCV"),
    (r"\[", "GL260INLINEMATHOPENBRACKETZXCV"),
    (r"\]", "GL260INLINEMATHCLOSEBRACKETZXCV"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for manual build/check flows.

    Purpose:
        Define and parse command-line behavior for this build utility.
    Why:
        Build and CI workflows need explicit modes for generation and validation.
    Args:
        argv: Optional explicit argument vector for tests; defaults to sys.argv.
    Returns:
        Parsed namespace with flags controlling check/write behavior.
    Side Effects:
        None.
    Exceptions:
        argparse exits with status code 2 on invalid arguments.
    """

    parser = argparse.ArgumentParser(
        description="Build or validate docs/user-manual.html from docs/user-manual.md."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if docs/user-manual.html is missing or out of date.",
    )
    return parser.parse_args(argv)


def read_utf8(path: Path) -> str:
    """Read one UTF-8 text file with deterministic error reporting.

    Purpose:
        Centralize file reads used by the manual build and check workflow.
    Why:
        Shared read behavior keeps failures consistent and easier to diagnose.
    Args:
        path: Absolute file path to read.
    Returns:
        The decoded UTF-8 file content.
    Side Effects:
        Accesses filesystem content at ``path``.
    Exceptions:
        Propagates ``OSError`` for missing/unreadable files and ``UnicodeError``
        for invalid UTF-8 payloads.
    """

    return path.read_text(encoding="utf-8")


def write_utf8(path: Path, content: str) -> None:
    """Write one UTF-8 text file, creating parent folders as needed.

    Purpose:
        Emit generated HTML payloads deterministically.
    Why:
        Build workflows should not require pre-created docs folders.
    Args:
        path: Output file path to write.
        content: Text payload to persist.
    Returns:
        None.
    Side Effects:
        Creates parent directories and writes output bytes to disk.
    Exceptions:
        Propagates ``OSError`` on filesystem write failures.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def source_sha256(text: str) -> str:
    """Compute the SHA-256 hash for source tracking metadata.

    Purpose:
        Stamp generated HTML with a deterministic fingerprint of the source Markdown.
    Why:
        Hash metadata helps maintainers verify generated output provenance.
    Args:
        text: Source Markdown payload.
    Returns:
        Hexadecimal SHA-256 digest string.
    Side Effects:
        None.
    Exceptions:
        None under normal usage.
    """

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _protect_inline_math_delimiters(markdown_text: str) -> str:
    """Protect inline LaTeX delimiters before Markdown conversion.

    Purpose:
        Preserve escaped LaTeX delimiters that Python-Markdown would otherwise
        treat as generic escapes.
    Why:
        Manual content uses `\\(...\\)` and `\\[...\\]` notation that must
        survive into HTML for MathJax runtime rendering.
    Args:
        markdown_text: Source Markdown payload.
    Returns:
        Markdown text with deterministic temporary sentinel substitutions.
    Side Effects:
        None.
    Exceptions:
        None under normal usage.
    """

    protected_text = markdown_text
    # Replace only delimiter tokens so equation content remains unchanged.
    for source, sentinel in INLINE_MATH_SENTINELS:
        protected_text = protected_text.replace(source, sentinel)
    return protected_text


def _restore_inline_math_delimiters(rendered_text: str) -> str:
    """Restore protected inline LaTeX delimiters after Markdown conversion.

    Purpose:
        Convert temporary sentinel tokens back to canonical LaTeX delimiters.
    Why:
        The HTML output needs real math delimiters for MathJax parsing.
    Args:
        rendered_text: Converted HTML fragment containing sentinel substitutions.
    Returns:
        HTML fragment with restored `\\(...\\)` and `\\[...\\]` delimiters.
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
    """Render Markdown content and table-of-contents HTML.

    Purpose:
        Convert source manual Markdown into semantic HTML content.
    Why:
        The project maintains authoring ergonomics in Markdown while publishing HTML.
    Args:
        markdown_text: Manual source markdown text.
    Returns:
        Tuple of ``(body_html, toc_html)``.
    Side Effects:
        None.
    Exceptions:
        Propagates exceptions raised by the markdown renderer.
    """

    protected_markdown = _protect_inline_math_delimiters(markdown_text)
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
        extension_configs={"toc": {"permalink": True, "toc_depth": "2-4"}},
        output_format="html5",
    )
    body_html = _restore_inline_math_delimiters(md.convert(protected_markdown))
    toc_html = _restore_inline_math_delimiters(
        md.toc or "<ul><li>No headings detected</li></ul>"
    )
    return body_html, toc_html


def build_html_document(*, body_html: str, toc_html: str, source_hash: str) -> str:
    """Wrap rendered manual content in a shared interactive HTML shell.

    Purpose:
        Apply repository-standard styling and client-side behavior to manual content.
    Why:
        A single-page wiki needs sticky navigation, search filtering, and image
        lightbox interactions for usable long-form reading.
    Args:
        body_html: Rendered manual body HTML.
        toc_html: Rendered table-of-contents markup.
        source_hash: SHA-256 fingerprint of the Markdown source.
    Returns:
        Full HTML document string.
    Side Effects:
        None.
    Exceptions:
        None under normal usage.
    """

    # Preserve a deterministic shell so --check compares stable byte output.
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="manual-source-sha256" content="{source_hash}">
  <title>GL-260 User Manual</title>
  <style>
    :root {{
      --bg: #f5f7f8;
      --card: #ffffff;
      --ink: #0f1f28;
      --muted: #4c6672;
      --edge: #ccdae0;
      --accent: #0f6f82;
      --accent-soft: #e5f1f4;
      --shadow: rgba(20, 44, 56, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; }}
    body {{
      font-family: "Segoe UI", Tahoma, Verdana, sans-serif;
      background: linear-gradient(180deg, #eaf0f3 0%, var(--bg) 100%);
      color: var(--ink);
      line-height: 1.6;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      gap: 16px;
      align-items: start;
      width: min(1800px, calc(100vw - 24px));
      margin: 12px auto;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--edge);
      border-radius: 14px;
      box-shadow: 0 10px 24px var(--shadow);
    }}
    .sidebar {{
      position: sticky;
      top: 12px;
      max-height: calc(100vh - 24px);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .side-head {{
      padding: 14px 16px 10px;
      border-bottom: 1px solid var(--edge);
      background: linear-gradient(180deg, #f8fcfd 0%, #f3f9fb 100%);
      border-radius: 14px 14px 0 0;
    }}
    .side-head h1 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.3;
    }}
    .side-head .meta {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
    }}
    .side-tools {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--edge);
      background: #fcfeff;
    }}
    .side-tools label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .side-tools input {{
      width: 100%;
      border: 1px solid var(--edge);
      border-radius: 10px;
      padding: 9px 10px;
      font-size: 13px;
    }}
    nav.toc {{
      overflow: auto;
      padding: 10px 12px 14px;
      font-size: 13px;
    }}
    nav.toc ul {{ list-style: none; margin: 0; padding-left: 0; }}
    nav.toc ul ul {{ padding-left: 14px; border-left: 1px dashed var(--edge); margin-left: 6px; }}
    nav.toc li {{ margin: 5px 0; }}
    nav.toc a {{
      text-decoration: none;
      color: var(--ink);
      border-radius: 8px;
      display: inline-block;
      padding: 2px 6px;
    }}
    nav.toc a:hover {{
      background: var(--accent-soft);
      color: #0b4f5d;
    }}
    .content {{
      min-width: 0;
      padding: 20px 28px 28px;
    }}
    .content h1, .content h2, .content h3, .content h4 {{
      line-height: 1.25;
      scroll-margin-top: 16px;
    }}
    .content h2 {{
      margin-top: 30px;
      border-top: 1px solid var(--edge);
      padding-top: 20px;
    }}
    .content h2:first-of-type {{
      margin-top: 0;
      border-top: none;
      padding-top: 0;
    }}
    .content p, .content li {{
      max-width: 95ch;
    }}
    .content code {{
      background: #edf2f5;
      border: 1px solid #dde6eb;
      border-radius: 6px;
      padding: 1px 5px;
      font-size: 0.92em;
    }}
    .content pre {{
      background: #0f202a;
      color: #e4eef2;
      border-radius: 10px;
      padding: 14px 16px;
      overflow: auto;
      border: 1px solid #102a37;
      max-width: min(120ch, 100%);
    }}
    .content pre code {{
      background: transparent;
      border: none;
      color: inherit;
      padding: 0;
    }}
    .content .math-display-block {{
      border: 1px solid var(--edge);
      border-radius: 10px;
      background: #fbfdfe;
      padding: 12px 14px;
      margin: 10px 0;
      overflow-x: auto;
      max-width: min(120ch, 100%);
    }}
    .content pre.latex-fallback {{
      margin-top: 8px;
    }}
    .content pre.latex-fallback.math-fallback-hidden {{
      display: none;
    }}
    .content table {{
      border-collapse: collapse;
      width: min(120ch, 100%);
      margin: 8px 0 16px;
      font-size: 14px;
    }}
    .content th, .content td {{
      border: 1px solid var(--edge);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }}
    .content th {{
      background: #f2f8fa;
    }}
    figure {{
      margin: 14px 0 18px;
      width: min(120ch, 100%);
    }}
    figure img {{
      max-width: 100%;
      border: 1px solid var(--edge);
      border-radius: 10px;
      box-shadow: 0 6px 18px rgba(22, 51, 64, 0.12);
      cursor: zoom-in;
      background: #f9fcfd;
    }}
    figure figcaption {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    details {{
      width: min(120ch, 100%);
      border: 1px solid var(--edge);
      border-radius: 10px;
      background: #fbfefe;
      padding: 8px 12px;
      margin: 10px 0 14px;
    }}
    details summary {{
      cursor: pointer;
      font-weight: 600;
      color: #163945;
    }}
    #image-lightbox {{
      position: fixed;
      inset: 0;
      background: rgba(8, 18, 24, 0.85);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 14px;
      z-index: 1000;
    }}
    #image-lightbox.open {{
      display: flex;
    }}
    #image-lightbox img {{
      max-width: min(96vw, 1800px);
      max-height: 90vh;
      border-radius: 10px;
      border: 1px solid #8aa4af;
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4);
      background: #fff;
    }}
    #image-lightbox button {{
      position: absolute;
      top: 16px;
      right: 16px;
      border: 1px solid #7c97a3;
      border-radius: 999px;
      width: 36px;
      height: 36px;
      background: rgba(255, 255, 255, 0.95);
      color: #143542;
      font-size: 18px;
      cursor: pointer;
    }}
    @media (max-width: 1160px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      .sidebar {{
        position: static;
        max-height: none;
      }}
      nav.toc {{
        max-height: 320px;
      }}
      .content {{
        padding: 16px 16px 22px;
      }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar card" aria-label="Manual navigation">
      <div class="side-head">
        <h1>GL-260 User Manual</h1>
        <div class="meta">Canonical HTML built from <code>docs/user-manual.md</code><br>Source SHA-256: <code>{source_hash[:16]}</code></div>
      </div>
      <div class="side-tools">
        <label for="toc-filter">Filter sections</label>
        <input id="toc-filter" type="text" placeholder="Type to find workflows..." />
      </div>
      <nav class="toc" id="toc-nav">
        {toc_html}
      </nav>
    </aside>
    <main class="content card" id="manual-content">
      {body_html}
    </main>
  </div>
  <div id="image-lightbox" role="dialog" aria-modal="true" aria-label="Screenshot viewer">
    <button id="lightbox-close" type="button" aria-label="Close image preview">x</button>
    <img id="lightbox-image" alt="">
  </div>
  <script>
    (function () {{
      const filterInput = document.getElementById("toc-filter");
      const tocNav = document.getElementById("toc-nav");
      const manualContent = document.getElementById("manual-content");
      const tocLinks = Array.from(tocNav.querySelectorAll("a[href^='#']"));
      const headingMap = new Map();
      const headingNodes = Array.from(document.querySelectorAll("#manual-content h2, #manual-content h3, #manual-content h4"));
      for (const heading of headingNodes) {{
        if (heading.id) {{
          headingMap.set("#" + heading.id, heading);
        }}
      }}

      function applyFilter() {{
        const needle = String((filterInput?.value || "")).trim().toLowerCase();
        for (const link of tocLinks) {{
          const linkText = (link.textContent || "").toLowerCase();
          const heading = headingMap.get(link.getAttribute("href"));
          const headingText = heading ? (heading.textContent || "").toLowerCase() : "";
          const show = !needle || linkText.includes(needle) || headingText.includes(needle);
          const row = link.closest("li");
          if (row) {{
            row.style.display = show ? "" : "none";
          }}
        }}
      }}

      if (filterInput) {{
        filterInput.addEventListener("input", applyFilter);
      }}
      applyFilter();

      function prepareLatexDisplayBlocks() {{
        if (!manualContent) {{
          return [];
        }}
        const latexCodeNodes = Array.from(
          manualContent.querySelectorAll("pre > code.language-latex")
        );
        const prepared = [];
        for (const codeNode of latexCodeNodes) {{
          const preNode = codeNode.closest("pre");
          if (!preNode || !preNode.parentNode) {{
            continue;
          }}
          const latexRaw = String(codeNode.textContent || "").trim();
          if (!latexRaw) {{
            continue;
          }}
          const displayNode = document.createElement("div");
          displayNode.className = "math-display-block";
          displayNode.textContent = `\\\\[\\n${{latexRaw}}\\n\\\\]`;
          preNode.parentNode.insertBefore(displayNode, preNode);
          preNode.classList.add("latex-fallback");
          prepared.push({{ displayNode, fallbackNode: preNode }});
        }}
        return prepared;
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
        const localMathJax = "mathjax/es5/tex-mml-chtml.js";
        const cdnMathJax = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js";
        return loadScript(localMathJax).catch(function () {{
          return loadScript(cdnMathJax);
        }});
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
            const displayNodes = prepared.map(function (entry) {{
              return entry.displayNode;
            }});
            return window.MathJax.typesetPromise(displayNodes).then(function () {{
              for (const entry of prepared) {{
                entry.fallbackNode.classList.add("math-fallback-hidden");
              }}
            }});
          }})
          .catch(function () {{
            // Keep raw LaTeX fallbacks visible when MathJax is unavailable.
            for (const entry of prepared) {{
              if (entry.displayNode && entry.displayNode.parentNode) {{
                entry.displayNode.parentNode.removeChild(entry.displayNode);
              }}
            }}
          }});
      }}
      initializeMathRendering();

      const lightbox = document.getElementById("image-lightbox");
      const lightboxImage = document.getElementById("lightbox-image");
      const closeButton = document.getElementById("lightbox-close");
      const contentImages = Array.from(document.querySelectorAll("#manual-content img"));

      function closeLightbox() {{
        lightbox.classList.remove("open");
        lightboxImage.removeAttribute("src");
        lightboxImage.removeAttribute("alt");
      }}

      for (const img of contentImages) {{
        img.addEventListener("click", function () {{
          const src = img.getAttribute("src");
          if (!src) {{
            return;
          }}
          lightboxImage.setAttribute("src", src);
          lightboxImage.setAttribute("alt", img.getAttribute("alt") || "Manual image preview");
          lightbox.classList.add("open");
        }});
      }}

      if (closeButton) {{
        closeButton.addEventListener("click", closeLightbox);
      }}
      lightbox.addEventListener("click", function (event) {{
        if (event.target === lightbox) {{
          closeLightbox();
        }}
      }});
      document.addEventListener("keydown", function (event) {{
        if (event.key === "Escape" && lightbox.classList.contains("open")) {{
          closeLightbox();
        }}
      }});
    }})();
  </script>
</body>
</html>
"""


def build_expected_html(markdown_path: Path) -> str:
    """Build the deterministic HTML payload expected from one Markdown source.

    Purpose:
        Encapsulate Markdown-to-HTML conversion for write/check modes.
    Why:
        Shared logic guarantees parity between generation and validation paths.
    Args:
        markdown_path: Source Markdown path.
    Returns:
        Complete generated HTML string.
    Side Effects:
        Reads source Markdown from disk.
    Exceptions:
        Propagates markdown and filesystem exceptions for caller handling.
    """

    markdown_text = read_utf8(markdown_path)
    body_html, toc_html = render_markdown(markdown_text)
    return build_html_document(
        body_html=body_html,
        toc_html=toc_html,
        source_hash=source_sha256(markdown_text),
    )


def run() -> int:
    """Execute build/check behavior and return a process exit code.

    Purpose:
        Provide a single orchestration entry point for CLI execution.
    Why:
        The script supports two deterministic modes: write and strict freshness check.
    Args:
        None.
    Returns:
        Process exit code (`0` success, `1` failure).
    Side Effects:
        May write generated HTML or emit terminal diagnostics.
    Exceptions:
        Exceptions are caught and converted into user-facing error messages.
    """

    args = parse_args()
    try:
        expected_html = build_expected_html(MANUAL_MD_PATH)
    except Exception as exc:  # pragma: no cover - explicit CLI safety path
        print(f"[manual-build] Failed to build expected HTML: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if not MANUAL_HTML_PATH.exists():
            print(
                "[manual-build] Check failed: docs/user-manual.html is missing. "
                "Run `python scripts/build_user_manual.py`.",
                file=sys.stderr,
            )
            return 1
        try:
            current_html = read_utf8(MANUAL_HTML_PATH)
        except Exception as exc:  # pragma: no cover - explicit CLI safety path
            print(
                f"[manual-build] Check failed while reading HTML: {exc}",
                file=sys.stderr,
            )
            return 1
        if current_html != expected_html:
            print(
                "[manual-build] Check failed: docs/user-manual.html is out of date. "
                "Run `python scripts/build_user_manual.py`.",
                file=sys.stderr,
            )
            return 1
        print("[manual-build] Check passed: docs/user-manual.html is up to date.")
        return 0

    try:
        write_utf8(MANUAL_HTML_PATH, expected_html)
    except Exception as exc:  # pragma: no cover - explicit CLI safety path
        print(f"[manual-build] Failed to write HTML: {exc}", file=sys.stderr)
        return 1

    print("[manual-build] Generated docs/user-manual.html")
    return 0


if __name__ == "__main__":
    sys.exit(run())
