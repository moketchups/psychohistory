#!/usr/bin/env python3
"""
Psychohistory Prediction Engine — Real-Time Data Ingestion Pipeline

Pulls current events from multiple sources and maps them against:
- 5 pressure windows (engine dates)
- WHO (player mentions)
- WHERE (theater mentions)
- WHY (incentive signals — financial, energy, tech, military)

Sources: Tavily (web search), GNews (structured news), RSS (geopolitical),
         yfinance (market fear/greed proxy)

Output: current_events.json — structured data for dashboard
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── API Keys (from environment variables) ────────────────────────────────────
TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")

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
            resp = client.search(q, max_results=max_per_query, search_depth="basic")
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


# ── Tagging Engine ────────────────────────────────────────────────────────────

def tag_event(event):
    """Tag an event with WHO, WHERE, WHY dimensions."""
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

    # 1. Tavily web search
    print("[1/4] Tavily web search...")
    tavily_results = fetch_tavily(TAVILY_QUERIES, max_per_query=3)
    all_events.extend(tavily_results)
    print(f"  -> {len(tavily_results)} results")

    # 2. GNews structured news
    print("[2/4] GNews headlines...")
    gnews_results = fetch_gnews()
    all_events.extend(gnews_results)
    print(f"  -> {len(gnews_results)} results")

    # 3. RSS feeds
    print("[3/4] RSS feeds...")
    rss_results = fetch_rss(RSS_FEEDS)
    all_events.extend(rss_results)
    print(f"  -> {len(rss_results)} results")

    # 4. Market data
    print("[4/4] Market indicators...")
    market_data = fetch_market_data()
    print(f"  -> {len(market_data)} tickers")

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
        },
        "engine_position": {
            "active_windows": active_windows,
            "next_window": next_window,
        },
        "market_data": market_data,
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

    print(f"\n{'='*60}")
    print(f"Pipeline complete. {len(deduped)} events ingested.")
    print(f"{'='*60}\n")

    return output


if __name__ == "__main__":
    run_pipeline()
