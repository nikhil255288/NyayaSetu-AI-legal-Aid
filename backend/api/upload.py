# backend/api/upload.py
"""
Document upload endpoint.
POST /api/upload
Accepts PDF or image of a legal document, extracts text, parses it.
"""
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from agents.doc_parser_agent import parse_document

router = APIRouter()


class UploadResponse(BaseModel):
    doc_type: str
    sections_cited: list[str]
    key_facts: list[str]
    plain_explanation: str
    legal_response: str
    urgent_actions: list[str]
    raw_text_preview: str   # first 300 chars of extracted text


def extract_text_from_file(content: bytes, filename: str) -> str:
    """Extract text from PDF or plain text file."""
    fname = filename.lower()

    if fname.endswith(".pdf"):
        try:
            import fitz  # pymupdf
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PDF support requires pymupdf. Run: pip install pymupdf"
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read PDF: {e}")

    elif fname.endswith((".txt", ".text")):
        return content.decode("utf-8", errors="ignore")

    elif fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
        # OCR path — requires pytesseract
        try:
            from PIL import Image
            import pytesseract
            image = Image.open(io.BytesIO(content))
            return pytesseract.image_to_string(image, lang="eng+hin")
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Image OCR requires Pillow and pytesseract. "
                       "Run: pip install Pillow pytesseract and install Tesseract."
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Upload PDF, TXT, or image (PNG/JPG)."
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    if len(content) < 50:
        raise HTTPException(status_code=400, detail="File is empty or too small")

    # Extract text
    text = extract_text_from_file(content, file.filename)

    if len(text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Could not extract readable text from this file"
        )

    # Parse with AI
    parsed = parse_document(text)

    return UploadResponse(
        doc_type=parsed.doc_type,
        sections_cited=parsed.sections_cited,
        key_facts=parsed.key_facts,
        plain_explanation=parsed.plain_explanation,
        legal_response=parsed.legal_response,
        urgent_actions=parsed.urgent_actions,
        raw_text_preview=text[:300],
    )