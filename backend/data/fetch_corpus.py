# backend/data/fetch_corpus.py
"""
Downloads and extracts Indian legal corpus from public government sources.
Run once: python data/fetch_corpus.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib.request
from pathlib import Path

CORPUS_DIR = Path(__file__).parent / "corpus"
CORPUS_DIR.mkdir(exist_ok=True)

# Public government PDF sources
SOURCES = {
    "BNS.pdf": "https://cdnbbsr.s3waas.gov.in/s380537a945c7aaa788ccfcdf1b99b5d8f/uploads/2023/08/2023082485.pdf",
    "BNSS.pdf": "https://cdnbbsr.s3waas.gov.in/s380537a945c7aaa788ccfcdf1b99b5d8f/uploads/2023/08/2023082484.pdf",
}

def download_pdfs():
    for filename, url in SOURCES.items():
        dest = CORPUS_DIR / filename
        if dest.exists():
            print(f"[SKIP] {filename} already exists")
            continue
        print(f"[DOWNLOAD] {filename} ...")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  → saved to {dest}")
        except Exception as e:
            print(f"  → failed: {e}. Download manually from India Code website.")

def extract_pdf_to_text(pdf_path: Path, txt_path: Path):
    import fitz  # pymupdf
    print(f"[EXTRACT] {pdf_path.name} → {txt_path.name}")
    doc = fitz.open(str(pdf_path))
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    txt_path.write_text(full_text, encoding="utf-8")
    print(f"  → {len(full_text)} chars extracted")
    doc.close()

if __name__ == "__main__":
    download_pdfs()
    for pdf_file in CORPUS_DIR.glob("*.pdf"):
        txt_file = pdf_file.with_suffix(".txt")
        if not txt_file.exists():
            extract_pdf_to_text(pdf_file, txt_file)
    print("\n✅ Corpus ready. Now run: python data/ingest.py")