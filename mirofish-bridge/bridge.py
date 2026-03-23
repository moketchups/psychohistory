"""
bridge.py — Orchestrator for psychohistory population swarm simulation.

Generates population agents, information sources, event timeline, and simulation
config. Produces all artifacts MiroFish needs to run a population-level simulation.
"""

import json
import os
import argparse
from datetime import datetime

from populations import generate_population, build_follow_graph, write_population
from sources import generate_sources
from events import generate_event_timeline


def run(total_masses: int = 500, max_rounds: int = 50, seed: int = 42):
    """Run the full population simulation bridge."""
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(out, exist_ok=True)

    # ── 1. Generate Populations ──────────────────────────────────────────
    print(f"Step 1: Generating {total_masses} mass agents + inflexible minorities...")
    agents = generate_population(total_masses=total_masses, seed=seed)

    segments = {}
    for a in agents:
        seg = a.get('_segment', 'unknown')
        segments[seg] = segments.get(seg, 0) + 1
    for s, c in sorted(segments.items(), key=lambda x: -x[1]):
        print(f"  {s:25s} {c}")

    # ── 2. Generate Information Sources ──────────────────────────────────
    print(f"\nStep 2: Generating information sources...")
    source_start_id = 10000
    sources = generate_sources(start_id=source_start_id)
    print(f"  {len(sources)} sources generated")

    # ── 3. Build Follow Graph ────────────────────────────────────────────
    print(f"\nStep 3: Building follow graph...")
    agents = build_follow_graph(agents, source_start_id)
    # Sources don't follow anyone
    for s in sources:
        s['following_agentid_list'] = '[]'

    # ── 4. Combine All Agents ────────────────────────────────────────────
    all_agents = agents + sources
    total = len(all_agents)
    print(f"  Total agents: {total} ({len(agents)} population + {len(sources)} sources)")

    # Write profiles
    profiles_path = os.path.join(out, 'agents_reddit.json')
    clean_agents = []
    for a in all_agents:
        profile = {k: v for k, v in a.items() if not k.startswith('_')}
        clean_agents.append(profile)
    with open(profiles_path, 'w') as f:
        json.dump(clean_agents, f, indent=2, ensure_ascii=False)
    print(f"  Written to {profiles_path}")

    # ── 5. Generate Event Timeline ───────────────────────────────────────
    print(f"\nStep 4: Generating event timeline...")
    timeline = generate_event_timeline(sources)
    total_events = sum(len(v) for v in timeline.values())
    print(f"  {total_events} events across {len(timeline)} rounds")

    # Round 0 events become initial_posts
    initial_posts = []
    for post in timeline.get(0, []):
        initial_posts.append({
            'poster_agent_id': post['agent_id'],
            'content': post['content'],
            'poster_type': 'Organization',
        })

    # ── 6. Generate Simulation Config ────────────────────────────────────
    print(f"\nStep 5: Generating simulation config...")
    sim_id = f"psychohistory_swarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Agent configs — activity levels from population data
    agent_configs = []
    for a in all_agents:
        activity = a.get('_activity', 0.3)
        agent_configs.append({
            'agent_id': a['user_id'],
            'entity_name': a.get('name', f"Agent_{a['user_id']}"),
            'entity_type': a.get('_segment', 'mass'),
            'activity_level': activity,
            'active_hours': list(range(7, 24)),  # 7am-11pm
            'response_delay_min': 5,
            'response_delay_max': 120,
        })

    config = {
        'simulation_id': sim_id,
        'project_id': 'psychohistory_swarm',
        'graph_id': f'swarm_{sim_id}',
        'simulation_requirement': (
            f'Population swarm simulation with {total} agents. '
            f'Testing psychohistory framework predictions via emergent mass behavior. '
            f'Event injections simulate pressure windows from engine prediction timeline.'
        ),
        'time_config': {
            'total_simulation_hours': max_rounds,
            'minutes_per_round': 60,
            'agents_per_hour_min': max(5, total // 50),
            'agents_per_hour_max': max(20, total // 10),
            'peak_hours': [12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
            'peak_activity_multiplier': 1.8,
            'off_peak_hours': [0, 1, 2, 3, 4, 5, 6],
            'off_peak_activity_multiplier': 0.15,
            'morning_hours': [7, 8, 9, 10, 11],
            'morning_activity_multiplier': 0.8,
            'work_hours': [],
            'work_activity_multiplier': 1.0,
        },
        'agent_configs': agent_configs,
        'event_config': {
            'initial_posts': initial_posts,
            'scheduled_events': [],
            'hot_topics': [
                'jobs', 'layoffs', 'automation', 'AI', 'rent', 'inflation',
                'union', 'strike', 'CBDC', 'bitcoin', 'oil', 'war',
                'Palantir', 'surveillance', 'DOGE', 'market crash',
            ],
            'narrative_direction': (
                'Structural pressure increases through escalating economic, '
                'geopolitical, and technological disruptions. Population agents '
                'respond based on their material conditions, media diets, and anxieties.'
            ),
        },
        'reddit_config': {
            'platform': 'reddit',
            'recency_weight': 0.3,
            'popularity_weight': 0.4,
            'relevance_weight': 0.3,
            'viral_threshold': 15,
            'echo_chamber_strength': 0.5,
        },
        # Store event timeline for manual injection during simulation
        '_event_timeline': {str(k): v for k, v in timeline.items() if k > 0},
        'generated_at': datetime.now().isoformat(),
    }

    config_path = os.path.join(out, 'simulation_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  Written to {config_path}")

    # ── Summary ──────────────────────────────────────────────────────────
    inflexible_count = sum(1 for a in agents if a.get('_segment', '').startswith('inflexible_'))
    mass_count = len(agents) - inflexible_count

    print(f"\n{'=' * 60}")
    print(f"POPULATION SWARM BRIDGE COMPLETE")
    print(f"{'=' * 60}")
    print(f"\n  Masses:              {mass_count}")
    print(f"  Inflexible minorities: {inflexible_count} ({inflexible_count/len(agents)*100:.1f}%)")
    print(f"  Information sources:   {len(sources)}")
    print(f"  Total agents:          {total}")
    print(f"  Event injections:      {total_events} across {len(timeline)} rounds")
    print(f"  Max rounds:            {max_rounds}")
    print(f"\nBCS ratio: {inflexible_count}/{mass_count} = {inflexible_count/mass_count*100:.1f}%")
    print(f"  (BCS threshold for consensus flip: 10-17%)")
    print(f"  {'ABOVE THRESHOLD — flip predicted' if inflexible_count/mass_count >= 0.10 else 'BELOW THRESHOLD — flip unlikely'}")
    print(f"\nOutput: {out}/")
    print(f"  agents_reddit.json     — {total} agent profiles")
    print(f"  simulation_config.json — config with event timeline")
    print(f"\nNOTE: Events for rounds 3-37 stored in config._event_timeline.")
    print(f"These must be injected during simulation via IPC or by modifying")
    print(f"the simulation runner to read scheduled events per round.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Psychohistory Population Swarm Bridge')
    parser.add_argument('--masses', type=int, default=500,
                        help='Number of mass population agents (default 500)')
    parser.add_argument('--rounds', type=int, default=50,
                        help='Max simulation rounds (default 50)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed (default 42)')
    args = parser.parse_args()

    run(total_masses=args.masses, max_rounds=args.rounds, seed=args.seed)
