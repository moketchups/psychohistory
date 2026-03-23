"""
config.py — Constants for the psychohistory-to-MiroFish bridge.

Classification tables: org vs person, entity subtypes, agent tiers,
country/timezone mappings, framework-to-persona injections.
"""

# ── Organization vs Person ───────────────────────────────────────────────────
# Player nodes that represent organizations, institutions, coalitions, or groups
# (everything else is classified as Person)

ORG_IDS = {
    'affinity_partners', 'amazon', 'american_bitcoin', 'anthropic', 'asml_monopoly',
    'axonius', 'battelle', 'blackrock', 'brics', 'british_crown', 'bush_dynasty',
    'bytedance_tiktok', 'cfr', 'chabad', 'china', 'cia', 'city_of_london',
    'clinton_machine', 'club_rome', 'dar_global', 'darpa', 'deepmind', 'deepseek_ai',
    'democracy_now', 'doe', 'emanuels', 'eu_8ra', 'freemasonry', 'fsb',
    'goldman_sachs', 'google', 'gru_russia', 'huawei', 'india', 'iran', 'israel',
    'jesuits', 'lincoln_project', 'mega_group', 'meta', 'mistral_ai', 'mossad',
    'mp_materials', 'mss_china', 'nso_group', 'nvidia', 'openai', 'oracle',
    'orsini', 'pla_ssf', 'pnac', 'polymarket', 'rally_forge', 'rapidus', 'raw_india',
    'rosatom', 'rosgvardia', 'rothschild', 'rss', 'russia', 'samsung', 'sandia',
    'sandworm', 'sentinelone', 'seshat', 'sk_hynix', 'svr', 'talpiot',
    'tavistock', 'team8', 'tencent_wechat', 'the_intercept', 'tpusa',
    'truemed', 'tsmc_chokepoint', 'tyt', 'ufwd', 'unit8200', 'unusual_machines',
    'trumprx', 'founders_fund', 'vatican', 'wagner_africa', 'wef',
    'wellness_co', 'wiz', 'qanon',
}

# ── Entity Subtype Classification ────────────────────────────────────────────
# Maps player node IDs to one of 8 MiroFish subtypes (+ Person/Organization fallback)
# Types 1-8 are for persons, type 10 is for organizations

SUBTYPE_MAP = {
    # 1: Executive — command layer, heads of state, C-suite
    'Executive': {
        'trump', 'netanyahu', 'putin', 'xi_jinping', 'modi', 'mbs', 'orban',
        'king_charles', 'prince_william', 'pope_francis_sj', 'pope_leo_xiv',
        'arturo_sosa', 'lagarde', 'schwab', 'von_der_leyen', 'vestager',
    },
    # 2: Financier — capital allocation, fund managers, financial architects
    'Financier': {
        'kushner', 'bezos', 'adani', 'ambani', 'jensen_huang', 'satya_nadella',
        'stanley_fischer', 'lev_leviev', 'safra_catz', 'reid_hoffman',
        'romney_bain', 'sacks', 'pierce', 'carstens',
    },
    # 3: Technologist — builders of AI, compute, surveillance infrastructure
    'Technologist': {
        'musk', 'altman', 'sam_altman', 'ellison', 'thiel', 'zuckerberg',
        'karp', 'karpathy', 'lonsdale', 'sankar', 'luckey', 'schlicht',
        'kurzweil', 'harari', 'bostrom', 'nilekani', 'morris_chang',
        'bryan_johnson', 'srinivasan', 'lieber',
    },
    # 4: Intelligence — state intelligence, surveillance, cyber operations
    'Intelligence': {
        'doval', 'patrushev', 'dyumin', 'gerasimov', 'charles_flynn',
        'michael_flynn', 'pottinger', 'aquino', 'vallely',
        'epstein', 'ghislaine', 'maxwell', 'junkermann', 'craig_spence',
        'felix_sater', 'bigelow', 'grusch',
    },
    # 5: Politician — elected/appointed, kayfabe operators, managed opposition
    'Politician': {
        'vance', 'obama', 'trump_jr', 'eric_trump', 'ivanka_trump',
        'roger_stone', 'paul_manafort', 'roy_cohn', 'michael_anton',
        'virginia_giuffre', 'lincoln_project',
    },
    # 6: Media — journalists, narrative managers, alt media, influencers
    'Media': {
        'anderson_cooper', 'carlson', 'rogan', 'alex_jones', 'david_icke',
        'vedmore', 'webb', 'chen_pool', 'owens', 'mappin',
    },
    # 7: Military — defense, geopolitical theater actors
    'Military': {
        'kadyrov', 'prigozhin', 'sechin', 'kovalchuk',
        'jaishankar', 'cai_qi', 'he_lifeng', 'li_qiang', 'wang_huning',
    },
    # 8: Ideologue — framework creators, researchers, theorists, occult lineage
    'Ideologue': {
        'breshears', 'jiang', 'turchin', 'roemmele', 'alan_berman',
        'herrington', 'helbing', 'vallee', 'strassman', 'carhart_harris',
        'griffiths', 'giordano', 'yarvin', 'nick_land', 'taxil',
        'john_dee', 'blavatsky', 'eliphas_levi', 'crowley', 'parsons',
        'weishaupt', 'zevi', 'frank', 'dobruschka', 'meyer_lansky',
        'schneerson_rebbe', 'yehuda_krinsky', 'berel_lazar', 'erika_kirk',
        'benzion_netanyahu', 'matthius', 'christian_smalls', 'sean_obrien',
        'sara_nelson', 'shawn_fain',
    },
}


