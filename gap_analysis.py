#!/usr/bin/env python3
"""
Gap Analysis Engine — Layer 3 of the Psychohistory Prediction System

Architecture:
  Layer 0: Constitution (Alan's work) — LOCKED
  Layer 1: Engine output (PREDICTIONS.md, WORLDSTATE.md) — derived from Layer 0
  Layer 2: Managed data (current_events.json) — institutional sources
  Layer 3: THIS FILE — measures the gap between Layer 1 and Layer 2

The managed data never enters the prediction. It sits beside it.
The gap between engine prediction and institutional narrative IS the intelligence.

Four measurements per anchor:
  CONVERGING: institutional data moving toward engine prediction
  DIVERGING:  institutional data moving away from engine prediction
  SILENCE:    expected data absent or dramatically reduced
  CONTRADICTION: two institutional sources disagree about same domain

All classification is arithmetic. No AI scoring, no semantic similarity, no LLM judgment.
The anchor file defines what to measure. The code does subtraction. The human interprets.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.request
import urllib.parse

from prediction_anchors import SEARCH_PRIORITIES, SOURCE_OWNERS

# ── Configuration ─────────────────────────────────────────────────────────────

BASELINES_FILE = Path(__file__).parent / "baselines.json"
GAP_REPORT_FILE = Path(__file__).parent / "gap_report.json"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")
SILENCE_THRESHOLD = 0.2  # Flag if current < 20% of baseline
MEASUREMENT_DAYS = 30    # Rolling window for all measurements


# ── API Fetchers ──────────────────────────────────────────────────────────────

def _http_get_json(url, timeout=30):
    """Shared HTTP GET returning parsed JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": "psychohistory-engine/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_usgs_earthquakes(min_magnitude=5.0, days=MEASUREMENT_DAYS):
    """USGS earthquake data. Source owner: US Dept of Interior."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    params = urllib.parse.urlencode({
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
    })
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?{params}"
    try:
        data = _http_get_json(url)
        features = data.get("features", [])
        return {
            "source_owner": "usgs",
            "count": len(features),
            "period_days": days,
            "min_magnitude": min_magnitude,
            "max_magnitude": max((f["properties"]["mag"] for f in features), default=0),
            "events_preview": [
                {
                    "mag": f["properties"]["mag"],
                    "place": f["properties"]["place"],
                }
                for f in sorted(features, key=lambda x: -x["properties"]["mag"])[:10]
            ],
        }
    except Exception as e:
        print(f"  USGS error: {e}")
        return {"source_owner": "usgs", "count": None, "error": str(e)}


def fetch_nasa_donki(event_type="CME", days=MEASUREMENT_DAYS):
    """NASA DONKI space weather. Source owner: US Gov (NASA/NOAA)."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    params = urllib.parse.urlencode({
        "startDate": start.strftime("%Y-%m-%d"),
        "endDate": end.strftime("%Y-%m-%d"),
        "api_key": NASA_API_KEY,
    })
    url = f"https://api.nasa.gov/DONKI/{event_type}?{params}"
    try:
        data = _http_get_json(url)
        count = len(data) if isinstance(data, list) else 0
        return {
            "source_owner": "nasa_donki",
            "event_type": event_type,
            "count": count,
            "period_days": days,
        }
    except Exception as e:
        print(f"  NASA DONKI ({event_type}) error: {e}")
        return {"source_owner": "nasa_donki", "event_type": event_type, "count": None, "error": str(e)}


_gdelt_last_call = 0
_GDELT_DELAY = 10  # seconds between GDELT API calls

