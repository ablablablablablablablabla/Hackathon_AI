# api/routes.py
import os
import tempfile
import shutil
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI
from core.plagiarism import run_plagiarism_check
from core.doppelganger import run_doppelganger_search
from adapters.pdf_parser import extract_text_from_pdf
from settings import settings
from logger import logger

app = FastAPI(title="Scientific Text Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=settings.openai_api_key)

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
            input_text = extract_text_from_pdf(pdf_path, max_chars=settings.max_pdf_chars)
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
            result = await run_plagiarism_check(input_text, client)
        elif mode == "doppelganger":
            result = await run_doppelganger_search(input_text, client)
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
