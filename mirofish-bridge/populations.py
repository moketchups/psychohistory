"""
populations.py — Generate demographic population agents for swarm simulation.

Creates thousands of anonymous agents across 7 demographic segments + inflexible
minorities. Agents are regular people with short personas, varied anxieties,
different media diets, and no framework awareness.
"""

import json
import random
import csv
from typing import List, Dict
from dataclasses import dataclass, field


# ── Demographic Templates ────────────────────────────────────────────────────

CITIES_RUSTBELT = ['Detroit', 'Cleveland', 'Pittsburgh', 'Gary', 'Flint', 'Youngstown', 'Dayton', 'Toledo', 'Buffalo', 'Milwaukee']
CITIES_SUNBELT = ['Phoenix', 'Houston', 'Dallas', 'Austin', 'Atlanta', 'Tampa', 'Nashville', 'Charlotte', 'Las Vegas', 'Raleigh']
CITIES_COAST = ['New York', 'Los Angeles', 'San Francisco', 'Seattle', 'Boston', 'Portland', 'Denver', 'Miami', 'Chicago', 'Minneapolis']
CITIES_GLOBAL = ['Lagos', 'Manila', 'Mexico City', 'Jakarta', 'Dhaka', 'Karachi', 'Cairo', 'Nairobi', 'Sao Paulo', 'Lima']
CITIES_MILITARY = ['San Diego', 'Norfolk', 'Colorado Springs', 'Fayetteville', 'Killeen', 'Jacksonville', 'Honolulu', 'El Paso']

MEDIA_MAINSTREAM = ['CNN', 'MSNBC', 'NBC News', 'ABC News', 'NPR']
MEDIA_RIGHT = ['Fox News', 'Daily Wire', 'Newsmax', 'OAN']
MEDIA_ALT = ['Joe Rogan', 'Breaking Points', 'podcasts', 'Substack', 'independent YouTube']
MEDIA_SOCIAL = ['TikTok', 'Instagram', 'Twitter/X', 'Reddit', 'Facebook groups']
MEDIA_NONE = ['does not follow news closely', 'gets news from friends and family']

WORKER_JOBS = ['auto parts factory', 'warehouse fulfillment', 'retail', 'food service', 'delivery driver', 'construction', 'janitor', 'meatpacking plant', 'call center', 'hotel housekeeping']
WORKER_ANXIETIES = ['automation replacing my job', 'rent going up again', 'no health insurance', 'kids cant afford college', 'hours getting cut', 'plant closing rumors', 'new robot arms on the line', 'gig work pays less each year']

PROF_JOBS = ['lawyer', 'doctor', 'software engineer', 'marketing manager', 'accountant', 'architect', 'HR director', 'financial analyst', 'project manager', 'pharmacist']
PROF_ANXIETIES = ['AI doing my job cheaper', 'mortgage underwater', 'student loans never ending', 'cant make partner', 'credentials worth less every year', 'competing with 200 applicants per opening', 'burnout', 'kids tuition is $80K/year']

INVESTOR_TYPES = ['401k holder', 'small business owner', 'retiree on fixed income', 'day trader', 'rental property owner', 'pension fund dependent']
INVESTOR_ANXIETIES = ['market crash wiping out retirement', 'inflation eating savings', 'interest rates killing my business', 'ETF concentration risk', 'Social Security running out', 'CBDC replacing cash']

TECH_JOBS = ['ML engineer', 'startup founder', 'DevOps engineer', 'data scientist', 'product manager at FAANG', 'AI researcher', 'frontend developer', 'security engineer']
TECH_ANXIETIES = ['AI replacing developers', 'my company building something dangerous', 'stock options worthless', 'H1B visa uncertainty', 'model collapse is real', 'building surveillance tools', 'layoffs every quarter']

STUDENT_FIELDS = ['computer science', 'nursing', 'business', 'liberal arts', 'engineering', 'education', 'biology', 'communications']
STUDENT_ANXIETIES = ['$80K in debt with no job prospects', 'degree worthless by the time I graduate', 'climate catastrophe before Im 40', 'cant afford rent near campus', 'AI writing better papers than me', 'no future']

MILITARY_ROLES = ['active duty Army', 'Navy veteran', 'Marine veteran', 'Air Force active', 'National Guard', 'defense contractor', 'military spouse']
MILITARY_ANXIETIES = ['VA benefits getting cut by DOGE', 'Palantir replacing human analysts', 'deployment to Iran theater', 'drone warfare replacing boots', 'classified stuff I cant talk about', 'transition to civilian life']

