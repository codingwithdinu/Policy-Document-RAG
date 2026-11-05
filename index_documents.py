from pathlib import Path
from app.config import UPLOAD_DIR, VECTOR_INDEX_PATH, ALLOWED_EXTENSIONS
from app.services.parser import extract_text
from app.services.chunker import chunk_text
from app.services.embedder import embed_chunks
from app.services.retriever import save_to_faiss

def index_all_documents():
    folder = Path(UPLOAD_DIR); folder.mkdir(parents=True, exist_ok=True)
    chunks, metadata = [], []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTENSIONS: continue
        print(f"[index] {path.name}")
        for number, chunk in enumerate(chunk_text(extract_text(str(path)))):
            chunks.append(chunk); metadata.append({"source":path.name,"chunk_index":number,"page":None,"text":chunk})
    if not chunks:
        print("No readable documents found; index was not changed."); return 0
    total = save_to_faiss(embed_chunks(chunks),metadata,VECTOR_INDEX_PATH)
    print(f"Indexed {total} chunks."); return total
if __name__ == "__main__": index_all_documents()
