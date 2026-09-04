#!/usr/bin/env python3
"""Render the production reference markdown into print-ready HTML and PDF.

Sources live in src/_data/refs/production/*.md; output goes to to_print/production/.
Markdown is converted with the markdown-it bundled in node_modules; the PDF is
printed with Playwright's Chromium.

Usage:
    python scripts/reference_generators/generate_production_docs.py
    python scripts/reference_generators/generate_production_docs.py ghost_lonely
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src/_data/refs/production"
OUT = ROOT / "to_print/production"

BASE_CSS = """@page { size: letter; margin: 0.45in; }
body { font-family: Georgia, "Times New Roman", serif; font-size: 9.5pt;
       line-height: 1.28; color: #1a1a1a; margin: 0; }
h1 { font-size: 14pt; color: #4a148c; letter-spacing: 0.5px;
     border-bottom: 1.5px solid #4a148c; padding-bottom: 3px; margin: 0 0 8px; }
h2 { font-size: 11.5pt; color: #4a148c; margin: 11px 0 3px;
     page-break-after: avoid; break-after: avoid; }
h3 { font-size: 10pt; margin: 8px 0 2px;
     page-break-after: avoid; break-after: avoid; }
.blk { page-break-inside: avoid; break-inside: avoid; }
p { margin: 3px 0; }
strong { color: #3a1060; }
em { color: #444; }
blockquote { margin: 4px 0 4px 2px; padding: 1px 0 1px 10px;
             border-left: 2px solid #c3aee0; }
blockquote p { margin: 2px 0; }
ul { margin: 3px 0; padding-left: 17px; }
li { margin: 1px 0; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 5px 0; }
th, td { border: 1px solid #b9b9b9; padding: 2px 6px; text-align: left;
         vertical-align: top; }
th { background: #f2ecda; }
pre { font-family: Menlo, Consolas, "DejaVu Sans Mono", monospace; font-size: 7.5pt;
      line-height: 1.1; white-space: pre; page-break-inside: avoid; margin: 4px 0; }
code { font-family: inherit; }
hr { border: 0; border-top: 1px solid #e2e2e2; margin: 8px 0; }
a { color: inherit; text-decoration: none; }"""

# Per-document tweaks, appended after the base sheet.
GHOST_CSS = (
    'body { font-size: 8.4pt; line-height: 1.18; } '
    'h1 { font-size: 12.5pt; margin-bottom: 3px; padding-bottom: 2px; } '
    'h2 { background: #f2ecda; padding: 2px 5px; font-size: 9pt; margin: 6px 0 2px; } '
    'table { font-size: 8pt; margin: 2px 0; } th, td { padding: 1px 5px; } '
    'ul { margin: 2px 0; padding-left: 13px; } li { margin: 0; } p { margin: 2px 0; } '
    'blockquote { margin: 2px 0 2px 2px; padding-left: 8px; } '
    'blockquote p { margin: 1px 0; }'
)

EXTRA_CSS = {
    "quick_sheet": "body { font-size: 10.5pt; } table { font-size: 10pt; } th, td { padding: 3px 7px; }",
    "floor_plan": "pre { font-size: 7pt; } table { font-size: 8.5pt; } th, td { padding: 2px 4px; }",
    "role_briefs": "h2 { background: #f2ecda; padding: 3px 6px; margin-top: 12px; }",
    "run_of_show": (
        "h1 { font-size: 12pt; border: 0; background: #f2ecda; padding: 3px 6px; "
        "margin: 10px 0 4px; } h1:first-of-type { font-size: 14pt; background: none; "
        "padding: 0 0 3px; border-bottom: 1.5px solid #4a148c; }"
    ),
    "prop_sheet": (
        "body { column-count: 2; column-gap: 0.3in; font-size: 8pt; line-height: 1.22; } "
        "h1 { column-span: all; font-size: 13pt; margin-bottom: 5px; } "
        "h2 { background: #f2ecda; padding: 2px 5px; font-size: 9.5pt; margin: 7px 0 3px; } "
        "h3 { margin-top: 5px; font-size: 8.5pt; } ul { padding-left: 14px; } "
        "li { margin: 0; } p { margin: 1px 0; }"
    ),
    "ghost_lonely": GHOST_CSS,
    "ghost_heartbroken": GHOST_CSS,
    "ghost_alchemist": GHOST_CSS,
}

TITLES = {
    "ghost_lonely": "The Lonely Ghost — Lost Souls",
    "ghost_heartbroken": "The Heartbroken Ghost — Lost Souls",
    "ghost_alchemist": "The Alchemist — Lost Souls",
}

RENDER_JS = r"""
const MarkdownIt = require(process.argv[1]);
const fs = require('fs');
const md = new MarkdownIt({ html: true, typographer: false });
process.stdout.write(md.render(fs.readFileSync(process.argv[2], 'utf8')));
"""


def render_markdown(md_path):
    js = ROOT / "node_modules/markdown-it"
    result = subprocess.run(
        ["node", "-e", RENDER_JS, "--", str(js), str(md_path)],
        capture_output=True, text=True, check=True, cwd=ROOT,
    )
    return result.stdout


def title_for(stem, html):
    if stem in TITLES:
        return TITLES[stem]
    heading = html.split("<h1>", 1)
    if len(heading) > 1:
        return heading[1].split("</h1>", 1)[0] + " — Lost Souls"
    return stem.replace("_", " ").title() + " — Lost Souls"


def build(stem):
    md_path = SRC / f"{stem}.md"
    if not md_path.exists():
        sys.exit(f"No such document: {md_path}")
    body = render_markdown(md_path)
    css = BASE_CSS
    if stem in EXTRA_CSS:
        css += "\n" + EXTRA_CSS[stem]
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        f"<title>{title_for(stem, body)}</title>\n<style>\n{css}\n</style>\n"
        f"</head>\n<body>\n{body}</body>\n</html>\n"
    )
    html_path = OUT / f"{stem}.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path


def to_pdf(html_paths):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for html_path in html_paths:
            page.goto(html_path.as_uri())
            page.emulate_media(media="print")
            pdf_path = html_path.with_suffix(".pdf")
            page.pdf(path=str(pdf_path), format="Letter", print_background=True)
            print(f"  {pdf_path.relative_to(ROOT)}")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docs", nargs="*", help="document stems (default: all)")
    args = parser.parse_args()

    stems = args.docs or sorted(p.stem for p in SRC.glob("*.md"))
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Building {len(stems)} document(s):")
    to_pdf([build(stem) for stem in stems])


if __name__ == "__main__":
    main()
