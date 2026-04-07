"""
Engine indexer + matcher.

Builds an embedding index of the engine's content (scorecard, divergences,
predictions, players, concepts) and matches incoming news events to the
top-N most similar engine elements.

Phase 1: retrieval only. No LLM interpretation. The frontend will display
"this event relates to X, Y, Z" based on cosine similarity of embeddings.

Usage:
    from engine_index import build_engine_index, match_events_to_engine

    index = build_engine_index()  # one-time per pipeline run
    enriched_events = match_events_to_engine(events, index)
"""

import json
import os
import math
from pathlib import Path

# Engine data lives in psychohistory-v2/data/
ENGINE_DATA_DIR = Path("/Users/jamienucho/psychohistory-v2/data")

# Cache the index file in the deploy dir so subsequent runs can reuse it
INDEX_CACHE_PATH = Path(__file__).parent / "engine_index_cache.json"


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
EMBED_MODEL = "text-embedding-3-small"  # 1536 dims, cheap
SIMILARITY_THRESHOLD = 0.30  # min cosine similarity to count as a match
TOP_K = 3  # top matches to return per event


def slugify(text):
    return (text or "").lower().replace("'", "").replace("$", "").replace("/", "-").replace(" ", "-").replace(",", "")[:60]


def _load_engine_elements():
    """Read engine JSONs and build a flat list of {id, type, label, text}."""
    elements = []

    # Scorecard rows
    try:
        with open(ENGINE_DATA_DIR / "scorecard.json") as f:
            scorecard = json.load(f)
        for row in scorecard:
            if row.get("severity", "").upper().find("MERGED") != -1:
                continue
            topic = row.get("topic", "")
            text = f"{topic}. {row.get('analysis', '')[:1500]}"
            elements.append({
                "id": f"scorecard:{slugify(topic)}",
                "type": "scorecard",
                "label": topic,
                "url_path": f"/scorecard/{slugify(topic)}",
                "text": text,
            })
    except Exception as e:
        print(f"  engine_index: scorecard load error: {e}")

    # Divergences
    try:
        with open(ENGINE_DATA_DIR / "divergences.json") as f:
            divergences = json.load(f)
        for d in divergences:
            title = d.get("title", "")
            content = d.get("content", "") or d.get("description", "")
            text = f"{title}. {content[:1500]}"
            elements.append({
                "id": f"divergence:{slugify(title)}",
                "type": "divergence",
                "label": title,
                "url_path": f"/divergences/{slugify(title)}",
                "text": text,
            })
    except Exception as e:
        print(f"  engine_index: divergences load error: {e}")

    # Predictions (one element per year)
    try:
        with open(ENGINE_DATA_DIR / "predictions.json") as f:
            predictions = json.load(f)
        for p in predictions:
            year = p.get("year", "")
            headline = p.get("headline", "")
            conditions = p.get("conditions", {})
            watch_for = conditions.get("watch_for", "")[:1500]
            text = f"Year {year}: {headline}. Watch for: {watch_for}"
            elements.append({
                "id": f"prediction:{year}",
                "type": "prediction",
                "label": f"{year} prediction",
                "url_path": f"/predictions/{year}",
                "text": text,
            })
    except Exception as e:
        print(f"  engine_index: predictions load error: {e}")

    # Players (one per card)
    try:
        with open(ENGINE_DATA_DIR / "players.json") as f:
            players_data = json.load(f)
        for section in players_data:
            section_title = section.get("title", "")
            for card in section.get("cards", []):
                name = card.get("name", "")
                role = card.get("role", "")
                content = card.get("content", "") or " ".join(card.get("paragraphs", []) or [])
                text = f"{name} ({role}). {content[:1000]}"
                elements.append({
                    "id": f"player:{slugify(name)}",
                    "type": "player",
                    "label": name,
                    "url_path": f"/players/{slugify(section_title)}",
                    "text": text,
                })
    except Exception as e:
        print(f"  engine_index: players load error: {e}")

    # Concepts
    try:
        with open(ENGINE_DATA_DIR / "concepts.json") as f:
            concepts = json.load(f)
        for c in concepts:
            name = c.get("term") or c.get("name") or ""
            definition = c.get("definition") or c.get("description") or ""
            text = f"{name}: {definition[:1000]}"
            elements.append({
                "id": f"concept:{slugify(name)}",
                "type": "concept",
                "label": name,
                "url_path": f"/concepts/{slugify(name)}",
                "text": text,
            })
    except Exception as e:
        print(f"  engine_index: concepts load error: {e}")

    return elements


