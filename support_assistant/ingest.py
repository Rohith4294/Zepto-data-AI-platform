"""
Part 2: load the 8 policy docs, chunk them, embed each chunk with
all-MiniLM-L6-v2, and store the vectors in a persistent ChromaDB collection.
Run once before starting the API:  python support_assistant/ingest.py
"""
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).resolve().parent
DOCS_DIR = HERE / "docs"
DB_DIR = HERE / "chroma_db"
COLLECTION_NAME = "zepto_policies"
EMBED_MODEL = "all-MiniLM-L6-v2"


def load_documents():
    """Read all 8 .txt files -> list of (doc_id, text)."""
    docs = []
    for path in sorted(DOCS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        docs.append((path.stem, text))
    return docs


def build_collection():
    print(f"Loading embedding model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(path=str(DB_DIR))

    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(name=COLLECTION_NAME)

    docs = load_documents()
    ids, texts, metadatas = [], [], []
    for doc_id, text in docs:
        ids.append(doc_id)
        texts.append(text)
        metadatas.append({"source": doc_id})

    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts).tolist()
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Stored {collection.count()} chunks in collection '{COLLECTION_NAME}'")
    print(f"ChromaDB persisted at: {DB_DIR}")


if __name__ == "__main__":
    build_collection()