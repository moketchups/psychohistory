#!/usr/bin/env python3
"""
Psychohistory Prediction Engine — Real-Time Data Ingestion Pipeline

Pulls current events from multiple sources and maps them against:
- 5 pressure windows (engine dates)
- WHO (player mentions)
- WHERE (theater mentions)
- WHY (incentive signals — financial, energy, tech, military)

Sources:
  Layer 1.5 — Capital flow intelligence (free public data):
    SEC EDGAR Form 4 (insider buys/sells), House financial disclosures
    (congressional trades), FINRA daily short sale volume
  Layer 2 — Managed data collection:
    Tavily (deep web search), GNews (structured news), RSS (geopolitical),
    yfinance (market fear/greed proxy)
  Layer 2.5 — Consciousness measurement:
    Polymarket + Manifold (prediction market odds),
    X/Twitter (volume per search priority)
  Layer 2.5 — Deep research:
    OpenAlex (academic papers)

Output: current_events.json — structured data for dashboard

Architecture note: Prediction markets and X volume are NOT news events.
They are measurements of aggregate belief. They sit in separate sections
of the output JSON, never mixed into the events array.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# ── API Keys (from environment variables) ────────────────────────────────────
TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ── Pressure Windows ─────────────────────────────────────────────────────────
PRESSURE_WINDOWS = [
    {
        "id": "W1",
        "name": "Saturn-Neptune Conjunction",
        "start": "2026-01-14",
        "end": "2026-03-18",
        "peak_days": ["2026-01-25", "2026-02-15", "2026-03-05"],
        "aspect": "Saturn conjunct Neptune",
        "theme": "Old structures dissolving into new paradigms"
    },
    {
        "id": "W2",
        "name": "Uranus-Pluto Trine Near-Exact",
        "start": "2026-06-29",
        "end": "2026-07-28",
        "peak_days": ["2026-07-01", "2026-07-10", "2026-07-28"],
        "aspect": "Uranus trine Pluto (0.20 deg)",
        "theme": "Deep structural power shift — transformation enabled"
    },
    {
        "id": "W3",
        "name": "Year Peak",
        "start": "2026-11-01",
        "end": "2026-12-31",
        "peak_days": ["2026-11-15", "2026-12-01", "2026-12-15"],
        "aspect": "Multiple activations converge",
        "theme": "Highest sustained pressure of 2026"
    },
    {
        "id": "W4",
        "name": "Uranus-Pluto EXACT Trine",
        "start": "2027-05-01",
        "end": "2027-06-30",
        "peak_days": ["2027-05-15", "2027-06-01", "2027-06-15"],
        "aspect": "Uranus trine Pluto (exact)",
        "theme": "Peak structural transformation pressure"
    },
    {
        "id": "W5",
        "name": "Spatial Activation + Year Peak",
        "start": "2027-11-01",
        "end": "2027-12-31",
        "peak_days": ["2027-11-15", "2027-12-01", "2027-12-15"],
        "aspect": "Spatial + temporal convergence",
        "theme": "Fibonacci geometry activates at cycle peak"
    }
]

# ── Player Map (WHO) ──────────────────────────────────────────────────────────
PLAYERS = {
    "Musk": ["musk", "elon", "tesla", "spacex", "doge", "x corp", "neuralink", "starlink"],
    "Altman": ["altman", "openai", "worldcoin", "world coin", "orb", "proof of humanity", "chatgpt"],
    "Thiel": ["thiel", "palantir", "founders fund", "anduril"],
    "BlackRock": ["blackrock", "larry fink", "aladdin", "ishares"],
    "Genesis_Mission": ["doe national lab", "department of energy", "manhattan project", "nuclear", "fusion", "assp", "advanced scientific"],
    "DOGE": ["doge", "government efficiency", "federal cuts", "agency restructur"],
    "Emanuel": ["rahm emanuel", "ari emanuel", "endeavor", "wme"],
    "Technate": ["technocracy", "technate", "energy accounting", "technocratic"],
    "Trump_Admin": ["trump", "white house", "executive order", "tariff"],
    "China": ["china", "xi jinping", "ccp", "beijing", "pla", "taiwan strait"],
    "Israel": ["israel", "netanyahu", "idf", "mossad", "unit 8200", "gaza", "west bank"],
    "AI_Industry": ["artificial intelligence", "ai model", "frontier model", "agi", "superintelligence", "ai safety", "llm", "large language model"],
    "Club_of_Rome": ["club of rome", "limits to growth", "industrial collapse", "overshoot", "resource depletion", "world3"],
    "BRICS": ["brics", "dedollarization", "yuan", "ruble", "multipolar", "global south"],
    "Iran": ["iran", "tehran", "khamenei", "irgc", "strait of hormuz", "persian gulf"],
}

# ── Theater Map (WHERE) ──────────────────────────────────────────────────────
THEATERS = {
    "Domestic_US": ["congress", "senate", "supreme court", "federal", "washington", "pentagon", "cia", "fbi", "nsa"],
    "Fortress_Hemisphere": ["greenland", "venezuela", "panama canal", "usmca", "canada", "mexico border"],
    "DOE_Labs": ["oak ridge", "los alamos", "sandia", "livermore", "argonne", "fermilab", "brookhaven", "pacific northwest", "idaho national"],
    "Dead_Internet": ["bot", "synthetic content", "deepfake", "misinformation", "dead internet", "ai generated"],
    "Middle_East": ["israel", "gaza", "iran", "syria", "saudi", "uae", "yemen", "houthi"],
    "Indo_Pacific": ["taiwan", "south china sea", "philippines", "japan", "korea", "aukus", "quad"],
    "Europe": ["nato", "ukraine", "russia", "eu", "european union", "germany", "france", "uk"],
    "Latin_America": ["cuba", "brazil", "argentina", "colombia", "chile", "ecuador", "bolivia", "mexico"],
    "Financial_System": ["federal reserve", "interest rate", "treasury", "bond", "yield curve", "banking crisis", "inflation", "recession"],
    "Energy_Markets": ["oil price", "crude oil", "opec", "natural gas", "lng", "energy crisis", "oil shock"],
}

# ── Incentive Signals (WHY — follow the money) ───────────────────────────────
INCENTIVE_SIGNALS = {
    "Energy_Infrastructure": ["energy grid", "power plant", "nuclear energy", "fusion reactor", "energy storage", "grid modernization", "smr", "small modular reactor"],
    "Compute_Control": ["data center", "gpu", "chip", "semiconductor", "compute", "cloud infrastructure", "sovereign cloud", "rare earth", "neodymium"],
    "Surveillance_Expansion": ["surveillance", "pre-crime", "predictive policing", "facial recognition", "biometric", "digital id", "pegasus", "nso group"],
    "Financial_Consolidation": ["acquisition", "merger", "monopol", "antitrust", "market concentration", "aladdin", "blackrock"],
    "Military_Tech": ["defense contract", "hypersonic", "autonomous weapon", "drone", "cyber warfare", "space force"],
    "Bifurcation_Signals": ["two-tier", "inequality", "wealth gap", "access", "rationing", "subscription", "paywall", "managed decline", "austerity"],
    "Resource_Grab": ["rare earth", "lithium", "cobalt", "oil reserve", "mineral rights", "arctic", "greenland", "strategic reserve"],
    "Model_Collapse": ["ai hallucin", "model collapse", "synthetic data", "scaling law", "diminishing return", "benchmark plateau", "ai accuracy"],
    "Forgery_Payoff": ["disinformation", "deepfake", "propaganda", "false flag", "narrative warfare", "information warfare", "psyop"],
}

# ── Search Queries ────────────────────────────────────────────────────────────
TAVILY_QUERIES = [
    "DOGE government restructuring federal agencies 2026",
    "Department of Energy national labs AI nuclear 2026",
    "OpenAI Worldcoin digital identity 2026",
    "Palantir government contracts surveillance 2026",
    "BlackRock Aladdin ESG energy infrastructure 2026",
    "Trump executive orders energy policy 2026",
    "artificial intelligence regulation frontier models 2026",
    "geopolitical tension Taiwan China military 2026",
    "financial markets recession indicators 2026",
    "Elon Musk DOGE federal spending cuts",
    "nuclear fusion energy breakthrough 2026",
    "data center GPU shortage compute infrastructure",
    "Iran war escalation oil price energy shock 2026",
    "rare earth minerals Greenland Arctic strategic resources",
    "AI model collapse hallucination scaling limits 2026",
    "Cuba Latin America sphere of influence 2026",
    "BRICS dedollarization multipolar order 2026",
    "limits to growth resource depletion overshoot",
]

RSS_FEEDS = [
    ("Reuters World", "https://feeds.reuters.com/reuters/worldNews"),
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Reuters Tech", "https://feeds.reuters.com/reuters/technologyNews"),
    ("AP Top", "https://rsshub.app/apnews/topics/apf-topnews"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("Defense One", "https://www.defenseone.com/rss/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
]

# ── Search Priorities (mapped to 10 program.md priorities) ───────────────────
# Each priority has keywords for prediction markets, X pulse, and academic search
SEARCH_PRIORITIES = {
    "genesis_mission": {
        "label": "Genesis Mission / DOE / Nuclear",
        "market_terms": ["nuclear energy", "fusion energy", "Department of Energy"],
        "x_terms": ["DOE national lab", "nuclear fusion", "Genesis Mission", "Manhattan Project"],
        "academic_terms": ["nuclear fusion energy policy", "national laboratory governance"],
    },
    "donroe_doctrine": {
        "label": "Donroe Doctrine / Fortress Hemisphere",
        "market_terms": ["Greenland", "Panama Canal", "Cuba invasion", "Venezuela"],
        "x_terms": ["Greenland acquisition", "Monroe Doctrine", "Fortress America", "hemispheric control"],
        "academic_terms": ["hemispheric security doctrine", "US territorial expansion"],
    },
    "model_collapse": {
        "label": "Model Collapse / AI Scaling Limits",
        "market_terms": ["AI bubble", "artificial intelligence", "AGI"],
        "x_terms": ["model collapse", "AI scaling", "AI hallucination", "synthetic data"],
        "academic_terms": ["model collapse synthetic data", "AI scaling laws diminishing returns"],
    },
    "financial_consolidation": {
        "label": "Financial Consolidation",
        "market_terms": ["recession", "stock market crash", "banking crisis", "BlackRock"],
        "x_terms": ["BlackRock Aladdin", "financial consolidation", "too big to fail", "market concentration"],
        "academic_terms": ["financial market concentration systemic risk", "asset manager systemic importance"],
    },
    "phoenix_adjacent": {
        "label": "Phoenix-Adjacent / Geological-Cosmic",
        "market_terms": ["solar storm", "earthquake", "volcanic eruption"],
        "x_terms": ["solar maximum", "geomagnetic storm", "Carrington event", "seismic activity"],
        "academic_terms": ["solar cycle geomagnetic storm infrastructure", "seismic cycle periodicity"],
    },
    "player_movements": {
        "label": "Player Movements",
        "market_terms": ["Elon Musk", "Peter Thiel", "Sam Altman", "Palantir"],
        "x_terms": ["DOGE government", "Palantir contract", "OpenAI", "Neuralink"],
        "academic_terms": ["technology oligopoly governance", "surveillance capitalism"],
    },
    "brics": {
        "label": "BRICS / Dedollarization",
        "market_terms": ["BRICS", "dollar reserve currency", "dedollarization", "yuan"],
        "x_terms": ["BRICS currency", "dedollarization", "petrodollar", "multipolar order"],
        "academic_terms": ["dedollarization reserve currency transition", "BRICS financial architecture"],
    },
    "christian_reich": {
        "label": "Rise of Christian Reich",
        "market_terms": ["Christian nationalism", "theocracy"],
        "x_terms": ["Christian nationalism", "dominionism", "Project 2025", "theocratic"],
        "academic_terms": ["Christian nationalism US politics", "dominion theology political movement"],
    },
    "pax_judaica": {
        "label": "Pax Judaica / Succession",
        "market_terms": ["Israel Palestine", "Israel Iran", "Netanyahu"],
        "x_terms": ["Pax Judaica", "Israel expansion", "Netanyahu coalition", "Greater Israel"],
        "academic_terms": ["Israeli geopolitical strategy", "Middle East power transition"],
    },
    "club_of_rome": {
        "label": "Club of Rome / Limits to Growth",
        "market_terms": ["climate change", "resource depletion", "overshoot"],
        "x_terms": ["limits to growth", "Club of Rome", "overshoot collapse", "resource depletion"],
        "academic_terms": ["limits to growth world3 validation", "resource depletion overshoot model"],
    },
}

# ── Fetchers ──────────────────────────────────────────────────────────────────

def fetch_tavily(queries, max_per_query=5):
    """Search Tavily for prediction-relevant current events."""
    if not TAVILY_KEY:
        print("  TAVILY_API_KEY not set, skipping Tavily")
        return []
    from tavily import TavilyClient
    client = TavilyClient(api_key=TAVILY_KEY)
    results = []
    for q in queries:
        try:
            resp = client.search(q, max_results=max_per_query, search_depth="advanced")
            for r in resp.get("results", []):
                results.append({
                    "source": "tavily",
                    "query": q,
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                    "published": r.get("published_date", ""),
                    "score": r.get("score", 0),
                })
        except Exception as e:
            print(f"  Tavily error for '{q[:40]}': {e}")
    return results


def fetch_gnews(topics=None, max_results=20):
    """Fetch structured news from GNews."""
    from gnews import GNews
    gn = GNews(language="en", country="US", max_results=max_results, period="7d")
    results = []

    try:
        for article in gn.get_news("DOGE federal restructuring OR Department of Energy OR OpenAI OR Palantir OR nuclear fusion OR geopolitical"):
            results.append({
                "source": "gnews",
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "content": article.get("description", "")[:500],
                "published": article.get("published date", ""),
                "publisher": article.get("publisher", {}).get("title", ""),
            })
    except Exception as e:
        print(f"  GNews error: {e}")

    for topic in (topics or ["WORLD", "BUSINESS", "TECHNOLOGY", "SCIENCE"]):
        try:
            for article in gn.get_news_by_topic(topic):
                results.append({
                    "source": "gnews",
                    "topic": topic,
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "content": article.get("description", "")[:500],
                    "published": article.get("published date", ""),
                    "publisher": article.get("publisher", {}).get("title", ""),
                })
        except Exception as e:
            print(f"  GNews topic {topic} error: {e}")
    return results


def fetch_rss(feeds):
    """Fetch headlines from RSS feeds."""
    import feedparser
    results = []
    for name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                results.append({
                    "source": "rss",
                    "feed": name,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "content": entry.get("summary", "")[:500],
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"  RSS error for {name}: {e}")
    return results


def fetch_market_data():
    """Fetch market fear/greed indicators via yfinance."""
    import yfinance as yf
    results = {}
    tickers = {
        "VIX": "^VIX",
        "SP500": "^GSPC",
        "DXY": "DX-Y.NYB",
        "Gold": "GC=F",
        "Oil": "CL=F",
        "BTC": "BTC-USD",
        "TLT": "TLT",
        "10Y": "^TNX",
    }
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if not hist.empty:
                last = hist.iloc[-1]
                prev = hist.iloc[0] if len(hist) > 1 else last
                pct_change = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100
                results[name] = {
                    "price": round(float(last["Close"]), 2),
                    "change_5d": round(float(pct_change), 2),
                    "high_5d": round(float(hist["High"].max()), 2),
                    "low_5d": round(float(hist["Low"].min()), 2),
                }
        except Exception as e:
            print(f"  yfinance error for {name}: {e}")
    return results


# ── Prediction Market Fetchers ────────────────────────────────────────────

def _api_get(url, headers=None, timeout=15):
    """Simple GET request using stdlib only. Returns parsed JSON or None."""
    h = {"User-Agent": "psychohistory-engine/1.0 (moketchups.github.io/psychohistory)"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  API error: {url[:80]}... — {e}")
        return None


def fetch_prediction_markets():
    """
    Pull prediction market odds from Polymarket + Manifold.
    These are consciousness measurements — what the aggregate believes.
    Source owners: Polymarket (Shayne Coplan / crypto-native), Manifold (open-source).
    """
    results = {"polymarket": [], "manifold": [], "source_owners": {
        "polymarket": "Polymarket — crypto prediction market, US-restricted, whale-dominated",
        "manifold": "Manifold — open-source, play money + real sweepstakes, retail crowd",
    }}

    # ── Polymarket via gamma-api ──────────────────────────────────────────
    # No text search — pull active, high-volume markets and filter locally
    print("  Polymarket...")
    poly_url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&order=volume&ascending=false"
    poly_data = _api_get(poly_url)
    if poly_data:
        for m in poly_data:
            question = m.get("question", "").lower()
            # Check if market is relevant to any search priority
            matched_priorities = []
            for pid, priority in SEARCH_PRIORITIES.items():
                for term in priority["market_terms"]:
                    if term.lower() in question:
                        matched_priorities.append(pid)
                        break
            # Also match against player keywords
            matched_players = []
            for player, keywords in PLAYERS.items():
                if any(kw in question for kw in keywords):
                    matched_players.append(player)

            if matched_priorities or matched_players:
                results["polymarket"].append({
                    "question": m.get("question", ""),
                    "outcome_prices": m.get("outcomePrices", ""),
                    "volume": m.get("volume", 0),
                    "liquidity": m.get("liquidity", 0),
                    "end_date": m.get("endDate", ""),
                    "slug": m.get("slug", ""),
                    "priorities": matched_priorities,
                    "players": matched_players,
                })
        print(f"    -> {len(results['polymarket'])} relevant markets (of {len(poly_data)} total)")
    else:
        print("    -> Polymarket unavailable")

    # ── Manifold — search by priority keywords ────────────────────────────
    print("  Manifold...")
    manifold_seen = set()
    for pid, priority in SEARCH_PRIORITIES.items():
        for term in priority["market_terms"][:2]:  # Top 2 terms per priority
            encoded = urllib.parse.quote(term)
            mani_url = f"https://api.manifold.markets/v0/search-markets?term={encoded}&limit=5&sort=liquidity&filter=open"
            mani_data = _api_get(mani_url)
            if mani_data:
                for m in mani_data:
                    mid = m.get("id", "")
                    if mid in manifold_seen:
                        continue
                    manifold_seen.add(mid)
                    results["manifold"].append({
                        "question": m.get("question", ""),
                        "probability": round(m.get("probability", 0) * 100, 1),
                        "volume": m.get("volume", 0),
                        "total_liquidity": m.get("totalLiquidity", 0),
                        "unique_bettors": m.get("uniqueBettorCount", 0),
                        "url": m.get("url", ""),
                        "priority": pid,
                        "search_term": term,
                    })
            time.sleep(0.5)  # Be polite
    print(f"    -> {len(results['manifold'])} relevant markets")

    return results


def fetch_x_pulse():
    """
    Measure X/Twitter volume per search priority using v2 counts endpoint.
    This is a consciousness measurement — aggregate direction and intensity.
    Source owner: X Corp (Elon Musk) — editorial control via algorithm, visibility, suppression.
    """
    if not X_BEARER_TOKEN:
        print("  X_BEARER_TOKEN not set, skipping X pulse")
        return {"priorities": {}, "source_owner": "X Corp (Musk) — algorithmic ranking, shadow suppression, ad-driven visibility"}

    results = {
        "priorities": {},
        "source_owner": "X Corp (Musk) — algorithmic ranking, shadow suppression, ad-driven visibility",
    }
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}

    for pid, priority in SEARCH_PRIORITIES.items():
        priority_volume = {"label": priority["label"], "terms": {}, "total_7d": 0}
        for term in priority["x_terms"][:3]:  # Top 3 terms per priority
            encoded = urllib.parse.quote(term)
            # tweets/counts/recent gives last 7 days of volume
            url = f"https://api.twitter.com/2/tweets/counts/recent?query={encoded}&granularity=day"
            data = _api_get(url, headers=headers)
            if data and "data" in data:
                total = sum(d.get("tweet_count", 0) for d in data["data"])
                daily = [{"date": d.get("start", "")[:10], "count": d.get("tweet_count", 0)} for d in data["data"]]
                priority_volume["terms"][term] = {
                    "total_7d": total,
                    "daily": daily,
                }
                priority_volume["total_7d"] += total
            elif data and "errors" in data:
                print(f"    X API error for '{term}': {data['errors'][0].get('message', 'unknown')}")
            time.sleep(1)  # Rate limit: 300/15min, but be polite

        results["priorities"][pid] = priority_volume

    total_all = sum(p["total_7d"] for p in results["priorities"].values())
    results["total_7d_all_priorities"] = total_all
    print(f"    -> {total_all:,} total tweets across {len(results['priorities'])} priorities")

    return results


def fetch_research():
    """
    Pull academic papers from OpenAlex relevant to search priorities.
    Source owner: OpenAlex (OurResearch nonprofit) — open index of scholarly works.
    Inherits biases of academic publishing (institutional gatekeeping, citation networks).
    """
    results = {
        "papers": [],
        "source_owner": "OpenAlex (OurResearch nonprofit) — open scholarly index, inherits academic publishing bias",
    }
    seen_ids = set()

    for pid, priority in SEARCH_PRIORITIES.items():
        for term in priority["academic_terms"][:1]:  # 1 query per priority
            encoded = urllib.parse.quote(term)
            url = f"https://api.openalex.org/works?search={encoded}&per_page=3&sort=relevance_score:desc&mailto=psychohistory@moketchups.github.io"
            data = _api_get(url)
            if data and "results" in data:
                for work in data["results"]:
                    wid = work.get("id", "")
                    if wid in seen_ids:
                        continue
                    seen_ids.add(wid)
                    primary_loc = work.get("primary_location") or {}
                    source_info = primary_loc.get("source") or {}
                    results["papers"].append({
                        "title": work.get("title", ""),
                        "year": work.get("publication_year"),
                        "cited_by": work.get("cited_by_count", 0),
                        "doi": work.get("doi", ""),
                        "open_access": (work.get("open_access") or {}).get("is_oa", False),
                        "source": source_info.get("display_name", ""),
                        "priority": pid,
                        "search_term": term,
                    })
            time.sleep(0.5)  # Be polite

    print(f"    -> {len(results['papers'])} papers across {len(SEARCH_PRIORITIES)} priorities")
    return results


def fetch_gdelt():
    """
    Pull global event articles from GDELT DOC API per search priority.
    Source owner: GDELT (Kalev Leetaru / Google Jigsaw partnership) — monitors
    global news in 100+ languages. Inherits all media biases of source publications.
    Rate limit: 1 request per 5 seconds.
    """
    results = {
        "articles": [],
        "source_owner": "GDELT (Kalev Leetaru / Google Jigsaw) — global news monitor, inherits media editorial bias",
    }
    seen_urls = set()

    for pid, priority in SEARCH_PRIORITIES.items():
        # Use first market term as GDELT query
        term = priority["market_terms"][0]
        encoded = urllib.parse.quote(term)
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded}&mode=artlist&maxrecords=10&format=json&timespan=7d"
        data = _api_get(url)
        if data and "articles" in data:
            for art in data["articles"]:
                art_url = art.get("url", "")
                if art_url in seen_urls:
                    continue
                seen_urls.add(art_url)
                results["articles"].append({
                    "title": art.get("title", ""),
                    "url": art_url,
                    "source_country": art.get("sourcecountry", ""),
                    "language": art.get("language", ""),
                    "domain": art.get("domain", ""),
                    "seendate": art.get("seendate", ""),
                    "priority": pid,
                    "search_term": term,
                })
        time.sleep(12)  # GDELT rate limit: aggressive, needs 10-12s between requests

    print(f"    -> {len(results['articles'])} articles across {len(SEARCH_PRIORITIES)} priorities")
    return results


def fetch_fred_sdt():
    """
    Pull Structural-Demographic Theory proxy metrics from FRED.
    Source owner: Federal Reserve Bank of St. Louis — US government institution.
    These measure elite overproduction, popular immiseration, and inequality.
    """
    if not FRED_API_KEY:
        print("  FRED_API_KEY not set, skipping FRED SDT metrics")
        return {"metrics": {}, "source_owner": "Federal Reserve Bank of St. Louis — US government institution"}

    results = {
        "metrics": {},
        "source_owner": "Federal Reserve Bank of St. Louis — US government institution, reports what serves Fed mandate",
    }

    # SDT proxy series
    series = {
        "top1_wealth_share": {"id": "WFRBST01134", "label": "Net worth held by Top 1%", "sdt": "elite_overproduction"},
        "bottom50_wealth_share": {"id": "WFRBSB50215", "label": "Net worth held by Bottom 50%", "sdt": "popular_immiseration"},
        "labor_share_gdp": {"id": "LABSHPUSA156NRUG", "label": "Labor compensation share of GDP", "sdt": "popular_immiseration"},
        "median_household_income": {"id": "MEHOINUSA672N", "label": "Real median household income", "sdt": "popular_immiseration"},
        "gini_coefficient": {"id": "GINIALLRF", "label": "Gini ratio for families", "sdt": "inequality"},
        "median_weekly_earnings": {"id": "LES1252881600Q", "label": "Median usual weekly real earnings", "sdt": "popular_immiseration"},
    }

    for key, s in series.items():
        url = (f"https://api.stlouisfed.org/fred/series/observations"
               f"?series_id={s['id']}&api_key={FRED_API_KEY}&file_type=json"
               f"&sort_order=desc&limit=5")
        data = _api_get(url)
        if data and "observations" in data:
            obs = [o for o in data["observations"] if o.get("value", ".") != "."]
            if obs:
                latest = obs[0]
                results["metrics"][key] = {
                    "label": s["label"],
                    "value": latest.get("value", ""),
                    "date": latest.get("date", ""),
                    "sdt_category": s["sdt"],
                    "series_id": s["id"],
                }
        time.sleep(0.5)

    print(f"    -> {len(results['metrics'])} SDT metrics")
    return results


def fetch_world_bank():
    """
    Pull global structural indicators from World Bank API.
    Source owner: World Bank — international development institution.
    Free, no key needed. Provides global coverage FRED can't.
    """
    results = {
        "indicators": {},
        "source_owner": "World Bank — international development institution, reflects member state reporting",
    }

    # Key countries for engine tracking
    countries = ["USA", "CHN", "ISR", "RUS", "DEU", "GBR", "BRA", "IND"]
    indicators = {
        "gini": "SI.POV.GINI",
        "gdp_per_capita": "NY.GDP.PCAP.CD",
        "top10_income_share": "SI.DST.10TH.10",
        "bottom10_income_share": "SI.DST.FRST.10",
        "unemployment": "SL.UEM.TOTL.ZS",
        "inflation": "FP.CPI.TOTL.ZG",
    }

    for ind_key, ind_code in indicators.items():
        country_str = ";".join(countries)
        url = f"https://api.worldbank.org/v2/country/{country_str}/indicator/{ind_code}?format=json&date=2018:2024&per_page=100"
        data = _api_get(url)
        if data and len(data) > 1:
            country_data = {}
            for record in data[1]:
                if record.get("value") is not None:
                    cc = record.get("countryiso3code", "")
                    if cc not in country_data:  # Take most recent
                        country_data[cc] = {
                            "value": record["value"],
                            "date": record.get("date", ""),
                            "country": record.get("country", {}).get("value", ""),
                        }
            results["indicators"][ind_key] = {
                "code": ind_code,
                "countries": country_data,
            }
        time.sleep(0.5)

    total_points = sum(len(v.get("countries", {})) for v in results["indicators"].values())
    print(f"    -> {len(results['indicators'])} indicators, {total_points} data points across {len(countries)} countries")
    return results


# ── Layer 1.5: Capital Flow Intelligence (Free Public Data) ──────────────────

# Engine-relevant tickers for insider/short tracking
# Genesis-adjacent: energy, nuclear, defense, compute
# Rug tickers: consumer, legacy tech, civilian infrastructure
ENGINE_TICKERS = {
    "genesis_adjacent": [
        "SMR", "NNE", "LEU", "CCJ", "UEC",      # Nuclear / uranium
        "NVDA", "AMD", "TSM", "AVGO", "MRVL",    # Compute / GPU
        "PLTR", "LMT", "RTX", "NOC", "GD",       # Defense / surveillance
        "FSLR", "NEE", "CEG", "VST",              # Energy infrastructure
    ],
    "rug_candidates": [
        "SPY", "QQQ", "DIA",                      # Broad market
        "XLF", "KRE",                             # Financial / regional banks
        "XLY", "XRT",                             # Consumer discretionary / retail
        "XLC",                                     # Communication services
        "IYR",                                     # Real estate
    ],
}
ALL_TRACKED_TICKERS = ENGINE_TICKERS["genesis_adjacent"] + ENGINE_TICKERS["rug_candidates"]

SEC_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_insider_trades():
    """
    Pull recent Form 4 insider transactions from SEC EDGAR full-text search.
    Layer 1.5: What corporate insiders are DOING with their own money.
    Source owner: SEC — mandatory public filings, no editorial bias.
    """
    results = {
        "transactions": [],
        "summary": {"total_buys": 0, "total_sells": 0, "genesis_buys": 0, "genesis_sells": 0, "rug_sells": 0},
        "source_owner": "SEC EDGAR — mandatory public filings, no editorial bias, 2-day filing delay",
    }

    today = datetime.now()
    start = (today - timedelta(days=14)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    for category, tickers in ENGINE_TICKERS.items():
        for ticker in tickers:
            url = (
                f"https://efts.sec.gov/LATEST/search-index"
                f"?q=%22{ticker}%22&forms=4"
                f"&dateRange=custom&startdt={start}&enddt={end}"
                f"&from=0&size=5"
            )
            req = urllib.request.Request(url, headers={"User-Agent": SEC_UA})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                hits = data.get("hits", {}).get("hits", [])
                for hit in hits:
                    src = hit.get("_source", {})
                    names = src.get("display_names", [])
                    filing = {
                        "ticker": ticker,
                        "category": category,
                        "entity": names[0] if names else "",
                        "filed": src.get("file_date", ""),
                        "form": src.get("form", "4"),
                        "description": src.get("file_description", ""),
                        "accession": src.get("adsh", ""),
                    }
                    results["transactions"].append(filing)
            except Exception:
                pass  # Silent — SEC rate limits are strict, don't flood logs
            time.sleep(0.15)  # Stay well under 10 req/s

    # Count filings by category — Form 4 search index doesn't expose buy/sell detail
    # The signal is filing VOLUME: lots of insider activity = something is happening
    genesis_filings = [t for t in results["transactions"] if t["category"] == "genesis_adjacent"]
    rug_filings = [t for t in results["transactions"] if t["category"] == "rug_candidates"]
    results["summary"] = {
        "total_filings": len(results["transactions"]),
        "genesis_filings": len(genesis_filings),
        "rug_filings": len(rug_filings),
        "genesis_tickers_active": len(set(t["ticker"] for t in genesis_filings)),
        "rug_tickers_active": len(set(t["ticker"] for t in rug_filings)),
    }

    print(f"    -> {results['summary']['total_filings']} insider filings (14-day window)")
    print(f"       Genesis: {results['summary']['genesis_filings']} filings across {results['summary']['genesis_tickers_active']} tickers")
    print(f"       Rug:     {results['summary']['rug_filings']} filings across {results['summary']['rug_tickers_active']} tickers")
    return results


def fetch_congress_trades():
    """
    Pull recent congressional financial disclosures from House clerk.
    Layer 1.5: What politicians are doing with THEIR money.
    Source owner: US House of Representatives — mandatory public disclosure.
    """
    results = {
        "filings": [],
        "summary": {"total": 0, "matched_players": 0},
        "source_owner": "US House/Senate — mandatory STOCK Act filings, 45-day delay common",
    }

    year = datetime.now().year
    zip_url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.ZIP"

    try:
        import zipfile
        import io
        import xml.etree.ElementTree as ET

        req = urllib.request.Request(zip_url, headers={"User-Agent": SEC_UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            zdata = io.BytesIO(resp.read())

        with zipfile.ZipFile(zdata) as zf:
            for name in zf.namelist():
                if name.endswith(".xml"):
                    tree = ET.parse(zf.open(name))
                    root = tree.getroot()

                    # Parse all Member elements
                    for member in root.iter("Member"):
                        prefix = member.findtext("Prefix", "").strip()
                        last = member.findtext("Last", "").strip()
                        first = member.findtext("First", "").strip()
                        filing_type = member.findtext("FilingType", "").strip()
                        filing_date = member.findtext("FilingDate", "").strip()
                        doc_id = member.findtext("DocID", "").strip()

                        # Only PTR (Periodic Transaction Reports) — actual trades
                        if filing_type != "P":
                            continue

                        filing = {
                            "name": f"{first} {last}".strip(),
                            "prefix": prefix,
                            "filing_type": "Periodic Transaction Report",
                            "filing_date": filing_date,
                            "doc_id": doc_id,
                            "url": f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf",
                        }

                        # Match against engine players
                        name_lower = filing["name"].lower()
                        filing["matched_players"] = []
                        for player, keywords in PLAYERS.items():
                            if any(kw in name_lower for kw in keywords):
                                filing["matched_players"].append(player)

                        results["filings"].append(filing)
                        results["summary"]["total"] += 1
                        if filing["matched_players"]:
                            results["summary"]["matched_players"] += 1

        # Sort by date, most recent first
        results["filings"].sort(key=lambda x: x.get("filing_date", ""), reverse=True)
        # Keep only last 60 days
        cutoff = (datetime.now() - timedelta(days=60)).strftime("%m/%d/%Y")
        results["filings"] = [f for f in results["filings"] if f.get("filing_date", "") >= cutoff]
        results["summary"]["total"] = len(results["filings"])

    except Exception as e:
        print(f"    Congress trades error: {e}")

    print(f"    -> {results['summary']['total']} House PTR filings (last 60 days), {results['summary']['matched_players']} matched engine players")
    return results


def fetch_short_volume():
    """
    Pull daily short sale volume from FINRA for engine-tracked tickers.
    Layer 1.5: Where is short pressure building?
    Source owner: FINRA — exchange-reported data, no editorial bias.
    """
    results = {
        "tickers": {},
        "summary": {"high_short_ratio": []},
        "source_owner": "FINRA — exchange-reported daily short sale volume, no editorial bias",
    }

    # Try last 3 trading days (weekends/holidays may not have data)
    today = datetime.now()
    for days_back in range(0, 5):
        check_date = today - timedelta(days=days_back)
        if check_date.weekday() >= 5:  # Skip weekends
            continue
        date_str = check_date.strftime("%Y%m%d")
        url = f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date_str}.txt"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": SEC_UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                text = resp.read().decode("utf-8")

            for line in text.strip().split("\n"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 5:
                    continue
                symbol = parts[1]
                if symbol not in ALL_TRACKED_TICKERS:
                    continue
                try:
                    short_vol = int(float(parts[2]))
                    short_exempt = int(float(parts[3]))
                    total_vol = int(float(parts[4]))
                except (ValueError, IndexError):
                    continue
                if total_vol == 0:
                    continue

                ratio = (short_vol + short_exempt) / total_vol
                category = "genesis_adjacent" if symbol in ENGINE_TICKERS["genesis_adjacent"] else "rug_candidates"
                results["tickers"][symbol] = {
                    "date": date_str,
                    "short_volume": short_vol,
                    "short_exempt": short_exempt,
                    "total_volume": total_vol,
                    "short_ratio": round(ratio, 4),
                    "category": category,
                }
                if ratio > 0.5:
                    results["summary"]["high_short_ratio"].append({
                        "ticker": symbol,
                        "ratio": round(ratio, 4),
                        "category": category,
                    })

            if results["tickers"]:
                print(f"    -> Found data for {date_str}")
                break  # Got data, stop looking
        except urllib.error.HTTPError:
            continue  # Try previous day
        except Exception as e:
            print(f"    FINRA error for {date_str}: {e}")
            continue

    # Sort high short ratio
    results["summary"]["high_short_ratio"].sort(key=lambda x: -x["ratio"])

    genesis_shorts = {k: v for k, v in results["tickers"].items() if v["category"] == "genesis_adjacent"}
    rug_shorts = {k: v for k, v in results["tickers"].items() if v["category"] == "rug_candidates"}
    print(f"    -> {len(results['tickers'])} tickers tracked ({len(genesis_shorts)} genesis, {len(rug_shorts)} rug)")
    print(f"       High short ratio (>50%): {len(results['summary']['high_short_ratio'])} tickers")
    return results


# ── Tagging Engine ────────────────────────────────────────────────────────────

def tag_event(event):
    """Tag an event with WHO, WHERE, WHY dimensions + source owner."""
    text = (event.get("title", "") + " " + event.get("content", "")).lower()
    tags = {"players": [], "theaters": [], "incentives": []}

    for player, keywords in PLAYERS.items():
        if any(kw in text for kw in keywords):
            tags["players"].append(player)

    for theater, keywords in THEATERS.items():
        if any(kw in text for kw in keywords):
            tags["theaters"].append(theater)

    for signal, keywords in INCENTIVE_SIGNALS.items():
        if any(kw in text for kw in keywords):
            tags["incentives"].append(signal)

    tags["relevance"] = len(tags["players"]) + len(tags["theaters"]) + len(tags["incentives"])

    # Source owner tagging — WHO controls this data
    source = event.get("source", "")
    if source == "tavily":
        tags["source_owner"] = "tavily"
        tags["owner_note"] = "Tavily AI — aggregates web, inherits all web biases"
    elif source == "gnews":
        tags["source_owner"] = "gnews"
        tags["owner_note"] = "Google News — Google controls ranking and visibility"
    elif source == "rss":
        tags["source_owner"] = "rss"
        tags["owner_note"] = f"RSS ({event.get('feed', 'unknown')}) — editorial selection bias"
    else:
        tags["source_owner"] = "unknown"
        tags["owner_note"] = "Unknown source"

    return tags


def map_to_windows(event):
    """Map an event to active/upcoming pressure windows."""
    today = datetime.now().date()
    mapped = []
    for w in PRESSURE_WINDOWS:
        ws = datetime.strptime(w["start"], "%Y-%m-%d").date()
        we = datetime.strptime(w["end"], "%Y-%m-%d").date()
        if (ws - timedelta(days=30)) <= today <= we:
            mapped.append(w["id"])
    return mapped


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run_pipeline():
    """Execute the full data ingestion pipeline."""
    timestamp = datetime.now().isoformat()
    print(f"\n{'='*60}")
    print(f"PSYCHOHISTORY DATA INGESTION — {timestamp}")
    print(f"{'='*60}\n")

    all_events = []

    # ── Layer 2: Managed data collection ─────────────────────────────────
    print("[1/14] Tavily deep web search...")
    tavily_results = fetch_tavily(TAVILY_QUERIES, max_per_query=3)
    all_events.extend(tavily_results)
    print(f"  -> {len(tavily_results)} results")

    print("[2/14] GNews headlines...")
    gnews_results = fetch_gnews()
    all_events.extend(gnews_results)
    print(f"  -> {len(gnews_results)} results")

    print("[3/14] RSS feeds...")
    rss_results = fetch_rss(RSS_FEEDS)
    all_events.extend(rss_results)
    print(f"  -> {len(rss_results)} results")

    print("[4/14] Market indicators...")
    market_data = fetch_market_data()
    print(f"  -> {len(market_data)} tickers")

    # ── Layer 2.5: Consciousness measurement ─────────────────────────────
    print("[5/14] Prediction markets (Polymarket + Manifold)...")
    prediction_markets = fetch_prediction_markets()

    print("[6/14] X pulse (volume per search priority)...")
    x_pulse = fetch_x_pulse()

    # ── Layer 2.5: Deep research ─────────────────────────────────────────
    print("[7/14] Academic research (OpenAlex)...")
    research = fetch_research()

    # ── Layer 2.5: Global event tracking ─────────────────────────────────
    print("[8/14] GDELT global articles...")
    gdelt = fetch_gdelt()

    # ── Layer 2.5: Structural-demographic indicators ─────────────────────
    print("[9/14] FRED SDT metrics...")
    fred_sdt = fetch_fred_sdt()

    print("[10/14] World Bank global indicators...")
    world_bank = fetch_world_bank()

    # ── Layer 1.5: Capital Flow Intelligence (free public data) ────────
    print("[11/14] SEC insider trades (Form 4)...")
    insider_trades = fetch_insider_trades()

    print("[12/14] Congressional financial disclosures...")
    congress_trades = fetch_congress_trades()

    print("[13/14] FINRA short sale volume...")
    short_volume = fetch_short_volume()

    print("[14/14] Done with data collection.")

    # ── Dedup by title ────────────────────────────────────────────────────────
    seen_titles = set()
    deduped = []
    for e in all_events:
        title_key = e.get("title", "").lower().strip()[:80]
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped.append(e)
    print(f"\nDeduped: {len(all_events)} -> {len(deduped)} unique events")

    # ── Tag every event ───────────────────────────────────────────────────────
    print("Tagging events (WHO/WHERE/WHY)...")
    for event in deduped:
        event["tags"] = tag_event(event)
        event["windows"] = map_to_windows(event)

    # ── Sort by relevance ─────────────────────────────────────────────────────
    deduped.sort(key=lambda e: e["tags"]["relevance"], reverse=True)

    # ── Phase 1: Engine matching (embedding-based retrieval) ──────────────────
    # Find which scorecard rows / divergences / predictions / players each
    # event structurally relates to. Adds 'engine_matches' field per event.
    # Skips silently if OPENAI_API_KEY is not set.
    try:
        from engine_index import build_engine_index, match_events_to_engine
        idx = build_engine_index()
        if idx is not None:
            # Only embed top 50 most relevant events to keep cost low
            top_for_matching = deduped[:50]
            match_events_to_engine(top_for_matching, idx)
            # The function mutates events in place
    except Exception as e:
        print(f"  engine_index: skipped ({e})")

    # ── Compute dimension summaries ───────────────────────────────────────────
    player_counts = {}
    theater_counts = {}
    incentive_counts = {}
    for event in deduped:
        for p in event["tags"]["players"]:
            player_counts[p] = player_counts.get(p, 0) + 1
        for t in event["tags"]["theaters"]:
            theater_counts[t] = theater_counts.get(t, 0) + 1
        for i in event["tags"]["incentives"]:
            incentive_counts[i] = incentive_counts.get(i, 0) + 1

    # ── Active windows ────────────────────────────────────────────────────────
    today = datetime.now().date()
    active_windows = []
    next_window = None
    for w in PRESSURE_WINDOWS:
        ws = datetime.strptime(w["start"], "%Y-%m-%d").date()
        we = datetime.strptime(w["end"], "%Y-%m-%d").date()
        if ws <= today <= we:
            active_windows.append(w)
        elif today < ws and next_window is None:
            next_window = w
            days_until = (ws - today).days
            next_window["days_until"] = days_until

    # ── Build output ──────────────────────────────────────────────────────────
    output = {
        "timestamp": timestamp,
        "date": str(today),
        "meta": {
            "total_events": len(deduped),
            "sources": {
                "tavily": len(tavily_results),
                "gnews": len(gnews_results),
                "rss": len(rss_results),
            },
            "high_relevance_events": len([e for e in deduped if e["tags"]["relevance"] >= 3]),
            "prediction_markets": {
                "polymarket": len(prediction_markets.get("polymarket", [])),
                "manifold": len(prediction_markets.get("manifold", [])),
            },
            "x_pulse_total_7d": x_pulse.get("total_7d_all_priorities", 0),
            "research_papers": len(research.get("papers", [])),
            "gdelt_articles": len(gdelt.get("articles", [])),
            "fred_metrics": len(fred_sdt.get("metrics", {})),
            "world_bank_indicators": len(world_bank.get("indicators", {})),
            "insider_filings": insider_trades.get("summary", {}).get("total_filings", 0),
            "congress_filings": congress_trades.get("summary", {}).get("total", 0),
            "short_volume_tickers": len(short_volume.get("tickers", {})),
        },
        "engine_position": {
            "active_windows": active_windows,
            "next_window": next_window,
        },
        "market_data": market_data,
        "prediction_markets": prediction_markets,
        "x_pulse": x_pulse,
        "research": research,
        "gdelt": gdelt,
        "fred_sdt": fred_sdt,
        "world_bank": world_bank,
        "insider_trades": insider_trades,
        "congress_trades": congress_trades,
        "short_volume": short_volume,
        "dimension_summary": {
            "WHO": dict(sorted(player_counts.items(), key=lambda x: -x[1])),
            "WHERE": dict(sorted(theater_counts.items(), key=lambda x: -x[1])),
            "WHY": dict(sorted(incentive_counts.items(), key=lambda x: -x[1])),
        },
        "events": deduped,
    }

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = Path(__file__).parent / "current_events.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved -> {out_path}")
    print(f"  {len(deduped)} events, {len(market_data)} market tickers")

    # ── Print summary ─────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("DIMENSION SUMMARY")
    print(f"{'─'*60}")

    print(f"\nWHO (player mentions):")
    for p, c in sorted(player_counts.items(), key=lambda x: -x[1])[:8]:
        print(f"  {p}: {c}")

    print(f"\nWHERE (theater activity):")
    for t, c in sorted(theater_counts.items(), key=lambda x: -x[1])[:6]:
        print(f"  {t}: {c}")

    print(f"\nWHY (incentive signals):")
    for i, c in sorted(incentive_counts.items(), key=lambda x: -x[1])[:6]:
        print(f"  {i}: {c}")

    # Prediction market summary
    poly_count = len(prediction_markets.get("polymarket", []))
    mani_count = len(prediction_markets.get("manifold", []))
    if poly_count or mani_count:
        print(f"\nPREDICTION MARKETS:")
        print(f"  Polymarket: {poly_count} relevant markets")
        print(f"  Manifold: {mani_count} relevant markets")
        for m in prediction_markets.get("polymarket", [])[:5]:
            prices = m.get("outcome_prices", "")
            print(f"    [{','.join(m.get('priorities', []))}] {m['question'][:60]} -- {prices}")
        for m in prediction_markets.get("manifold", [])[:5]:
            print(f"    [{m.get('priority', '')}] {m['question'][:60]} -- {m.get('probability', '?')}%")

    # X pulse summary
    x_total = x_pulse.get("total_7d_all_priorities", 0)
    if x_total:
        print(f"\nX PULSE (7-day volume):")
        for pid, pdata in sorted(x_pulse.get("priorities", {}).items(), key=lambda x: -x[1].get("total_7d", 0)):
            if pdata.get("total_7d", 0) > 0:
                print(f"  {pdata.get('label', pid)}: {pdata['total_7d']:,}")

    # Research summary
    papers = research.get("papers", [])
    if papers:
        print(f"\nRESEARCH ({len(papers)} papers):")
        for p in sorted(papers, key=lambda x: -x.get("cited_by", 0))[:5]:
            print(f"  [{p.get('priority', '')}] {p['title'][:60]} ({p.get('year', '?')}, {p.get('cited_by', 0)} cites)")

    # Capital flow summary
    insider_summary = insider_trades.get("summary", {})
    short_summary = short_volume.get("summary", {})
    congress_summary = congress_trades.get("summary", {})
    if insider_summary.get("total_buys", 0) or insider_summary.get("total_sells", 0):
        print(f"\nCAPITAL FLOW (Layer 1.5):")
        print(f"  Insider trades: {insider_summary.get('total_buys', 0)} buys / {insider_summary.get('total_sells', 0)} sells")
        print(f"    Genesis buys: {insider_summary.get('genesis_buys', 0)} | Genesis sells: {insider_summary.get('genesis_sells', 0)}")
        print(f"    Rug sells: {insider_summary.get('rug_sells', 0)}")
    if congress_summary.get("total", 0):
        print(f"  Congress PTRs (60d): {congress_summary.get('total', 0)} ({congress_summary.get('matched_players', 0)} matched engine players)")
    high_short = short_summary.get("high_short_ratio", [])
    if high_short:
        print(f"  High short ratio (>50%): {', '.join(s['ticker'] + ' ' + str(int(s['ratio']*100)) + '%' for s in high_short[:10])}")

    print(f"\n{'='*60}")
    print(f"Pipeline complete. {len(deduped)} events, {poly_count}+{mani_count} markets, {x_total:,} tweets, {len(papers)} papers.")
    print(f"{'='*60}\n")

    return output


if __name__ == "__main__":
    run_pipeline()
