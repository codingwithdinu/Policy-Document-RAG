from pathlib import Path
import pdfplumber
from docx import Document

def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_from_pdf(str(path))
    if suffix == ".docx":
        return extract_from_docx(str(path))
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")

def extract_from_pdf(path: str) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(f"[Page {page_number}]\n{page_text}")
    return "\n\n".join(pages).strip()

def extract_from_docx(path: str) -> str:
    doc = Document(path)
    blocks = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                blocks.append(" | ".join(cells))
    return "\n".join(blocks).strip()
