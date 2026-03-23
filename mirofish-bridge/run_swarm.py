"""
run_swarm.py — Custom simulation runner for psychohistory population swarm.

Wraps MiroFish's Reddit simulation with event injection at specific rounds.
Reads _event_timeline from simulation_config.json and injects ManualActions
for information source bots at scheduled rounds.
"""

import asyncio
import json
import os
import sys
import signal

# Add MiroFish backend to path
MIROFISH_BACKEND = '/Users/jamienucho/MiroFish/backend'
sys.path.insert(0, MIROFISH_BACKEND)
sys.path.insert(0, os.path.join(MIROFISH_BACKEND, 'scripts'))

# Load env before importing oasis
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(MIROFISH_BACKEND), '.env'))

import oasis
from oasis import LLMAction, ManualAction
from oasis.social_platform.typing import ActionType

from action_logger import PlatformActionLogger
from datetime import datetime
from camel.models import ModelFactory
from camel.types.enums import ModelPlatformType


async def run_swarm(config_path: str, max_rounds: int = 50):
    """Run the population swarm simulation with event injection."""

    with open(config_path) as f:
        config = json.load(f)

    sim_dir = os.path.dirname(config_path)

    # Load agent profiles
    profiles_path = os.path.join(sim_dir, 'reddit_profiles.json')
    with open(profiles_path) as f:
        profiles = json.load(f)

    # Build mapping: original user_id -> OASIS sequential index
    # OASIS assigns agent IDs 0..N-1 based on array position, ignoring user_id
    uid_to_oasis = {}
    for idx, p in enumerate(profiles):
        uid_to_oasis[p['user_id']] = idx

    # Load event timeline and remap agent_ids to OASIS IDs
    event_timeline = {}
    for k, v in config.get('_event_timeline', {}).items():
        remapped = []
        for event in v:
            oasis_id = uid_to_oasis.get(event['agent_id'])
            if oasis_id is not None:
                remapped.append({**event, 'agent_id': oasis_id})
        event_timeline[int(k)] = remapped

    # Also remap initial_posts
    raw_initial = config.get('event_config', {}).get('initial_posts', [])
    remapped_initial = []
    for post in raw_initial:
        oasis_id = uid_to_oasis.get(post['poster_agent_id'])
        if oasis_id is not None:
            remapped_initial.append({**post, 'poster_agent_id': oasis_id})
    config.setdefault('event_config', {})['initial_posts'] = remapped_initial

    print(f"{'=' * 60}")
    print(f"PSYCHOHISTORY POPULATION SWARM SIMULATION")
    print(f"{'=' * 60}")
    print(f"Agents: {len(profiles)}")
    print(f"Max rounds: {max_rounds}")
    print(f"Scheduled events: {sum(len(v) for v in event_timeline.values())} across {len(event_timeline)} rounds")
    print(f"{'=' * 60}")

    # Create LLM model
    llm_api_key = os.environ.get('LLM_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
    llm_base_url = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    llm_model_name = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')

    print(f"LLM: {llm_model_name} @ {llm_base_url}")

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=llm_model_name,
        api_key=llm_api_key,
        url=llm_base_url,
    )

    # Setup database
    db_path = os.path.join(sim_dir, 'reddit_simulation.db')
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create OASIS environment (same pattern as MiroFish run_reddit_simulation.py:577)
    from oasis.social_agent.agents_generator import generate_reddit_agent_graph

    agent_graph = await generate_reddit_agent_graph(
        profile_path=profiles_path,
        model=model,
    )

    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
        semaphore=30,
    )
    await env.reset()

    # Setup logger
    reddit_dir = os.path.join(sim_dir, 'reddit')
    os.makedirs(reddit_dir, exist_ok=True)
    logger = PlatformActionLogger(reddit_dir, 'reddit')

    logger.log_simulation_start({'total_rounds': max_rounds, 'agents_count': len(profiles), 'platform': 'reddit'})

    # Agent config lookup
    agent_configs = {c['agent_id']: c for c in config.get('agent_configs', [])}
    time_config = config.get('time_config', {})
    peak_hours = set(time_config.get('peak_hours', []))
    off_peak_hours = set(time_config.get('off_peak_hours', []))
    peak_mult = time_config.get('peak_activity_multiplier', 1.5)
    off_peak_mult = time_config.get('off_peak_activity_multiplier', 0.2)

    # ── Initial Posts (Round 0) ──────────────────────────────────────────
    initial_posts = config.get('event_config', {}).get('initial_posts', [])
    if initial_posts:
        print(f"\nInjecting {len(initial_posts)} initial posts...")
        init_actions = {}
        for post in initial_posts:
            agent_id = post['poster_agent_id']
            agent = agent_graph.get_agent(agent_id)
            if agent:
                init_actions[agent] = ManualAction(
                    action_type=ActionType.CREATE_POST,
                    action_args={'content': post['content']}
                )
        if init_actions:
            await env.step(init_actions)
            for agent, action in init_actions.items():
                logger.log_action(0, agent.agent_id, getattr(agent, 'name', f'Agent_{agent.agent_id}'),
                                  'CREATE_POST', action.action_args, None, True)
        logger.log_round_end(0, len(init_actions))

    # ── Main Simulation Loop ─────────────────────────────────────────────
    print(f"\nStarting simulation loop...")
    start_time = datetime.now()
    import random

    for round_num in range(1, max_rounds + 1):
        simulated_hour = round_num % 24
        round_actions = {}

        # Inject scheduled events for this round
        if round_num in event_timeline:
            events = event_timeline[round_num]
            print(f"\n  >>> INJECTING {len(events)} events at round {round_num} <<<")
            for event in events:
                agent_id = event['agent_id']
                agent = agent_graph.get_agent(agent_id)
                if agent:
                    round_actions[agent] = ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={'content': event['content']}
                    )
                    logger.log_action(round_num, agent_id,
                                      getattr(agent, 'name', f'Source_{agent_id}'),
                                      'CREATE_POST', {'content': event['content']},
                                      None, True)

        # Select active agents for this round
        if simulated_hour in peak_hours:
            multiplier = peak_mult
        elif simulated_hour in off_peak_hours:
            multiplier = off_peak_mult
        else:
            multiplier = 1.0

        min_agents = int(time_config.get('agents_per_hour_min', 5) * multiplier)
        max_agents = int(time_config.get('agents_per_hour_max', 20) * multiplier)
        target = random.randint(min_agents, max_agents)

        # Filter to agents active this hour, apply activity_level probability
        candidates = []
        all_agents = agent_graph.get_agents()
        for agent_id, agent in all_agents:
            ac = agent_configs.get(agent_id, {})
            active_hours = ac.get('active_hours', list(range(7, 24)))
            activity_level = ac.get('activity_level', 0.3)
            if simulated_hour in active_hours and random.random() < activity_level:
                candidates.append((agent_id, agent))

        # Sample from candidates
        selected = random.sample(candidates, min(target, len(candidates)))

        for agent_id, agent in selected:
            if agent not in round_actions:  # don't overwrite event injections
                round_actions[agent] = LLMAction()

        if round_actions:
            results = await env.step(round_actions)

            # Log LLM actions (results returned from step)
            action_count = len(round_actions)
            logger.log_round_end(round_num, action_count)

        # Progress
        if round_num % 5 == 0 or round_num == 1:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  Round {round_num}/{max_rounds} "
                  f"({round_num/max_rounds*100:.0f}%) "
                  f"- {len(round_actions)} actions "
                  f"- hour {simulated_hour:02d} "
                  f"- {elapsed:.0f}s elapsed")

    total_elapsed = (datetime.now() - start_time).total_seconds()
    logger.log_simulation_end(max_rounds, 0)  # total_actions counted from log

    print(f"\n{'=' * 60}")
    print(f"SIMULATION COMPLETE")
    print(f"  Rounds: {max_rounds}")
    print(f"  Elapsed: {total_elapsed:.0f}s")
    print(f"  Actions log: {reddit_dir}/actions.jsonl")
    print(f"  Database: {db_path}")
    print(f"{'=' * 60}")

    # Cleanup
    await reddit_platform.stop()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Psychohistory Population Swarm Simulation')
    parser.add_argument('--config', required=True, help='Path to simulation_config.json')
    parser.add_argument('--max-rounds', type=int, default=50, help='Max rounds (default 50)')
    args = parser.parse_args()

    asyncio.run(run_swarm(args.config, args.max_rounds))
