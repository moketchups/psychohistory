#!/usr/bin/env python3
"""
Prediction Anchors — Layer 3 Measurement Definitions

Maps each search priority to concrete, measurable indicators from managed data sources.
Every measurement is tagged with source_owner (WHO controls the data).

These anchors are the CONTRACT between the engine and the managed data.
The engine (Layer 0-1) makes predictions. The anchors define what to measure.
The APIs provide the measurements. The gap between prediction and measurement is the product.

The managed data never enters the prediction. It sits beside it as a mirror.
"""

SEARCH_PRIORITIES = {
    "genesis_mission": {
        "label": "Genesis Mission / DOE / Nuclear",
        "description": "Signs of compute infrastructure buildout",
        "prediction_summary": "Compute buildout accelerates through 2032, energy grid bifurcates",
        "prediction_years": [2027, 2028, 2029, 2030, 2031, 2032],
        "expected_trajectory": "increasing",
        "anchors": {
            "yfinance": [
                {
                    "ticker": "URA",
                    "name": "Uranium ETF",
                    "expected_direction": "up",
                    "rationale": "Nuclear buildout for Genesis compute = uranium demand",
                },
                {
                    "ticker": "SMR",
                    "name": "NuScale Power",
                    "expected_direction": "up",
                    "rationale": "Small modular reactors for dedicated compute power",
                },
            ],
            "gdelt": [
                {
                    "query": "department energy nuclear data center compute infrastructure",
                    "name": "DOE compute events",
                    "expected_direction": "up",
                },
            ],
            "fred": [
                {
                    "series_id": "B006RC1Q027SBEA",
                    "name": "Federal nondefense R&D spending",
                    "expected_direction": "up",
                },
            ],
        },
    },
    "donroe_doctrine": {
        "label": "Donroe Doctrine — Hemisphere Consolidation",
        "description": "Greenland, Venezuela, Cuba, Arctic resource grab",
        "prediction_summary": "Hemisphere secured by 2027, energy stockpile for Genesis",
        "prediction_years": [2026, 2027, 2028],
        "expected_trajectory": "increasing then stabilizing",
        "anchors": {
            "yfinance": [
                {
                    "ticker": "CL=F",
                    "name": "Crude Oil",
                    "expected_direction": "up",
                    "rationale": "Resource competition drives energy prices",
                },
                {
                    "ticker": "GC=F",
                    "name": "Gold",
                    "expected_direction": "up",
                    "rationale": "Geopolitical instability = flight to hard assets",
                },
            ],
            "gdelt": [
                {
                    "query": "Greenland minerals rare earth Arctic resources",
                    "name": "Donroe resource grab events",
                    "expected_direction": "up",
                },
                {
                    "query": "Venezuela Cuba Panama hemisphere Monroe doctrine",
                    "name": "Hemisphere consolidation events",
                    "expected_direction": "up",
                },
            ],
        },
    },
    "model_collapse": {
        "label": "Model Collapse — AI Scaling Failures",
        "description": "Benchmark plateaus, synthetic data, diminishing returns",
        "prediction_summary": "Model Collapse visible by 2027, total by 2032",
        "prediction_years": [2027, 2028, 2029, 2030, 2031, 2032],
        "expected_trajectory": "increasing reports of failure",
        "anchors": {
            "gdelt": [
                {
                    "query": "AI model collapse scaling limits synthetic data hallucination plateau",
                    "name": "Model collapse reports",
                    "expected_direction": "up",
                },
            ],
            "yfinance": [
                {
                    "ticker": "MSFT",
                    "name": "Microsoft (OpenAI backer)",
                    "expected_direction": "complex",
                    "rationale": "AI-dependent valuation vulnerable to scaling failures",
                },
                {
                    "ticker": "GOOGL",
                    "name": "Alphabet (DeepMind)",
                    "expected_direction": "complex",
                    "rationale": "Same exposure as MSFT",
                },
            ],
        },
    },
    "financial_consolidation": {
        "label": "Financial Consolidation",
        "description": "BlackRock, Apollo, Technate rail activity",
        "prediction_summary": "Consolidation accelerates, Ouroboros Loop breaks at 2032",
        "prediction_years": [2027, 2029, 2032, 2035, 2036],
        "expected_trajectory": "increasing concentration then rupture",
        "anchors": {
            "yfinance": [
                {
                    "ticker": "BLK",
                    "name": "BlackRock",
                    "expected_direction": "complex",
                    "rationale": "Consolidation grows AUM until Ouroboros breaks",
                },
                {
                    "ticker": "^VIX",
                    "name": "VIX fear index",
                    "expected_direction": "up",
                    "rationale": "Systemic stress = rising volatility",
                },
                {
                    "ticker": "^TNX",
                    "name": "10-Year Treasury yield",
                    "expected_direction": "complex",
                    "rationale": "Debt sustainability indicator",
                },
            ],
            "fred": [
                {
                    "series_id": "GFDEBTN",
                    "name": "Federal Debt Total",
                    "expected_direction": "up",
                    "rationale": "Debt accumulation = capital crisis",
                },
                {
                    "series_id": "M2SL",
                    "name": "M2 Money Supply",
                    "expected_direction": "up",
                    "rationale": "Money printing to sustain unsustainable system",
                },
            ],
        },
    },
    "phoenix_adjacent": {
        "label": "Phoenix-Adjacent — Geological & Electromagnetic",
        "description": "Astronomical anomalies, geological activity, EM events",
        "prediction_summary": "Anomalies increase from 2028, intensify through 2039",
        "prediction_years": [2028, 2030, 2031, 2032, 2038, 2039, 2040],
        "expected_trajectory": "increasing",
        "anchors": {
            "usgs": [
                {
                    "min_magnitude": 5.0,
                    "name": "Significant quakes 5.0+",
                    "expected_direction": "up",
                    "rationale": "Phoenix approach = increased geological activity",
                },
                {
                    "min_magnitude": 6.0,
                    "name": "Major quakes 6.0+",
                    "expected_direction": "up",
                    "rationale": "Tracking severe events separately",
                },
            ],
            "nasa_donki": [
                {
                    "event_type": "CME",
                    "name": "Coronal Mass Ejections",
                    "expected_direction": "up",
                    "rationale": "EM disruption from approaching object",
                },
                {
                    "event_type": "GST",
                    "name": "Geomagnetic Storms",
                    "expected_direction": "up",
                    "rationale": "G4+ storms = Null Zone effects",
                },
                {
                    "event_type": "FLR",
                    "name": "Solar Flares",
                    "expected_direction": "up",
                    "rationale": "Solar activity increase",
                },
            ],
        },
    },
    "player_movements": {
        "label": "Player Movements",
        "description": "Musk/DOGE, Altman/OpenAI, Thiel/Palantir, Trump admin",
        "prediction_summary": "Players execute Technate blueprint, consolidation visible",
        "prediction_years": [2026, 2027, 2028, 2029, 2030],
        "expected_trajectory": "increasing consolidation",
        "anchors": {
            "yfinance": [
                {
                    "ticker": "TSLA",
                    "name": "Tesla (Musk)",
                    "expected_direction": "complex",
                    "rationale": "Hereditary technocrat vehicle",
                },
                {
                    "ticker": "PLTR",
                    "name": "Palantir (Thiel)",
                    "expected_direction": "up",
                    "rationale": "Surveillance state expansion = Palantir growth",
                },
            ],
            "gdelt": [
                {
                    "query": "DOGE government restructuring federal agencies efficiency cuts",
                    "name": "DOGE restructuring events",
                    "expected_direction": "up",
                },
                {
                    "query": "OpenAI Anthropic frontier AI model regulation safety",
                    "name": "AI industry events",
                    "expected_direction": "up",
                },
            ],
        },
    },
    "brics_counter": {
        "label": "BRICS Counter-Strategy",
        "description": "Dedollarization, multipolar moves",
        "prediction_summary": "Dedollarization accelerates, USD reserve share declines",
        "prediction_years": [2027, 2029, 2032, 2039],
        "expected_trajectory": "increasing",
        "anchors": {
            "yfinance": [
                {
                    "ticker": "DX-Y.NYB",
                    "name": "US Dollar Index (DXY)",
                    "expected_direction": "down",
                    "rationale": "Dedollarization = weakening dollar",
                },
                {
                    "ticker": "GC=F",
                    "name": "Gold (BRICS reserve alt)",
                    "expected_direction": "up",
                    "rationale": "BRICS central banks accumulating",
                },
            ],
            "fred": [
                {
                    "series_id": "DTWEXBGS",
                    "name": "Trade Weighted Dollar Index",
                    "expected_direction": "down",
                    "rationale": "Dollar weight declining in global trade",
                },
            ],
            "gdelt": [
                {
                    "query": "BRICS dedollarization yuan ruble multipolar currency",
                    "name": "BRICS dedollarization events",
                    "expected_direction": "up",
                },
            ],
        },
    },
    "christian_reich": {
        "label": "Rise of Christian Reich",
        "description": "Celebrity conversions, Christian nationalism, Heritage Foundation",
        "prediction_summary": "Christianity instrumentalized as control architecture, peaks CY127 (2029)",
        "prediction_years": [2026, 2027, 2028, 2029],
        "expected_trajectory": "increasing",
        "anchors": {
            "gdelt": [
                {
                    "query": "Christian nationalism Heritage Foundation religious politics evangelical",
                    "name": "Christian nationalism events",
                    "expected_direction": "up",
                },
            ],
        },
    },
    "pax_judaica": {
        "label": "Pax Judaica Signals",
        "description": "US-Israel friction, intelligence transfers",
        "prediction_summary": "American infrastructure migrating to Israel, resolves at CY137 (2039)",
        "prediction_years": [2029, 2032, 2036, 2039],
        "expected_trajectory": "increasing friction",
        "anchors": {
            "gdelt": [
                {
                    "query": "US Israel relations friction intelligence technology transfer",
                    "name": "US-Israel friction events",
                    "expected_direction": "up",
                },
                {
                    "query": "Israel technology infrastructure cyber Unit 8200 Oracle Jerusalem",
                    "name": "Israel tech buildup events",
                    "expected_direction": "up",
                },
            ],
        },
    },
    "club_of_rome": {
        "label": "Club of Rome / Limits to Growth",
        "description": "Resource depletion, overshoot indicators",
        "prediction_summary": "Industrial output peaks early 21st century, decline ~2040",
        "prediction_years": [2030, 2032, 2035, 2038, 2039, 2040],
        "expected_trajectory": "plateau then decline",
        "anchors": {
            "yfinance": [
                {
                    "ticker": "CL=F",
                    "name": "Crude Oil (extraction cost proxy)",
                    "expected_direction": "up",
                    "rationale": "Escalating extraction costs",
                },
                {
                    "ticker": "DBC",
                    "name": "Commodity Index ETF",
                    "expected_direction": "up",
                    "rationale": "Resource scarcity = rising commodity prices",
                },
            ],
            "fred": [
                {
                    "series_id": "INDPRO",
                    "name": "Industrial Production Index",
                    "expected_direction": "complex",
                    "rationale": "World3 BAU predicts plateau then decline",
                },
                {
                    "series_id": "GFDEGDQ188S",
                    "name": "Federal Debt to GDP Ratio",
                    "expected_direction": "up",
                    "rationale": "Capital consumed by maintenance costs",
                },
            ],
        },
    },
}


