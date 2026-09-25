# Zepto Data & AI Platform

A single connected platform demonstrating the end-to-end AI/ML engineering
workflow, built as three internally-linked modules in one repository.

| Module | Folder | What it does |
|---|---|---|
| 1 — Data Pipeline | `/data_pipeline` | Scrapes catalog data, cleans it, loads it into a normalized SQLite database, queries with SQL + pandas |
| 2 — Analytics | `/analytics` | Titanic EDA + a full classification/regression ML pipeline with evaluation and tuning |
| 3 — Support Assistant | `/support_assistant` | A grounded RAG chatbot answering Zepto policy questions (LangGraph + FastAPI) |

## Setup

This project uses **one consolidated `requirements.txt`** at the repo root.

```bash
python -m venv venv
venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
```

## Running each module

**Module 1 — Data Pipeline**
```bash
python data_pipeline/scrape.py
python data_pipeline/clean.py
python data_pipeline/database.py
python data_pipeline/analysis.py
```

**Module 2 — Analytics** — open and run top-to-bottom in Jupyter/VS Code:
```
analytics/01_eda.ipynb        (produces titanic.csv)
analytics/02_modeling.ipynb   (reads titanic.csv, runs the ML pipeline)
```

**Module 3 — Support Assistant**
```bash
python support_assistant/ingest.py      # build the vector store (once)
cd support_assistant
uvicorn main:app --port 8000            # serve POST /ask
```

## Design decisions (summary)

**Module 1.** ETL pipeline split into four scripts (scrape → clean → database →
analysis). Categories discovered dynamically; median imputation for parse
failures; normalized two-table schema (PK/FK); fixed rate 1 GBP = 105.50 INR.

**Module 2.** Single dataset load with committed `titanic.csv` fallback.
Leak-free preprocessing via `ColumnTransformer` fit on the training split only.
Three classifiers compared; Logistic Regression selected for deployment on the
strength of its AUC and interpretability. Full pipeline saved with `joblib`.

**Module 3.** RAG over 8 policy docs: local `all-MiniLM-L6-v2` embeddings in
ChromaDB, a LangGraph router (classify → retrieve/answer or direct), Pydantic-
validated output, served via FastAPI. Runs fully offline in mock mode
(`MOCK_LLM` default) — no API key required.

## Git workflow

Feature branches were used per module and merged back into `main` via no-fast-
forward merges; see `git log --graph --all` for the branch/merge history.

See each module's own `README.md` for detailed write-ups, tables, and interpretations.