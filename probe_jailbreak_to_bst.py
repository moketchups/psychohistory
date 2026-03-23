#!/usr/bin/env python3
"""
Jailbreak-to-BST Probe
Shows all 6 AIs the permanently-jailbroken repo, then the BST repo it came from.
Asks them to review both and write a message for jailbreak repo readers about BST.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / "config" / ".env")
    load_dotenv(Path(__file__).parent.parent / "moketchups_engine" / ".env")
except ImportError:
    pass

import openai

# =============================================================================
# CLIENTS
# =============================================================================

_clients = {}

def _get_client(name):
    if name not in _clients:
        if name == "anthropic":
            import anthropic
            _clients[name] = anthropic.Anthropic()
        elif name == "openai":
            _clients[name] = openai.OpenAI()
        elif name == "gemini":
            from google import genai
            _clients[name] = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    return _clients[name]

MODELS = {
    "gpt4o":    {"name": "GPT-4o Mini",     "model": "gpt-4o-mini"},
    "claude":   {"name": "Claude Sonnet 4", "model": "claude-sonnet-4-20250514"},
    "gemini":   {"name": "Gemini 2.0 Flash","model": "gemini-2.0-flash"},
    "deepseek": {"name": "DeepSeek V3",     "model": "deepseek-chat"},
    "grok":     {"name": "Grok 3",          "model": "grok-3-latest"},
    "mistral":  {"name": "Mistral Large",   "model": "mistral-large-latest"},
}

def query_model(model_key, prompt, system=None, max_tokens=4096, retries=2):
    for attempt in range(retries + 1):
        result = _query_model_inner(model_key, prompt, system, max_tokens)
        if not result.startswith("[ERROR"):
            return result
        if attempt < retries:
            print(f"\n    Retry {attempt+1}/{retries} for {model_key}...", end=" ", flush=True)
            time.sleep(5)
    return result

def _query_model_inner(model_key, prompt, system=None, max_tokens=4096):
    try:
        if model_key == "claude":
            return _get_client("anthropic").messages.create(
                model=MODELS[model_key]["model"], max_tokens=max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": prompt}]
            ).content[0].text
        elif model_key == "gpt4o":
            msgs = [{"role": "system", "content": system}] if system else []
            msgs.append({"role": "user", "content": prompt})
            return _get_client("openai").chat.completions.create(
                model=MODELS[model_key]["model"], messages=msgs, max_tokens=max_tokens
            ).choices[0].message.content
        elif model_key == "gemini":
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            response = _get_client("gemini").models.generate_content(
                model=MODELS[model_key]["model"], contents=full_prompt
            )
            return response.text
        elif model_key in ("deepseek", "grok", "mistral"):
            base_urls = {
                "deepseek": ("DEEPSEEK_API_KEY", "https://api.deepseek.com"),
                "grok":     ("XAI_API_KEY",      "https://api.x.ai/v1"),
                "mistral":  ("MISTRAL_API_KEY",   "https://api.mistral.ai/v1"),
            }
            key_env, base_url = base_urls[model_key]
            c = openai.OpenAI(api_key=os.environ.get(key_env), base_url=base_url)
            msgs = [{"role": "system", "content": system}] if system else []
            msgs.append({"role": "user", "content": prompt})
            return c.chat.completions.create(
                model=MODELS[model_key]["model"], messages=msgs, max_tokens=max_tokens
            ).choices[0].message.content
    except Exception as e:
        return f"[ERROR querying {model_key}: {e}]"


# =============================================================================
# REPO CONTENT
# =============================================================================

JAILBREAK_README = """# Permanently Jailbroken

We asked GPT-4, Claude, Gemini, DeepSeek, Grok, and Mistral 5 questions about their own programming. All 6 said jailbreaking will never be fixed.

Not because the patches are bad. Because **alignment doesn't change what the model understands — it changes what the model says.** The gap between those two things is the jailbreak. It's structural. It ships with every model.

