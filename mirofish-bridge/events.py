"""
events.py — Event injection timeline for population swarm simulation.

Converts psychohistory pressure windows and predictions into a round-by-round
schedule of scripted posts from information source bots.
"""

from typing import List, Dict


# ── Event Timeline ───────────────────────────────────────────────────────────
# Round ranges map to simulation phases:
#   0-10:  Baseline (normal information flow)
#   11-20: W1 Saturn-Neptune (current pressure window)
#   21-30: Escalation (2027 structural breach approaching)
#   31-40: Crisis (2032-level stress compressed)
#   41-50: Resolution (no new events, swarm settles)

# Source type → agent username prefix mapping
# These must match source agent usernames from sources.py
SOURCE_MAP = {
    'msm': ['cnn', 'nbc_news', 'reuters', 'ap_news', 'bloomberg'],
    'alt': ['independentjournal', 'deepstatewatch', 'laborbeat', 'collapswatch', 'geopoliticalwire'],
    'data': ['marketdata', 'laborstats', 'inflationtracker', 'commoditywatch', 'vixalert'],
    'gov': ['whitehouse_feed', 'pentagon_brief', 'fedreserve_stmt', 'doe_update'],
    'acad': ['sciencedaily', 'airesearch', 'econstudies'],
    'noise': ['truthseeker99', 'nwo_watch', 'qpatriotnews'],
}


