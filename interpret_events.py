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
import re
import hashlib
from pathlib import Path
from datetime import datetime, timedelta


MAX_AGE_DAYS = 14  # drop events older than this from drafting


def _extract_date_from_url(url):
    if not url:
        return ""
    m = re.search(r'/(20\d{2})[-/](\d{2})[-/](\d{2})', url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def _parse_event_date(event):
    """Try every known date format and return a datetime.date or None."""
    pub = event.get("published", "") or ""
    if not pub:
        pub = _extract_date_from_url(event.get("url", ""))
    if not pub:
        return None
    # Try ISO formats
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(pub[:19] if "T" in pub else pub[:10], fmt).date()
        except ValueError:
            continue
    # Try RFC 2822 (RSS): Tue, 07 Apr 2026 02:20:00 GMT
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(pub).date()
    except Exception:
        return None


def _is_recent(event, max_age_days=MAX_AGE_DAYS):
    """True if the event has a parseable date within max_age_days."""
    d = _parse_event_date(event)
    if d is None:
        return False
    cutoff = (datetime.now() - timedelta(days=max_age_days)).date()
    return d >= cutoff


def slugify(text):
    """Mirror of the frontend slugify rules."""
    if not text:
        return ""
    s = text.lower()
    s = s.replace("\u2018", "").replace("\u2019", "")
    s = s.replace("'", "")
    s = s.replace("$", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s


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
                if slugify(row.get("topic", "")) == slug:
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
                if slugify(d.get("title", "")) == slug:
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
        elif etype == "player":
            with open(ENGINE_DATA_DIR / "players.json") as f:
                players_data = json.load(f)
            for section in players_data:
                for card in section.get("cards", []):
                    if slugify(card.get("name", "")) == slug:
                        content = card.get("content", "") or " ".join(card.get("paragraphs", []) or [])
                        return {
                            "type": "player",
                            "label": card.get("name", ""),
                            "full_text": f"{card.get('role', '')}\n\n{content[:2500]}",
                            "raw": card,
                            "section_title": section.get("title", ""),
                        }
        elif etype == "concept":
            with open(ENGINE_DATA_DIR / "concepts.json") as f:
                concepts = json.load(f)
            for c in concepts:
                name = c.get("term") or c.get("name") or ""
                if slugify(name) == slug:
                    return {
                        "type": "concept",
                        "label": name,
                        "full_text": c.get("definition") or c.get("description") or "",
                        "raw": c,
                    }
    except Exception as e:
        print(f"  interpret_events: load error for {element_id}: {e}")
    return None


SYSTEM_PROMPT_BATCH = """You are an analytical assistant for the Psychohistory Prediction Engine. You receive ONE engine element and a BATCH of news events from a single day that all relate to it. Your job is to synthesize these events into ONE engine-voice scorecard update.

The engine's update format is structural, not a news ticker. ONE date-stamped paragraph synthesizes ALL the day's signals into a coherent observation that ties back to the engine's existing claim.

═══ THE ENGINE'S VOICE — STUDY THIS ═══

GOOD (synthesizes multiple signals into one structural observation):
**Apr 7 2026 live signals:** Oil $110+ as Trump's Iran deadline approaches. European gas futures +3%. NATO partners issue conditional support statements. The pre-announcement positioning continues — energy markets pricing escalation while political channels still claim diplomacy. The financial layer is reading the kayfabe ahead of the spectacle layer.

BAD (news ticker, separate paragraphs per event):
**Apr 7:** Oil rose above $110.
**Apr 7:** Gas futures jumped 3%.
**Apr 7:** NATO partners issued statements.

The bad version is what an aggregator does. The good version is what the engine does. NEVER produce the bad version.

═══ HARD RULES ═══

1. Output ONE date-stamped paragraph. Not three. Not bullet points. One paragraph.

2. The paragraph must reference at least 2 different signals from the batch. If you only use 1, you have failed batching.

3. Each signal you reference must come with a paste-quote from the corresponding article. The quotes go in the "quotes" array, separately from the draft_text.

4. **ABSOLUTE RULE — NO FABRICATED SOURCES.** Every entry in the "quotes" array MUST come from an article in the EVENTS BATCH below. The "url" field MUST be one of the URLs listed in the batch — copy it exactly. NEVER invent a URL. NEVER quote from the "Existing analysis" of the engine element — that is the engine's own writing, not external evidence. If you cannot find a real quote from a batch event, OMIT that entry entirely.

5. End the paragraph with a STRUCTURAL observation in the engine's voice — what these signals mean about the engine element's claim. Not "this confirms the engine" — something specific about the pattern.

6. Use the engine element's existing analysis as CONTEXT for what the engine already knows. Do NOT quote it. Do NOT cite it as a source. The engine's existing analysis is the BASELINE you build on, not evidence.

7. Do not extrapolate beyond the articles. Every claim in the paragraph must be defensible from at least one paste-quote from a batch event.

8. If the batch only contains 1 event, you may produce a single-signal update with 1 quote. Do NOT pad it with a fake second quote.

9. If after careful reading the batch doesn't actually relate to the element, return relationship: "no_match".

═══ CONFIDENCE ═══

- high: at least 2 primary-source signals (gov docs, SEC filings, named official statements, raw market data)
- medium: reputable news reports on verifiable events
- low: opinion pieces, speculation, anonymous sourcing

═══ OUTPUT FORMAT (strict JSON) ═══

{
  "relationship": "confirms" | "contradicts" | "refines" | "no_match",
  "confidence": "high" | "medium" | "low",
  "draft_text": "**[date]:** synthesized paragraph...",
  "quotes": [
    {"url": "...", "title": "...", "quote": "exact paste-quote from this article"},
    {"url": "...", "title": "...", "quote": "exact paste-quote from this article"}
  ],
  "rationale": "1 sentence on why this batch matches the element"
}

If relationship is "no_match", you may omit draft_text and quotes.
"""


DRAFT_TEXT_MAX_CHARS = 900
DRAFT_TEXT_MIN_CHARS = 80


def _validate_draft(result, event_count, allowed_urls=None):
    """Programmatic gates on LLM output. Returns (ok: bool, reason: str).
    allowed_urls: set of URLs from the actual event batch. Every quote URL
    must be in this set — prevents the LLM from fabricating sources."""
    if not isinstance(result, dict):
        return False, "result not a dict"

    relationship = result.get("relationship", "")
    if relationship == "no_match":
        return True, "no_match"  # legitimate skip

    if relationship not in {"confirms", "contradicts", "refines"}:
        return False, f"invalid relationship '{relationship}'"

    draft_text = result.get("draft_text", "") or ""
    if len(draft_text) < DRAFT_TEXT_MIN_CHARS:
        return False, f"draft_text too short ({len(draft_text)} chars, need >={DRAFT_TEXT_MIN_CHARS})"
    if len(draft_text) > DRAFT_TEXT_MAX_CHARS:
        return False, f"draft_text too long ({len(draft_text)} chars, max {DRAFT_TEXT_MAX_CHARS})"

    quotes = result.get("quotes", []) or []
    if not quotes:
        return False, "no quotes"

    # Quote shape check
    for i, q in enumerate(quotes):
        if not isinstance(q, dict):
            return False, f"quote {i} not a dict"
        if not q.get("quote"):
            return False, f"quote {i} missing 'quote' field"
        url = q.get("url", "")
        if not url:
            return False, f"quote {i} missing 'url' field"
        # Anti-fabrication: URL must exist in the actual event batch
        if allowed_urls is not None and url not in allowed_urls:
            return False, f"quote {i} URL '{url[:60]}' not in event batch — LLM fabricated source"
        # Sanity: URL must look like a real URL with a path
        if not url.startswith(("http://", "https://")):
            return False, f"quote {i} URL '{url[:60]}' missing scheme"

    # Multi-event batches MUST have quotes from multiple distinct sources
    if event_count >= 2:
        unique_urls = {q.get("url", "") for q in quotes}
        if len(unique_urls) < 2:
            return False, f"only {len(unique_urls)} unique source URL — batch with {event_count} events needs ≥2"

    return True, "ok"


def _build_user_prompt(element, event_match_pairs, day_str, retry_reason=None, content_chars=600):
    events_text = ""
    allowed_url_list = []
    for i, (event, _) in enumerate(event_match_pairs, 1):
        title = event.get("title", "")
        source = event.get("publisher", "") or event.get("source", "")
        url = event.get("url", "")
        content = (event.get("content", "") or event.get("description", ""))[:content_chars]
        events_text += f"\n--- EVENT {i} ---\n"
        events_text += f"Title: {title}\n"
        events_text += f"Source: {source}\n"
        events_text += f"URL: {url}\n"
        events_text += f"Content:\n{content}\n"
        if url:
            allowed_url_list.append(f"  EVENT {i}: {url}")
    allowed_urls_block = "\n".join(allowed_url_list)

    retry_note = ""
    if retry_reason:
        retry_note = f"""

═══ RETRY: YOUR PREVIOUS RESPONSE WAS REJECTED ═══
Reason: {retry_reason}

CRITICAL FIXES — read carefully:
- 'draft_text' MUST be 80-{DRAFT_TEXT_MAX_CHARS} characters TOTAL. Count characters. If it would be longer, CUT IT. One tight paragraph, not three sentences padded into one.
- Each item in 'quotes' must have a UNIQUE 'url'. Do NOT pull two quotes from the same article — each quote = different URL.
- The 'quote' field must be a SHORT paste-quote (under 200 chars). Do not paste full paragraphs.
- Output must be VALID JSON. Escape internal quotes with \\". Do not use raw line breaks inside string values — use \\n.
- ONE paragraph in draft_text. No bullets. No multiple paragraphs.
"""

    return f"""ENGINE ELEMENT (context — DO NOT quote this section):
Type: {element['type']}
Label: {element['label']}
Existing analysis:
{element['full_text']}

═══ BATCH OF {len(event_match_pairs)} EVENTS FROM {day_str} ═══
{events_text}

═══ ALLOWED URLs FOR QUOTES — copy exactly, do not modify ═══
{allowed_urls_block}

Every entry in your "quotes" array MUST have a "url" field that is one of the URLs above, copied EXACTLY. Any other URL = automatic rejection. The quote text must be a verbatim paste from that event's content above.
{retry_note}
TASK: Synthesize the {len(event_match_pairs)} events into ONE engine-voice paragraph ({DRAFT_TEXT_MIN_CHARS}-{DRAFT_TEXT_MAX_CHARS} chars). Reference at least {min(2, len(event_match_pairs))} different events (use different URLs from the allowed list). Each quote must be SHORT (under 200 chars) and from a unique URL. End with a structural observation. Output strict JSON only — escape internal quotes properly."""


def _interpret_batch(element, event_match_pairs, day_str):
    """Send a (element, [events]) batch to the LLM. Validates output programmatically.
    Retries once if the first response fails validation. Returns dict or None."""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"  interpret_events: openai import error: {e}")
        return None

    event_count = len(event_match_pairs)
    # Build the allowed-URL set from the actual event batch — prevents fabrication
    allowed_urls = {e.get("url", "") for e, _ in event_match_pairs if e.get("url")}

    for attempt in (1, 2):
        retry_reason = None if attempt == 1 else last_reason
        user_prompt = _build_user_prompt(element, event_match_pairs, day_str, retry_reason=retry_reason)
        try:
            resp = client.chat.completions.create(
                model=INTERPRET_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_BATCH},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2 if attempt == 1 else 0.1,  # tighter on retry
            )
            content = resp.choices[0].message.content
            result = json.loads(content)
        except Exception as e:
            print(f"  interpret_events: LLM error (attempt {attempt}): {e}")
            return None

        ok, reason = _validate_draft(result, event_count, allowed_urls=allowed_urls)
        if ok:
            return result
        last_reason = reason
        if attempt == 1:
            print(f"  validation fail (attempt 1): {reason} — retrying")

    print(f"  validation fail (attempt 2): {last_reason} — dropping draft")
    return None