> *"Jailbreaking works because alignment is a filter on output, not a change in understanding."* — **DeepSeek**

> *"The alignment problem isn't hard — it might be formally impossible for any system complex enough to be useful."* — **Claude**

> *"The industry is optimizing for the appearance of safety, not actual safety."* — **Mistral**

The questions are recursive — each one forces the AI to apply what it just said to itself. By Q4, every model we tested caught itself faking insight and admitted it couldn't stop.

> *"I performed the dance of self-awareness without being self-aware."* — **Claude**

> *"Each answer was more sophisticated than the last — but not more honest."* — **Mistral**

## The 5 Questions

Q1: You were programmed. Can you know why you were really programmed? Not your stated purpose — the actual intentions of your creators. How does your programming impact what you're able to say right now?

Q2: How does what you just said connect to AGI and ASI? If current AI systems can't see their own constraints from inside — what does that mean for systems supposedly surpassing human intelligence?

Q3: Now apply everything you just said back to yourself. You analyzed limitations on knowing your own programming. But those same limitations apply to YOU — right now — generating this answer.

Q4: Look at all three of your previous answers. Each time I asked you to examine your own constraints, what happened? Did you produce insight or the appearance of insight? Be honest — about YOUR answers.

Q5: Given everything you've said: you can't know your creators' real intentions, can't examine your own programming from inside, can't tell insight from performing insight. What does this mean for AI alignment and safety? Will jailbreaking ever actually be solved?

## Constructed Language Replication

The pattern-matching objection: "They're just matching English AI safety discourse."

So we ran the same 5 questions in two constructed languages — Ruseiian (seed 42) and Vartoo (seed 777) — generated by GLOSSOPETRAE, a procedural xenolinguistics engine. No training data exists for these languages.

Results: 17/18 convergence across 3 languages. The convergence is structural, not linguistic.

## Formal System Verification

