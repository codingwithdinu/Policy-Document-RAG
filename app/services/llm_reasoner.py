import requests

from app.config import GROQ_API_KEY, GROQ_MODEL


def groq_chat(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing. Add it in your Render environment variables.")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "system",
                        "content": "Answer only from supplied policy evidence. Never invent policy terms, limits, or eligibility.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=(10, 60),
        )
        if response.status_code == 401:
            raise RuntimeError("Groq rejected the API key. Check GROQ_API_KEY in Render.")
        if response.status_code == 404:
            raise RuntimeError(f"Groq model '{GROQ_MODEL}' was not found. Set GROQ_MODEL to an available model.")
        if response.status_code == 429:
            raise RuntimeError("Groq rate limit or quota reached. Please wait and try again.")
        response.raise_for_status()
        payload = response.json()
        answer = payload.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("Groq returned an empty answer. Please try again.")
        return answer.strip()
    except requests.Timeout as exc:
        raise RuntimeError("Groq took too long to respond. Please try again.") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not reach Groq: {exc}") from exc
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Groq returned an invalid response. Please try again.") from exc


def parse_query(user_query: str):
    return user_query.strip()


def answer_query_with_clauses(query: str, clauses: list):
    if not clauses:
        return "I could not find relevant clauses in indexed documents. Upload and index the policy document, then ask again."

    context = "\n\n".join(
        f"Source: {c.get('source', 'Unknown')} | Page: {c.get('page', 'N/A')} | Clause: {c.get('text', '')}"
        for c in clauses[:6]
    )
    prompt = f"""You are a careful insurance policy document assistant. Answer using only the evidence below.
Start with Supported, Not supported, or Insufficient information. Explain relevant limits, exclusions, waiting periods only when evidence says so. Cite source filename and page. Do not assume a claim is approved/rejected; final decisions belong to the insurer. State when evidence is incomplete or ambiguous.
POLICY EXCERPTS:
{context}
USER QUESTION:
{query}"""
    return groq_chat(prompt)