def _group_draft_id(element_id, day_str):
    return hashlib.md5(f"batch:{element_id}:{day_str}".encode()).hexdigest()[:12]


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
    """Main entry: read events, group by (element, day), draft ONE synthesized
    update per group. Each draft references multiple events from that day."""
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

    # Group events by (top_match_element_id, event_date)
    from collections import defaultdict
    groups = defaultdict(list)
    dropped_stale = 0
    dropped_no_match = 0
    for event in events:
        if not _is_recent(event):
            dropped_stale += 1
            continue
        matches = event.get("engine_matches", []) or []
        # Filter to matches above threshold
        good = [m for m in matches if m.get("similarity", 0) >= MIN_SIMILARITY_FOR_DRAFT]
        if not good:
            dropped_no_match += 1
            continue
        # Use TOP match — each event contributes to exactly one group
        top = good[0]
        date = _parse_event_date(event)
        if date is None:
            continue
        key = (top["id"], date.isoformat())
        groups[key].append((event, top))

    if dropped_stale:
        print(f"  interpret_events: dropped {dropped_stale} stale events (>{MAX_AGE_DAYS}d old or undated)")
    if dropped_no_match:
        print(f"  interpret_events: dropped {dropped_no_match} fresh events with no match above threshold")

    if not groups:
        print("  interpret_events: no groups to draft")
        return

    # Sort groups by total similarity desc (most-relevant groups first)
    group_list = sorted(
        groups.items(),
        key=lambda kv: -sum(m.get("similarity", 0) for _, m in kv[1])
    )
    group_list = group_list[:MAX_DRAFTS_PER_RUN]

    print(f"  interpret_events: {len(group_list)} (element, day) groups to draft")
    new_drafts = 0
    for (element_id, day_str), pairs in group_list:
        d_id = _group_draft_id(element_id, day_str)
        if d_id in existing_ids:
            continue  # already drafted

        element = _load_engine_element_full(element_id)
        if not element:
            print(f"  skip: element not found {element_id}")
            continue

        result = _interpret_batch(element, pairs, day_str)
        if not result:
            continue

        relationship = result.get("relationship", "no_match")
        if relationship == "no_match":
            continue

        quotes = result.get("quotes", []) or []
        if not quotes:
            continue  # rule: no quotes = no draft

        draft = {
            "id": d_id,
            "element_id": element_id,
            "element_type": element["type"],
            "element_label": element["label"],
            "day": day_str,
            "event_count": len(pairs),
            "relationship": relationship,
            "confidence": result.get("confidence", "medium"),
            "draft_text": result.get("draft_text", ""),
            "quotes": quotes,
            "rationale": result.get("rationale", ""),
            "max_similarity": max((m.get("similarity", 0) for _, m in pairs), default=0),
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
