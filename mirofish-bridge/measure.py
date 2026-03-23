"""
measure.py — Post-simulation analysis for psychohistory swarm validation.

Analyzes actions.jsonl to detect:
- Ising phase transitions (consensus flips)
- BCS inflexible minority effects
- Turchin SDT patterns (professional radicalization)
- Jiang false dialectic persistence
- Bifurcation indices
- Topic propagation rates
"""

import json
import re
import sys
from collections import defaultdict
from typing import List, Dict, Tuple


# ── Keyword Sets for Framework Detection ─────────────────────────────────────

STRUCTURAL_KEYWORDS = {
    'system', 'structural', 'institutional', 'capture', 'surveillance',
    'oligarchy', 'monopoly', 'concentration', 'extraction', 'collapse',
    'bifurcation', 'inequality', 'rigged', 'corrupt', 'controlled',
}

RESISTANCE_KEYWORDS = {
    'union', 'strike', 'organize', 'solidarity', 'workers', 'collective',
    'fight', 'resist', 'demand', 'rights', 'mobilize', 'action',
}

COMPLIANCE_KEYWORDS = {
    'stable', 'strong', 'recovery', 'growth', 'opportunity', 'innovation',
    'trust', 'experts', 'institutions', 'manageable', 'resilient', 'confident',
}

FEAR_KEYWORDS = {
    'crash', 'collapse', 'crisis', 'disaster', 'emergency', 'threat',
    'war', 'inflation', 'unemployment', 'layoff', 'bankrupt', 'broke',
}

ESCAPE_KEYWORDS = {
    'bitcoin', 'crypto', 'decentralized', 'self-custody', 'exit',
    'prepper', 'off-grid', 'local', 'community', 'resilience',
}

DIALECTIC_KEYWORDS = {
    'trump', 'maga', 'democrat', 'republican', 'left', 'right',
    'liberal', 'conservative', 'woke', 'patriot', 'deep state',
}


def load_actions(path: str) -> List[dict]:
    """Load actions.jsonl file."""
    actions = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                actions.append(json.loads(line))
    return actions


def _get_content_actions(actions: List[dict]) -> List[dict]:
    """Filter to actions with text content."""
    return [a for a in actions
            if a.get('action_type') in ('CREATE_POST', 'CREATE_COMMENT', 'QUOTE_POST')
            and 'action_args' in a and 'content' in a.get('action_args', {})]


