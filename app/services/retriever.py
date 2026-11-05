import json, os
from pathlib import Path
import faiss
import numpy as np
from app.config import VECTOR_INDEX_PATH

def save_to_faiss(embeddings, metadatas, index_path=VECTOR_INDEX_PATH):
    if not embeddings or not metadatas: raise ValueError("No extractable document text was found to index.")
    vectors = np.asarray(embeddings, dtype="float32")
    if vectors.ndim != 2 or len(vectors) != len(metadatas): raise ValueError("Embedding and metadata counts do not match.")
    index = faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
    Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    tmp_i, tmp_m = index_path + ".tmp", index_path + "_metadata.json.tmp"
    faiss.write_index(index, tmp_i)
    with open(tmp_m, "w", encoding="utf-8") as stream: json.dump(metadatas, stream, ensure_ascii=False)
    os.replace(tmp_i, index_path); os.replace(tmp_m, index_path + "_metadata.json")
    return len(metadatas)

def load_faiss_index(index_path=VECTOR_INDEX_PATH):
    metadata_path = index_path + "_metadata.json"
    if not os.path.exists(index_path) or not os.path.exists(metadata_path): return None, []
    index = faiss.read_index(index_path)
    with open(metadata_path, encoding="utf-8") as stream: metadata = json.load(stream)
    return index, metadata

def retrieve_chunks(query, top_k=6):
    from app.services.embedder import embed_query
    index, metadata = load_faiss_index()
    if index is None or not metadata or index.ntotal == 0: return []
    vector = np.asarray([embed_query(query)], dtype="float32")
    scores, indices = index.search(vector, min(max(1, top_k), index.ntotal))
    results = []
    for score, position in zip(scores[0], indices[0]):
        if 0 <= position < len(metadata):
            item = dict(metadata[position]); item["score"] = round(float(score), 4); results.append(item)
    return results