GLOBAL_SOUTH_CONTEXTS = [
    'factory worker in Manila, family depends on remittances',
    'farmer outside Lagos, crop yields declining three years straight',
    'call center worker in Bangalore, handles American customer complaints',
    'street vendor in Mexico City, dollar prices affect everything',
    'textile worker in Dhaka, exports to brands I cant afford',
    'driver in Jakarta, fuel prices doubled this year',
    'teacher in Nairobi, paid in currency that keeps falling',
    'miner in DRC, cobalt for phones I dont own',
]

MBTI_WORKING = ['ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP', 'ESTP']
MBTI_PROFESSIONAL = ['INTJ', 'ENTJ', 'ISTJ', 'ESTJ', 'ENTP', 'INTP']
MBTI_INVESTOR = ['ISTJ', 'INTJ', 'ESTJ', 'ENTJ']
MBTI_TECH = ['INTJ', 'INTP', 'ENTP', 'ISTP', 'ENTJ']
MBTI_STUDENT = ['ENFP', 'INFP', 'ENTP', 'INTP', 'ISFP', 'ENFJ']
MBTI_MILITARY = ['ISTJ', 'ESTJ', 'ISTP', 'ESTP', 'ENTJ']


def _pick(lst):
    return random.choice(lst)


def _media_diet():
    """Generate a realistic media diet — most people get news from 1-2 sources."""
    primary = _pick([MEDIA_MAINSTREAM, MEDIA_RIGHT, MEDIA_ALT, MEDIA_SOCIAL, MEDIA_NONE])
    return _pick(primary)


# ── Population Generators ────────────────────────────────────────────────────

def _gen_worker(agent_id: int) -> dict:
    age = random.randint(22, 62)
    city = _pick(CITIES_RUSTBELT + CITIES_SUNBELT)
    job = _pick(WORKER_JOBS)
    years = random.randint(1, min(age - 18, 30))
    anxiety = _pick(WORKER_ANXIETIES)
    media = _media_diet()

    persona = (f"{job} worker, {city}, age {age}. {years} years in. "
               f"Gets news from {media}. Worried about {anxiety}.")

    return {
        'user_id': agent_id,
        'username': f'worker_{agent_id}',
        'name': f'Worker {agent_id}',
        'bio': f'{job} worker in {city}',
        'persona': persona,
        'karma': random.randint(50, 500),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'female']),
        'mbti': _pick(MBTI_WORKING),
        'country': 'US',
        'profession': job,
        'interested_topics': ['jobs', 'cost of living', 'unions'],
        '_segment': 'worker',
        '_activity': round(random.uniform(0.1, 0.3), 2),
    }


def _gen_professional(agent_id: int) -> dict:
    age = random.randint(28, 58)
    city = _pick(CITIES_COAST + CITIES_SUNBELT)
    job = _pick(PROF_JOBS)
    anxiety = _pick(PROF_ANXIETIES)
    media = _media_diet()

    persona = (f"{job}, {city}, age {age}. "
               f"Gets news from {media}. Worried about {anxiety}.")

    return {
        'user_id': agent_id,
        'username': f'prof_{agent_id}',
        'name': f'Professional {agent_id}',
        'bio': f'{job} in {city}',
        'persona': persona,
        'karma': random.randint(200, 2000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'female']),
        'mbti': _pick(MBTI_PROFESSIONAL),
        'country': 'US',
        'profession': job,
        'interested_topics': ['economy', 'career', 'housing'],
        '_segment': 'professional',
        '_activity': round(random.uniform(0.15, 0.35), 2),
    }


def _gen_investor(agent_id: int) -> dict:
    age = random.randint(40, 75)
    city = _pick(CITIES_COAST + CITIES_SUNBELT)
    inv_type = _pick(INVESTOR_TYPES)
    anxiety = _pick(INVESTOR_ANXIETIES)
    media = _media_diet()

    persona = (f"{inv_type}, {city}, age {age}. "
               f"Gets news from {media}. Worried about {anxiety}.")

    return {
        'user_id': agent_id,
        'username': f'inv_{agent_id}',
        'name': f'Investor {agent_id}',
        'bio': f'{inv_type} in {city}',
        'persona': persona,
        'karma': random.randint(300, 3000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'female']),
        'mbti': _pick(MBTI_INVESTOR),
        'country': 'US',
        'profession': inv_type,
        'interested_topics': ['markets', 'retirement', 'inflation'],
        '_segment': 'investor',
        '_activity': round(random.uniform(0.15, 0.35), 2),
    }


