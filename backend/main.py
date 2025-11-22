import os
import re
import json
import logging
import tempfile
import shutil
import datetime
import requests
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI
from bs4 import BeautifulSoup


try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("scientific_analyzer")


OPENAI_API_KEY = ""
client = OpenAI(api_key=OPENAI_API_KEY)

# === Constants ===
PLAGIARISM_THRESHOLD = 0.5

# === FastAPI app ===
app = FastAPI(title="Scientific Text Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def extract_text_from_pdf(pdf_path: str) -> str:
    if not fitz:
        logger.error("PyMuPDF (fitz) is not installed")
        return ""
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text[:5000]
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_abstract_from_url(url: str) -> str:
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, 'html.parser')
        for pattern in ['abstract', 'Abstract', 'article-section__content', 'main-content']:
            el = soup.find(id=re.compile(pattern, re.I)) or soup.find(class_=re.compile(pattern, re.I))
            if el:
                p = el.find('p')
                if p:
                    return p.get_text().strip()
        meta = soup.find('meta', {'name': 'description'})
        if meta:
            return meta.get('content', '').strip()
    except Exception as e:
        logger.debug(f"Failed to extract abstract from {url}: {e}")
    return ""

def generate_summary(text: str, client: OpenAI) -> str:
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
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return ""

def get_similarity_score(s1: str, s2: str, client: OpenAI) -> float:
    prompt = f"Rate the semantic similarity of two scientific summaries. Respond ONLY with a number from 0.0 to 1.0.\nSummary 1: {s1}\nSummary 2: {s2}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.0
        )
        text = resp.choices[0].message.content.strip()
        match = re.search(r"(\d*\.?\d+)", text)
        return float(match.group(1)) if match else 0.0
    except:
        return 0.0

def get_tfidf_similarity(text1: str, text2: str) -> float:
    """Возвращает косинусное сходство на основе TF-IDF (локальная оценка вероятности плагиата)."""
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(np.clip(sim, 0.0, 1.0))
    except Exception as e:
        logger.warning(f"TF-IDF similarity failed: {e}")
        return 0.0

def generate_reason(pdf_sum: str, art_sum: str, client: OpenAI) -> str:
    prompt = f"""
    Explain in 1–2 sentences in **English** why these two texts are semantically similar (shared object, process, conditions, or conclusions).
    Your text: {pdf_sum}
    Article: {art_sum}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except:
        return "High semantic similarity in content."

def generate_search_query_for_plagiarism(text: str, client: OpenAI) -> str:
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.3
        )
        query = response.choices[0].message.content.strip()
        return re.sub(r'["\[\]`]', '', query)
    except Exception as e:
        logger.error(f"Error generating plagiarism search query: {e}")
        return ""

def generate_search_query_for_doppelganger(text: str, client: OpenAI) -> str:
    prompt = f"""
    You are a cross-disciplinary scientific search expert.
    Create a concise English Crossref query that captures the core conceptual pattern of the text —
    not specific terms like species or stress types, but general dynamics:
    e.g., "nonlinear response during transition phase", "interaction of sequential perturbations", "emergent behavior after system reset".

    Avoid domain-specific nouns. Focus on universal scientific concepts: system dynamics, phase transition, perturbation response, adaptive window.

    Return ONLY the query. No explanations.

    Text: {text[:2000]}
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80,
        temperature=0.3
    )
    query = resp.choices[0].message.content.strip()
    return re.sub(r'["\[\]`]', '', query)

