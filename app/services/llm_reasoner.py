import requests
from app.config import GROQ_API_KEY, GROQ_MODEL

def groq_chat(prompt: str) -> str:
    if not GROQ_API_KEY: raise RuntimeError("GROQ_API_KEY is not configured. Add it to your environment.")
    response = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": GROQ_MODEL, "temperature": 0.1, "messages":[
            {"role":"system","content":"Answer only from supplied policy evidence. Never invent policy terms, limits, or eligibility."},
            {"role":"user","content":prompt}]}, timeout=45)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def parse_query(user_query: str):
    return user_query.strip()

def answer_query_with_clauses(query: str, clauses: list):
    if not clauses: return "I could not find relevant clauses in indexed documents. Upload and index the policy document, then ask again."
    context = "\n\n".join(f"Source: {c.get('source','Unknown')} | Page: {c.get('page','N/A')} | Clause: {c.get('text','')}" for c in clauses[:6])
    prompt = f"""You are a careful insurance policy document assistant. Answer using only the evidence below.
Start with Supported, Not supported, or Insufficient information. Explain relevant limits, exclusions, waiting periods only when evidence says so. Cite source filename and page. Do not assume a claim is approved/rejected; final decisions belong to the insurer. State when evidence is incomplete or ambiguous.
POLICY EXCERPTS:
{context}
USER QUESTION:
{query}"""
    return groq_chat(prompt)
