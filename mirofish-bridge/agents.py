"""
agents.py — Generate MiroFish OASIS agent profiles from psychohistory player data.

Joins KG nodes, KG edges, and HTML player cards to produce detailed agent profiles
in both Reddit JSON and Twitter CSV formats.
"""

import csv
import io
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

from extract import KGNode, KGEdge, PlayerCard
from config import (
    ORG_IDS, get_entity_subtype, get_tier, get_active_hours,
    COUNTRY_MAP, FRAMEWORK_PERSONA,
)


@dataclass
class AgentProfile:
    user_id: int
    username: str
    name: str
    bio: str
    persona: str
    age: int = 45
    gender: str = 'male'
    mbti: str = 'INTJ'
    country: str = 'US'
    profession: str = ''
    interested_topics: List[str] = field(default_factory=list)
    # Reddit-specific
    karma: int = 1000
    # Twitter-specific
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500
    # Simulation params
    stance: str = 'neutral'
    activity_level: float = 0.5
    sentiment_bias: float = 0.0
    influence_weight: float = 1.0
    active_hours: List[int] = field(default_factory=list)
    # Metadata
    source_node_id: str = ''
    entity_type: str = ''
    tier: int = 3
    created_at: str = '2026-03-15'

    def to_reddit_format(self) -> dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'name': self.name,
            'bio': self.bio,
            'persona': self.persona,
            'karma': self.karma,
            'created_at': self.created_at,
            'age': self.age,
            'gender': self.gender,
            'mbti': self.mbti,
            'country': self.country,
            'profession': self.profession,
            'interested_topics': self.interested_topics,
        }

    def to_twitter_format(self) -> dict:
        """OASIS Twitter format requires specific column names:
        username, name, description, user_char, followers_count, following_count
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'name': self.name,
            'description': self.bio,           # OASIS reads 'description' not 'bio'
            'user_char': self.persona,          # OASIS reads 'user_char' not 'persona'
            'followers_count': self.follower_count,  # OASIS reads 'followers_count'
            'following_count': self.friend_count,    # OASIS reads 'following_count'
            'following_agentid_list': '[]',
            'previous_tweets': '',
            'age': self.age,
            'gender': self.gender,
            'mbti': self.mbti,
            'country': self.country,
            'profession': self.profession,
        }

    def to_agent_config(self) -> dict:
        return {
            'agent_id': self.user_id,
            'entity_name': self.name,
            'entity_type': self.entity_type,
            'activity_level': self.activity_level,
            'posts_per_hour': 1.5 if self.tier == 1 else 0.8 if self.tier == 2 else 0.3,
            'comments_per_hour': 2.0 if self.tier == 1 else 1.0 if self.tier == 2 else 0.5,
            'active_hours': self.active_hours,
            'response_delay_min': 5,
            'response_delay_max': 60,
            'sentiment_bias': self.sentiment_bias,
            'stance': self.stance,
            'influence_weight': self.influence_weight,
        }


# ── Profile Generation ───────────────────────────────────────────────────────

def _match_player_card(node: KGNode, player_cards: List[PlayerCard]) -> Optional[PlayerCard]:
    """Match a KG node to its HTML player card by name similarity."""
    node_label_lower = node.label.lower().strip()
    # Direct match
    for card in player_cards:
        if card.name.lower().strip() == node_label_lower:
            return card
    # Partial match (node label is contained in card name or vice versa)
    for card in player_cards:
        card_lower = card.name.lower().strip()
        if node_label_lower in card_lower or card_lower in node_label_lower:
            return card
    # Match on first word (e.g., "Netanyahu" matches "Netanyahu")
    first_word = node_label_lower.split()[0] if node_label_lower else ''
    for card in player_cards:
        if first_word and card.name.lower().startswith(first_word):
            return card
    return None


def _get_connected_topics(node_id: str, edges: List[KGEdge],
                          nodes_by_id: Dict[str, KGNode]) -> List[str]:
    """Extract interested_topics from KG edges — what this player connects to."""
    topics = set()
    for edge in edges:
        other_id = None
        if edge.source == node_id:
            other_id = edge.target
        elif edge.target == node_id:
            other_id = edge.source

        if other_id and other_id in nodes_by_id:
            other = nodes_by_id[other_id]
            if other.type in ('mechanism', 'framework', 'concept', 'artifact'):
                topics.add(other.label)
    return sorted(topics)[:10]  # cap at 10


def _get_framework_persona(node_id: str, edges: List[KGEdge],
                           nodes_by_id: Dict[str, KGNode]) -> str:
    """Build framework-awareness text for agents connected to framework nodes."""
    framework_text = []
    for edge in edges:
        other_id = None
        if edge.source == node_id:
            other_id = edge.target
        elif edge.target == node_id:
            other_id = edge.source

        if other_id and other_id in nodes_by_id:
            other = nodes_by_id[other_id]
            if other.type == 'framework' and other.id in FRAMEWORK_PERSONA:
                framework_text.append(FRAMEWORK_PERSONA[other.id])

    return ' '.join(framework_text)


def _compute_edge_degree(node_id: str, edges: List[KGEdge]) -> int:
    """Count how many edges connect to this node."""
    return sum(1 for e in edges if e.source == node_id or e.target == node_id)


def _infer_stance(node_id: str, edges: List[KGEdge]) -> str:
    """Infer agent stance from edge relationships."""
    technate_nodes = {
        'genesis', 'technate', 'aladdin', 'palantir', 'doge_unit',
        'mindwar', 'model_collapse', 'algo_govern',
    }
    resistance_nodes = {
        'stewards_ark', 'root_source', 'labor_variable',
    }

    controls_technate = False
    opposes_technate = False

    for edge in edges:
        if edge.source == node_id:
            if edge.target in technate_nodes and edge.relationship in ('controls', 'enables', 'feeds'):
                controls_technate = True
            if edge.target in resistance_nodes and edge.relationship in ('controls', 'enables', 'validates'):
                opposes_technate = True
        if edge.target == node_id:
            if edge.source in technate_nodes and edge.relationship in ('controls', 'feeds'):
                controls_technate = True

    if controls_technate and not opposes_technate:
        return 'supportive'
    if opposes_technate and not controls_technate:
        return 'opposing'
    if get_entity_subtype(node_id) == 'Ideologue':
        return 'observer'
    return 'neutral'


def _infer_gender(node: KGNode) -> str:
    """Infer gender from node description."""
    if node.id in ORG_IDS:
        return 'other'
    desc_lower = node.description.lower()
    # Check for female indicators
    female_indicators = [' she ', ' her ', 'queen', 'princess', 'sister',
                         'mother', 'wife', 'woman', 'female', 'actress']
    for ind in female_indicators:
        if ind in desc_lower:
            return 'female'
    # Specific known females
    known_female = {
        'ivanka_trump', 'ghislaine', 'virginia_giuffre', 'lagarde',
        'von_der_leyen', 'vestager', 'safra_catz', 'junkermann',
        'erika_kirk', 'sara_nelson', 'blavatsky', 'owens',
    }
    if node.id in known_female:
        return 'female'
    return 'male'


def _infer_age(node: KGNode) -> int:
    """Infer approximate age. Organizations get 50."""
    if node.id in ORG_IDS:
        return 50
    # Check for birth/death years in description
    year_match = re.search(r'\((\d{4})-(\d{4})\)', node.description)
    if year_match:
        return 2026 - int(year_match.group(1))  # historical figure, use birth year
    year_match = re.search(r'\((\d{4})-\)', node.description)
    if year_match:
        return 2026 - int(year_match.group(1))
    # Known approximate ages
    age_map = {
        'trump': 79, 'netanyahu': 76, 'putin': 73, 'xi_jinping': 72,
        'modi': 75, 'musk': 54, 'altman': 40, 'thiel': 58, 'bezos': 62,
        'zuckerberg': 41, 'kushner': 45, 'mbs': 40, 'vance': 41,
        'karp': 57, 'ellison': 81, 'jensen_huang': 63,
        'obama': 64, 'breshears': 56, 'alan_berman': 35,
        'rogan': 58, 'carlson': 56, 'schwab': 87,
    }
    return age_map.get(node.id, 50)


# MBTI mapping for key players (based on behavioral patterns)
MBTI_MAP = {
    'trump': 'ESTP', 'netanyahu': 'ENTJ', 'putin': 'ISTJ', 'xi_jinping': 'ISTJ',
    'musk': 'INTJ', 'altman': 'ENTJ', 'thiel': 'INTJ', 'bezos': 'ISTJ',
    'zuckerberg': 'INTJ', 'kushner': 'ISTJ', 'mbs': 'ENTJ', 'vance': 'INTJ',
    'karp': 'INTP', 'ellison': 'ENTJ', 'obama': 'ENFJ', 'modi': 'ENTJ',
    'breshears': 'INTP', 'jiang': 'INTP', 'roemmele': 'ENTP', 'alan_berman': 'INTP',
    'turchin': 'INTJ', 'webb': 'ISTJ', 'rogan': 'ESTP', 'carlson': 'ENTP',
    'yarvin': 'INTP', 'michael_flynn': 'ESTJ', 'schwab': 'ENTJ',
    'sacks': 'ENTJ', 'jensen_huang': 'ENTJ',
}


def generate_profiles(nodes: List[KGNode], edges: List[KGEdge],
                      player_cards: List[PlayerCard],
                      max_tier: int = 2) -> List[AgentProfile]:
    """Generate MiroFish agent profiles from psychohistory data.

    Args:
        nodes: All KG nodes
        edges: All KG edges
        player_cards: HTML player cards
        max_tier: Maximum tier to include (1=core only, 2=core+secondary, 3=all)

    Returns: List of AgentProfile objects
    """
    nodes_by_id = {n.id: n for n in nodes}
    player_nodes = [n for n in nodes if n.type == 'player' and get_tier(n.id) <= max_tier]

    profiles = []
    for idx, node in enumerate(player_nodes):
        card = _match_player_card(node, player_cards)
        entity_type = get_entity_subtype(node.id)
        tier = get_tier(node.id)
        degree = _compute_edge_degree(node.id, edges)

        # Build persona: KG description + player card analysis + framework awareness
        persona_parts = [node.description]
        if card and card.analysis:
            # Add card analysis if substantially different from KG description
            if len(card.analysis) > len(node.description) * 1.2:
                persona_parts.append(card.analysis)
        framework_text = _get_framework_persona(node.id, edges, nodes_by_id)
        if framework_text:
            persona_parts.append(f"[Framework awareness: {framework_text}]")

        persona = ' '.join(persona_parts)

        # Bio: role + first sentence of description
        role = card.role if card else entity_type
        first_sentence = node.description.split('.')[0] + '.'
        bio = f"{role}. {first_sentence}"
        if len(bio) > 200:
            bio = bio[:197] + '...'

        # Username
        username = node.id.replace('_', '')
        if node.id in ORG_IDS:
            username = node.id.replace('_', '_')

        # Influence weight from edge degree
        influence = min(3.0, max(0.5, degree / 10.0))

        # Social metrics scaled by influence
        follower_count = min(50000, int(degree * 200 + 100))
        karma = min(100000, int(degree * 500 + 500))

        profile = AgentProfile(
            user_id=idx,
            username=username,
            name=node.label,
            bio=bio,
            persona=persona,
            age=_infer_age(node),
            gender=_infer_gender(node),
            mbti=MBTI_MAP.get(node.id, 'INTJ'),
            country=COUNTRY_MAP.get(node.id, 'US'),
            profession=card.role if card else entity_type,
            interested_topics=_get_connected_topics(node.id, edges, nodes_by_id),
            karma=karma,
            friend_count=min(5000, int(degree * 50 + 50)),
            follower_count=follower_count,
            statuses_count=min(20000, int(degree * 100 + 200)),
            stance=_infer_stance(node.id, edges),
            activity_level=0.8 if tier == 1 else 0.5 if tier == 2 else 0.3,
            sentiment_bias=0.3 if _infer_stance(node.id, edges) == 'supportive' else
                           -0.3 if _infer_stance(node.id, edges) == 'opposing' else 0.0,
            influence_weight=influence,
            active_hours=get_active_hours(node.id),
            source_node_id=node.id,
            entity_type=entity_type,
            tier=tier,
        )
        profiles.append(profile)

    return profiles


def write_reddit_profiles(profiles: List[AgentProfile], path: str):
    """Write profiles in MiroFish Reddit JSON format."""
    data = [p.to_reddit_format() for p in profiles]
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_twitter_profiles(profiles: List[AgentProfile], path: str):
    """Write profiles in MiroFish Twitter CSV format."""
    if not profiles:
        return
    data = [p.to_twitter_format() for p in profiles]
    fieldnames = list(data[0].keys())
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Serialize lists as JSON strings
            row_copy = dict(row)
            for k, v in row_copy.items():
                if isinstance(v, list):
                    row_copy[k] = json.dumps(v)
            writer.writerow(row_copy)


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

    profiles = generate_profiles(data.nodes, data.edges, data.player_cards, max_tier=2)

    print(f"Generated {len(profiles)} agent profiles")
    print(f"\nBy type:")
    type_counts = {}
    for p in profiles:
        type_counts[p.entity_type] = type_counts.get(p.entity_type, 0) + 1
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:20s} {c}")

    print(f"\nBy stance:")
    stance_counts = {}
    for p in profiles:
        stance_counts[p.stance] = stance_counts.get(p.stance, 0) + 1
    for s, c in sorted(stance_counts.items(), key=lambda x: -x[1]):
        print(f"  {s:20s} {c}")

    print(f"\nSample profiles:")
    for p in profiles[:3]:
        print(f"\n  [{p.user_id}] {p.name} ({p.entity_type}, Tier {p.tier})")
        print(f"  Stance: {p.stance}, Activity: {p.activity_level}")
        print(f"  Topics: {', '.join(p.interested_topics[:5])}")
        print(f"  Bio: {p.bio[:100]}...")
        print(f"  Persona length: {len(p.persona)} chars")

    # Write outputs
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    write_reddit_profiles(profiles, os.path.join(out, 'agents_reddit.json'))
    write_twitter_profiles(profiles, os.path.join(out, 'agents_twitter.csv'))
    print(f"\nWritten to {out}/agents_reddit.json and agents_twitter.csv")
