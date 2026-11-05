from functools import lru_cache
from app.config import EMBEDDING_MODEL

@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)

def embed_chunks(chunks):
    if not chunks:
        return []
    return get_model().encode(chunks, normalize_embeddings=True, show_progress_bar=False).tolist()

def embed_query(text):
    return get_model().encode([text], normalize_embeddings=True, show_progress_bar=False)[0].tolist()
