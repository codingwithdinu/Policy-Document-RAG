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
    folder = Path(UPLOAD_DIR); folder.mkdir(parents=True, exist_ok=True)
    chunks, metadata = [], []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTENSIONS: continue
        text = extract_text(str(path))
        for number, chunk in enumerate(chunk_text(text)):
            match = re.search(r"\[Page (\d+)\]", chunk)
            chunks.append(chunk)
            metadata.append({"source":path.name,"chunk_index":number,"page":int(match.group(1)) if match else None,"text":chunk})
    if not chunks: return 0
    return save_to_faiss(embed_chunks(chunks), metadata)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS: raise HTTPException(status_code=415, detail="Only PDF, DOCX, and TXT files are supported.")
    folder = Path(UPLOAD_DIR); folder.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^a-zA-Z0-9_-]+","-",Path(filename).stem).strip("-") or "policy"
    target = folder / f"{stem}-{uuid4().hex[:8]}{suffix}"
    limit = MAX_UPLOAD_MB * 1024 * 1024; size = 0
    try:
        with target.open("wb") as output:
            while True:
                block = await file.read(1024 * 1024)
                if not block: break
                size += len(block)
                if size > limit:
                    output.close(); target.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_MB} MB limit.")
                output.write(block)
        if size == 0:
            target.unlink(missing_ok=True); raise HTTPException(status_code=400, detail="The selected file is empty.")
        text = extract_text(str(target))
        if not text.strip():
            target.unlink(missing_ok=True); raise HTTPException(status_code=422, detail="No readable text found. Scanned PDFs need OCR before upload.")
        count = rebuild_index()
        return {"message":"Document uploaded and indexed successfully.","filename":target.name,"bytes":size,"chunks_indexed":count}
    except HTTPException: raise
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Could not process document: {exc}") from exc
    finally: await file.close()

@router.get("/documents")
def list_documents():
    folder = Path(UPLOAD_DIR); folder.mkdir(parents=True, exist_ok=True)
    index, metadata = load_faiss_index()
    docs = {p.name:{"filename":p.name,"size_bytes":p.stat().st_size,"indexed_chunks":0} for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS}
    for item in metadata:
        if item.get("source") in docs: docs[item["source"]]["indexed_chunks"] += 1
    return {"documents":list(docs.values()),"indexed":bool(index is not None and index.ntotal)}