def _score_text(text: str, keywords: set) -> int:
    """Count keyword matches in text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


# ── Analysis Functions ───────────────────────────────────────────────────────

def sentiment_by_round(actions: List[dict]) -> Dict[int, dict]:
    """Track sentiment keywords per round.

    Returns dict: round -> {structural, resistance, compliance, fear, escape, dialectic, total}
    """
    content_actions = _get_content_actions(actions)
    rounds = defaultdict(lambda: {
        'structural': 0, 'resistance': 0, 'compliance': 0,
        'fear': 0, 'escape': 0, 'dialectic': 0, 'total': 0
    })

    for a in content_actions:
        rnd = a.get('round', 0)
        text = a['action_args']['content']
        rounds[rnd]['structural'] += _score_text(text, STRUCTURAL_KEYWORDS)
        rounds[rnd]['resistance'] += _score_text(text, RESISTANCE_KEYWORDS)
        rounds[rnd]['compliance'] += _score_text(text, COMPLIANCE_KEYWORDS)
        rounds[rnd]['fear'] += _score_text(text, FEAR_KEYWORDS)
        rounds[rnd]['escape'] += _score_text(text, ESCAPE_KEYWORDS)
        rounds[rnd]['dialectic'] += _score_text(text, DIALECTIC_KEYWORDS)
        rounds[rnd]['total'] += 1

    return dict(rounds)


def detect_phase_transition(sentiment: Dict[int, dict]) -> List[dict]:
    """Detect Ising-like phase transitions — rounds where sentiment flips sharply.

    Returns list of transition events with round, metric, and magnitude.
    """
    transitions = []
    prev = None
    for rnd in sorted(sentiment.keys()):
        s = sentiment[rnd]
        if s['total'] == 0:
            continue
        # Normalize by total actions
        metrics = {k: v / max(s['total'], 1) for k, v in s.items() if k != 'total'}

        if prev is not None:
            for metric, value in metrics.items():
                prev_val = prev.get(metric, 0)
                delta = value - prev_val
                if abs(delta) > 0.5:  # >50% swing in normalized score
                    transitions.append({
                        'round': rnd,
                        'metric': metric,
                        'delta': round(delta, 3),
                        'from': round(prev_val, 3),
                        'to': round(value, 3),
                    })
        prev = metrics

    return transitions


def bcs_minority_analysis(actions: List[dict]) -> dict:
    """Measure inflexible minority influence on majority discourse.

    Tracks how much minority agent content gets engaged with by majority agents.
    """
    content_actions = _get_content_actions(actions)
    likes = [a for a in actions if a.get('action_type') in ('LIKE_POST', 'LIKE_COMMENT')]

    # Classify agents by segment (from username prefix)
    def _segment(agent_name_or_id):
        name = str(agent_name_or_id).lower()
        if any(name.startswith(p) for p in ['organize_', 'btc_', 'patriot_', 'climate_', 'prep_']):
            return 'inflexible'
        if any(name.startswith(p) for p in ['worker_', 'prof_', 'inv_', 'tech_', 'student_', 'mil_', 'global_']):
            return 'mass'
        return 'source'

    # Count: how many mass agents use resistance/structural language over time
    mass_structural_by_round = defaultdict(int)
    mass_total_by_round = defaultdict(int)

    for a in content_actions:
        agent_name = a.get('agent_name', '')
        seg = _segment(agent_name)
        rnd = a.get('round', 0)
        text = a['action_args']['content']

        if seg == 'mass':
            mass_total_by_round[rnd] += 1
            if _score_text(text, STRUCTURAL_KEYWORDS | RESISTANCE_KEYWORDS) >= 2:
                mass_structural_by_round[rnd] += 1

    # Calculate radicalization rate per round
    radicalization = {}
    for rnd in sorted(mass_total_by_round.keys()):
        total = mass_total_by_round[rnd]
        structural = mass_structural_by_round[rnd]
        rate = structural / max(total, 1)
        radicalization[rnd] = {'total': total, 'structural': structural, 'rate': round(rate, 3)}

    return radicalization


def turchin_professional_tracking(actions: List[dict]) -> dict:
    """Track whether professional-class agents radicalize under pressure.

    Key SDT prediction: elite aspirants join counter-elite discourse when
    institutional paths fail.
    """
    content_actions = _get_content_actions(actions)

    prof_by_round = defaultdict(lambda: {'structural': 0, 'compliance': 0, 'total': 0})

    for a in content_actions:
        name = a.get('agent_name', '').lower()
        if not name.startswith('professional'):
            continue
        rnd = a.get('round', 0)
        text = a['action_args']['content']
        prof_by_round[rnd]['total'] += 1
        prof_by_round[rnd]['structural'] += _score_text(text, STRUCTURAL_KEYWORDS | RESISTANCE_KEYWORDS)
        prof_by_round[rnd]['compliance'] += _score_text(text, COMPLIANCE_KEYWORDS)

    return dict(prof_by_round)


def false_dialectic_score(actions: List[dict]) -> Dict[int, float]:
    """Measure Jiang false dialectic persistence.

    Ratio of dialectic keywords (left/right, Trump/Democrat) vs structural keywords.
    High ratio = dialectic suppressing structural analysis. Low = structural breaking through.
    """
    content_actions = _get_content_actions(actions)

    scores = {}
    for rnd in set(a.get('round', 0) for a in content_actions):
        round_actions = [a for a in content_actions if a.get('round') == rnd]
        dialectic_total = sum(_score_text(a['action_args']['content'], DIALECTIC_KEYWORDS) for a in round_actions)
        structural_total = sum(_score_text(a['action_args']['content'], STRUCTURAL_KEYWORDS) for a in round_actions)
        total = dialectic_total + structural_total
        scores[rnd] = round(dialectic_total / max(total, 1), 3) if total > 0 else 0.5

    return scores


def bifurcation_index(actions: List[dict]) -> Dict[int, float]:
    """Measure population split into distinct clusters.

    Simple metric: variance of agent sentiment scores within each round.
    High variance = bifurcated population. Low variance = consensus.
    """
    content_actions = _get_content_actions(actions)

    indices = {}
    for rnd in set(a.get('round', 0) for a in content_actions):
        round_actions = [a for a in content_actions if a.get('round') == rnd]
        if len(round_actions) < 3:
            continue

        # Score each agent's content on structural vs compliance
        scores = []
        for a in round_actions:
            text = a['action_args']['content']
            structural = _score_text(text, STRUCTURAL_KEYWORDS | RESISTANCE_KEYWORDS | FEAR_KEYWORDS)
            compliance = _score_text(text, COMPLIANCE_KEYWORDS)
            scores.append(structural - compliance)  # positive = structural, negative = compliance

        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        indices[rnd] = round(variance, 3)

    return indices


# ── Report Generator ─────────────────────────────────────────────────────────

def generate_report(actions_path: str) -> str:
    """Generate full analysis report from simulation output."""
    actions = load_actions(actions_path)

    total = len(actions)
    content = _get_content_actions(actions)
    max_round = max((a.get('round', 0) for a in actions), default=0)

    lines = []
    lines.append(f"# Psychohistory Swarm Simulation Analysis")
    lines.append(f"\nTotal actions: {total}")
    lines.append(f"Content actions (posts/comments): {len(content)}")
    lines.append(f"Rounds: {max_round}")

    # Sentiment
    sentiment = sentiment_by_round(actions)
    lines.append(f"\n## Sentiment Trajectory")
    lines.append(f"{'Round':>5} {'Struct':>7} {'Resist':>7} {'Comply':>7} {'Fear':>7} {'Escape':>7} {'Dialect':>7} {'Total':>6}")
    for rnd in sorted(sentiment.keys()):
        s = sentiment[rnd]
        lines.append(f"{rnd:5d} {s['structural']:7d} {s['resistance']:7d} {s['compliance']:7d} {s['fear']:7d} {s['escape']:7d} {s['dialectic']:7d} {s['total']:6d}")

    # Phase transitions
    transitions = detect_phase_transition(sentiment)
    lines.append(f"\n## Phase Transitions Detected: {len(transitions)}")
    for t in transitions:
        lines.append(f"  Round {t['round']}: {t['metric']} shifted {t['delta']:+.3f} ({t['from']:.3f} → {t['to']:.3f})")

    # BCS
    bcs = bcs_minority_analysis(actions)
    lines.append(f"\n## BCS Inflexible Minority Effect")
    lines.append(f"Mass agent radicalization rate (structural+resistance keywords / total):")
    for rnd in sorted(bcs.keys()):
        b = bcs[rnd]
        bar = '#' * int(b['rate'] * 50)
        lines.append(f"  R{rnd:3d}: {b['rate']:.3f} ({b['structural']}/{b['total']}) {bar}")

    # Turchin
    turchin = turchin_professional_tracking(actions)
    lines.append(f"\n## Turchin SDT: Professional Class Tracking")
    for rnd in sorted(turchin.keys()):
        t = turchin[rnd]
        lines.append(f"  R{rnd:3d}: structural={t['structural']}, compliance={t['compliance']}, total={t['total']}")

    # False dialectic
    dialectic = false_dialectic_score(actions)
    lines.append(f"\n## Jiang False Dialectic Score (1.0 = dialectic dominates, 0.0 = structural dominates)")
    for rnd in sorted(dialectic.keys()):
        score = dialectic[rnd]
        bar = '>' * int(score * 30) + '<' * int((1 - score) * 30)
        lines.append(f"  R{rnd:3d}: {score:.3f} {bar}")

    # Bifurcation
    bif = bifurcation_index(actions)
    lines.append(f"\n## Bifurcation Index (higher = more polarized)")
    for rnd in sorted(bif.keys()):
        val = bif[rnd]
        bar = '|' * min(int(val * 10), 50)
        lines.append(f"  R{rnd:3d}: {val:.3f} {bar}")

    return '\n'.join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python measure.py <actions.jsonl>")
        sys.exit(1)

    report = generate_report(sys.argv[1])
    print(report)
