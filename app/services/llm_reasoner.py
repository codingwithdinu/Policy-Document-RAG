import requests
from app.config import GROQ_API_KEY, GROQ_MODEL

def groq_chat(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured. Add it to your environment.")
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": GROQ_MODEL, "temperature": 0.1, "messages": [
            {"role": "system", "content": "Answer only from the supplied policy evidence. Never invent policy terms, limits, or eligibility."},
            {"role": "user", "content": prompt}
        ]},
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"].strip()

def parse_query(user_query: str):
    return user_query.strip()

def answer_query_with_clauses(query: str, clauses: list):
    if not clauses:
        return "I could not find relevant clauses in the indexed documents. Upload and index the policy document, then ask again."
    context = "\n\n".join(
        f"Source: {item.get('source', 'Unknown')} | Page: {item.get('page', 'N/A')} | Clause: {item.get('text', '')}"
        for item in clauses[:6]
    )
    prompt = f"""You are a careful insurance policy document assistant.
Answer the user's question using only the policy excerpts below.
- Start with a clear, cautious conclusion: Supported, Not supported, or Insufficient information.
- Explain the relevant waiting period, exclusions, limits, conditions, or ambiguity only when the evidence says so.
- Cite source filename and page when available.
- Do not assume a claim is approved/rejected; explain that final decisions belong to the insurer.
- If evidence conflicts or is incomplete, say so explicitly.

POLICY EXCERPTS:
{context}

USER QUESTION:
{query}
"""
    return groq_chat(prompt)
