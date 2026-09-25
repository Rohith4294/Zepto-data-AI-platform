r"""
Part 5: LangGraph StateGraph with 3 nodes and a conditional edge.

Flow:  classify_intent --> (policy_question)  --> retrieve_and_answer
                       \--> (general_question) --> direct_answer

MOCK_LLM gates only the GENERATION step inside each node. Retrieval always
runs for real. Default (unset or "1") = mock/graded baseline.
"""
import os
from pathlib import Path
from typing import TypedDict, List

import chromadb
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END

HERE = Path(__file__).resolve().parent
DB_DIR = HERE / "chroma_db"
COLLECTION_NAME = "zepto_policies"
EMBED_MODEL = "all-MiniLM-L6-v2"

POLICY_KEYWORDS = ["delivery", "return", "refund", "membership",
                   "tracking", "cancel", "gift card", "support hours"]

_model = SentenceTransformer(EMBED_MODEL)
_client = chromadb.PersistentClient(path=str(DB_DIR))
_collection = _client.get_collection(COLLECTION_NAME)


def _mock_llm() -> bool:
    """True = mock mode (graded baseline). Default when unset or '1'."""
    return os.environ.get("MOCK_LLM", "1") != "0"


class GraphState(TypedDict):
    query: str
    intent: str
    answer: str
    sources: List[str]
    confidence: float


def classify_intent(state: GraphState) -> GraphState:
    query = state["query"].lower()
    if _mock_llm():
        is_policy = any(kw in query for kw in POLICY_KEYWORDS)
        state["intent"] = "policy_question" if is_policy else "general_question"
    else:
        state["intent"] = "policy_question"
    return state


def retrieve_and_answer(state: GraphState) -> GraphState:
    q_emb = _model.encode([state["query"]]).tolist()
    results = _collection.query(query_embeddings=q_emb, n_results=3)

    retrieved_docs = results["documents"][0]
    retrieved_ids = results["ids"][0]
    top_chunk = retrieved_docs[0]

    if _mock_llm():
        snippet = top_chunk[:200]
        state["answer"] = f"Based on the retrieved context: {snippet}"
    else:
        state["answer"] = f"[real-LLM answer would go here]"

    state["sources"] = retrieved_ids
    state["confidence"] = 1.0
    return state


def direct_answer(state: GraphState) -> GraphState:
    if _mock_llm():
        state["answer"] = "I can only answer questions about Zepto policies right now."
    else:
        state["answer"] = "[real-LLM direct answer would go here]"
    state["sources"] = []
    state["confidence"] = 1.0
    return state


def route_by_intent(state: GraphState) -> str:
    return state["intent"]


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("retrieve_and_answer", retrieve_and_answer)
    workflow.add_node("direct_answer", direct_answer)

    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "policy_question": "retrieve_and_answer",
            "general_question": "direct_answer",
        },
    )

    workflow.add_edge("retrieve_and_answer", END)
    workflow.add_edge("direct_answer", END)

    return workflow.compile()


app_graph = build_graph()


if __name__ == "__main__":
    for q in ["What is your return policy?", "What is the capital of France?"]:
        result = app_graph.invoke({"query": q})
        print(f"\nQ: {q}")
        print(f"  intent:     {result['intent']}")
        print(f"  answer:     {result['answer'][:80]}...")
        print(f"  sources:    {result['sources']}")
        print(f"  confidence: {result['confidence']}")