def is_doppelganger(original: str, candidate_abstract: str) -> dict:
    prompt = f"""
    Analyze two scientific texts and respond strictly in the following format — three separate lines:

    Line 1: "Yes" or "No"
    Line 2: Scientific domain of the candidate (e.g., neuroscience, sociology, materials science, machine learning)
    Line 3: 1–2 sentences in **English**: why the works are (or are not) doppelgängers. Describe similarity in logic, pattern, or concept — despite different objects or disciplines.

    Original text:
    {original[:1500]}

    Candidate:
    {candidate_abstract[:1500]}
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.2
        )
        raw = resp.choices[0].message.content.strip()
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

def rank_doppelgangers(doppelgangers: list, original_text: str) -> dict:
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
        top_list = [
            {**entry, "place": i} for i, entry in enumerate(all_entries, start=1)
        ]
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
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            raw = resp.choices[0].message.content.strip()

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

            top_list = [
                {**entry, "place": i + 1} for i, entry in enumerate(top_unique)
            ]

            justification_match = re.search(r'Justification.*?:\s*(.+)', raw, re.DOTALL | re.IGNORECASE)
            justification = justification_match.group(1).strip() if justification_match else "Automatic justification unavailable."

        except Exception as e:
            logger.warning(f"Failed to rank doppelgängers: {e}")
            top_list = [
                {**entry, "place": i + 1} for i, entry in enumerate(all_entries[:3])
            ]
            justification = "Ranking failed — top three doppelgängers selected by order."

    return {
        "all_doppelgangers_with_reasons": all_entries,
        "top_3": {
            "papers": top_list,
            "justification": justification
        }
    }

def search_papers_on_crossref(query: str, limit: int = 100):
    try:
        resp = requests.get(
            "https://api.crossref.org/works",
            params={
                "query.bibliographic": query,
                "rows": limit,
                "sort": "relevance",
                "select": "title,URL,abstract"
            },
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()["message"]["items"]
    except Exception as e:
        logger.error(f"Crossref API error: {e}")
    return []



def run_plagiarism_check(input_text: str) -> dict:
    if not input_text.strip():
        return {"type": "error", "message": "Input text is empty"}

    summary = generate_summary(input_text, client)
    if not summary:
        return {"type": "error", "message": "Failed to generate summary"}

    query = generate_search_query_for_plagiarism(input_text, client)
    if not query:
        return {"type": "error", "message": "Failed to generate search query"}

    papers = search_papers_on_crossref(query, limit=100)
    max_sim = 0.0

    for paper in papers:
        title = paper.get("title", [""])[0] if paper.get("title") else "Untitled"
        url = paper.get("URL", "")
        abstract = paper.get("abstract", "")

        if not abstract or len(abstract) < 50:
            abstract = extract_abstract_from_url(url)
            if not abstract or len(abstract) < 50:
                continue

        art_summary = generate_summary(abstract, client)
        if not art_summary:
            continue

        llm_sim = get_similarity_score(summary, art_summary, client)
        local_sim = get_tfidf_similarity(input_text[:2000], abstract[:2000])
        combined_score = 0.7 * llm_sim + 0.3 * local_sim
        combined_score = float(np.clip(combined_score, 0.0, 1.0))

        if combined_score > max_sim:
            max_sim = combined_score

        if combined_score >= PLAGIARISM_THRESHOLD:
            reason = generate_reason(summary, art_summary, client)
            return {
                "type": "plagiarism",
                "url": url,
                "title": title,
                "reason": reason,
                "probability": round(combined_score, 3),
                "llm_similarity": round(llm_sim, 3),
                "local_similarity": round(local_sim, 3)
            }

    return {
        "type": "no_plagiarism",
        "message": "No significant plagiarism detected",
        "max_similarity_encountered": round(max_sim, 3)
    }

def run_doppelganger_search(input_text: str) -> dict:
    query = generate_search_query_for_doppelganger(input_text, client)
    if not query:
        return {"type": "error", "message": "Failed to generate interdisciplinary query"}

    items = search_papers_on_crossref(query, limit=50)
    doppelgangers = []

    for item in items:
        title = (item.get("title") or [""])[0]
        url = item.get("URL", "")
        abstract = item.get("abstract", "") or ""

        if not abstract or len(abstract) < 100:
            abstract = extract_abstract_from_url(url)
            if not abstract or len(abstract) < 100:
                continue

        result = is_doppelganger(input_text, abstract)
        if result["is_doppelganger"]:
            doppelgangers.append({
                "title": title,
                "url": url,
                "domain": result["domain"],
                "reason": result["reason"]
            })

    ranking = rank_doppelgangers(doppelgangers, input_text)

    return {
        "type": "doppelganger",
        "count": len(doppelgangers),
        "all_doppelgangers_with_reasons": ranking["all_doppelgangers_with_reasons"],
        "top_3": ranking["top_3"]
    }



@app.post("/api/analyze")
async def analyze_endpoint(
    request: Request,
    mode: Optional[str] = Form(None),
    file: UploadFile = File(None)
):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        mode = body.get("mode")
        text = body.get("text")

        if mode not in ("plagiarism", "doppelganger"):
            raise HTTPException(status_code=400, detail='mode must be "plagiarism" or "doppelganger"')
        if not isinstance(text, str) or not text.strip():
            raise HTTPException(status_code=400, detail="text is required and must be a non-empty string")
        input_text = text

    elif "multipart/form-data" in content_type:
        if mode not in ("plagiarism", "doppelganger"):
            raise HTTPException(status_code=400, detail='mode must be "plagiarism" or "doppelganger"')
        if not file:
            raise HTTPException(status_code=400, detail="file is required in multipart request")
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "uploaded.pdf")
        try:
            with open(pdf_path, "wb") as f:
                f.write(await file.read())
            input_text = extract_text_from_pdf(pdf_path)
            if not input_text.strip():
                return JSONResponse({
                    "mode": mode,
                    "result": {"type": "error", "message": "PDF contains no extractable text"}
                })
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        raise HTTPException(status_code=400, detail="Unsupported Content-Type. Use application/json or multipart/form-data.")

    try:
        if mode == "plagiarism":
            result = run_plagiarism_check(input_text)
        elif mode == "doppelganger":
            result = run_doppelganger_search(input_text)
        else:
            raise HTTPException(status_code=400, detail="Unknown mode")
    except Exception as e:
        logger.exception("Analysis execution error")
        return JSONResponse({
            "mode": mode,
            "result": {"type": "error", "message": f"Internal error: {str(e)}"}
        })

    return JSONResponse({
        "mode": mode,
        "result": result
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)