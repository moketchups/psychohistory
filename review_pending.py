"""
Phase 2: Interactive CLI for reviewing pending engine updates.

Walks through pending_updates.json one at a time. For each:
  - Display engine element, news event, draft, quote
  - Prompt: approve / edit / reject / skip / quit
  - On approve: append the draft text to the relevant engine JSON
  - At end: offer to rebuild export.txt and commit

Run after the pipeline (data_feeds.py + interpret_events.py) has populated
pending_updates.json. Run as often as you want; it remembers state.

Usage:
    python3 review_pending.py
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

DEPLOY_DIR = Path(__file__).parent
ENGINE_DATA_DIR = Path("/Users/jamienucho/psychohistory-v2/data")
PENDING_PATH = DEPLOY_DIR / "pending_updates.json"

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


def color(text, c):
    return f"{c}{text}{RESET}"


def load_pending():
    if not PENDING_PATH.exists():
        return []
    try:
        with open(PENDING_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading pending: {e}")
        return []


def save_pending(pending):
    with open(PENDING_PATH, "w") as f:
        json.dump(pending, f, indent=2, default=str)


def slugify(text):
    return (text or "").lower().replace("'", "").replace("$", "").replace("/", "-").replace(" ", "-").replace(",", "")[:60]


def apply_to_scorecard(element_id, draft_text):
    """Append a draft text to a scorecard row's analysis field."""
    slug = element_id.split(":", 1)[1]
    path = ENGINE_DATA_DIR / "scorecard.json"
    with open(path) as f:
        rows = json.load(f)
    for row in rows:
        if slugify(row.get("topic", "")) == slug:
            existing = row.get("analysis", "")
            row["analysis"] = (existing + "\n\n" + draft_text).strip()
            with open(path, "w") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
            return True
    return False


def apply_to_divergence(element_id, draft_text):
    slug = element_id.split(":", 1)[1]
    path = ENGINE_DATA_DIR / "divergences.json"
    with open(path) as f:
        divs = json.load(f)
    for d in divs:
        if slugify(d.get("title", "")) == slug:
            content_field = "content" if "content" in d else "description"
            existing = d.get(content_field, "")
            d[content_field] = (existing + "\n\n" + draft_text).strip()
            with open(path, "w") as f:
                json.dump(divs, f, indent=2, ensure_ascii=False)
            return True
    return False


def apply_to_prediction(element_id, draft_text):
    slug = element_id.split(":", 1)[1]
    path = ENGINE_DATA_DIR / "predictions.json"
    with open(path) as f:
        preds = json.load(f)
    for p in preds:
        if str(p.get("year", "")) == slug:
            conditions = p.setdefault("conditions", {})
            existing = conditions.get("watch_for", "")
            conditions["watch_for"] = (existing + "\n\n" + draft_text).strip()
            with open(path, "w") as f:
                json.dump(preds, f, indent=2, ensure_ascii=False)
            return True
    return False


def apply_draft(draft):
    """Apply an approved draft to the relevant engine JSON. Returns True on success."""
    text = draft.get("edited_text") or draft.get("draft_text", "")
    if not text:
        return False
    etype = draft.get("element_type")
    eid = draft.get("element_id")
    try:
        if etype == "scorecard":
            return apply_to_scorecard(eid, text)
        elif etype == "divergence":
            return apply_to_divergence(eid, text)
        elif etype == "prediction":
            return apply_to_prediction(eid, text)
    except Exception as e:
        print(color(f"  Apply error: {e}", RED))
        return False
    return False


def display_draft(draft, idx, total):
    """Pretty-print one draft for the user."""
    rel = draft.get("relationship", "?").upper()
    rel_color = {"CONFIRMS": GREEN, "CONTRADICTS": RED, "REFINES": YELLOW}.get(rel, WHITE)
    conf = draft.get("confidence", "?").upper()
    conf_color = {"HIGH": GREEN, "MEDIUM": YELLOW, "LOW": DIM}.get(conf, WHITE)

    print()
    print(color("─" * 78, DIM))
    print(f"{color(f'[{idx}/{total}]', BOLD)} "
          f"{color(draft['element_type'].upper(), MAGENTA)} → "
          f"{color(draft['element_label'], BOLD)}")
    print(f"  {color(rel, rel_color)} · {color(conf + ' confidence', conf_color)} · "
          f"similarity {int(draft.get('similarity', 0) * 100)}%")
    print()
    print(color("DRAFT:", BOLD))
    text = draft.get("edited_text") or draft.get("draft_text", "")
    for line in text.split("\n"):
        print(f"  {line}")
    print()
    print(color("PASTE-QUOTE FROM SOURCE:", BOLD))
    quote = draft.get("quote", "")
    print(f"  {color('“' + quote + '”', CYAN)}")
    print()
    print(color("SOURCE:", BOLD))
    print(f"  {draft.get('source_publisher', 'unknown')} — {draft.get('source_title', '')[:80]}")
    print(f"  {color(draft.get('source_url', ''), BLUE)}")
    if draft.get("rationale"):
        print()
        print(color("RATIONALE:", DIM) + " " + color(draft["rationale"], DIM))
    print()


def edit_draft_text(current_text):
    """Open the user's $EDITOR with the draft text. Returns edited text."""
    import os
    import tempfile
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write(current_text)
        path = f.name
    try:
        subprocess.call([editor, path])
        with open(path) as f:
            return f.read().strip()
    finally:
        os.unlink(path)