def get_entity_subtype(node_id: str) -> str:
    """Return the MiroFish entity subtype for a player node ID."""
    if node_id in ORG_IDS:
        return 'Organization'
    for subtype, ids in SUBTYPE_MAP.items():
        if node_id in ids:
            return subtype
    return 'Person'  # fallback for unclassified individuals


# ── Agent Tiers ──────────────────────────────────────────────────────────────
# Tier 1: always included, high activity (~40 agents)
# Tier 2: included at medium scale (~40 agents)
# Tier 3: everything else (optional for large runs)

TIER_1 = {
    # Core power nodes
    'trump', 'netanyahu', 'putin', 'xi_jinping', 'musk', 'altman', 'thiel',
    'kushner', 'mbs', 'modi', 'bezos', 'zuckerberg', 'ellison', 'sacks',
    # Key organizations
    'blackrock', 'unit8200', 'openai', 'anthropic', 'google', 'doe',
    'china', 'russia', 'iran', 'israel', 'brics',
    # Framework/research
    'breshears', 'jiang', 'roemmele', 'alan_berman', 'turchin', 'webb',
    # Key operatives
    'karp', 'vance', 'michael_flynn', 'jensen_huang',
    # Key orgs
    'chabad', 'jesuits', 'club_rome', 'freemasonry',
}

TIER_2 = {
    'trump_jr', 'eric_trump', 'ivanka_trump', 'carlson', 'rogan',
    'obama', 'clinton_machine', 'bush_dynasty', 'emanuels',
    'epstein', 'ghislaine', 'maxwell', 'felix_sater', 'roger_stone',
    'lonsdale', 'luckey', 'karpathy', 'yarvin',
    'eu_8ra', 'vatican', 'british_crown', 'city_of_london',
    'schwab', 'lagarde', 'von_der_leyen',
    'doval', 'patrushev', 'wang_huning',
    'sentinelone', 'team8', 'wiz', 'axonius', 'nso_group',
    'herrington', 'helbing', 'vallee', 'strassman',
    'alex_jones', 'david_icke', 'vedmore', 'owens',
    'carstens', 'romney_bain', 'goldman_sachs',
    'shawn_fain', 'christian_smalls', 'sara_nelson',
}


def get_tier(node_id: str) -> int:
    if node_id in TIER_1:
        return 1
    if node_id in TIER_2:
        return 2
    return 3


# ── Country / Timezone ───────────────────────────────────────────────────────