def fetch_gdelt_events(query, days=MEASUREMENT_DAYS):
    """GDELT v2 event count. Source owner: Google Jigsaw (State Dept lineage)."""
    global _gdelt_last_call
    elapsed = time.time() - _gdelt_last_call
    if elapsed < _GDELT_DELAY:
        time.sleep(_GDELT_DELAY - elapsed)
    _gdelt_last_call = time.time()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    params = urllib.parse.urlencode({
        "query": query,
        "mode": "artlist",
        "maxrecords": 250,
        "format": "json",
        "startdatetime": start.strftime("%Y%m%d%H%M%S"),
        "enddatetime": end.strftime("%Y%m%d%H%M%S"),
    })
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?{params}"

    # Try twice with backoff
    for attempt in range(2):
        try:
            data = _http_get_json(url, timeout=45)
            articles = data.get("articles", [])
            return {
                "source_owner": "gdelt",
                "query": query,
                "count": len(articles),
                "period_days": days,
            }
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                print(f"    GDELT rate limited, waiting 15s...")
                time.sleep(15)
                _gdelt_last_call = time.time()
                continue
            print(f"  GDELT error '{query[:40]}': {e}")
            return {"source_owner": "gdelt", "query": query, "count": None, "error": str(e)}
        except Exception as e:
            print(f"  GDELT error '{query[:40]}': {e}")
            return {"source_owner": "gdelt", "query": query, "count": None, "error": str(e)}


