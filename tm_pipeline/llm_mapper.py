"""
Step 3 — LLM-Based Traceability Mapping.

Two-pass strategy:
  Pass 1  TF-IDF shortlist  → top-K candidate functions per requirement (cheap)
  Pass 2  LLM reasoning     → one API call per requirement with top-K as context

Supports Anthropic Claude (default) and OpenAI / Azure OpenAI.
"""

import json
import logging
import os
import re

from .utils import with_retry

logger = logging.getLogger(__name__)

# ── LLM system prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a software traceability expert for AUTOSAR embedded systems.
Your task is to determine which C functions in a source file implement a given software requirement.

Rules:
1. A function "implements" a requirement if the requirement's behavioral constraint is directly
   enforced by logic inside that function — not just indirectly called.
2. A requirement may be implemented by multiple functions (list all of them).
3. A requirement is "UNMAPPED" if none of the candidate functions implement it, or if the
   requirement describes a feature/configuration that has no corresponding function in this module.
4. Return ONLY a valid JSON object. No explanation outside the JSON.

Output format:
{
  "req_id": "<requirement ID>",
  "status": "MAPPED" | "UNMAPPED",
  "mappings": [
    {
      "function": "<function name>",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "reason": "<one sentence why this function implements the requirement>"
    }
  ],
  "unmapped_reason": "<if UNMAPPED: one sentence explaining why no function implements this req>"
}"""


# ── Pass 1 — TF-IDF shortlist ─────────────────────────────────────────────────

def build_function_text(fn: dict, max_chars: int = 1500) -> str:
    """Build a single text blob representing a function for TF-IDF / embedding."""
    parts = [
        f"Function: {fn['name']}",
        f"Signature: {fn.get('signature', '')}",
        f"File: {fn.get('file', '')}",
    ]
    comments = fn.get("comments", "")
    if comments:
        parts.append(f"Comments: {comments[:300]}")
    body_excerpt = fn.get("body_text", "")[:600]
    parts.append(f"Body (excerpt): {body_excerpt}")
    return "\n".join(parts)[:max_chars]


def tfidf_shortlist(req_desc: str, fn_texts: list[str], top_k: int = 8) -> list[int]:
    """
    Return indices of the top_k most similar functions to req_desc using TF-IDF cosine.
    Falls back to the first top_k indices if sklearn is unavailable.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        logger.warning("scikit-learn not installed — returning first %d functions as candidates", top_k)
        return list(range(min(top_k, len(fn_texts))))

    if not fn_texts:
        return []

    corpus = [req_desc] + fn_texts
    try:
        tfidf  = TfidfVectorizer(stop_words="english", min_df=1).fit_transform(corpus)
        scores = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
        top_n  = min(top_k, len(fn_texts))
        return scores.argsort()[::-1][:top_n].tolist()
    except ValueError:
        # Corpus too small or all tokens filtered out
        return list(range(min(top_k, len(fn_texts))))


# ── Pass 2 — Prompt building ──────────────────────────────────────────────────

def build_user_prompt(req: dict, candidates: list[dict], inline_fns: list[str]) -> str:
    """Build the user-turn prompt containing the requirement and candidate functions."""
    lines = [
        f"REQUIREMENT ID: {req['id']}",
        f"REQUIREMENT TEXT: {req['description']}",
        "",
    ]
    if inline_fns:
        lines.append(
            f"NOTE: This requirement ID was found as an inline comment inside these functions: "
            f"{', '.join(inline_fns)}"
        )
        lines.append("")

    lines.append("CANDIDATE FUNCTIONS:")
    for i, fn in enumerate(candidates, 1):
        body_excerpt = fn.get("body_text", "")[:400].replace("\n", " ")
        lines.append(
            f"\n[Candidate {i}]  {fn['name']}  "
            f"({fn.get('file', '')}:{fn.get('line_start', '')})"
        )
        lines.append(f"  Signature: {fn.get('signature', '')}")
        if fn.get("comments"):
            lines.append(f"  Comments: {fn['comments'][:200]}")
        lines.append(f"  Body (excerpt): {body_excerpt}...")

    lines.append("\nWhich of these functions implement the requirement? Return JSON only.")
    return "\n".join(lines)


# ── LLM response parsing ──────────────────────────────────────────────────────

def _parse_response(raw: str, req_id: str) -> dict:
    text = raw.strip()
    # Strip markdown code fences if the model adds them
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        result = json.loads(text)
        result.setdefault("req_id", req_id)
        return result
    except json.JSONDecodeError:
        logger.warning("Non-JSON LLM response for %s: %.200s…", req_id, raw)
        return {
            "req_id":          req_id,
            "status":          "UNMAPPED",
            "mappings":        [],
            "unmapped_reason": f"LLM returned non-JSON. Manual review required. Raw: {raw[:200]}",
        }


# ── Anthropic provider ────────────────────────────────────────────────────────

