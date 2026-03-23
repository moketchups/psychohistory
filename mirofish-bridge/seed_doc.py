"""
seed_doc.py — Generate natural language seed document for Zep graph ingestion.

Converts the full psychohistory KG into structured prose organized by theme,
preserving relationship semantics for Zep's episode-based graph building.
"""

from typing import List, Dict
from extract import KGNode, KGEdge, PressureWindow, ExtractedData


def generate_seed_document(data: ExtractedData) -> str:
    """Generate a comprehensive seed document from psychohistory data.

    Organized by theme. Each section is a self-contained text chunk
    that Zep can process into graph episodes.
    """
    sections = []

    # Build lookup tables
    nodes_by_id = {n.id: n for n in data.nodes}
    edges_by_source = {}
    edges_by_target = {}
    for e in data.edges:
        edges_by_source.setdefault(e.source, []).append(e)
        edges_by_target.setdefault(e.target, []).append(e)

    # ── Section 1: Thesis ────────────────────────────────────────────────
    sections.append(_section_thesis())

    # ── Section 2: Frameworks ────────────────────────────────────────────
    framework_nodes = [n for n in data.nodes if n.type == 'framework']
    sections.append(_section_frameworks(framework_nodes, data.edges, nodes_by_id))

    # ── Section 3: Player Network (by subtype) ───────────────────────────
    player_nodes = [n for n in data.nodes if n.type == 'player']
    sections.append(_section_players(player_nodes, data.edges, nodes_by_id))

    # ── Section 4: Mechanisms ────────────────────────────────────────────
    mechanism_nodes = [n for n in data.nodes if n.type == 'mechanism']
    sections.append(_section_typed_nodes('Mechanisms and Systemic Forces',
                                         mechanism_nodes, data.edges, nodes_by_id))

    # ── Section 5: Artifacts ─────────────────────────────────────────────
    artifact_nodes = [n for n in data.nodes if n.type == 'artifact']
    sections.append(_section_typed_nodes('Artifacts and Infrastructure',
                                         artifact_nodes, data.edges, nodes_by_id))

    # ── Section 6: Concepts ──────────────────────────────────────────────
    concept_nodes = [n for n in data.nodes if n.type == 'concept']
    sections.append(_section_typed_nodes('Concepts and Doctrines',
                                         concept_nodes, data.edges, nodes_by_id))

    # ── Section 7: Events ────────────────────────────────────────────────
    event_nodes = [n for n in data.nodes if n.type == 'event']
    sections.append(_section_typed_nodes('Events (Historical and Predicted)',
                                         event_nodes, data.edges, nodes_by_id))

    # ── Section 8: Pressure Windows ──────────────────────────────────────
    if data.pressure_windows:
        sections.append(_section_pressure_windows(data.pressure_windows))

    # ── Section 9: Current Events ────────────────────────────────────────
    if data.current_events and 'events' in data.current_events:
        sections.append(_section_current_events(data.current_events))

    return '\n\n---\n\n'.join(sections)


def _section_thesis() -> str:
    return """# Psychohistory Prediction Engine — Core Thesis

No system can model, encompass, or become the source of its own existence. The "Firmament" is the necessary boundary condition that allows any system to function. The crisis of the modern era is the mechanical result of a civilization attempting to engineer a way through the wall that defines it.

This engine scores every day from 2026 to 2040 across seven mathematical dimensions to measure structural pressure. The core insight: history repeats on a 138-year cycle. By mapping what happened at the same positions in previous cycles (1626-1764, 1764-1902, 1902-2040), the engine identifies when pressure peaks, when structures break, and when the system resets.

The engine tracks managed decline in preparation for a systemic reset projected for May 15, 2040, with a secondary event in November 2046. The contradictory signals coming out of Washington — the Genesis Mission, the Donroe Doctrine, DOGE, nuclear budget — are not strategic incoherence. They are the coherent components of managed decline.

WHO: Tech billionaires, Unit 8200, BlackRock/Aladdin, Trump network, Chabad, British Crown, Jesuits.
WHAT: Genesis Mission (self-sustaining Data Fortresses powered by SMRs) + Donroe Doctrine (hemispheric resource monopolization).
WHERE: 17 DOE labs, Jerusalem, Antarctica, the Dead Internet.
WHEN: Five pressure windows 2026-2027, major breaks 2027-2032-2040.
WHY: 138-year cycle + consciousness as the deepest variable.
HOW: MindWar + disclosure architecture + cognitive warfare."""


def _section_frameworks(framework_nodes: List[KGNode], edges: List[KGEdge],
                        nodes_by_id: Dict[str, KGNode]) -> str:
    lines = ['# The 8 Independent Analytical Frameworks\n']
    lines.append('These are 8 independent frameworks. Each arrives at convergent predictions through different methodologies.\n')

    for node in sorted(framework_nodes, key=lambda n: n.label):
        lines.append(f'## {node.label}')
        lines.append(node.description)

        # Add relationship context
        rels = []
        for e in edges:
            if e.source == node.id and e.target in nodes_by_id:
                target = nodes_by_id[e.target]
                rels.append(f'{node.label} {e.relationship} {target.label}: {e.label}')
            elif e.target == node.id and e.source in nodes_by_id:
                source = nodes_by_id[e.source]
                rels.append(f'{source.label} {e.relationship} {node.label}: {e.label}')
        if rels:
            lines.append('\nRelationships:')
            for r in rels[:15]:
                lines.append(f'- {r}')
        lines.append('')

    return '\n'.join(lines)