COUNTRY_MAP = {
    # US-based
    'trump': 'US', 'kushner': 'US', 'trump_jr': 'US', 'eric_trump': 'US',
    'ivanka_trump': 'US', 'musk': 'US', 'altman': 'US', 'thiel': 'US',
    'bezos': 'US', 'zuckerberg': 'US', 'ellison': 'US', 'sacks': 'US',
    'karp': 'US', 'vance': 'US', 'michael_flynn': 'US', 'obama': 'US',
    'jensen_huang': 'US', 'rogan': 'US', 'carlson': 'US', 'alex_jones': 'US',
    'roger_stone': 'US', 'epstein': 'US', 'breshears': 'US', 'alan_berman': 'US',
    'roemmele': 'US', 'webb': 'US', 'yarvin': 'US', 'luckey': 'US',
    'lonsdale': 'US', 'reid_hoffman': 'US', 'bryan_johnson': 'US',
    'grusch': 'US', 'bigelow': 'US', 'anderson_cooper': 'US',
    'shawn_fain': 'US', 'christian_smalls': 'US', 'sara_nelson': 'US',
    # Israel
    'netanyahu': 'Israel', 'unit8200': 'Israel', 'nso_group': 'Israel',
    'team8': 'Israel', 'sentinelone': 'Israel', 'wiz': 'Israel',
    'axonius': 'Israel', 'talpiot': 'Israel', 'mossad': 'Israel',
    'israel': 'Israel', 'lev_leviev': 'Israel', 'stanley_fischer': 'Israel',
    # Russia
    'putin': 'Russia', 'russia': 'Russia', 'patrushev': 'Russia',
    'dyumin': 'Russia', 'gerasimov': 'Russia', 'fsb': 'Russia',
    'svr': 'Russia', 'gru_russia': 'Russia', 'kovalchuk': 'Russia',
    'kadyrov': 'Russia', 'sechin': 'Russia', 'rosatom': 'Russia',
    'prigozhin': 'Russia', 'sandworm': 'Russia',
    # China
    'xi_jinping': 'China', 'china': 'China', 'wang_huning': 'China',
    'li_qiang': 'China', 'cai_qi': 'China', 'he_lifeng': 'China',
    'pla_ssf': 'China', 'mss_china': 'China', 'ufwd': 'China',
    'huawei': 'China', 'bytedance_tiktok': 'China', 'tencent_wechat': 'China',
    'deepseek_ai': 'China', 'jiang': 'China',
    # India
    'modi': 'India', 'india': 'India', 'doval': 'India',
    'jaishankar': 'India', 'adani': 'India', 'ambani': 'India',
    'nilekani': 'India', 'rss': 'India', 'raw_india': 'India',
    # Saudi
    'mbs': 'Saudi Arabia',
    # UK
    'british_crown': 'UK', 'city_of_london': 'UK', 'king_charles': 'UK',
    'prince_william': 'UK', 'tavistock': 'UK', 'mappin': 'UK',
    'david_icke': 'UK', 'nick_land': 'UK', 'vedmore': 'UK',
    # EU
    'eu_8ra': 'EU', 'von_der_leyen': 'Germany', 'vestager': 'Denmark',
    'lagarde': 'France', 'mistral_ai': 'France',
    # Vatican
    'vatican': 'Vatican', 'pope_francis_sj': 'Vatican', 'pope_leo_xiv': 'Vatican',
    'arturo_sosa': 'Vatican', 'jesuits': 'Vatican',
    # Hungary
    'orban': 'Hungary',
    # Taiwan/Korea/Japan
    'tsmc_chokepoint': 'Taiwan', 'morris_chang': 'Taiwan',
    'samsung': 'South Korea', 'sk_hynix': 'South Korea',
    'rapidus': 'Japan',
    # Switzerland
    'schwab': 'Switzerland', 'wef': 'Switzerland', 'carstens': 'Switzerland',
}

# UTC offsets for activity hour calculation
TIMEZONE_OFFSETS = {
    'US': -5, 'Israel': 2, 'Russia': 3, 'China': 8, 'India': 5,
    'Saudi Arabia': 3, 'UK': 0, 'EU': 1, 'Germany': 1, 'Denmark': 1,
    'France': 1, 'Vatican': 1, 'Hungary': 1, 'Taiwan': 8,
    'South Korea': 9, 'Japan': 9, 'Switzerland': 1,
}


def get_active_hours(node_id: str) -> list:
    """Return active hours (0-23 UTC) for a player based on their country."""
    country = COUNTRY_MAP.get(node_id, 'US')
    offset = TIMEZONE_OFFSETS.get(country, 0)
    # Active 7am-11pm local time
    local_hours = list(range(7, 24))
    return [(h - offset) % 24 for h in local_hours]


# ── Framework Persona Injections ─────────────────────────────────────────────
# Text appended to agent personas based on their KG edge connections to frameworks

FRAMEWORK_PERSONA = {
    'phoenix_cycle': 'Operates within a 138-year civilizational cycle framework. Interprets current events as terminal-phase indicators approaching the May 2040 reset. References historical parallels from 1764-1902 and 1902-2040 cycles.',
    'bst': 'Understands Bounded System Theory: no system can model its own source (Godel incompleteness). Sees AI recursive self-improvement as mathematically impossible. Identifies the Firmament as the resolution limit.',
    'world3_bau2': 'Tracks Club of Rome BAU2 projections: pollution-driven industrial decline beginning in the 2030s, not resource scarcity. References Herrington/KPMG validation of the World3 model.',
    'secular_cycles': 'Follows Turchin Structural-Demographic Theory: elite overproduction drives instability cycles. Monitors wealth inequality metrics, popular immiseration, and institutional fracture indicators.',
    'false_dialectic': 'Applies Jiang Predictive History framework: identifies managed opposition and false dialectics. Views political conflicts as choreographed narratives serving transnational capital.',
    'ising_model': 'Uses Ising/BCS sociophysics models: phase transitions in social consensus, inflexible minority dynamics. Calculates when 10-17% committed minorities flip flexible majorities.',
    'comp_historiography': 'References Seshat computational historiography: pattern validation across 800+ societies. Uses AI co-historian methodology for structural comparison.',
    'game_continuity': 'Tracks 380-year antinomian chain and game-theoretic continuity. Maps Cohn lineage, managed asset architecture, and institutional capture across generations.',
}