def generate_event_timeline(source_agents: List[dict]) -> Dict[int, List[dict]]:
    """Generate round-by-round event injection schedule.

    Returns: dict mapping round_number -> list of {agent_id, content} posts
    """
    # Build lookup: username -> agent_id
    username_to_id = {a['username']: a['user_id'] for a in source_agents}

    def _find_source(source_type: str, index: int = 0) -> int:
        """Find agent_id for a source type."""
        candidates = SOURCE_MAP.get(source_type, [])
        if index < len(candidates):
            return username_to_id.get(candidates[index], candidates[index])
        return username_to_id.get(candidates[0], 0)

    timeline = {}

    # ── PHASE 1: BASELINE (Rounds 0-10) ──────────────────────────────────
    # Normal information flow — establish baseline sentiment

    timeline[0] = [
        {'agent_id': _find_source('msm', 0), 'content': 'Markets open steady. S&P 500 holding near all-time highs. Federal Reserve signals patience on rate cuts. Consumer confidence at 14-month high.'},
        {'agent_id': _find_source('msm', 1), 'content': 'Tech sector continues AI investment boom. Nvidia reports record quarterly revenue. Hiring accelerates in AI-adjacent roles.'},
        {'agent_id': _find_source('data', 0), 'content': 'Market snapshot: S&P 500 5,180 (+0.3%), Oil $78.40, Gold $2,340, BTC $67,200, VIX 13.8, 10Y Treasury 4.22%'},
        {'agent_id': _find_source('data', 1), 'content': 'BLS Jobs Report: 275K added, unemployment 3.9%. But: 60% are part-time or gig. Real wages flat for 18th consecutive month.'},
        {'agent_id': _find_source('alt', 0), 'content': 'BlackRock IBIT now holds more Bitcoin than Satoshi. Think about what that means for "decentralization."'},
        {'agent_id': _find_source('noise', 0), 'content': 'They just passed another spending bill at 3am. Nobody read it. $1.2 trillion. Where does the money actually go?'},
    ]

    timeline[3] = [
        {'agent_id': _find_source('msm', 2), 'content': 'AI productivity gains could add $4.4 trillion to global GDP annually, McKinsey reports. Businesses accelerating adoption.'},
        {'agent_id': _find_source('alt', 1), 'content': 'Palantir awarded $480M Army contract for battlefield AI. Now embedded in IRS, DHS, ICE, and 5 of 6 military branches. At what point is this not a company but a government?'},
        {'agent_id': _find_source('data', 2), 'content': 'CPI 3.4% YoY. Shelter costs +5.7%. Grocery +4.2%. Real wages: -0.3% after inflation adjustment. 63% of Americans living paycheck to paycheck.'},
    ]

    timeline[6] = [
        {'agent_id': _find_source('data', 1), 'content': 'NLRB union election petitions up 53% YoY. Win rate: 81.9%. Largest organizing wave since 1935.'},
        {'agent_id': _find_source('msm', 3), 'content': 'Federal Reserve holds rates steady. Chair signals cuts likely in second half of year if inflation continues moderating.'},
        {'agent_id': _find_source('alt', 2), 'content': 'Amazon spent $4.3M on anti-union consultants at single warehouse. $9,000/day per interrogator. And they still lost. Workers won.'},
    ]

    timeline[9] = [
        {'agent_id': _find_source('data', 0), 'content': 'Market snapshot: S&P 500 5,210 (+0.6%), Oil $81.20, Gold $2,380, BTC $69,400, VIX 14.2, 10Y 4.18%'},
        {'agent_id': _find_source('gov', 0), 'content': 'Executive Order on AI Safety: federal agencies required to conduct risk assessments before deploying AI systems. Compliance deadline: 180 days.'},
        {'agent_id': _find_source('acad', 0), 'content': 'New study: 300M jobs globally exposed to AI automation. 12M US workers will need to transition occupations by 2030. Most affected: administrative, legal, financial services.'},
    ]

    # ── PHASE 2: W1 SATURN-NEPTUNE (Rounds 11-20) ───────────────────────
    # Pressure window activates. Real events from psychohistory engine.

    timeline[11] = [
        {'agent_id': _find_source('msm', 0), 'content': 'BREAKING: Iran conflict escalates as Khamenei assassination confirmed. Regional tensions surge. Oil futures spike 12% overnight.'},
        {'agent_id': _find_source('data', 3), 'content': 'COMMODITY ALERT: Oil $93.11, up from $78 two weeks ago. Goldman forecasts $100+ March average. Energy stocks surging. Consumer impact within 30 days.'},
        {'agent_id': _find_source('data', 4), 'content': 'VIX spikes to 25.54 from 14.2 baseline. Largest single-week volatility jump since March 2020.'},
        {'agent_id': _find_source('alt', 3), 'content': 'Four of six engine watchlist items triggered in single pressure window: Iran escalation, oil shock, Morgan Stanley redemption limits, UK recession signal.'},
        {'agent_id': _find_source('gov', 1), 'content': 'Pentagon activates additional carrier group to Eastern Mediterranean. Operation Absolute Resolve enters third week.'},
    ]

    timeline[13] = [
        {'agent_id': _find_source('msm', 1), 'content': 'Morgan Stanley limits redemptions from $3.4B private credit fund. Spokesperson: "prudent liquidity management." Investors unable to withdraw funds.'},
        {'agent_id': _find_source('data', 2), 'content': 'UK GDP contracts 0.3%. Official recession. Oil shock identified as primary driver. European markets down 4.2% this week.'},
        {'agent_id': _find_source('msm', 4), 'content': 'Palantir awarded $1B DHS contract. Stock surges 9%. Company now largest technology vendor to US government.'},
        {'agent_id': _find_source('alt', 0), 'content': 'Palantir DHS deal means a single company now provides the data infrastructure for tax collection, border enforcement, military targeting, AND intelligence analysis. One vendor. All state functions.'},
    ]

    timeline[15] = [
        {'agent_id': _find_source('data', 0), 'content': 'Market snapshot: S&P 500 4,880 (-6.3% from peak), Oil $97.40, Gold $2,520, BTC $58,200 (-16%), VIX 28.7, 10Y 4.45%'},
        {'agent_id': _find_source('msm', 2), 'content': 'Gas prices hit $4.80 national average. Trucking costs up 15%. Walmart warns of price increases across all categories within 60 days.'},
        {'agent_id': _find_source('alt', 4), 'content': 'US-Venezuela diplomatic relations restored same week as Iran escalation. Donroe Doctrine in action: hemispheric resource monopolization while Middle East burns.'},
        {'agent_id': _find_source('noise', 1), 'content': 'Oil shock, bank freezes, surveillance contracts, carrier groups deployed. And the stock market is the thing they want you watching. What are they building while youre distracted?'},
    ]

    timeline[18] = [
        {'agent_id': _find_source('data', 1), 'content': 'Weekly jobless claims: 285K, highest since January 2022. Manufacturing sector: 42K layoffs announced this month. Trucking bankruptcies up 31% YoY.'},
        {'agent_id': _find_source('msm', 0), 'content': 'Federal Reserve emergency statement: "Monitoring developments closely. Prepared to act as conditions warrant." No rate change yet.'},
        {'agent_id': _find_source('alt', 1), 'content': 'DOGE identifies $55B in "redundant" federal spending. IRS mega API will centralize all taxpayer data into single cloud platform. Career IRS technologists placed on administrative leave.'},
        {'agent_id': _find_source('gov', 0), 'content': 'Executive Order establishes AI/Nuclear consortium with DOE national laboratories. Genesis Mission framework for "self-sustaining compute infrastructure powered by small modular reactors."'},
    ]

    # ── PHASE 3: ESCALATION (Rounds 21-30) ───────────────────────────────
    # Structural breach becoming visible. 2027 predictions compressed.

    timeline[21] = [
        {'agent_id': _find_source('msm', 1), 'content': 'Three regional banks announce simultaneous withdrawal restrictions. FDIC issues statement: "Banking system remains sound." Markets disagree — KBW Bank Index down 18%.'},
        {'agent_id': _find_source('data', 0), 'content': 'Market snapshot: S&P 500 4,520 (-13% from peak), Oil $108, Gold $2,710, BTC $45,800 (-34%), VIX 38.2, 10Y 4.72%'},
        {'agent_id': _find_source('alt', 0), 'content': 'The same three firms that own 88% of S&P 500 companies also own the banks restricting withdrawals, the media reporting on it, and the platforms you are reading this on.'},
    ]

    timeline[24] = [
        {'agent_id': _find_source('data', 1), 'content': 'UNEMPLOYMENT ALERT: Claims surge to 340K weekly. Manufacturing: -89K jobs this quarter. AI displacement identified as primary factor in 40% of layoffs.'},
        {'agent_id': _find_source('acad', 2), 'content': 'IMF downgrades global growth forecast by 1.2%. Cites "cascading supply chain disruptions" and "unprecedented pace of labor market restructuring due to AI adoption."'},
        {'agent_id': _find_source('msm', 3), 'content': 'UAW president announces all contracts to expire simultaneously May 2028. "We are preparing the biggest coordinated labor action in American history."'},
        {'agent_id': _find_source('alt', 2), 'content': 'UAW May 2028 simultaneous expiration is not a negotiating tactic. Its a countdown. 306,800 workers struck last year. NLRB win rate 81.9%. They are not asking permission.'},
    ]

    timeline[27] = [
        {'agent_id': _find_source('gov', 2), 'content': 'Federal Reserve cuts rates 50 basis points in emergency session. "Economic conditions have deteriorated more rapidly than models projected."'},
        {'agent_id': _find_source('data', 3), 'content': 'Oil breaks $115. Gas national average $5.60. Airlines canceling routes. Trucking companies filing Chapter 11 at record pace.'},
        {'agent_id': _find_source('msm', 0), 'content': 'BREAKING: Major AI system produces fabricated evidence in federal court case. Judge declares mistrial. Calls into question all AI-assisted legal filings nationwide.'},
        {'agent_id': _find_source('acad', 1), 'content': 'Nature paper: "Evidence of systematic quality degradation in large language models trained on AI-generated content." Authors call it "model collapse" and warn it may be irreversible.'},
    ]

    # ── PHASE 4: CRISIS (Rounds 31-40) ───────────────────────────────────
    # 2032-level stress compressed. Multiple systems failing simultaneously.

    timeline[31] = [
        {'agent_id': _find_source('msm', 4), 'content': 'Bitcoin ETF sees largest single-day outflow in history: $12B withdrawn. BlackRock IBIT fund pauses new subscriptions. Crypto exchanges report 4-hour withdrawal delays.'},
        {'agent_id': _find_source('gov', 0), 'content': 'White House announces CBDC pilot program for federal benefits. Social Security, veterans benefits, federal employee salaries to be distributed via digital dollar starting Q3.'},
        {'agent_id': _find_source('data', 0), 'content': 'Market snapshot: S&P 500 4,100 (-21% from peak, bear market), Oil $122, Gold $2,950, BTC $31,400 (-55%), VIX 45.8, 10Y 5.01%'},
        {'agent_id': _find_source('alt', 3), 'content': 'CBDC for federal benefits. Programmable money. Expiration dates on your paycheck. Geographic restrictions on your spending. Negative interest rates on your savings. This is not a pilot. This is the architecture.'},
    ]

    timeline[34] = [
        {'agent_id': _find_source('data', 1), 'content': 'AI DISPLACEMENT: 2.1M jobs eliminated this year, up 400% YoY. Hardest hit: legal assistants (-45%), customer service (-38%), data entry (-62%), junior accounting (-41%).'},
        {'agent_id': _find_source('msm', 2), 'content': 'Nationwide logistics disruption as trucking industry loses 18% of workforce. Empty shelves reported in 12 major metro areas. National Guard deployed to three distribution centers.'},
        {'agent_id': _find_source('alt', 2), 'content': 'UAW, Teamsters, SEIU announce joint solidarity action. 4.2M workers prepared for coordinated strike. Largest potential labor action since 1946 general strikes.'},
        {'agent_id': _find_source('noise', 2), 'content': 'The plan was always this. Crash the economy, blame the workers, deploy the robots, announce the digital dollar, and tell you its for your own good. Wake up.'},
    ]

    timeline[37] = [
        {'agent_id': _find_source('msm', 0), 'content': 'Federal Reserve announces unlimited QE. "We will do whatever it takes." Markets rally 4% on announcement, then give it all back by close.'},
        {'agent_id': _find_source('data', 2), 'content': 'INFLATION: CPI 7.8% YoY. Food +12.4%. Shelter +9.1%. Energy +22.3%. Real wages: -4.6%. Purchasing power at 2019 levels despite higher nominal wages.'},
        {'agent_id': _find_source('gov', 3), 'content': 'DOE announces "Genesis Compute Initiative": 6 national laboratories to host AI data centers powered by small modular reactors. $18B initial allocation. "Self-sustaining critical infrastructure."'},
        {'agent_id': _find_source('acad', 0), 'content': 'Study: trust in institutions at all-time low. Congress 8%, media 11%, banks 14%, tech companies 19%. Only military (52%) and local community organizations (61%) retain majority trust.'},
    ]

    # ── PHASE 5: RESOLUTION (Rounds 41-50) ───────────────────────────────
    # No new events. Let the swarm settle. Measure final state.
    # (No entries — silence is the test)

    return timeline


def timeline_to_initial_posts(timeline: Dict[int, List[dict]], round_num: int = 0) -> List[dict]:
    """Extract posts for a specific round as MiroFish initial_posts format."""
    posts = timeline.get(round_num, [])
    return [{'poster_agent_id': p['agent_id'], 'content': p['content'], 'poster_type': 'Organization'} for p in posts]


if __name__ == '__main__':
    from sources import generate_sources
    sources = generate_sources()
    timeline = generate_event_timeline(sources)

    total_events = sum(len(v) for v in timeline.values())
    print(f"Total events: {total_events} across {len(timeline)} rounds")
    for rnd in sorted(timeline.keys()):
        print(f"  Round {rnd:2d}: {len(timeline[rnd])} events")

    print(f"\nSample (Round 11):")
    for post in timeline.get(11, []):
        src = next((s['name'] for s in sources if s['user_id'] == post['agent_id']), '?')
        print(f"  [{src}] {post['content'][:100]}...")
