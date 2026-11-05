from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import retriever, llm_reasoner

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)


@router.post("/query")
def handle_query(payload: QueryRequest):
    try:
        query_text = payload.query.strip()
        if not query_text:
            raise HTTPException(status_code=422, detail="Please enter a question.")

        matches = retriever.retrieve_chunks(llm_reasoner.parse_query(query_text), top_k=6)
        if not matches:
            return {
                "query": query_text,
                "answer": "No indexed policy evidence was found. Upload a text-readable policy document first.",
                "clauses": [],
                "sources": [],
            }

        answer = llm_reasoner.answer_query_with_clauses(query_text, matches)
        return {
            "query": query_text,
            "answer": answer,
            "clauses": matches,
            "sources": [
                {
                    "source": clause.get("source"),
                    "page": clause.get("page"),
                    "score": clause.get("score"),
                }
                for clause in matches
            ],
        }
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Question processing failed: {exc}") from exc
