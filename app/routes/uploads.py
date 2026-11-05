from pathlib import Path
import re
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import UPLOAD_DIR, MAX_UPLOAD_MB, ALLOWED_EXTENSIONS
from app.services.parser import extract_text
from app.services.chunker import chunk_text
from app.services.embedder import embed_chunks
from app.services.retriever import load_faiss_index, save_to_faiss

router = APIRouter()

def rebuild_index():
    upload_dir = Path(UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    chunks, metadata = [], []
    for path in sorted(upload_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        text = extract_text(str(path))
        document_chunks = chunk_text(text)
        for number, chunk in enumerate(document_chunks):
            chunks.append(chunk)
            page_match = __import__("re").search(r"\[Page (\d+)\]", chunk)
            metadata.append({"source": path.name, "chunk_index": number, "page": int(page_match.group(1)) if page_match else None, "text": chunk})
    if not chunks:
        return 0
    return save_to_faiss(embed_chunks(chunks), metadata)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only PDF, DOCX, and TXT files are supported.")
    upload_dir = Path(UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(filename).stem).strip("-") or "policy"
    target = upload_dir / f"{safe_stem}-{uuid4().hex[:8]}{suffix}"
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    output.close()
                    target.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_MB} MB limit.")
                output.write(chunk)
        if size == 0:
            target.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="The selected file is empty.")
        extracted = extract_text(str(target))
        if not extracted.strip():
            target.unlink(missing_ok=True)
            raise HTTPException(status_code=422, detail="No readable text found. Scanned PDFs need OCR before upload.")
        total_chunks = rebuild_index()
        return {"message": "Document uploaded and indexed successfully.", "filename": target.name, "bytes": size, "chunks_indexed": total_chunks}
    except HTTPException:
        raise
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Could not process document: {exc}") from exc
    finally:
        await file.close()

@router.get("/documents")
def list_documents():
    upload_dir = Path(UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    index, metadata = load_faiss_index()
    docs = {}
    for path in upload_dir.iterdir():
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            docs[path.name] = {"filename": path.name, "size_bytes": path.stat().st_size, "indexed_chunks": 0}
    for item in metadata:
        if item.get("source") in docs:
            docs[item["source"]]["indexed_chunks"] += 1
    return {"documents": list(docs.values()), "indexed": bool(index and index.ntotal)}
