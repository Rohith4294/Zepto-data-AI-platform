"""
Part 6: FastAPI wrapper exposing POST /ask.
Accepts {"query": str}, runs the LangGraph, returns the validated
answer/sources/confidence response.

Run locally:  uvicorn main:app --reload --port 8000   (from inside support_assistant)
"""
from fastapi import FastAPI
from schemas import AskRequest, AskResponse
from graph import app_graph

app = FastAPI(title="Zepto Support Assistant")


@app.get("/")
def health():
    return {"status": "ok", "service": "Zepto Support Assistant"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    # Run the query through the LangGraph pipeline
    result = app_graph.invoke({"query": request.query})

    # Package into the validated Pydantic response schema
    return AskResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
    )