def _embed_batch(texts, batch_size=100):
    """Call OpenAI embeddings API in batches. Returns list of vectors."""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
            all_embeddings.extend([d.embedding for d in resp.data])
        return all_embeddings
    except Exception as e:
        print(f"  engine_index: embedding error: {e}")
        return None


def build_engine_index(force_rebuild=False):
    """
    Build the engine embedding index. Cached to disk so subsequent runs
    only need to re-embed if the engine content changed.

    Returns: dict with 'elements' (list) and 'embeddings' (list of vectors)
             OR None if embeddings unavailable.
    """
    if not OPENAI_API_KEY:
        print("  engine_index: OPENAI_API_KEY not set, skipping engine matching")
        return None

    elements = _load_engine_elements()
    if not elements:
        print("  engine_index: no elements loaded")
        return None

    # Check cache
    cache_key_text = "|".join(sorted([e["id"] + ":" + str(len(e["text"])) for e in elements]))
    cache_key = hash(cache_key_text)

    if not force_rebuild and INDEX_CACHE_PATH.exists():
        try:
            with open(INDEX_CACHE_PATH) as f:
                cached = json.load(f)
            if cached.get("cache_key") == cache_key:
                print(f"  engine_index: using cached index ({len(cached['elements'])} elements)")
                return cached
        except Exception as e:
            print(f"  engine_index: cache read error: {e}")

    # Build fresh
    print(f"  engine_index: building fresh embeddings for {len(elements)} elements...")
    texts = [e["text"] for e in elements]
    embeddings = _embed_batch(texts)
    if embeddings is None:
        return None

    index = {
        "cache_key": cache_key,
        "model": EMBED_MODEL,
        "elements": elements,
        "embeddings": embeddings,
    }

    try:
        with open(INDEX_CACHE_PATH, "w") as f:
            json.dump(index, f)
        print(f"  engine_index: cached to {INDEX_CACHE_PATH}")
    except Exception as e:
        print(f"  engine_index: cache write error: {e}")

    return index


def _cosine_similarity(a, b):
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def match_events_to_engine(events, index, top_k=TOP_K, threshold=SIMILARITY_THRESHOLD):
    """
    For each event, find the top-K most similar engine elements.
    Adds 'engine_matches' field to each event.

    events: list of event dicts (must have 'title' and 'content' or similar)
    index: output of build_engine_index()

    Returns: list of events with engine_matches added.
    """
    if index is None or not events:
        return events

    # Embed events
    event_texts = []
    for e in events:
        title = e.get("title", "") or ""
        content = (e.get("content", "") or e.get("description", "") or "")[:800]
        event_texts.append(f"{title}. {content}")

    print(f"  engine_index: embedding {len(event_texts)} events...")
    event_embeddings = _embed_batch(event_texts)
    if event_embeddings is None:
        return events

    elements = index["elements"]
    elem_embeddings = index["embeddings"]

    matched_count = 0
    for event, ev_emb in zip(events, event_embeddings):
        # Compute similarity to every element
        scored = []
        for elem, el_emb in zip(elements, elem_embeddings):
            sim = _cosine_similarity(ev_emb, el_emb)
            if sim >= threshold:
                scored.append((sim, elem))
        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]
        if top:
            matched_count += 1
            event["engine_matches"] = [
                {
                    "id": elem["id"],
                    "type": elem["type"],
                    "label": elem["label"],
                    "url_path": elem["url_path"],
                    "similarity": round(sim, 3),
                }
                for sim, elem in top
            ]
        else:
            event["engine_matches"] = []

    print(f"  engine_index: {matched_count}/{len(events)} events matched to engine")
    return events


if __name__ == "__main__":
    # CLI test: build index and dump element count
    print("Building engine index...")
    idx = build_engine_index(force_rebuild=True)
    if idx:
        print(f"Built index with {len(idx['elements'])} elements")
        types = {}
        for e in idx['elements']:
            types[e['type']] = types.get(e['type'], 0) + 1
        for t, c in types.items():
            print(f"  {t}: {c}")
    else:
        print("Index build failed (likely missing OPENAI_API_KEY)")