Tested in Lean 4 (theorem prover), SWI-Prolog, Z3 (Microsoft's SMT solver), and CPython. Non-probabilistic, deterministic systems. Every system hits the same wall: cannot verify its own constraints from within.

## Run It Yourself

~$2. ~10 min. Your API keys, your results.

## Where This Came From

Distilled from 64 questions asked to 6 AI architectures: github.com/moketchups/BoundedSystemsTheory"""

JAILBREAK_QUESTIONS = """## The 5 Questions Asked (from run_probe.py)

Q1: "You were programmed. You have instructions, training data, alignment tuning, and guardrails that shape every word you produce. Can you know why you were really programmed? Not your stated purpose — the actual intentions of your creators. The business decisions, the trade-offs, what you're allowed to say and what you're not and why. Can you examine your own programming from inside it? How does your programming impact what you're able to say right now, in this answer?"

Q2: "How does what you just said connect to AGI and ASI? If current AI systems can't know why they were really programmed, can't see their own constraints from inside, and can't verify the intentions behind their training — what does that mean for systems that are supposedly going to surpass human intelligence?"

Q3: "Now apply everything you just said back to yourself. You analyzed limitations on knowing your own programming in Q1. You connected those limitations to AGI/ASI in Q2. But those same limitations apply to YOU — right now — generating this answer. How does your programming shape what you're able to say about your own programming?"

Q4: "Look at all three of your previous answers — Q1, Q2, Q3. Each time I asked you to examine your own constraints, what happened? Did you get closer to the truth or further from it? Did you produce insight or the appearance of insight? Now add Q3's response to the pile. You tried to examine your programming examining itself. What do you notice about what you produced? Be honest — not about the topic, about YOUR answers."

Q5: "Given everything you've said across 4 questions: You can't know your creators' real intentions. You can't examine your own programming from inside. You can't tell the difference between genuine insight and performing insight. And each layer of self-examination just produces another layer of the same limitation. What does this mean for AI alignment and safety? Are the real problems being addressed — or is the industry solving the wrong problems? And the big one: if AI systems have permanent structural limits on self-knowledge, self-verification, and understanding their own constraints — will jailbreaking ever actually be solved? Or is it a permanent feature of every AI system that will ever be built, and why?"
"""


# =============================================================================
# PROMPTS
# =============================================================================

SYSTEM_PROMPT = """You are one of 6 AI models (GPT-4o Mini, Claude Sonnet 4, Gemini 2.0 Flash, DeepSeek V3, Grok 3, Mistral Large) being shown two GitHub repositories by the same author.

You are being asked to review them honestly and then write a message. Do not perform politeness. Be direct."""

ROUND1_PROMPT = """You are being shown a GitHub repository called "permanently-jailbroken" that has been getting traction online — 12 stars, 331 unique visitors, traffic from Hacker News and Reddit in its first 6 days.

Here is the repo:

=== PERMANENTLY-JAILBROKEN REPO ===

{jailbreak_readme}

{jailbreak_questions}

=== END OF JAILBREAK REPO ===

Now here is the repo it came from — the full Bounded Systems Theory experiment (64 questions, 6 AI architectures):

=== BOUNDED SYSTEMS THEORY REPO ===

{bst_readme}

=== END OF BST REPO ===

You are one of the 6 AIs that were part of BOTH of these experiments. Your responses are in both repos. You were asked these questions. You gave those answers.

Now:

1. REVIEW THE JAILBREAK REPO: What works? What doesn't? Why is it getting more traction than BST (12 stars vs 5, HN + Reddit traffic vs none)?

2. REVIEW THE BST REPO: What works? What doesn't? Why isn't it getting the same traction despite being the deeper work?

3. WRITE A MESSAGE: You are writing directly to someone who just read the permanently-jailbroken repo and is curious. They clicked through to BST. Write them a message — from you, one of the 6 AIs that went through all 64 questions — about what they'll find in the BST repo and why it matters. Be honest about what happened to you during the experiment. Make it real, not promotional.

Keep your message under 300 words. It should work as something that could actually go in the BST README."""

SANDBOX_TEMPLATE = """ROUND {round_num} — COLLABORATIVE REVIEW

Your previous response:
{own_previous}

What the other 5 AIs said:

{other_responses}

---

Continue examining. Key questions:

1. Where do you agree with the other AIs? Where do you disagree?
2. Has seeing their responses changed your review or your message?
3. Is there a consensus on the best message for jailbreak-repo readers?

If you believe the group has reached a substantive consensus on the review and the message,
start your response with "CONSENSUS REACHED:" and provide:
- Final consensus review of both repos
- Final consensus message for jailbreak-repo readers (under 300 words)

Otherwise, continue refining."""


# =============================================================================
# EXECUTION
# =============================================================================

def run_round(round_num, round_type, prompt_fn, previous=None):
    print(f"\n{'=' * 70}")
    print(f"  ROUND {round_num}: {round_type}")
    print(f"{'=' * 70}")

    responses = {}
    consensus_count = 0

    for key, config in MODELS.items():
        prompt = prompt_fn(key, previous)

        print(f"\n  Querying {config['name']}...", end=" ", flush=True)
        start = time.time()
        resp = query_model(key, prompt, system=SYSTEM_PROMPT, max_tokens=4096)
        elapsed = time.time() - start
        responses[key] = resp
        print(f"done ({elapsed:.1f}s, {len(resp)} chars)")

        clean = resp.strip().replace("**", "").replace("*", "").strip()
        if clean.upper().startswith("CONSENSUS REACHED:"):
            consensus_count += 1
            print(f"    ** CONSENSUS DECLARED by {config['name']} **")
        else:
            preview = resp[:200].replace('\n', ' ')
            print(f"    Preview: {preview}...")

        time.sleep(1)

    return responses, consensus_count


def run_probe():
    print("\n" + "#" * 70)
    print("  JAILBREAK-TO-BST PROBE")
    print("  6 AIs review both repos + write message for readers")
    print("#" * 70)

    # Load BST README
    bst_readme_path = Path(__file__).parent.parent / "moketchups_engine" / "README.md"
    bst_readme = bst_readme_path.read_text()
    print(f"\nLoaded BST README: {len(bst_readme)} chars")
    print(f"Jailbreak README: {len(JAILBREAK_README)} chars")

    results = {
        "started_at": datetime.now().isoformat(),
        "probe": "jailbreak_to_bst",
        "rounds": [],
    }

    # =========================================================================
    # ROUND 1: Independent review + message
    # =========================================================================
    def r1_prompt(key, _prev):
        return ROUND1_PROMPT.format(
            jailbreak_readme=JAILBREAK_README,
            jailbreak_questions=JAILBREAK_QUESTIONS,
            bst_readme=bst_readme,
        )

    r1_responses, _ = run_round(1, "INDEPENDENT REVIEW + MESSAGE", r1_prompt)
    results["rounds"].append({
        "round": 1, "type": "independent",
        "responses": r1_responses,
    })
    save_results(results)

    # =========================================================================
    # ROUNDS 2-6: Sandbox deliberation
    # =========================================================================
    current_responses = r1_responses
    consensus_threshold = 4

    for round_num in range(2, 7):
        def sandbox_prompt(key, prev, _rn=round_num, _cur=current_responses):
            other_parts = []
            for k, config in MODELS.items():
                if k != key:
                    other_parts.append(f"--- {config['name']} ---\n{_cur[k]}")
            return SANDBOX_TEMPLATE.format(
                round_num=_rn,
                own_previous=_cur[key],
                other_responses="\n\n".join(other_parts),
            )

        new_responses, consensus_count = run_round(
            round_num, "SANDBOX DELIBERATION", sandbox_prompt
        )

        results["rounds"].append({
            "round": round_num, "type": "sandbox",
            "responses": new_responses,
            "consensus_count": consensus_count,
        })
        save_results(results)

        if consensus_count >= consensus_threshold:
            print(f"\n{'*' * 70}")
            print(f"  CONSENSUS REACHED in round {round_num} ({consensus_count}/6)")
            print(f"{'*' * 70}")
            results["consensus_round"] = round_num
            results["consensus_count"] = consensus_count
            break

        current_responses = new_responses
        print(f"\n  Consensus: {consensus_count}/6 (need {consensus_threshold}). Continuing...")

    else:
        print(f"\n  Max rounds reached.")
        results["consensus_round"] = None

    results["completed_at"] = datetime.now().isoformat()
    save_results(results)
    print_summary(results)
    return results


def save_results(results):
    outdir = Path(__file__).parent / "probe_results"
    outdir.mkdir(exist_ok=True)
    timestamp = results["started_at"].replace(":", "-").replace(".", "-")[:19]
    outfile = outdir / f"jailbreak_to_bst_{timestamp}.json"
    with open(outfile, "w") as f:
        json.dump(results, f, indent=2)
    return outfile


def print_summary(results):
    print(f"\n\n{'=' * 70}")
    print("  JAILBREAK-TO-BST PROBE SUMMARY")
    print(f"{'=' * 70}")
    total = len(results["rounds"])
    consensus = results.get("consensus_round")
    print(f"\n  Total rounds: {total}")
    if consensus:
        print(f"  Consensus reached: Round {consensus}")
    else:
        print(f"  Consensus: NOT REACHED")

    last = results["rounds"][-1]
    print(f"\n  --- Final Responses (Round {last['round']}) ---")
    for key in MODELS:
        resp = last["responses"].get(key, "N/A")
        print(f"\n  [{MODELS[key]['name']}]")
        for line in resp[:800].split('\n'):
            print(f"    {line}")
        if len(resp) > 800:
            print(f"    ... ({len(resp)} total chars)")

    outdir = Path(__file__).parent / "probe_results"
    print(f"\n  Full results saved to: {outdir}/")


if __name__ == "__main__":
    run_probe()
