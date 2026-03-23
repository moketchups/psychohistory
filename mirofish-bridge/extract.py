"""
extract.py — Parse psychohistory index.html into structured data.

Extracts: KG nodes, KG edges, player cards (HTML), predictions, pressure windows.
Also loads current_events.json and pressure windows from data_feeds.py.
"""

import json
import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from html.parser import HTMLParser


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class KGNode:
    id: str
    type: str      # player, mechanism, framework, artifact, event, concept
    label: str
    description: str

@dataclass
class KGEdge:
    source: str
    target: str
    relationship: str
    label: str

@dataclass
class PlayerCard:
    name: str
    role: str
    analysis: str   # full HTML content stripped to text
    section: str     # which section header this card falls under

@dataclass
class Prediction:
    year: int
    headline: str
    content: str     # full text content

@dataclass
class PressureWindow:
    id: str
    name: str
    start: str
    end: str
    peak_days: List[str]
    theme: str

@dataclass
class ExtractedData:
    nodes: List[KGNode] = field(default_factory=list)
    edges: List[KGEdge] = field(default_factory=list)
    player_cards: List[PlayerCard] = field(default_factory=list)
    predictions: List[Prediction] = field(default_factory=list)
    pressure_windows: List[PressureWindow] = field(default_factory=list)
    current_events: Dict = field(default_factory=dict)


# ── JS Array Parsing ─────────────────────────────────────────────────────────

def _extract_js_array(html: str, var_name: str) -> str:
    """Extract the raw text of a JS array literal from the HTML."""
    pattern = rf'{var_name}\s*=\s*\['
    match = re.search(pattern, html)
    if not match:
        raise ValueError(f"Could not find {var_name} in HTML")

    start = match.end() - 1  # include the opening [
    depth = 0
    i = start
    while i < len(html):
        c = html[i]
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                return html[start:i + 1]
        elif c == "'" or c == '"':
            # skip string literals
            quote = c
            i += 1
            while i < len(html) and html[i] != quote:
                if html[i] == '\\':
                    i += 1  # skip escaped char
                i += 1
        elif c == '/' and i + 1 < len(html) and html[i + 1] == '/':
            # skip single-line comment
            while i < len(html) and html[i] != '\n':
                i += 1
        i += 1
    raise ValueError(f"Could not find closing bracket for {var_name}")


def _parse_js_object_line(line: str, keys: List[str]) -> Optional[Dict[str, str]]:
    """Parse a single JS object literal line like {id:'x', t:'y', l:'z', d:'...'}.

    Uses the known key order to split the line reliably, avoiding issues
    with apostrophes inside single-quoted string values.
    """
    line = line.strip().rstrip(',')
    if not line.startswith('{') or not line.endswith('}'):
        return None

    inner = line[1:-1]  # strip { }
    result = {}

    for i, key in enumerate(keys):
        if i == 0:
            # First key: find at start of inner string
            pattern = key + ":'"
            if not inner.startswith(pattern):
                return None
            val_start = len(pattern)
        else:
            # Subsequent keys: find ", key:'" pattern (preceded by comma)
            pattern = ", " + key + ":'"
            idx = inner.find(pattern)
            if idx == -1:
                pattern = "," + key + ":'"
                idx = inner.find(pattern)
            if idx == -1:
                return None
            val_start = idx + len(pattern)

        if i < len(keys) - 1:
            # Find the NEXT key pattern to determine where this value ends
            next_key = keys[i + 1]
            next_pattern = "', " + next_key + ":'"
            val_end = inner.find(next_pattern, val_start)
            if val_end == -1:
                next_pattern = "'," + next_key + ":'"
                val_end = inner.find(next_pattern, val_start)
            if val_end == -1:
                return None
            result[key] = inner[val_start:val_end]
        else:
            # Last key: value ends at the final '
            val_end = inner.rfind("'")
            if val_end <= val_start:
                return None
            result[key] = inner[val_start:val_end]

    return result