def _gen_tech(agent_id: int) -> dict:
    age = random.randint(24, 45)
    city = _pick(['San Francisco', 'Seattle', 'Austin', 'New York', 'Boston', 'Denver', 'Portland', 'Los Angeles'])
    job = _pick(TECH_JOBS)
    anxiety = _pick(TECH_ANXIETIES)
    media = _media_diet()

    persona = (f"{job}, {city}, age {age}. "
               f"Gets news from {media}. Worried about {anxiety}.")

    return {
        'user_id': agent_id,
        'username': f'tech_{agent_id}',
        'name': f'Tech {agent_id}',
        'bio': f'{job} in {city}',
        'persona': persona,
        'karma': random.randint(500, 5000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'female', 'male', 'male']),  # tech skews male
        'mbti': _pick(MBTI_TECH),
        'country': 'US',
        'profession': job,
        'interested_topics': ['AI', 'technology', 'startups'],
        '_segment': 'tech',
        '_activity': round(random.uniform(0.2, 0.4), 2),
    }


def _gen_student(agent_id: int) -> dict:
    age = random.randint(18, 26)
    city = _pick(CITIES_COAST + CITIES_SUNBELT)
    field = _pick(STUDENT_FIELDS)
    anxiety = _pick(STUDENT_ANXIETIES)

    persona = (f"{field} student, {city}, age {age}. "
               f"Gets news from {_pick(MEDIA_SOCIAL)}. Worried about {anxiety}.")

    return {
        'user_id': agent_id,
        'username': f'student_{agent_id}',
        'name': f'Student {agent_id}',
        'bio': f'{field} student in {city}',
        'persona': persona,
        'karma': random.randint(100, 1000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'female']),
        'mbti': _pick(MBTI_STUDENT),
        'country': 'US',
        'profession': f'{field} student',
        'interested_topics': ['education', 'climate', 'jobs'],
        '_segment': 'student',
        '_activity': round(random.uniform(0.2, 0.5), 2),
    }


def _gen_military(agent_id: int) -> dict:
    age = random.randint(22, 55)
    city = _pick(CITIES_MILITARY)
    role = _pick(MILITARY_ROLES)
    anxiety = _pick(MILITARY_ANXIETIES)

    persona = (f"{role}, {city}, age {age}. "
               f"Gets news from {_media_diet()}. Worried about {anxiety}.")

    return {
        'user_id': agent_id,
        'username': f'mil_{agent_id}',
        'name': f'Military {agent_id}',
        'bio': f'{role} in {city}',
        'persona': persona,
        'karma': random.randint(100, 800),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'male', 'male', 'female']),
        'mbti': _pick(MBTI_MILITARY),
        'country': 'US',
        'profession': role,
        'interested_topics': ['defense', 'veterans', 'security'],
        '_segment': 'military',
        '_activity': round(random.uniform(0.1, 0.3), 2),
    }


def _gen_global_south(agent_id: int) -> dict:
    context = _pick(GLOBAL_SOUTH_CONTEXTS)
    age = random.randint(20, 50)
    country = context.split(' in ')[-1].split(',')[0] if ' in ' in context else 'Global South'

    persona = (f"{context}, age {age}. "
               f"Sends money home. Dollar exchange rate affects everything.")

    return {
        'user_id': agent_id,
        'username': f'global_{agent_id}',
        'name': f'Global {agent_id}',
        'bio': context.split(',')[0],
        'persona': persona,
        'karma': random.randint(10, 200),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'female']),
        'mbti': _pick(MBTI_WORKING),
        'country': country,
        'profession': context.split(' in ')[0] if ' in ' in context else 'worker',
        'interested_topics': ['economy', 'remittances', 'prices'],
        '_segment': 'global_south',
        '_activity': round(random.uniform(0.05, 0.2), 2),
    }


# ── Inflexible Minorities ───────────────────────────────────────────────────

