import json
import os
from pathlib import Path

import faiss
import numpy as np

from app.config import VECTOR_INDEX_PATH


def save_to_faiss(embeddings, metadatas, index_path=VECTOR_INDEX_PATH):
    if len(embeddings) == 0 or len(metadatas) == 0:
        clear_faiss_index(index_path)
        return 0

    vectors = np.asarray(embeddings, dtype="float32")
    if vectors.ndim != 2 or len(vectors) != len(metadatas):
        raise ValueError("Embedding and metadata counts do not match.")
    if not np.isfinite(vectors).all():
        raise ValueError("Embeddings contain invalid numeric values.")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    target = Path(index_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = str(target) + "_metadata.json"
    tmp_index = str(target) + ".tmp"
    tmp_metadata = metadata_path + ".tmp"

    try:
        faiss.write_index(index, tmp_index)
        with open(tmp_metadata, "w", encoding="utf-8") as stream:
            json.dump(metadatas, stream, ensure_ascii=False)
        os.replace(tmp_index, str(target))
        os.replace(tmp_metadata, metadata_path)
    finally:
        for temp_path in (tmp_index, tmp_metadata):
            if os.path.exists(temp_path):
                os.remove(temp_path)
    return len(metadatas)


def clear_faiss_index(index_path=VECTOR_INDEX_PATH):
    for path in (index_path, index_path + "_metadata.json"):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def load_faiss_index(index_path=VECTOR_INDEX_PATH):
    metadata_path = index_path + "_metadata.json"
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        return None, []
    index = faiss.read_index(index_path)
    with open(metadata_path, encoding="utf-8") as stream:
        metadata = json.load(stream)
    if index.ntotal != len(metadata):
        raise RuntimeError("The search index and its metadata are out of sync. Re-upload the policy documents.")
    return index, metadata


def retrieve_chunks(query, top_k=6):
    from app.services.embedder import embed_query

    index, metadata = load_faiss_index()
    if index is None or not metadata or index.ntotal == 0:
        return []

    vector = np.asarray([embed_query(query)], dtype="float32")
    scores, indices = index.search(vector, min(max(1, top_k), index.ntotal))
    results = []
    for score, position in zip(scores[0], indices[0]):
        if 0 <= position < len(metadata):
            item = dict(metadata[position])
            item["score"] = round(float(score), 4)
            results.append(item)
    return results
