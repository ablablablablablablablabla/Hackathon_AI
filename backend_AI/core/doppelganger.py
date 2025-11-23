# api/core/doppelganger.py
import re
import asyncio
from typing import Dict, Any
from openai import OpenAI
from adapters.crossref import search_papers_on_crossref
from adapters.web_parser import extract_abstract_from_url
from settings import settings
from logger import logger

# reuse helper to run sync OpenAI calls without blocking
async def _run_sync(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)

async def generate_search_query_for_doppelganger(text: str, client: OpenAI) -> str:
    prompt = f"""
    You are a cross-disciplinary scientific search expert.
    Create a concise English Crossref query that captures the core conceptual pattern of the text —
    not specific terms like species or stress types, but general dynamics:
    e.g., "nonlinear response during transition phase", "interaction of sequential perturbations", "emergent behavior after system reset".

    Avoid domain-specific nouns. Focus on universal scientific concepts: system dynamics, phase transition, perturbation response, adaptive window.

    Return ONLY the query. No explanations.

    Text: {text[:2000]}
    """
    try:
        def sync_call():
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=0.3,
                timeout=settings.openai_timeout
            )
            query = resp.choices[0].message.content.strip()
            return re.sub(r'["\[\]`]', '', query)
        return await _run_sync(sync_call)
    except Exception as e:
        logger.error(f"Error generating doppelganger query: {e}")
        return ""

async def is_doppelganger(original: str, candidate_abstract: str, client: OpenAI) -> dict:
    prompt = f"""
    Analyze two scientific texts and respond strictly in the following format — three separate lines:

    Line 1: "Yes" or "No"
    Line 2: Scientific domain of the candidate (e.g., neuroscience, sociology, materials science, machine learning)
    Line 3: 1–2 sentences in English: why the works are (or are not) doppelgängers. Describe similarity in logic, pattern, or concept — despite different objects or disciplines.

    Original text:
    {original[:1500]}

    Candidate:
    {candidate_abstract[:1500]}
    """
    try:
        def sync_call():
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.2,
                timeout=settings.openai_timeout
            )
            return resp.choices[0].message.content.strip()
        raw = await _run_sync(sync_call)
        lines = [line.strip() for line in raw.split('\n') if line.strip()]

        if len(lines) < 3:
            return {"is_doppelganger": False, "reason": "", "domain": ""}

        is_doppel = lines[0].lower() == "yes"
        domain = lines[1]
        reason = lines[2]

        return {
            "is_doppelganger": is_doppel,
            "reason": reason,
            "domain": domain
        }
    except Exception as e:
        logger.warning(f"Error analyzing paper (doppelganger): {e}")
        return {"is_doppelganger": False, "reason": "", "domain": ""}

async def rank_doppelgangers(doppelgangers: list, original_text: str, client: OpenAI) -> dict:
    if not doppelgangers:
        return {
            "all_doppelgangers_with_reasons": [],
            "top_3": {"papers": [], "justification": "No doppelgängers found."}
        }

    all_entries = []
    for i, d in enumerate(doppelgangers, start=1):
        all_entries.append({
            "id": i,
            "title": d["title"],
            "url": d["url"],
            "domain": d["domain"],
            "reason": d["reason"]
        })

    if len(doppelgangers) <= 3:
        top_list = [{**entry, "place": i} for i, entry in enumerate(all_entries, start=1)]
        justification = "Fewer than four doppelgängers found — all included in top."
    else:
        titles_reasons = "\n\n".join(
            f"{i+1}. {d['title']} ({d['domain']})\n   Reason: {d['reason']}"
            for i, d in enumerate(doppelgangers)
        )

        prompt = f"""
        Below are scientific papers identified as doppelgängers to the original text.
        Select the TOP-3 most significant ones — those where the analogy:
        - is deepest (not superficial),
        - offers the greatest potential for interdisciplinary breakthrough,
        - or clearly reflects the same conceptual structure.

        Respond in this format:
        TOP-1: [number from list]
        TOP-2: [number]
        TOP-3: [number]

        Justification (2–3 sentences in English): why these three papers are stronger than the others?

        Original text:
        {original_text[:800]}

        Candidates:
        {titles_reasons}
        """
        try:
            def sync_call():
                resp = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3,
                    timeout=settings.openai_timeout
                )
                return resp.choices[0].message.content.strip()
            raw = await _run_sync(sync_call)

            top_indices = []
            for line in raw.split('\n'):
                if line.startswith("TOP-"):
                    match = re.search(r'TOP-\d+:\s*(\d+)', line)
                    if match:
                        idx = int(match.group(1)) - 1
                        if 0 <= idx < len(doppelgangers):
                            top_indices.append(idx)

            seen = set()
            top_unique = []
            for idx in top_indices:
                if idx not in seen:
                    top_unique.append(all_entries[idx])
                    seen.add(idx)
                    if len(top_unique) == 3:
                        break

            if len(top_unique) < 3:
                for i in range(len(all_entries)):
                    if i not in seen and len(top_unique) < 3:
                        top_unique.append(all_entries[i])

            top_list = [{**entry, "place": i + 1} for i, entry in enumerate(top_unique)]
            justification_match = re.search(r'Justification.*?:\s*(.+)', raw, re.DOTALL | re.IGNORECASE)
            justification = justification_match.group(1).strip() if justification_match else "Automatic justification unavailable."

        except Exception as e:
            logger.warning(f"Failed to rank doppelgängers: {e}")
            top_list = [{**entry, "place": i + 1} for i, entry in enumerate(all_entries[:3])]
            justification = "Ranking failed — top three doppelgängers selected by order."

    return {
        "all_doppelgangers_with_reasons": all_entries,
        "top_3": {
            "papers": top_list,
            "justification": justification
        }
    }

async def run_doppelganger_search(input_text: str, client: OpenAI) -> Dict[str, Any]:
    query = await generate_search_query_for_doppelganger(input_text, client)
    if not query:
        return {"type": "error", "message": "Failed to generate interdisciplinary query"}

    items = await search_papers_on_crossref(query, limit=settings.crossref_doppelganger_limit)
    doppelgangers = []

    async def process_item(item):
        title = (item.get("title") or [""])[0]
        url = item.get("URL", "")
        abstract = item.get("abstract", "") or ""

        if not abstract or len(abstract) < 100:
            abstract = await extract_abstract_from_url(url)
            if not abstract or len(abstract) < 100:
                return None

        result = await is_doppelganger(input_text, abstract, client)
        if result["is_doppelganger"]:
            return {
                "title": title,
                "url": url,
                "domain": result["domain"],
                "reason": result["reason"]
            }
        return None

    semaphore = asyncio.Semaphore(6)
    async def sem_process(it):
        async with semaphore:
            return await process_item(it)

    tasks = [sem_process(it) for it in items]
    results = await asyncio.gather(*tasks)
    for r in results:
        if r:
            doppelgangers.append(r)

    ranking = await rank_doppelgangers(doppelgangers, input_text, client)

    return {
        "type": "doppelganger",
        "count": len(doppelgangers),
        "all_doppelgangers_with_reasons": ranking["all_doppelgangers_with_reasons"],
        "top_3": ranking["top_3"]
    }
