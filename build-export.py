#!/usr/bin/env python3
"""Build a plain-text export + llms.txt of the psychohistory site for chatbot consumption.

Reads engine-state counts from V2 data files at build time so headers stay live.
"""

import re, html, os, json

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
V2_DATA = os.path.join(os.path.dirname(SITE_DIR), "psychohistory-v2", "data")

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


def engine_counts():
    """Read live counts from V2 data files; return dict or None on failure."""
    try:
        players = json.load(open(os.path.join(V2_DATA, 'players.json')))
        return {
            'nodes': len(json.load(open(os.path.join(V2_DATA, 'nodes.json')))),
            'edges': len(json.load(open(os.path.join(V2_DATA, 'edges.json')))),
            'scorecard': len(json.load(open(os.path.join(V2_DATA, 'scorecard.json')))),
            'divergences': len(json.load(open(os.path.join(V2_DATA, 'divergences.json')))),
            'concepts': len(json.load(open(os.path.join(V2_DATA, 'concepts.json')))),
            'players': len(players),
            'cards': sum(len(p.get('cards', [])) for p in players),
            'predictions': len(json.load(open(os.path.join(V2_DATA, 'predictions.json')))),
            'ticker': len(json.load(open(os.path.join(V2_DATA, 'ticker.json')))),
        }
    except Exception as e:
        print(f"WARNING: could not read V2 counts: {e}")
        return None


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
    counts = engine_counts() or {}
    nodes_str = f"{counts.get('nodes', '?')} nodes" if counts else "live engine"

    header = f"""PSYCHOHISTORY PREDICTION ENGINE — FULL PLAIN TEXT EXPORT
========================================================
Site: https://moketchups.com
8 independent analytical frameworks. {nodes_str}. 14-year trajectory (2026-2040).

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
    return size_kb


def build_llms(export_size_kb=None):
    """Regenerate llms.txt with live engine counts. Writes to /llms.txt + /psychohistory/llms.txt."""
    counts = engine_counts()
    if not counts:
        print("WARNING: skipping llms.txt regeneration (counts unavailable)")
        return

    if export_size_kb is None:
        try:
            export_size_kb = os.path.getsize(os.path.join(SITE_DIR, 'export.txt')) / 1024
        except OSError:
            export_size_kb = 0

    text = f"""# Psychohistory Prediction Engine
# https://moketchups.com/psychohistory/
# Author: Alan Berman (@moketchups)

## About
A structural analysis engine tracking {counts['nodes']:,} entities, {counts['edges']:,} connections, {counts['divergences']} divergences, and 14 years of predictions (2027-2040). Built on 8 independent analytical frameworks that converge on the same pressure window with zero coordination.

## Core Framework
Bounded System Theory (BST): No system can model, encompass, or become the source of its own existence. The crisis of the modern era is the mechanical result of a civilization attempting to engineer past the wall that defines it.

## Data
- Full export (~{export_size_kb:.0f}KB plain text): https://moketchups.com/export.txt
- {counts['nodes']:,} knowledge graph nodes, {counts['edges']:,} edges
- {counts['scorecard']} scorecard variables tracked against live events
- {counts['divergences']} divergences (where the engine might be wrong)
- {counts['predictions']} prediction years (2027-2040) with sub-sections
- {counts['concepts']} defined concepts
- {counts['players']} player sections, {counts['cards']:,} cards
- {counts['ticker']:,} ticker entries
- Live data pipeline updating every 6 hours

## Key Concepts
- Jiang Test: Three questions to determine if a conflict is genuine or theater
- Galam Threshold: 10-17% committed minority flips flexible majority
- Joulework: Energy-denominated finance (Bitcoin as proto-Joulework)
- Phoenix Cycle: 138-year historical cycle, next reset May 2040
- Donroe Doctrine: Terminal resource strategy (drill, hoard, fortify)
- Technate: The bounded system reaching for immortality through three converging rails
- Spectacle Governance: One-way physical-architecture ratchet locking operator-class venue function into federal property

## Endpoints
- Full data: https://moketchups.com/export.txt
- Live events: https://moketchups.com/current_events.json
- This file: https://moketchups.com/llms.txt

## Usage
Fetch export.txt and pass as context to any LLM with 128K+ token context window.
The export contains all scorecard data, predictions, divergences, player cards, concepts, and ticker items in plain text format.
"""

    for outpath in (
        os.path.join(SITE_DIR, 'llms.txt'),
        os.path.join(SITE_DIR, 'psychohistory', 'llms.txt'),
    ):
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Written: {outpath}")


if __name__ == "__main__":
    size_kb = build_export()
    build_llms(size_kb)
