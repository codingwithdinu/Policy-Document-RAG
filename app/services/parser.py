from pathlib import Path
import pdfplumber
from docx import Document

def extract_text(file_path: str) -> str:
    path = Path(file_path)
    if path.suffix.lower() == ".pdf": return extract_from_pdf(str(path))
    if path.suffix.lower() == ".docx": return extract_from_docx(str(path))
    if path.suffix.lower() == ".txt": return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")

def extract_from_pdf(path: str) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            value = page.extract_text() or ""
            if value.strip(): pages.append(f"[Page {number}]\n{value}")
    return "\n\n".join(pages).strip()

def extract_from_docx(path: str) -> str:
    doc = Document(path)
    blocks = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells): blocks.append(" | ".join(cells))
    return "\n".join(blocks).strip()
