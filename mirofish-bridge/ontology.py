"""
ontology.py — Map psychohistory's 6 node types to MiroFish's 10 entity types.

Only player nodes become agents. Mechanism, framework, artifact, event, concept
nodes exist in the Zep seed document as contextual knowledge but not as agents.
"""

import json
from typing import List, Dict
from extract import KGNode
from config import ORG_IDS, SUBTYPE_MAP, ONTOLOGY_TYPES, ONTOLOGY_EDGES, get_entity_subtype


def classify_nodes(nodes: List[KGNode]) -> Dict[str, str]:
    """Classify every player node into one of the 10 MiroFish entity types.

    Returns: dict mapping node_id -> entity_type_name
    """
    classification = {}
    for node in nodes:
        if node.type != 'player':
            continue
        classification[node.id] = get_entity_subtype(node.id)
    return classification


def generate_ontology_json(nodes: List[KGNode], edges=None) -> dict:
    """Generate the MiroFish-compatible ontology JSON.

    Returns the ontology dict with entity_types and edge_types.
    """
    # Count entities per type for examples
    classification = classify_nodes(nodes)
    type_examples = {}
    for node_id, entity_type in classification.items():
        if entity_type not in type_examples:
            type_examples[entity_type] = []
        # Find the node label
        for n in nodes:
            if n.id == node_id:
                type_examples[entity_type].append(n.label)
                break

    # Build ontology with examples
    entity_types = []
    for otype in ONTOLOGY_TYPES:
        entry = dict(otype)
        entry['examples'] = type_examples.get(otype['name'], [])[:5]
        entity_types.append(entry)

    ontology = {
        'entity_types': entity_types,
        'edge_types': ONTOLOGY_EDGES,
        'analysis_summary': (
            'Psychohistory Prediction Engine knowledge graph: '
            f'{len(classification)} player entities classified across 10 types. '
            'Tracks geopolitical, financial, technological, and intelligence networks '
            'across a 14-year trajectory (2026-2040) using 8 independent analytical frameworks.'
        ),
    }
    return ontology


def get_agent_node_ids(nodes: List[KGNode], max_tier: int = 2) -> List[str]:
    """Return node IDs that should become simulation agents, filtered by tier."""
    from config import get_tier
    return [
        n.id for n in nodes
        if n.type == 'player' and get_tier(n.id) <= max_tier
    ]


def print_classification_report(nodes: List[KGNode]):
    """Print a summary of how nodes are classified."""
    classification = classify_nodes(nodes)
    type_counts = {}
    for entity_type in classification.values():
        type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

    print(f"Total player nodes classified: {len(classification)}")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:20s} {c}")

    # Check for unclassified (should all be 'Person' fallback)
    unclassified = [nid for nid, nt in classification.items() if nt == 'Person']
    if unclassified:
        print(f"\nFallback 'Person' ({len(unclassified)}):")
        for nid in sorted(unclassified):
            print(f"  {nid}")


if __name__ == '__main__':
    import os
    from extract import parse_index_html

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = parse_index_html(
        os.path.join(base, 'index.html'),
        os.path.join(base, 'data_feeds.py'),
    )

    print("=== Classification Report ===\n")
    print_classification_report(data.nodes)

    print("\n=== Ontology JSON ===\n")
    ontology = generate_ontology_json(data.nodes)
    print(json.dumps(ontology, indent=2)[:2000])

    print(f"\n=== Agent Counts by Tier ===")
    for tier in [1, 2, 3]:
        ids = get_agent_node_ids(data.nodes, max_tier=tier)
        print(f"  Tier <= {tier}: {len(ids)} agents")
