from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services import retriever, llm_reasoner
from app.services.formatter import format_output

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)

@router.post("/query")
def handle_query(payload: QueryRequest):
    try:
        parsed = llm_reasoner.parse_query(payload.query)
        matches = retriever.retrieve_chunks(parsed, top_k=6)
        if not matches:
            return {"query": payload.query, "answer": "No indexed policy evidence was found. Upload a policy document first, and make sure it contains selectable text.", "clauses": [], "sources": []}
        answer = llm_reasoner.answer_query_with_clauses(payload.query, matches)
        return {"query": payload.query, "answer": answer, "clauses": matches, "sources": [{"source": item.get("source"), "page": item.get("page"), "score": item.get("score")} for item in matches]}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Question processing failed: {exc}") from exc
