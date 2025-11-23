import re
import numpy as np
import asyncio
from typing import Dict, Any, Optional
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from adapters.crossref import search_papers_on_crossref
from adapters.web_parser import extract_abstract_from_url
from settings import settings
from logger import logger


async def _run_sync(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)

async def generate_summary(text: str, client: OpenAI) -> str:
    prompt = f"""
    Briefly convey the scientific essence of the text (2–3 sentences in **Russian**):
    - research object,
    - main process,
    - conditions of change,
    - conclusion.
    Text:
    {text[:3000]}
    """
    try:
        def sync_call():
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3,
                timeout=settings.openai_timeout
            )
            return resp.choices[0].message.content.strip()
        return await _run_sync(sync_call)
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return ""

async def get_embedding(text: str, client: OpenAI) -> Optional[list]:
    try:
        def sync_call():
            resp = client.embeddings.create(
                input=text[:8191],
                model=settings.embedding_model,
                timeout=settings.openai_timeout
            )
            return resp.data[0].embedding
        return await _run_sync(sync_call)
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return None

async def get_embedding_similarity(text1: str, text2: str, client: OpenAI) -> float:
    e1 = await get_embedding(text1, client)
    e2 = await get_embedding(text2, client)
    if e1 is None or e2 is None:
        return 0.0
    sim = cosine_similarity([e1], [e2])[0][0]
    return float(np.clip(sim, 0.0, 1.0))

async def get_llm_similarity_score(s1: str, s2: str, client: OpenAI) -> float:
    prompt = f"Rate the semantic similarity of two scientific summaries. Respond ONLY with a JSON object: {{\"score\": 0.0}}.\nSummary 1: {s1}\nSummary 2: {s2}"
    try:
        def sync_call():
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.0,
                response_format={"type": "json_object"},
                timeout=settings.openai_timeout
            )
            import json
            data = json.loads(resp.choices[0].message.content)
            score = float(data.get("score", 0.0))
            return float(np.clip(score, 0.0, 1.0))
        return await _run_sync(sync_call)
    except Exception as e:
        logger.warning(f"LLM similarity failed: {e}")
        return 0.0

async def generate_reason(pdf_sum: str, art_sum: str, client: OpenAI) -> str:
    prompt = f"""
    Explain in 1–2 sentences in **English** why these two texts are semantically similar (shared object, process, conditions, or conclusions).
    Your text: {pdf_sum}
    Article: {art_sum}
    """
    try:
        def sync_call():
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3,
                timeout=settings.openai_timeout
            )
            return response.choices[0].message.content.strip()
        return await _run_sync(sync_call)
    except Exception:
        return "High semantic similarity in content."

async def generate_search_query_for_plagiarism(text: str, client: OpenAI) -> str:
    prompt = f"""
    You are a scientific search expert.
    Based on the following text, generate ONE concise but highly precise English Crossref search query
    to find thematically similar articles.

    Use key concepts: model organism, enzyme, process, stress factors.
    Use English only. Do not add explanations — only the query.
    Example of a good query:
    Arabidopsis thaliana senescence beta-galactosidase photosynthesis drought stress

    Text:
    {text[:3000]}
    """
    try:
        def sync_call():
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=0.3,
                timeout=settings.openai_timeout
            )
            query = response.choices[0].message.content.strip()
            return re.sub(r'["\[\]`]', '', query)
        return await _run_sync(sync_call)
    except Exception as e:
        logger.error(f"Error generating plagiarism search query: {e}")
        return ""

async def run_plagiarism_check(input_text: str, client: OpenAI) -> Dict[str, Any]:
    if not input_text.strip():
        return {"type": "error", "message": "Input text is empty"}

    summary = await generate_summary(input_text, client)
    if not summary:
        return {"type": "error", "message": "Failed to generate summary"}

    query = await generate_search_query_for_plagiarism(input_text, client)
    if not query:
        return {"type": "error", "message": "Failed to generate search query"}

    papers = await search_papers_on_crossref(query, limit=settings.crossref_plagiarism_limit)
    max_sim = 0.0

    async def process_paper(paper):
        nonlocal max_sim
        title = (paper.get("title") or [""])[0] if paper.get("title") else "Untitled"
        url = paper.get("URL", "")
        abstract = paper.get("abstract", "")

        if not abstract or len(abstract) < 50:
            abstract = await extract_abstract_from_url(url)
            if not abstract or len(abstract) < 50:
                return None

        art_summary = await generate_summary(abstract, client)
        if not art_summary:
            return None

    
        llm_sim = await get_llm_similarity_score(summary, art_summary, client)
        local_sim = await get_embedding_similarity(input_text[:2000], abstract[:2000], client)
        combined_score = 0.7 * llm_sim + 0.3 * local_sim
        combined_score = float(np.clip(combined_score, 0.0, 1.0))

        if combined_score > max_sim:
            max_sim = combined_score

        if combined_score >= settings.plagiarism_threshold:
            reason = await generate_reason(summary, art_summary, client)
            return {
                "type": "plagiarism",
                "url": url,
                "title": title,
                "reason": reason,
                "probability": round(combined_score, 3),
                "llm_similarity": round(llm_sim, 3),
                "local_similarity": round(local_sim, 3)
            }
        return None


    tasks = [process_paper(p) for p in papers]

    semaphore = asyncio.Semaphore(6)

    async def sem_task(t):
        async with semaphore:
            return await t

    results = await asyncio.gather(*(sem_task(task) for task in tasks))
    for r in results:
        if r is not None:
            return r

    return {
        "type": "no_plagiarism",
        "message": "No significant plagiarism detected",
        "max_similarity_encountered": round(max_sim, 3)
    }



