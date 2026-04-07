"""
Phase 2: LLM interpretation of engine-matched events.

Takes events from current_events.json that have engine_matches (from
engine_index.py phase 1) and generates draft scorecard/divergence/
prediction updates using an LLM.

Drafts go to pending_updates.json for human review via review_pending.py.

The LLM is REQUIRED to paste-quote the source article. No quote = no draft.
The LLM does NOT commit anything — it only suggests. Human approves.

Usage:
    from interpret_events import interpret_matched_events
    interpret_matched_events()  # reads current_events.json, writes pending_updates.json
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime


# Auto-load env from known locations if not already set
def _load_env_files():
    candidates = [
        Path("/Users/jamienucho/moketchups_engine/.env"),
        Path.home() / ".env",
        Path(__file__).parent / ".env",
    ]
    for envfile in candidates:
        if not envfile.exists():
            continue
        try:
            with open(envfile) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value and key not in os.environ:
                        os.environ[key] = value
        except Exception:
            pass

_load_env_files()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
INTERPRET_MODEL = "gpt-4o-mini"  # cheap structured extraction
DEPLOY_DIR = Path(__file__).parent
ENGINE_DATA_DIR = Path("/Users/jamienucho/psychohistory-v2/data")
PENDING_PATH = DEPLOY_DIR / "pending_updates.json"
EVENTS_PATH = DEPLOY_DIR / "current_events.json"
MAX_DRAFTS_PER_RUN = 30  # cap LLM calls per pipeline run
MIN_SIMILARITY_FOR_DRAFT = 0.40  # only draft for high-similarity matches


def _event_id(event):
    """Stable ID for an event (URL-based hash)."""
    seed = (event.get("url") or event.get("title") or "")[:200]
    return hashlib.md5(seed.encode()).hexdigest()[:12]


def _draft_id(event_id, element_id):
    return hashlib.md5(f"{event_id}:{element_id}".encode()).hexdigest()[:12]


def _load_engine_element_full(element_id):
    """Look up an engine element's full text by ID for the LLM context."""
    parts = element_id.split(":", 1)
    if len(parts) != 2:
        return None
    etype, slug = parts

    try:
        if etype == "scorecard":
            with open(ENGINE_DATA_DIR / "scorecard.json") as f:
                rows = json.load(f)
            for row in rows:
                topic = (row.get("topic", "") or "").lower().replace("'", "").replace("$", "").replace("/", "-").replace(" ", "-").replace(",", "")[:60]
                if topic == slug:
                    return {
                        "type": "scorecard",
                        "label": row.get("topic", ""),
                        "full_text": row.get("analysis", "")[:3000],
                        "raw": row,
                    }
        elif etype == "divergence":
            with open(ENGINE_DATA_DIR / "divergences.json") as f:
                divs = json.load(f)
            for d in divs:
                title = (d.get("title", "") or "").lower().replace("'", "").replace("$", "").replace("/", "-").replace(" ", "-").replace(",", "")[:60]
                if title == slug:
                    return {
                        "type": "divergence",
                        "label": d.get("title", ""),
                        "full_text": (d.get("content", "") or d.get("description", ""))[:3000],
                        "raw": d,
                    }
        elif etype == "prediction":
            with open(ENGINE_DATA_DIR / "predictions.json") as f:
                preds = json.load(f)
            for p in preds:
                if str(p.get("year", "")) == slug:
                    conditions = p.get("conditions", {})
                    return {
                        "type": "prediction",
                        "label": f"{p.get('year', '')} prediction",
                        "full_text": f"{p.get('headline', '')}\n\nWatch for: {conditions.get('watch_for', '')[:2500]}",
                        "raw": p,
                    }
    except Exception as e:
        print(f"  interpret_events: load error for {element_id}: {e}")
    return None


