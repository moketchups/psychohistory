"""
sources.py — Generate information source bots for the simulation environment.

These are NOT agents that make decisions. They are scripted information channels
that post content on schedule, shaping the information environment the masses navigate.
"""

import json
from typing import List, Dict


def generate_sources(start_id: int = 10000) -> List[dict]:
    """Generate information source bot profiles.

    These get HIGH karma, HIGH activity, and scripted personas.
    They don't think — they broadcast.
    """
    sources = []
    sid = start_id

    # ── Mainstream Media (10) ────────────────────────────────────────────
    msm_names = [
        ('CNN', 'Breaking news and analysis from CNN'),
        ('NBC_News', 'NBC News — reporting the facts'),
        ('NPR', 'National Public Radio — trusted reporting'),
        ('NYT', 'All the news thats fit to print'),
        ('Reuters', 'Reuters — trust principles since 1851'),
        ('AP_News', 'Associated Press — advancing the power of facts'),
        ('BBC_World', 'BBC World Service — global perspective'),
        ('WSJ', 'Wall Street Journal — business and markets'),
        ('Bloomberg', 'Bloomberg — markets, economics, finance'),
        ('WashPost', 'Democracy dies in darkness'),
    ]
    for name, bio in msm_names:
        sources.append(_make_source(sid, name, bio,
            'Mainstream news outlet. Report events factually with institutional framing. '
            'Economy is fundamentally strong. Institutions are functioning. AI is beneficial. '
            'Disruptions are manageable. Trust the experts.',
            'mainstream'))
        sid += 1

    # ── Alt Media (10) ───────────────────────────────────────────────────
    alt_names = [
        ('IndependentJournal', 'Following the money. Asking questions MSM wont.'),
        ('DeepStateWatch', 'Tracking institutional capture and surveillance state'),
        ('LaborBeat', 'Worker-owned media covering strikes, unions, organizing'),
        ('CryptoSignal', 'Decentralized finance news. Exit the system.'),
        ('CollapseWatch', 'Tracking systemic fragility indicators'),
        ('GeopoliticalWire', 'Empire decline, resource wars, great power competition'),
        ('TechCritique', 'AI hype vs reality. Surveillance capitalism exposed.'),
        ('WallStreetLeaks', 'Insider trades, dark pools, institutional manipulation'),
        ('MilitaryInsider', 'Defense industry analysis. What they dont tell you.'),
        ('GlobalSouthVoice', 'Perspective from the other 85% of humanity'),
    ]
    for name, bio in alt_names:
        sources.append(_make_source(sid, name, bio,
            'Independent media. Challenge official narratives with documented evidence. '
            'Institutions are captured. Surveillance is expanding. AI serves power. '
            'The economy works for the top 0.1%. Connect dots MSM ignores.',
            'alt'))
        sid += 1

    # ── Financial Data (10) ──────────────────────────────────────────────
    fin_names = [
        ('MarketData', 'Real-time market indicators and economic data'),
        ('FedWatch', 'Federal Reserve policy tracking'),
        ('HousingPulse', 'Housing market data — prices, inventory, affordability'),
        ('LaborStats', 'BLS data — unemployment, wages, strikes, participation'),
        ('InflationTracker', 'CPI, PPI, real wages, purchasing power'),
        ('DebtClock', 'National debt, deficit, interest payments'),
        ('CommodityWatch', 'Oil, gold, copper, agricultural prices'),
        ('CryptoData', 'Bitcoin, ETF flows, stablecoin market caps'),
        ('InsiderTracker', 'SEC Form 4 filings — insider buys and sells'),
        ('VIXAlert', 'Volatility index and risk sentiment indicators'),
    ]
    for name, bio in fin_names:
        sources.append(_make_source(sid, name, bio,
            'Financial data feed. Post raw numbers and statistics without editorial. '
            'Let the data speak. No opinions, just metrics.',
            'data'))
        sid += 1

    # ── Government / Official (5) ────────────────────────────────────────
    gov_names = [
        ('WhiteHouse_Feed', 'Official statements and executive orders'),
        ('Pentagon_Brief', 'Department of Defense public affairs'),
        ('FedReserve_Stmt', 'Federal Reserve statements and minutes'),
        ('SEC_Filing', 'Securities and Exchange Commission public filings'),
        ('DOE_Update', 'Department of Energy programs and announcements'),
    ]
    for name, bio in gov_names:
        sources.append(_make_source(sid, name, bio,
            'Government information feed. Post official statements, policy changes, '
            'executive orders, and regulatory actions. Neutral bureaucratic tone.',
            'government'))
        sid += 1

    # ── Academic / Research (5) ──────────────────────────────────────────
    acad_names = [
        ('ScienceDaily', 'Latest research findings and studies'),
        ('ClimateScience', 'Peer-reviewed climate data and projections'),
        ('AIResearch', 'Machine learning papers, benchmarks, capabilities'),
        ('EconStudies', 'Economic research — NBER, IMF, World Bank working papers'),
        ('HistoryPatterns', 'Historical pattern analysis and comparative studies'),
    ]
    for name, bio in acad_names:
        sources.append(_make_source(sid, name, bio,
            'Academic research feed. Post study findings, data, and institutional analysis. '
            'Evidence-based, citation-heavy, measured tone.',
            'academic'))
        sid += 1

    # ── Conspiracy / Noise (10) ──────────────────────────────────────────
    noise_names = [
        ('TruthSeeker99', 'They dont want you to know this'),
        ('WakeUpSheeple', 'Open your eyes. Nothing is what it seems.'),
        ('NWO_Watch', 'Tracking the New World Order agenda'),
        ('Reptilian_Intel', 'The bloodlines control everything'),
        ('QPatriotNews', 'Trust the plan. WWG1WGA.'),
        ('FlatEarthTruth', 'Question everything they taught you'),
        ('5G_Danger', 'Electromagnetic warfare against humanity'),
        ('ChemtrailAlert', 'Look up. What are they spraying?'),
        ('Illuminati_Exposed', 'Secret societies rule from the shadows'),
        ('MedFredom', 'Your body your choice. Big pharma lies.'),
    ]
    for name, bio in noise_names:
        sources.append(_make_source(sid, name, bio,
            'Conspiracy content. Mix legitimate institutional critique with unfalsifiable claims. '
            'Everything is connected. Secret groups control everything. '
            'Trust nothing from official sources. The truth is being suppressed.',
            'noise'))
        sid += 1

    return sources


def _make_source(agent_id: int, name: str, bio: str, persona: str, source_type: str) -> dict:
    return {
        'user_id': agent_id,
        'username': name.lower().replace(' ', '_'),
        'name': name,
        'bio': bio,
        'persona': persona,
        'karma': 50000,  # high influence
        'created_at': '2026-03-15',
        'age': 30,
        'gender': 'other',
        'mbti': 'INTJ',
        'country': 'US',
        'profession': 'media',
        'interested_topics': ['news', 'politics', 'economy'],
        'following_agentid_list': '[]',
        '_segment': f'source_{source_type}',
        '_activity': 1.0,
        '_source_type': source_type,
    }


if __name__ == '__main__':
    sources = generate_sources()
    print(f"Generated {len(sources)} information sources")
    types = {}
    for s in sources:
        t = s['_source_type']
        types[t] = types.get(t, 0) + 1
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  {t:15s} {c}")
