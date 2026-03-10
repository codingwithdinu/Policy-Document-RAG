import os
import requests
from app.config import GROQ_API_KEY

GROQ_MODEL = "llama3-8b-8192"

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")

with open(os.path.join(_PROMPTS_DIR, "parse_query.txt")) as f:
    parse_prompt = f.read()
with open(os.path.join(_PROMPTS_DIR, "generate_decision.txt")) as f:
    decision_prompt = f.read()

def groq_chat(prompt, model="llama3-8b-8192"):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=body, headers=headers)
    data = res.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    return f"Error: {data.get('error', 'No valid response')}"
    
def answer_query_with_clauses(query, clauses):
    joined_clauses = "\n\n".join([f"Clause {i+1}: {clause['text']}" for i, clause in enumerate(clauses[:3])])
    
    prompt = f"""
You are an insurance assistant. Based on the policy clauses provided below, determine whether the given treatment scenario is covered under the insurance policy. 

Always follow these rules:
- If the treatment or condition falls under a waiting period that hasn't completed (e.g., 2-year waiting for surgeries or pre-existing conditions), respond: "Not Covered."
- If it’s an accident-related procedure (like ACL tear from injury), it may be covered immediately. Confirm from clauses.
- If the coverage is clearly mentioned, respond: "Yes, covered because ..." and explain.
- If the coverage is not mentioned or ambiguous, respond: "Not Covered." and explain.
- Always include a one-sentence reason after your Yes/No decision.

POLICY CLAUSES:
{joined_clauses}

QUESTION:
{query}
"""

    return groq_chat(prompt)

def parse_query(user_query: str):
    prompt = parse_prompt.replace("{query}", user_query)
    return groq_chat(prompt)

def generate_decision(parsed_query, retrieved_chunks):
    context = "\n".join([chunk['text'] for chunk in retrieved_chunks])
    prompt = decision_prompt.replace("{context}", context).replace("{query}", parsed_query)
    return groq_chat(prompt)