SYSTEM_PROMPT = """You are an analytical assistant for the Psychohistory Prediction Engine. Your job is to read a current news event and decide whether it confirms, contradicts, or refines a specific element in the engine. You are NOT writing freely. You are extracting structured data.

HARD RULES — violation = invalid output that will be rejected:

1. You MUST quote a specific paste-quote from the news article that supports your draft. If you cannot quote, return relationship: "no_match".

2. You MUST distinguish:
   - confirms: the event provides new evidence supporting the engine element's claim
   - contradicts: the event provides new evidence against the engine element's claim
   - refines: the event adds nuance or specifics without confirming or contradicting
   - no_match: the event is not actually relevant to the engine element

3. Confidence levels:
   - high: primary source (filing, gov doc, court record, named official statement)
   - medium: reputable news report on a verifiable event
   - low: opinion piece, speculation, or unverified claim

4. Your draft text must be 1-3 sentences max, written in the engine's voice (concise, structural, date-stamped). Format: "**[Date]:** [observation]. [structural significance]."

5. Do not extrapolate beyond what the article actually says. The draft must be defensible from the paste-quote alone.

OUTPUT FORMAT (strict JSON, no markdown, no commentary):
{
  "relationship": "confirms" | "contradicts" | "refines" | "no_match",
  "confidence": "high" | "medium" | "low",
  "draft_text": "**[Date]:** ...",
  "quote": "exact paste-quote from the article",
  "rationale": "1 sentence on why this matches the engine element"
}

If relationship is "no_match", you may omit draft_text and quote.
"""


def _interpret_one(event, element):
    """Send one (event, element) pair to the LLM. Returns dict or None."""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"  interpret_events: openai import error: {e}")
        return None

    user_prompt = f"""ENGINE ELEMENT:
Type: {element['type']}
Label: {element['label']}
Content:
{element['full_text']}

NEWS EVENT:
Title: {event.get('title', '')}
Source: {event.get('source', '')}{' (' + event.get('publisher', '') + ')' if event.get('publisher') else ''}
URL: {event.get('url', '')}
Published: {event.get('published', '')}
Content:
{(event.get('content', '') or event.get('description', ''))[:1500]}

TASK: Apply the rules. Output strict JSON only."""

    try:
        resp = client.chat.completions.create(
            model=INTERPRET_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"  interpret_events: LLM error: {e}")
        return None


def _load_pending():
    if PENDING_PATH.exists():
        try:
            with open(PENDING_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_pending(pending):
    with open(PENDING_PATH, "w") as f:
        json.dump(pending, f, indent=2, default=str)


def interpret_matched_events():
    """Main entry: read events, draft updates for high-similarity matches."""
    if not OPENAI_API_KEY:
        print("  interpret_events: OPENAI_API_KEY not set, skipping LLM interpretation")
        return

    if not EVENTS_PATH.exists():
        print(f"  interpret_events: {EVENTS_PATH} not found, skipping")
        return

    with open(EVENTS_PATH) as f:
        data = json.load(f)
    events = data.get("events", [])

    pending = _load_pending()
    existing_ids = {p["id"] for p in pending}

    # Build candidate list: (event, match) pairs above threshold
    candidates = []
    for event in events:
        matches = event.get("engine_matches", []) or []
        for match in matches:
            if match.get("similarity", 0) < MIN_SIMILARITY_FOR_DRAFT:
                continue
            ev_id = _event_id(event)
            d_id = _draft_id(ev_id, match["id"])
            if d_id in existing_ids:
                continue  # already drafted in a previous run
            candidates.append((event, match, d_id))

    # Sort by similarity desc and cap
    candidates.sort(key=lambda c: -c[1].get("similarity", 0))
    candidates = candidates[:MAX_DRAFTS_PER_RUN]

    if not candidates:
        print("  interpret_events: no new candidates to draft")
        return

    print(f"  interpret_events: drafting {len(candidates)} new updates...")
    new_drafts = 0
    for event, match, d_id in candidates:
        element = _load_engine_element_full(match["id"])
        if not element:
            continue

        result = _interpret_one(event, element)
        if not result:
            continue

        relationship = result.get("relationship", "no_match")
        if relationship == "no_match":
            continue

        if not result.get("quote"):
            continue  # rule violation: no quote = no draft

        draft = {
            "id": d_id,
            "event_id": _event_id(event),
            "element_id": match["id"],
            "element_type": element["type"],
            "element_label": element["label"],
            "relationship": relationship,
            "confidence": result.get("confidence", "medium"),
            "draft_text": result.get("draft_text", ""),
            "quote": result.get("quote", ""),
            "rationale": result.get("rationale", ""),
            "source_url": event.get("url", ""),
            "source_title": event.get("title", ""),
            "source_publisher": event.get("publisher", "") or event.get("source", ""),
            "source_published": event.get("published", ""),
            "similarity": match.get("similarity", 0),
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        pending.append(draft)
        new_drafts += 1

    _save_pending(pending)
    pending_count = len([p for p in pending if p.get("status") == "pending"])
    print(f"  interpret_events: {new_drafts} new drafts written. {pending_count} pending review.")


if __name__ == "__main__":
    interpret_matched_events()