# Source owner registry — WHO controls each data source and WHY
SOURCE_OWNERS = {
    "usgs": {
        "name": "US Geological Survey",
        "parent": "US Department of Interior",
        "incentive": "Control geological narrative thresholds",
        "data_type": "structured_scientific",
        "risk": "low for raw seismic, high for interpretation",
    },
    "nasa_donki": {
        "name": "NASA DONKI / NOAA Space Weather",
        "parent": "US Government (NASA/NOAA)",
        "incentive": "Classify and prioritize space weather events",
        "data_type": "structured_scientific",
        "risk": "low for raw data, controls what gets flagged",
    },
    "fred": {
        "name": "Federal Reserve Economic Data",
        "parent": "Federal Reserve System",
        "incentive": "Present monetary policy as working",
        "data_type": "structured_economic",
        "risk": "moderate — methodology changes, revisions",
    },
    "yfinance": {
        "name": "Market Data (Yahoo Finance)",
        "parent": "Multiple exchanges via Yahoo",
        "incentive": "Market prices are consensus, movable by large capital",
        "data_type": "market_prices",
        "risk": "moderate — large capital can move prices",
    },
    "gdelt": {
        "name": "GDELT Project",
        "parent": "Google Jigsaw (State Dept lineage)",
        "incentive": "Define what counts as an event, control classification",
        "data_type": "event_classification",
        "risk": "high — classification embeds assumptions",
    },
    "tavily": {
        "name": "Tavily Web Search",
        "parent": "Tavily AI",
        "incentive": "Aggregates web — inherits all web biases",
        "data_type": "web_search",
        "risk": "high — inherits SEO and platform biases",
    },
    "gnews": {
        "name": "Google News",
        "parent": "Google / Alphabet",
        "incentive": "Control news ranking and visibility",
        "data_type": "news_aggregation",
        "risk": "high — Google controls ranking",
    },
    "rss": {
        "name": "RSS Feeds (Reuters, AP, Al Jazeera, etc.)",
        "parent": "Multiple media organizations",
        "incentive": "Each outlet has editorial bias",
        "data_type": "news_editorial",
        "risk": "moderate — editorial selection bias",
    },
}
