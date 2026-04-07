#!/usr/bin/env python3
"""Build a plain-text export of the psychohistory site for chatbot consumption."""

import re, html, os

SITE_DIR = os.path.dirname(os.path.abspath(__file__))

SECTIONS = [
    ("index", "HOME — WHAT IS THIS"),
    ("framework", "FRAMEWORK — HOW THE ENGINE WORKS"),
    ("predictions", "PREDICTIONS — 14-YEAR TRAJECTORY (2027-2040)"),
    ("players", "PLAYERS — THE PEOPLE AND INSTITUTIONS"),
    ("scorecard", "SCORECARD — IS THE ENGINE RIGHT?"),
    ("divergences", "DIVERGENCES — WHERE THE ENGINE MIGHT BE WRONG"),
    ("live", "LIVE FEED — CURRENT EVENTS SCORED"),
    ("graph", "KNOWLEDGE GRAPH — NODE CONNECTIONS"),
]

def extract_text(filepath):
    """Extract readable text from Next.js RSC/HTML payload."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    text = html.unescape(content)

    # Remove RSC wire format headers
    text = re.sub(r'^\d+:[A-Z]\[.*?\]$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+:\[.*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+:T[0-9a-f]+,', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+:null$', '', text, flags=re.MULTILINE)

    # Remove script/style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

    # Convert HTML structure to text
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</(?:p|div|h[1-6]|li|tr|section|header|footer|article)>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)

    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [l.strip() for l in text.split('\n')]
    text = '\n'.join(l for l in lines if l)

    return text

def build_export():
    header = """PSYCHOHISTORY PREDICTION ENGINE — FULL PLAIN TEXT EXPORT
========================================================
Site: https://moketchups.com
8 independent analytical frameworks. 740+ nodes. 14-year trajectory (2026-2040).

This is a machine-readable plain text export of the full site content.
Each section below corresponds to a page on the site.

"""

    parts = [header]

    for filename, title in SECTIONS:
        # Try .txt first (RSC payload with embedded content), fall back to .html
        txt_path = os.path.join(SITE_DIR, f"{filename}.txt")
        html_path = os.path.join(SITE_DIR, f"{filename}.html")

        filepath = txt_path if os.path.exists(txt_path) else html_path
        if not os.path.exists(filepath):
            continue

        text = extract_text(filepath)
        if len(text.strip()) < 100:
            # RSC payload might be too minimal, try HTML version
            if os.path.exists(html_path) and filepath != html_path:
                text = extract_text(html_path)

        separator = "=" * len(title)
        parts.append(f"\n\n{'=' * 72}\n{title}\n{'=' * 72}\n\n{text}\n")

    output = '\n'.join(parts)

    outpath = os.path.join(SITE_DIR, "export.txt")
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(output)

    size_kb = os.path.getsize(outpath) / 1024
    print(f"Written: {outpath}")
    print(f"Size: {size_kb:.0f} KB")
    print(f"Sections: {len(SECTIONS)}")

if __name__ == "__main__":
    build_export()