def _gen_union_organizer(agent_id: int) -> dict:
    age = random.randint(28, 55)
    city = _pick(CITIES_RUSTBELT + ['Los Angeles', 'New York', 'Chicago'])

    persona = (f"Union organizer, {city}, age {age}. Spent {random.randint(3,20)} years organizing. "
               f"Seen companies spend millions to bust unions. ALU proved Amazon can be beaten. "
               f"May 2028 UAW expiration is the countdown. The working class has power "
               f"when it acts together. Every worker deserves a union.")

    return {
        'user_id': agent_id,
        'username': f'organize_{agent_id}',
        'name': f'Organizer {agent_id}',
        'bio': f'Union organizer, {city}',
        'persona': persona,
        'karma': random.randint(1000, 5000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'female']),
        'mbti': _pick(['ENFJ', 'ENTJ', 'ESTJ', 'ESFJ']),
        'country': 'US',
        'profession': 'union organizer',
        'interested_topics': ['labor', 'unions', 'workers rights', 'strikes'],
        '_segment': 'inflexible_union',
        '_activity': round(random.uniform(0.6, 0.9), 2),
    }


def _gen_crypto_max(agent_id: int) -> dict:
    age = random.randint(22, 45)

    persona = (f"Bitcoin maximalist, age {age}. Self-custody only. Not your keys not your coins. "
               f"CBDCs are digital slavery. ETFs are a trap — BlackRock will own the escape hatch. "
               f"The only money backed by physics. Exit the system or be consumed by it.")

    return {
        'user_id': agent_id,
        'username': f'btc_{agent_id}',
        'name': f'Crypto {agent_id}',
        'bio': 'Bitcoin fixes this',
        'persona': persona,
        'karma': random.randint(2000, 10000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'male', 'male', 'female']),
        'mbti': _pick(['INTJ', 'INTP', 'ENTP', 'ENTJ']),
        'country': 'US',
        'profession': 'crypto trader',
        'interested_topics': ['bitcoin', 'CBDC', 'financial freedom', 'decentralization'],
        '_segment': 'inflexible_crypto',
        '_activity': round(random.uniform(0.5, 0.8), 2),
    }


def _gen_maga(agent_id: int) -> dict:
    age = random.randint(30, 70)
    city = _pick(CITIES_RUSTBELT + CITIES_SUNBELT + CITIES_MILITARY)

    persona = (f"Patriot, {city}, age {age}. The system is rigged against regular Americans. "
               f"Trump is fighting the deep state. Drain the swamp. "
               f"Media lies about everything. Second Amendment. God and country.")

    return {
        'user_id': agent_id,
        'username': f'patriot_{agent_id}',
        'name': f'Patriot {agent_id}',
        'bio': f'American patriot, {city}',
        'persona': persona,
        'karma': random.randint(500, 3000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'male', 'female']),
        'mbti': _pick(['ESTJ', 'ISTJ', 'ESTP', 'ESFJ']),
        'country': 'US',
        'profession': _pick(WORKER_JOBS + ['small business owner', 'contractor', 'truck driver']),
        'interested_topics': ['politics', 'freedom', 'America'],
        '_segment': 'inflexible_maga',
        '_activity': round(random.uniform(0.5, 0.8), 2),
    }


def _gen_climate(agent_id: int) -> dict:
    age = random.randint(18, 35)

    persona = (f"Climate activist, age {age}. The IPCC gives us until 2030. "
               f"Corporations produce 71% of emissions. Individual action is a distraction "
               f"from systemic change. Fossil fuel companies knew since the 1970s. "
               f"System change not climate change.")

    return {
        'user_id': agent_id,
        'username': f'climate_{agent_id}',
        'name': f'Climate {agent_id}',
        'bio': 'System change not climate change',
        'persona': persona,
        'karma': random.randint(500, 3000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['female', 'male', 'female']),
        'mbti': _pick(['ENFP', 'INFP', 'ENFJ', 'INFJ']),
        'country': 'US',
        'profession': _pick(['student', 'nonprofit worker', 'teacher', 'researcher']),
        'interested_topics': ['climate', 'environment', 'justice'],
        '_segment': 'inflexible_climate',
        '_activity': round(random.uniform(0.5, 0.7), 2),
    }


def _gen_prepper(agent_id: int) -> dict:
    age = random.randint(30, 60)

    persona = (f"Collapse-aware prepper, age {age}. Grid goes down, what do you have? "
               f"Food storage, water filtration, local network. "
               f"The system is not fixable, build your own ark. "
               f"When the supply chain breaks, communities survive, not individuals.")

    return {
        'user_id': agent_id,
        'username': f'prep_{agent_id}',
        'name': f'Prepper {agent_id}',
        'bio': 'Prepare accordingly',
        'persona': persona,
        'karma': random.randint(300, 2000),
        'created_at': '2026-03-15',
        'age': age,
        'gender': _pick(['male', 'male', 'female']),
        'mbti': _pick(['ISTJ', 'INTJ', 'ISTP', 'INTP']),
        'country': 'US',
        'profession': _pick(['contractor', 'farmer', 'IT worker', 'electrician']),
        'interested_topics': ['preparedness', 'self-sufficiency', 'grid'],
        '_segment': 'inflexible_prepper',
        '_activity': round(random.uniform(0.4, 0.7), 2),
    }


