from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).resolve().parent
client = chromadb.PersistentClient(path=str(HERE / "chroma_db"))
collection = client.get_collection("zepto_policies")
model = SentenceTransformer("all-MiniLM-L6-v2")

query = "how long do I have to return a damaged item?"
q_emb = model.encode([query]).tolist()
results = collection.query(query_embeddings=q_emb, n_results=3)

print(f"Query: {query}\n")
for i, (doc_id, doc) in enumerate(zip(results["ids"][0], results["documents"][0]), 1):
    print(f"{i}. [{doc_id}] {doc[:90]}...")