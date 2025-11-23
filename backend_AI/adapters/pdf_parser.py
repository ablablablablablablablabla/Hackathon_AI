import fitz  # PyMuPDF
from logger import logger

def extract_text_from_pdf(pdf_path: str, max_chars: int = 5000) -> str:
    try:
        doc = fitz.open(pdf_path)
        text = []
        for page in doc:
            # get_text() is relatively fast; keep it simple
            text.append(page.get_text())
            if sum(len(t) for t in text) >= max_chars:
                break
        doc.close()
        joined = "".join(text)
        return joined[:max_chars]
    except Exception as e:
        logger.exception("Error extracting text from PDF")
        return ""

