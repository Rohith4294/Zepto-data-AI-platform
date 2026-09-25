# Module 3 — Support Assistant (RAG + LangGraph + FastAPI)

A grounded GenAI support assistant for Zepto. It answers policy questions using
retrieval-augmented generation over Zepto's own policy documents, orchestrated
by a LangGraph state graph and served via FastAPI. The entire graded path runs
fully offline in mock mode — no API key, no signup, no network calls to any LLM.

## Setup and run

```bash
pip install -r requirements.txt        # from repo root, or this folder's requirements.txt

# 1. Build the vector store (run once)
python support_assistant/ingest.py

# 2. Start the API (run from inside support_assistant/)
cd support_assistant
uvicorn main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000/docs` for the interactive API, or POST to
`http://127.0.0.1:8000/ask` with `{"query": "..."}`.

`MOCK_LLM` defaults to mock mode (the graded baseline) — no configuration needed.

## Files

| File | Role |
|---|---|
| `docs/doc_01…08.txt` | The 8 Zepto policy documents (the corpus) |
| `ingest.py` | Chunks, embeds (`all-MiniLM-L6-v2`), stores vectors in ChromaDB |
| `schemas.py` | Pydantic request/response models |
| `prompts.py` | Structured prompt template (used by the optional real-LLM path) |
| `graph.py` | LangGraph: 3 nodes + conditional routing |
| `main.py` | FastAPI `POST /ask` endpoint |
| `Dockerfile` | Builds and runs the app locally in a container |

## Architecture — the RAG pipeline

**Ingestion → Embedding → Retrieval → Generation.**

1. **Ingestion.** `ingest.py` reads the 8 `.txt` files in `docs/`. Each document
   is treated as one chunk (they are short single-paragraph policies).

2. **Embedding.** Each chunk is embedded with the `all-MiniLM-L6-v2`
   sentence-transformer model (384-dim vectors, generated locally, no API), and
   stored in a persistent ChromaDB collection named `zepto_policies`.

3. **Retrieval.** At query time, `graph.py`'s `retrieve_and_answer` node embeds
   the incoming question with the same model and queries ChromaDB for the top-3
   most similar chunks via cosine similarity. This step always runs for real, in
   both mock and real-LLM modes.

4. **Generation.** The final answer step branches on `MOCK_LLM`:
   - **Mock (default, graded):** returns a canned templated answer,
     `f"Based on the retrieved context: {top_chunk[:200]}"`, built from the single
     most similar chunk. No LLM call.
   - **Real-LLM (optional, `MOCK_LLM=0`):** would prompt a real LLM using the
     structured template in `prompts.py`, grounded only in the retrieved chunks.

### The LangGraph router

The graph has a `TypedDict` state and three nodes:

- **`classify_intent`** — routes the query. In mock mode it uses a keyword
  heuristic: if the lowercased query contains any of `delivery`, `return`,
  `refund`, `membership`, `tracking`, `cancel`, `gift card`, or `support hours`,
  it is a `policy_question`; otherwise `general_question`.
- **`retrieve_and_answer`** — for policy questions: retrieves + answers (above).
- **`direct_answer`** — for general questions: returns a fixed canned string,
  `"I can only answer questions about Zepto policies right now."`

A **conditional edge** from `classify_intent` routes to one of the two answer
nodes based on the intent. This routing does not depend on `MOCK_LLM` — only the
generation step inside each node does.

**Note on the mock classifier:** because it is keyword-based, a policy question
phrased without one of the listed keywords (e.g. "what is your first policy?")
routes to the general path. The optional `MOCK_LLM=0` path would classify by
meaning and handle such phrasings.

## Structured output

Every response is validated against a Pydantic schema (`schemas.py`): `answer`
(str), `sources` (list of doc ids — populated for policy questions, empty for
general), and `confidence` (float 0–1, fixed at 1.0 in mock mode). The
`response_model=AskResponse` on the FastAPI endpoint enforces this at the HTTP
boundary. The optional real-LLM path includes retry-on-validation-failure logic.

## Example calls (mock mode — the graded default)

**Policy question (routes to retrieval):**

```json
POST /ask   {"query": "what is your return policy?"}

{
  "answer": "Based on the retrieved context: Grocery and perishable items may be reported for a return within 24 hours of delivery if damaged, spoiled, or incorrect; non-perishable packaged items may be returned within 7 days of delivery in unop",
  "sources": ["doc_02", "doc_06", "doc_05"],
  "confidence": 1.0
}
[PASTE YOUR RETURN-POLICY RESPONSE HERE]
```

**General question (routes to direct answer):**

```json
POST /ask   {"query": "what is the capital of France?"}


{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

## Docker

```bash
cd support_assistant
docker build -t zepto-assistant .
docker run -p 7860:7860 zepto-assistant
```

Then POST to `http://127.0.0.1:7860/ask`. The Dockerfile installs dependencies,
builds the ChromaDB store at image-build time, and serves the app on port 7860.