def parse_kg_nodes(html: str) -> List[KGNode]:
    """Extract and parse the kgNodes array from index.html.

    Each node is on its own line: {id:'x', t:'type', l:'Label', d:'Description'}
    Parses line-by-line to handle apostrophes in description fields.
    """
    raw = _extract_js_array(html, 'const kgNodes')
    nodes = []
    for line in raw.split('\n'):
        line = line.strip()
        if not line.startswith('{id:'):
            continue
        parsed = _parse_js_object_line(line, ['id', 't', 'l', 'd'])
        if parsed:
            nodes.append(KGNode(
                id=parsed['id'],
                type=parsed['t'],
                label=parsed['l'],
                description=parsed['d']
            ))
    return nodes


def parse_kg_edges(html: str) -> List[KGEdge]:
    """Extract and parse the kgEdges array from index.html.

    Each edge is on its own line: {s:'source', t:'target', r:'rel', l:'label'}
    """
    raw = _extract_js_array(html, 'const kgEdges')
    edges = []
    for line in raw.split('\n'):
        line = line.strip()
        if not line.startswith('{s:'):
            continue
        parsed = _parse_js_object_line(line, ['s', 't', 'r', 'l'])
        if parsed:
            edges.append(KGEdge(
                source=parsed['s'],
                target=parsed['t'],
                relationship=parsed['r'],
                label=parsed['l']
            ))
    return edges


# ── HTML Player Card Parsing ─────────────────────────────────────────────────