def fetch_yfinance_indicator(ticker):
    """Market price from yfinance. Source owner: exchanges via Yahoo."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        hist = t.history(period="1mo")
        if hist.empty:
            return {"source_owner": "yfinance", "ticker": ticker, "price": None, "error": "no data"}
        first_close = float(hist.iloc[0]["Close"])
        last_close = float(hist.iloc[-1]["Close"])
        pct = ((last_close - first_close) / first_close) * 100 if first_close else 0
        return {
            "source_owner": "yfinance",
            "ticker": ticker,
            "price": round(last_close, 2),
            "price_start": round(first_close, 2),
            "pct_change_1mo": round(pct, 2),
            "high": round(float(hist["High"].max()), 2),
            "low": round(float(hist["Low"].min()), 2),
        }
    except Exception as e:
        print(f"  yfinance ({ticker}) error: {e}")
        return {"source_owner": "yfinance", "ticker": ticker, "price": None, "error": str(e)}


def fetch_fred_series(series_id):
    """FRED economic data. Source owner: Federal Reserve."""
    if not FRED_API_KEY:
        return {"source_owner": "fred", "series_id": series_id, "value": None, "error": "no key"}
    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_API_KEY)
        s = fred.get_series(series_id)
        vals = [float(v) for v in s.dropna().tail(6)]
        if not vals:
            return {"source_owner": "fred", "series_id": series_id, "value": None, "error": "empty"}
        pct = ((vals[-1] - vals[-2]) / abs(vals[-2])) * 100 if len(vals) > 1 and vals[-2] else 0
        return {
            "source_owner": "fred",
            "series_id": series_id,
            "value": round(vals[-1], 2),
            "prev_value": round(vals[-2], 2) if len(vals) > 1 else None,
            "pct_change": round(pct, 2),
        }
    except Exception as e:
        print(f"  FRED ({series_id}) error: {e}")
        return {"source_owner": "fred", "series_id": series_id, "value": None, "error": str(e)}


# ── Gap Classification (pure arithmetic) ─────────────────────────────────────

def _extract_value(measurement):
    """Pull the comparable number from a measurement dict."""
    for key in ("count", "price", "value"):
        v = measurement.get(key)
        if v is not None:
            return float(v)
    return None


def classify_gap(current_val, baseline_val, expected_direction):
    """
    Classify gap between current and baseline. Arithmetic only.
    Returns (gap_type, pct_change, detail_string).
    """
    if current_val is None or baseline_val is None:
        return "NO_DATA", 0.0, "missing data"

    if baseline_val == 0:
        if current_val == 0:
            return "FLAT", 0.0, "both zero"
        return "NEW_SIGNAL", float(current_val), f"new activity ({current_val}, baseline was 0)"

    pct = ((current_val - baseline_val) / abs(baseline_val)) * 100
    going_up = current_val > baseline_val
    going_down = current_val < baseline_val

    # Silence check: dramatic drop
    if baseline_val > 0 and current_val / baseline_val < SILENCE_THRESHOLD:
        return "SILENCE", round(pct, 1), f"dropped to {current_val/baseline_val:.0%} of baseline"

    # Simple directions
    if expected_direction == "up":
        if going_up:
            return "CONVERGING", round(pct, 1), f"+{pct:.1f}% (expected up)"
        if going_down:
            return "DIVERGING", round(pct, 1), f"{pct:.1f}% (expected up)"
        return "FLAT", 0.0, "no movement (expected up)"

    if expected_direction == "down":
        if going_down:
            return "CONVERGING", round(pct, 1), f"{pct:.1f}% (expected down)"
        if going_up:
            return "DIVERGING", round(pct, 1), f"+{pct:.1f}% (expected down)"
        return "FLAT", 0.0, "no movement (expected down)"

    # Complex trajectories — report without classifying
    return "TRACKING", round(pct, 1), f"{pct:+.1f}% (trajectory: {expected_direction})"


def detect_contradictions(priority_results):
    """
    Find cases where two managed sources in the same priority point opposite directions.
    Contradictions between managed sources reveal things neither intends to reveal.
    """
    contradictions = []
    for priority_id, measurements in priority_results.items():
        ups, downs = [], []
        for key, m in measurements.items():
            val = _extract_value(m)
            if val is None:
                continue
            pct = m.get("pct_change_1mo", m.get("pct_change", 0))
            if pct is None:
                continue
            entry = {"key": key, "source": m.get("source_owner", "?"), "pct": pct}
            if pct > 5:
                ups.append(entry)
            elif pct < -5:
                downs.append(entry)
        if ups and downs:
            contradictions.append({
                "priority": priority_id,
                "up_signals": ups,
                "down_signals": downs,
                "description": (
                    f"{priority_id}: "
                    + ", ".join(f"{u['source']}/{u['key']} +{u['pct']:.0f}%" for u in ups)
                    + " BUT "
                    + ", ".join(f"{d['source']}/{d['key']} {d['pct']:.0f}%" for d in downs)
                ),
            })
    return contradictions


# ── Measurement Pipeline ─────────────────────────────────────────────────────

def pull_all_measurements():
    """Pull measurements for every anchor across all search priorities."""
    timestamp = datetime.now(timezone.utc).isoformat() + "Z"
    print(f"\n{'='*60}")
    print(f"GAP ANALYSIS — {timestamp}")
    print(f"{'='*60}")

    results = {}

    # Collect all GDELT queries first, then interleave with other API calls
    # This avoids hammering GDELT with rapid-fire requests
    gdelt_queue = []
    for pid, priority in SEARCH_PRIORITIES.items():
        for anchor in priority.get("anchors", {}).get("gdelt", []):
            gdelt_queue.append((pid, anchor))

    # Pull non-GDELT data first (fast, no rate limits)
    for pid, priority in SEARCH_PRIORITIES.items():
        print(f"\n  [{priority['label']}]")
        measurements = {}

        for anchor in priority.get("anchors", {}).get("usgs", []):
            key = f"usgs_{anchor['min_magnitude']}"
            print(f"    USGS {anchor['name']}...")
            m = fetch_usgs_earthquakes(min_magnitude=anchor["min_magnitude"])
            m["expected_direction"] = anchor["expected_direction"]
            m["anchor_name"] = anchor["name"]
            measurements[key] = m

        for anchor in priority.get("anchors", {}).get("nasa_donki", []):
            key = f"nasa_{anchor['event_type']}"
            print(f"    NASA DONKI {anchor['name']}...")
            m = fetch_nasa_donki(event_type=anchor["event_type"])
            m["expected_direction"] = anchor["expected_direction"]
            m["anchor_name"] = anchor["name"]
            measurements[key] = m

        for anchor in priority.get("anchors", {}).get("yfinance", []):
            key = f"yf_{anchor['ticker'].replace('=', '').replace('^', '').replace('-', '')}"
            print(f"    yfinance {anchor['name']}...")
            m = fetch_yfinance_indicator(ticker=anchor["ticker"])
            m["expected_direction"] = anchor.get("expected_direction", "complex")
            m["anchor_name"] = anchor["name"]
            measurements[key] = m

        for anchor in priority.get("anchors", {}).get("fred", []):
            key = f"fred_{anchor['series_id']}"
            print(f"    FRED {anchor['name']}...")
            m = fetch_fred_series(series_id=anchor["series_id"])
            m["expected_direction"] = anchor.get("expected_direction", "complex")
            m["anchor_name"] = anchor["name"]
            measurements[key] = m

        results[pid] = {
            "label": priority["label"],
            "prediction_summary": priority["prediction_summary"],
            "expected_trajectory": priority["expected_trajectory"],
            "measurements": measurements,
        }

    # Now pull GDELT data with rate limiting (3s between calls)
    if gdelt_queue:
        print(f"\n  [GDELT — {len(gdelt_queue)} queries, rate-limited]")
        for pid, anchor in gdelt_queue:
            key = f"gdelt_{anchor['name'].replace(' ', '_')[:40]}"
            print(f"    GDELT {anchor['name']}...")
            m = fetch_gdelt_events(query=anchor["query"])
            m["expected_direction"] = anchor["expected_direction"]
            m["anchor_name"] = anchor["name"]
            results[pid]["measurements"][key] = m

    return {"timestamp": timestamp, "priorities": results}


# ── Baseline Management ──────────────────────────────────────────────────────

def load_baselines():
    if BASELINES_FILE.exists():
        with open(BASELINES_FILE) as f:
            return json.load(f)
    return None


def save_baselines(data):
    with open(BASELINES_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Baselines saved -> {BASELINES_FILE}")


# ── Gap Report Generation ────────────────────────────────────────────────────

def generate_gap_report(current, baselines):
    """Compare current measurements to baselines. Pure arithmetic."""
    report = {
        "timestamp": current["timestamp"],
        "baseline_timestamp": baselines["timestamp"],
        "priorities": {},
        "contradictions": [],
        "summary": {
            "CONVERGING": 0, "DIVERGING": 0, "SILENCE": 0,
            "FLAT": 0, "TRACKING": 0, "NO_DATA": 0, "NEW_SIGNAL": 0,
        },
    }

    raw_by_priority = {}

    for pid, pdata in current["priorities"].items():
        baseline_p = baselines.get("priorities", {}).get(pid, {})
        baseline_m = baseline_p.get("measurements", {})

        gaps = []
        raw_by_priority[pid] = pdata["measurements"]

        for key, m in pdata["measurements"].items():
            cur_val = _extract_value(m)
            bas_val = _extract_value(baseline_m.get(key, {}))
            exp_dir = m.get("expected_direction", "complex")

            gap_type, magnitude, detail = classify_gap(cur_val, bas_val, exp_dir)

            owner_id = m.get("source_owner", "unknown")
            owner = SOURCE_OWNERS.get(owner_id, {})

            gaps.append({
                "anchor": m.get("anchor_name", key),
                "source_owner": owner_id,
                "owner_incentive": owner.get("incentive", "unknown"),
                "current": cur_val,
                "baseline": bas_val,
                "gap_type": gap_type,
                "magnitude": magnitude,
                "detail": detail,
            })

            report["summary"][gap_type] = report["summary"].get(gap_type, 0) + 1

        report["priorities"][pid] = {
            "label": pdata["label"],
            "prediction_summary": pdata["prediction_summary"],
            "gaps": gaps,
        }

    report["contradictions"] = detect_contradictions(raw_by_priority)
    return report


def format_report_text(report):
    """Human-readable gap report."""
    lines = []
    ts = report["timestamp"][:10]
    bts = report["baseline_timestamp"][:10]
    lines.append(f"## Gap Report — {ts}")
    lines.append(f"Baseline captured: {bts}")
    lines.append("")

    s = report["summary"]
    lines.append(
        f"**Summary:** {s.get('CONVERGING',0)} converging | "
        f"{s.get('DIVERGING',0)} diverging | "
        f"{s.get('SILENCE',0)} silent | "
        f"{s.get('FLAT',0)} flat | "
        f"{s.get('TRACKING',0)} tracking | "
        f"{s.get('NO_DATA',0)} no data"
    )
    lines.append("")

    icons = {
        "CONVERGING": "CONVERGING",
        "DIVERGING": "DIVERGING",
        "SILENCE": "**SILENCE**",
        "FLAT": "FLAT",
        "TRACKING": "TRACKING",
        "NO_DATA": "NO_DATA",
        "NEW_SIGNAL": "NEW",
    }

    for pid, pdata in report["priorities"].items():
        lines.append(f"### {pdata['label']}")
        lines.append(f"ENGINE SAYS: {pdata['prediction_summary']}")
        lines.append("")
        for g in pdata["gaps"]:
            tag = f"[{g['source_owner'].upper()}]"
            icon = icons.get(g["gap_type"], g["gap_type"])
            lines.append(f"  {icon} {tag} {g['anchor']}: {g['detail']}")
            if g["gap_type"] == "SILENCE":
                lines.append(f"    WHO CONTROLS THIS: {g['owner_incentive']}")
        lines.append("")

    if report["contradictions"]:
        lines.append("### CROSS-SOURCE CONTRADICTIONS")
        for c in report["contradictions"]:
            lines.append(f"  CONTRADICTION: {c['description']}")
        lines.append("")
    else:
        lines.append("### CROSS-SOURCE CONTRADICTIONS")
        lines.append("  None detected this cycle.")
        lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    current = pull_all_measurements()
    baselines = load_baselines()

    if baselines is None:
        print(f"\n{'='*60}")
        print("FIRST RUN — Capturing baselines")
        print(f"{'='*60}")
        save_baselines(current)

        with open(GAP_REPORT_FILE, "w") as f:
            json.dump({
                "status": "baseline_captured",
                "timestamp": current["timestamp"],
                "note": "Baselines captured. Gap analysis starts on next cycle.",
            }, f, indent=2, default=str)

        # Also write readable report
        text_path = Path(__file__).parent / "gap_report.md"
        with open(text_path, "w") as f:
            f.write(f"## Gap Report — {current['timestamp'][:10]}\n\n")
            f.write("**FIRST RUN — Baselines captured.**\n\n")
            f.write("Gap analysis will begin on the next cycle.\n\n")
            f.write("### Baseline Values Captured\n\n")
            for pid, pdata in current["priorities"].items():
                f.write(f"**{pdata['label']}**\n")
                for key, m in pdata["measurements"].items():
                    val = _extract_value(m)
                    name = m.get("anchor_name", key)
                    owner = m.get("source_owner", "?")
                    f.write(f"  [{owner.upper()}] {name}: {val}\n")
                f.write("\n")

        print(f"\n  Baselines saved. Run again next cycle for gap analysis.")
        print(f"  Report: {text_path}")
        return

    # Generate gap report
    print(f"\n{'='*60}")
    print("GENERATING GAP REPORT")
    print(f"{'='*60}")

    report = generate_gap_report(current, baselines)

    # Save JSON
    with open(GAP_REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Save text
    text = format_report_text(report)
    text_path = Path(__file__).parent / "gap_report.md"
    with open(text_path, "w") as f:
        f.write(text)

    print(f"\n{text}")
    print(f"\n  JSON: {GAP_REPORT_FILE}")
    print(f"  Text: {text_path}")

    # Update baselines for next cycle
    save_baselines(current)


if __name__ == "__main__":
    run()