def main():
    pending = load_pending()
    pending_items = [p for p in pending if p.get("status") == "pending"]

    if not pending_items:
        print(color("No pending updates to review.", DIM))
        print(f"({len(pending)} total drafts in queue, all decided)")
        return

    # Sort by confidence: high → medium → low
    conf_order = {"high": 0, "medium": 1, "low": 2}
    pending_items.sort(key=lambda p: (conf_order.get(p.get("confidence", "low"), 3), -p.get("similarity", 0)))

    print(color(f"{BOLD}Psychohistory Engine — Review Queue{RESET}", CYAN))
    print(color(f"{len(pending_items)} pending updates", DIM))
    print()
    print("Commands: " + color("a", GREEN) + "pprove · " + color("e", YELLOW) + "dit · "
          + color("r", RED) + "eject · " + color("s", DIM) + "kip · " + color("q", DIM) + "uit")

    applied_count = 0
    rejected_count = 0
    skipped_count = 0

    for idx, draft in enumerate(pending_items, 1):
        display_draft(draft, idx, len(pending_items))
        while True:
            choice = input(color("> ", BOLD)).strip().lower()
            if choice == "a" or choice == "approve":
                if apply_draft(draft):
                    draft["status"] = "approved"
                    draft["decided_at"] = datetime.now().isoformat()
                    save_pending(pending)
                    applied_count += 1
                    print(color("✓ Applied to engine.", GREEN))
                else:
                    print(color("✗ Apply failed (engine element not found?). Marking as rejected.", RED))
                    draft["status"] = "rejected"
                    save_pending(pending)
                    rejected_count += 1
                break
            elif choice == "e" or choice == "edit":
                current = draft.get("edited_text") or draft.get("draft_text", "")
                edited = edit_draft_text(current)
                draft["edited_text"] = edited
                print(color("Edited. New text:", YELLOW))
                for line in edited.split("\n"):
                    print(f"  {line}")
                print(color("Now: [a]pprove or [r]eject?", BOLD))
                continue
            elif choice == "r" or choice == "reject":
                draft["status"] = "rejected"
                draft["decided_at"] = datetime.now().isoformat()
                save_pending(pending)
                rejected_count += 1
                print(color("✗ Rejected.", DIM))
                break
            elif choice == "s" or choice == "skip":
                skipped_count += 1
                print(color("→ Skipped (still pending).", DIM))
                break
            elif choice == "q" or choice == "quit":
                print()
                print(color(f"Quitting. Decided: {applied_count} approved, {rejected_count} rejected, {skipped_count} skipped.", DIM))
                _offer_finalize(applied_count)
                return
            else:
                print(color("? a/e/r/s/q", DIM))

    print()
    print(color("─" * 78, DIM))
    print(color(f"Done. {applied_count} approved · {rejected_count} rejected · {skipped_count} skipped", BOLD))
    _offer_finalize(applied_count)


def _offer_finalize(applied_count):
    """If anything was approved, offer to rebuild + push."""
    if applied_count == 0:
        return
    print()
    answer = input(color(f"Rebuild export.txt and push to live site? [y/N] ", BOLD)).strip().lower()
    if answer == "y":
        print(color("→ Rebuilding export.txt...", DIM))
        try:
            subprocess.run(["python3", str(DEPLOY_DIR / "build-export.py")], check=True)
        except Exception as e:
            print(color(f"  build-export error: {e}", RED))
            return
        print(color("→ Building site...", DIM))
        try:
            subprocess.run(["npm", "run", "build"], cwd="/Users/jamienucho/psychohistory-v2", check=True)
        except Exception as e:
            print(color(f"  npm build error: {e}", RED))
            return
        print(color("→ Syncing to deploy dir...", DIM))
        rsync_cmd = [
            "rsync", "-av", "--delete",
            "--exclude=.git", "--exclude=CNAME", "--exclude=.gitignore",
            "--exclude=README.md", "--exclude=current_events.json",
            "--exclude=data_feeds.py", "--exclude=engine_index.py",
            "--exclude=engine_index_cache.json", "--exclude=interpret_events.py",
            "--exclude=review_pending.py", "--exclude=pending_updates.json",
            "--exclude=.github", "--exclude=build-export.py", "--exclude=export.txt",
            "--exclude=psychohistory", "--exclude=sitemap.xml",
            "/Users/jamienucho/psychohistory-v2/out/",
            str(DEPLOY_DIR) + "/",
        ]
        try:
            subprocess.run(rsync_cmd, check=True, capture_output=True)
        except Exception as e:
            print(color(f"  rsync error: {e}", RED))
            return
        print(color("→ Committing and pushing...", DIM))
        try:
            subprocess.run(["git", "add", "-A"], cwd=str(DEPLOY_DIR), check=True)
            subprocess.run(["git", "commit", "-m", f"Engine updates from review session ({applied_count} approved)"], cwd=str(DEPLOY_DIR), check=True)
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=str(DEPLOY_DIR), check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=str(DEPLOY_DIR), check=True)
            print(color("✓ Live in ~1 minute.", GREEN))
        except Exception as e:
            print(color(f"  git error: {e}", RED))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(color("Interrupted.", DIM))
        sys.exit(0)
