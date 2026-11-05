def chunk_text(text: str, chunk_size: int = 450, overlap: int = 70):
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap smaller than chunk_size")
    words = text.split()
    step = chunk_size - overlap
    return [" ".join(words[start:start + chunk_size]).strip() for start in range(0, len(words), step) if words[start:start + chunk_size]]