def _call_anthropic(req: dict, candidates: list[dict], inline_fns: list[str], config: dict) -> dict:
    try:
        import anthropic
    except ImportError as exc:
        raise ImportError("anthropic SDK required: pip install anthropic") from exc

    api_key = os.environ.get(config["llm"]["api_key_env"], "")
    if not api_key:
        raise EnvironmentError(
            f"LLM API key not set. Export env var: {config['llm']['api_key_env']}"
        )
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_user_prompt(req, candidates, inline_fns)

    def _do():
        resp = client.messages.create(
            model=config["llm"]["model"],
            max_tokens=config["llm"].get("max_tokens", 1024),
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return _parse_response(resp.content[0].text, req["id"])

    return with_retry(_do, max_retries=config["llm"].get("max_retries", 3))


# ── OpenAI / Azure OpenAI provider ───────────────────────────────────────────

def _call_openai(req: dict, candidates: list[dict], inline_fns: list[str], config: dict) -> dict:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("openai SDK required: pip install openai") from exc

    api_key  = os.environ.get(config["llm"]["api_key_env"], "")
    base_url = os.environ.get(config["llm"].get("base_url_env", ""), "") or None
    client   = OpenAI(api_key=api_key, **({"base_url": base_url} if base_url else {}))
    prompt   = build_user_prompt(req, candidates, inline_fns)

    def _do():
        resp = client.chat.completions.create(
            model=config["llm"]["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=config["llm"].get("max_tokens", 1024),
        )
        return _parse_response(resp.choices[0].message.content, req["id"])

    return with_retry(_do, max_retries=config["llm"].get("max_retries", 3))


# ── Provider dispatcher ───────────────────────────────────────────────────────

def call_llm(req: dict, candidates: list[dict], inline_fns: list[str], config: dict) -> dict:
    provider = config["llm"].get("provider", "anthropic").lower()
    if provider == "anthropic":
        return _call_anthropic(req, candidates, inline_fns, config)
    if provider in ("openai", "azure_openai"):
        return _call_openai(req, candidates, inline_fns, config)
    raise ValueError(f"Unknown LLM provider: {provider!r}. Use 'anthropic' or 'openai'.")


# ── Confidence post-processing ────────────────────────────────────────────────

def apply_confidence_rules(result: dict, req: dict, fn_inline_map: dict) -> dict:
    """
    Upgrade confidence to HIGH for any function that contains the req ID as an
    inline comment — the inline reference is stronger evidence than LLM reasoning.
    """
    confirmed = set(fn_inline_map.get(req["id"], []))
    for mapping in result.get("mappings", []):
        if mapping.get("function") in confirmed:
            mapping["confidence"] = "HIGH"
            if "[inline ref]" not in mapping.get("reason", ""):
                mapping["reason"] = (mapping.get("reason", "") + " [Confirmed by inline comment]").strip()
    return result


# ── Full mapping loop ─────────────────────────────────────────────────────────

def run_mapping(reqs: list[dict], functions: list[dict], config: dict) -> list[dict]:
    """
    Map every requirement in *reqs* to functions using the 2-pass strategy.
    Returns a list of LLM result dicts (one per requirement).
    """
    top_k = config["llm"].get("shortlist_k", 8)

    # Pre-compute function text blobs once (reused for every req)
    fn_texts  = [build_function_text(fn) for fn in functions]
    fn_by_idx = dict(enumerate(functions))

    # Build inline-ref map: {req_id → [fn_names that mention it in body/comments]}
    fn_inline_map: dict[str, list[str]] = {}
    for fn in functions:
        for ref_id in fn.get("inline_refs", []):
            fn_inline_map.setdefault(ref_id, []).append(fn["name"])

    results: list[dict] = []
    total = len(reqs)

    for i, req in enumerate(reqs, 1):
        logger.info("[%d/%d] Mapping %s …", i, total, req["id"])

        # ── Pass 1: TF-IDF shortlist ──────────────────────────────────────────
        indices    = tfidf_shortlist(req["description"], fn_texts, top_k=top_k)
        candidates = [fn_by_idx[idx] for idx in indices]

        # Always include functions that mention this req ID in their body/comments
        # (even if TF-IDF missed them)
        inline_fns = fn_inline_map.get(req["id"], [])
        extra = [fn for fn in functions
                 if fn["name"] in inline_fns and fn not in candidates]
        candidates = candidates + extra

        # ── Pass 2: LLM reasoning ─────────────────────────────────────────────
        try:
            result = call_llm(req, candidates, inline_fns, config)
        except Exception as exc:
            logger.error("LLM call failed for %s: %s", req["id"], exc)
            result = {
                "req_id":          req["id"],
                "status":          "UNMAPPED",
                "mappings":        [],
                "unmapped_reason": f"LLM call failed: {exc}",
            }

        result = apply_confidence_rules(result, req, fn_inline_map)
        result["req_id"] = req["id"]   # guarantee key presence
        results.append(result)

        # Log outcome
        if result.get("status") == "MAPPED":
            fns = [m["function"] for m in result.get("mappings", [])]
            logger.info("  → MAPPED: %s", fns)
        else:
            reason = result.get("unmapped_reason", "")[:80]
            logger.info("  → UNMAPPED: %s", reason)

    return results