# ── MiroFish Ontology Definition ─────────────────────────────────────────────
# The 10 entity types for MiroFish ontology generation

ONTOLOGY_TYPES = [
    {
        'name': 'Executive',
        'description': 'Head of state, C-suite leader, or command-layer decision maker',
        'attributes': [
            {'name': 'domain', 'type': 'text', 'description': 'Primary domain of authority'},
            {'name': 'allegiance', 'type': 'text', 'description': 'Primary institutional allegiance'},
        ],
    },
    {
        'name': 'Financier',
        'description': 'Capital allocator, fund manager, or financial architect',
        'attributes': [
            {'name': 'aum', 'type': 'text', 'description': 'Assets under management or net worth'},
            {'name': 'vehicle', 'type': 'text', 'description': 'Primary financial vehicle or fund'},
        ],
    },
    {
        'name': 'Technologist',
        'description': 'Builder of AI, compute, surveillance, or digital infrastructure',
        'attributes': [
            {'name': 'platform', 'type': 'text', 'description': 'Primary technology platform'},
            {'name': 'stack_role', 'type': 'text', 'description': 'Role in the technology stack'},
        ],
    },
    {
        'name': 'Intelligence',
        'description': 'State intelligence officer, surveillance operator, or covert operative',
        'attributes': [
            {'name': 'agency', 'type': 'text', 'description': 'Intelligence agency or network affiliation'},
        ],
    },
    {
        'name': 'Politician',
        'description': 'Elected or appointed political figure, managed opposition operator',
        'attributes': [
            {'name': 'office', 'type': 'text', 'description': 'Current or former political office'},
        ],
    },
    {
        'name': 'Media',
        'description': 'Journalist, media personality, narrative manager, or influencer',
        'attributes': [
            {'name': 'platform', 'type': 'text', 'description': 'Primary media platform'},
            {'name': 'audience_tier', 'type': 'text', 'description': 'Audience size tier'},
        ],
    },
    {
        'name': 'Military',
        'description': 'Military commander, defense official, or geopolitical theater actor',
        'attributes': [
            {'name': 'theater', 'type': 'text', 'description': 'Primary theater of operations'},
        ],
    },
    {
        'name': 'Ideologue',
        'description': 'Framework creator, researcher, theorist, or intellectual architect',
        'attributes': [
            {'name': 'framework', 'type': 'text', 'description': 'Primary analytical framework or theory'},
            {'name': 'tier', 'type': 'text', 'description': 'Source confidence tier (1-4)'},
        ],
    },
    {
        'name': 'Person',
        'description': 'Individual actor not fitting other categories',
        'attributes': [
            {'name': 'role_desc', 'type': 'text', 'description': 'Primary functional role'},
        ],
    },
    {
        'name': 'Organization',
        'description': 'Institution, corporation, coalition, government, or collective entity',
        'attributes': [
            {'name': 'org_type', 'type': 'text', 'description': 'Type of organization'},
            {'name': 'jurisdiction', 'type': 'text', 'description': 'Primary jurisdiction or headquarters'},
        ],
    },
]

# Edge types for MiroFish ontology (mapped from psychohistory relationship types)
ONTOLOGY_EDGES = [
    {'name': 'CONTROLS', 'description': 'Direct authority, ownership, or command', 'source_targets': []},
    {'name': 'FEEDS', 'description': 'Supplies, enables, or provides resources to', 'source_targets': []},
    {'name': 'THREATENS', 'description': 'Poses risk, danger, or opposition to', 'source_targets': []},
    {'name': 'ENABLES', 'description': 'Makes possible or provides prerequisite for', 'source_targets': []},
    {'name': 'VALIDATES', 'description': 'Provides evidence or confirmation for', 'source_targets': []},
    {'name': 'CONNECTS', 'description': 'Structural link, alliance, or relationship', 'source_targets': []},
    {'name': 'CREATED', 'description': 'Founded, originated, or brought into existence', 'source_targets': []},
    {'name': 'PREDICTS', 'description': 'Forecasts or projects future outcome', 'source_targets': []},
    {'name': 'OPPOSES', 'description': 'Works against or counters', 'source_targets': []},
    {'name': 'INSTANTIATED_BY', 'description': 'Manifested or realized through', 'source_targets': []},
]