def _strip_html(html_str: str) -> str:
    """Remove HTML tags, decode entities, return plain text."""
    # Decode common HTML entities
    text = html_str
    text = text.replace('&mdash;', '—')
    text = text.replace('&ndash;', '–')
    text = text.replace('&rsquo;', '\u2019')
    text = text.replace('&lsquo;', '\u2018')
    text = text.replace('&rdquo;', '\u201d')
    text = text.replace('&ldquo;', '\u201c')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&ne;', '\u2260')
    text = text.replace('&rarr;', '\u2192')
    text = text.replace('&times;', '\u00d7')
    text = text.replace('&kappa;', '\u03ba')
    text = text.replace('&bull;', '\u2022')
    text = text.replace('&#8594;', '\u2192')
    text = re.sub(r'&\w+;', '', text)  # catch remaining entities
    text = re.sub(r'&#\d+;', '', text)
    # Strip tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_player_cards(html: str) -> List[PlayerCard]:
    """Extract player cards from the Players tab HTML."""
    cards = []
    current_section = "Unknown"

    # Find all section titles and player cards in order
    # Section titles: <div class="sec-title">...</div>
    # Player cards: <div class="pc" ...>...</div>

    # We'll parse the players tab section
    players_start = html.find('id="p-players"')
    if players_start == -1:
        return cards

    # Find next tab panel to bound the search
    players_end = html.find('id="p-divergences"', players_start)
    if players_end == -1:
        players_end = len(html)

    section = html[players_start:players_end]

    # Extract section titles
    sec_pattern = re.compile(r'<div\s+class="sec-title"[^>]*>(.*?)</div>', re.DOTALL)

    # Extract player cards — they can be complex with nested divs
    # Use a simpler approach: find <div class="pc" and match to closing </div>
    pos = 0
    while pos < len(section):
        # Check for section title
        sec_match = sec_pattern.search(section, pos)
        # Check for player card
        pc_idx = section.find('<div class="pc"', pos)

        if sec_match and (pc_idx == -1 or sec_match.start() < pc_idx):
            current_section = _strip_html(sec_match.group(1))
            pos = sec_match.end()
            continue

        if pc_idx == -1:
            break

        # Find the matching closing div for the player card
        depth = 0
        i = pc_idx
        while i < len(section):
            if section[i:i+4] == '<div':
                depth += 1
            elif section[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    card_html = section[pc_idx:i + 6]
                    break
            i += 1
        else:
            break

        pos = i + 6

        # Parse the card HTML
        name_match = re.search(r'<h4[^>]*>(.*?)</h4>', card_html, re.DOTALL)
        role_match = re.search(r'<div\s+class="role"[^>]*>(.*?)</div>', card_html, re.DOTALL)
        # Get all <p> content
        p_matches = re.findall(r'<p[^>]*>(.*?)</p>', card_html, re.DOTALL)

        name = _strip_html(name_match.group(1)) if name_match else "Unknown"
        role = _strip_html(role_match.group(1)) if role_match else ""
        analysis = ' '.join(_strip_html(p) for p in p_matches)

        cards.append(PlayerCard(
            name=name,
            role=role,
            analysis=analysis,
            section=current_section
        ))

    return cards


# ── Pressure Windows ─────────────────────────────────────────────────────────

def parse_pressure_windows_from_data_feeds(data_feeds_path: str) -> List[PressureWindow]:
    """Extract PRESSURE_WINDOWS from data_feeds.py (the canonical source)."""
    with open(data_feeds_path, 'r') as f:
        content = f.read()

    # Find the PRESSURE_WINDOWS list
    match = re.search(r'PRESSURE_WINDOWS\s*=\s*\[', content)
    if not match:
        return []

    start = match.end() - 1
    depth = 0
    i = start
    while i < len(content):
        if content[i] == '[':
            depth += 1
        elif content[i] == ']':
            depth -= 1
            if depth == 0:
                raw = content[start:i + 1]
                break
        i += 1
    else:
        return []

    # This is valid Python, eval it safely
    # Convert to JSON-compatible: replace single quotes
    raw = raw.replace("'", '"')
    data = json.loads(raw)

    windows = []
    for w in data:
        windows.append(PressureWindow(
            id=w['id'],
            name=w['name'],
            start=w['start'],
            end=w['end'],
            peak_days=w.get('peak_days', []),
            theme=w.get('theme', '')
        ))
    return windows


# ── Current Events ───────────────────────────────────────────────────────────

def load_current_events(path: str) -> Dict:
    """Load current_events.json."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)


# ── Main Extraction ──────────────────────────────────────────────────────────

def parse_index_html(index_path: str, data_feeds_path: str = None,
                     current_events_path: str = None) -> ExtractedData:
    """Full extraction pipeline. Returns ExtractedData with all components."""
    with open(index_path, 'r') as f:
        html = f.read()

    data = ExtractedData()

    # KG
    data.nodes = parse_kg_nodes(html)
    data.edges = parse_kg_edges(html)

    # Player cards
    data.player_cards = parse_player_cards(html)

    # Pressure windows
    if data_feeds_path and os.path.exists(data_feeds_path):
        data.pressure_windows = parse_pressure_windows_from_data_feeds(data_feeds_path)

    # Current events
    if current_events_path and os.path.exists(current_events_path):
        data.current_events = load_current_events(current_events_path)

    return data


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index = os.path.join(base, 'index.html')
    feeds = os.path.join(base, 'data_feeds.py')
    events = os.path.join(base, 'current_events.json')

    data = parse_index_html(index, feeds, events)

    print(f"Nodes:           {len(data.nodes)}")
    by_type = {}
    for n in data.nodes:
        by_type[n.type] = by_type.get(n.type, 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"  {t:20s} {c}")

    print(f"Edges:           {len(data.edges)}")
    by_rel = {}
    for e in data.edges:
        by_rel[e.relationship] = by_rel.get(e.relationship, 0) + 1
    for r, c in sorted(by_rel.items(), key=lambda x: -x[1]):
        print(f"  {r:20s} {c}")

    print(f"Player cards:    {len(data.player_cards)}")
    print(f"Pressure windows:{len(data.pressure_windows)}")
    print(f"Current events:  {len(data.current_events.get('events', []))} events")

    # Validate: check all edge endpoints exist as node IDs
    node_ids = {n.id for n in data.nodes}
    broken = 0
    for e in data.edges:
        if e.source not in node_ids:
            broken += 1
        if e.target not in node_ids:
            broken += 1
    print(f"Broken edge endpoints: {broken}")