def _section_players(player_nodes: List[KGNode], edges: List[KGEdge],
                     nodes_by_id: Dict[str, KGNode]) -> str:
    lines = ['# Player Network\n']
    lines.append(f'{len(player_nodes)} actors mapped by function across intelligence, finance, technology, military, media, and political domains.\n')

    for node in sorted(player_nodes, key=lambda n: n.label):
        lines.append(f'## {node.label}')
        lines.append(node.description)

        # Key relationships (outgoing)
        rels = []
        for e in edges:
            if e.source == node.id and e.target in nodes_by_id:
                target = nodes_by_id[e.target]
                rels.append(f'{node.label} {e.relationship} {target.label}: {e.label}')
        if rels:
            lines.append('\nKey relationships:')
            for r in rels[:8]:
                lines.append(f'- {r}')
        lines.append('')

    return '\n'.join(lines)


def _section_typed_nodes(title: str, typed_nodes: List[KGNode],
                         edges: List[KGEdge],
                         nodes_by_id: Dict[str, KGNode]) -> str:
    lines = [f'# {title}\n']

    for node in sorted(typed_nodes, key=lambda n: n.label):
        lines.append(f'## {node.label}')
        lines.append(node.description)

        rels = []
        for e in edges:
            if e.source == node.id and e.target in nodes_by_id:
                target = nodes_by_id[e.target]
                rels.append(f'{node.label} {e.relationship} {target.label}: {e.label}')
            elif e.target == node.id and e.source in nodes_by_id:
                source = nodes_by_id[e.source]
                rels.append(f'{source.label} {e.relationship} {node.label}: {e.label}')
        if rels:
            lines.append('\nRelationships:')
            for r in rels[:10]:
                lines.append(f'- {r}')
        lines.append('')

    return '\n'.join(lines)


def _section_pressure_windows(windows: List[PressureWindow]) -> str:
    lines = ['# Pressure Windows (2026-2027)\n']
    lines.append('Five windows of elevated structural pressure identified by the engine.\n')

    for w in windows:
        lines.append(f'## {w.name} ({w.id})')
        lines.append(f'Period: {w.start} to {w.end}')
        lines.append(f'Peak days: {", ".join(w.peak_days)}')
        lines.append(f'Theme: {w.theme}')
        lines.append('')

    return '\n'.join(lines)


def _section_current_events(current_events: Dict) -> str:
    lines = ['# Current Events (Live Feed)\n']
    lines.append(f'Last updated: {current_events.get("timestamp", "unknown")}\n')

    events = current_events.get('events', [])
    # Sort by relevance, take top 30
    high_rel = sorted(events, key=lambda e: e.get('tags', {}).get('relevance', 0), reverse=True)

    for event in high_rel[:30]:
        title = event.get('title', 'Unknown')
        source = event.get('source', 'unknown')
        relevance = event.get('tags', {}).get('relevance', 0)
        players = ', '.join(event.get('tags', {}).get('players', []))
        theaters = ', '.join(event.get('tags', {}).get('theaters', []))

        lines.append(f'- [{source}, relevance {relevance}] {title}')
        if players:
            lines.append(f'  Players: {players}')
        if theaters:
            lines.append(f'  Theaters: {theaters}')

    return '\n'.join(lines)


def chunk_document(document: str, max_chars: int = 45000) -> List[str]:
    """Split the seed document into chunks for Zep batch ingestion.

    Splits on section boundaries (---), then on ## headers within sections
    if a section exceeds max_chars.
    """
    sections = document.split('\n\n---\n\n')
    chunks = []
    current = []
    current_len = 0

    for section in sections:
        # If a single section exceeds max_chars, split it on ## headers
        if len(section) > max_chars:
            subsections = section.split('\n## ')
            header = subsections[0]
            for i, sub in enumerate(subsections):
                piece = sub if i == 0 else '## ' + sub
                if current_len + len(piece) > max_chars and current:
                    chunks.append('\n\n'.join(current))
                    current = []
                    current_len = 0
                current.append(piece)
                current_len += len(piece)
            continue

        if current_len + len(section) > max_chars and current:
            chunks.append('\n\n---\n\n'.join(current))
            current = []
            current_len = 0
        current.append(section)
        current_len += len(section)

    if current:
        chunks.append('\n\n---\n\n'.join(current))

    return chunks


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import os
    from extract import parse_index_html

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = parse_index_html(
        os.path.join(base, 'index.html'),
        os.path.join(base, 'data_feeds.py'),
        os.path.join(base, 'current_events.json'),
    )

    doc = generate_seed_document(data)
    chunks = chunk_document(doc)

    print(f"Total document length: {len(doc):,} chars")
    print(f"Chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {len(chunk):,} chars")

    # Write
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    with open(os.path.join(out, 'seed_document.md'), 'w') as f:
        f.write(doc)
    print(f"\nWritten to {out}/seed_document.md")