# ── Main Generator ───────────────────────────────────────────────────────────

SEGMENT_GENERATORS = {
    'worker': (_gen_worker, 0.30),
    'professional': (_gen_professional, 0.25),
    'investor': (_gen_investor, 0.15),
    'tech': (_gen_tech, 0.10),
    'student': (_gen_student, 0.10),
    'military': (_gen_military, 0.05),
    'global_south': (_gen_global_south, 0.05),
}

INFLEXIBLE_GENERATORS = {
    'union': (_gen_union_organizer, 50),
    'crypto': (_gen_crypto_max, 50),
    'maga': (_gen_maga, 50),
    'climate': (_gen_climate, 25),
    'prepper': (_gen_prepper, 25),
}


def generate_population(total_masses: int = 500,
                        inflexible_counts: Dict[str, int] = None,
                        seed: int = 42) -> List[dict]:
    """Generate the full population.

    Args:
        total_masses: Number of mass population agents
        inflexible_counts: Override inflexible minority counts (default from INFLEXIBLE_GENERATORS)
        seed: Random seed for reproducibility

    Returns: List of agent profile dicts (Reddit format)
    """
    random.seed(seed)
    agents = []
    agent_id = 0

    # Generate masses
    for segment, (gen_fn, proportion) in SEGMENT_GENERATORS.items():
        count = int(total_masses * proportion)
        for _ in range(count):
            agent = gen_fn(agent_id)
            agents.append(agent)
            agent_id += 1

    # Generate inflexible minorities
    if inflexible_counts is None:
        inflexible_counts = {k: v for k, (_, v) in INFLEXIBLE_GENERATORS.items()}

    for minority_type, count in inflexible_counts.items():
        gen_fn = INFLEXIBLE_GENERATORS[minority_type][0]
        for _ in range(count):
            agent = gen_fn(agent_id)
            agents.append(agent)
            agent_id += 1

    return agents


def build_follow_graph(agents: List[dict], source_start_id: int) -> List[str]:
    """Build follow relationships: masses follow sources, inflexible follow each other.

    Returns list of agent_id pairs as following_agentid_list strings.
    """
    source_ids = list(range(source_start_id, source_start_id + 100))  # up to 100 sources
    inflexible_ids = [a['user_id'] for a in agents if a.get('_segment', '').startswith('inflexible_')]

    for agent in agents:
        follows = []
        # Everyone follows 2-5 random sources
        n_sources = random.randint(2, min(5, len(source_ids)))
        follows.extend(random.sample(source_ids, n_sources))

        # Inflexible minorities follow each other within their group
        if agent.get('_segment', '').startswith('inflexible_'):
            same_group = [a['user_id'] for a in agents
                          if a.get('_segment') == agent['_segment'] and a['user_id'] != agent['user_id']]
            n_peers = min(10, len(same_group))
            if same_group:
                follows.extend(random.sample(same_group, n_peers))

        agent['following_agentid_list'] = json.dumps(follows)

    return agents


def write_population(agents: List[dict], path: str):
    """Write population profiles in MiroFish Reddit JSON format."""
    # Strip internal fields
    clean = []
    for a in agents:
        profile = {k: v for k, v in a.items() if not k.startswith('_')}
        if 'following_agentid_list' not in profile:
            profile['following_agentid_list'] = '[]'
        clean.append(profile)
    with open(path, 'w') as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    agents = generate_population(total_masses=500)
    print(f"Generated {len(agents)} agents")

    segments = {}
    for a in agents:
        seg = a.get('_segment', 'unknown')
        segments[seg] = segments.get(seg, 0) + 1
    for s, c in sorted(segments.items(), key=lambda x: -x[1]):
        print(f"  {s:25s} {c}")

    print(f"\nSample personas:")
    for seg in ['worker', 'professional', 'inflexible_union', 'inflexible_maga', 'inflexible_crypto']:
        for a in agents:
            if a.get('_segment') == seg:
                print(f"\n  [{seg}] {a['persona']}")
                break
