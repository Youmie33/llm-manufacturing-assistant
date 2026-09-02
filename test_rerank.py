from core.retrieval.embedder import Embedder
from core.retrieval.vector_store import QdrantStore
from core.retrieval.retriever import VectorRetriever
from core.rerank.reranker import rerank
from sentence_transformers import CrossEncoder

# 初始化
embedder = Embedder()
store = QdrantStore()
retriever = VectorRetriever(embedder, store)

reranker = rerank(
    CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
)

# 👉 測試 query
query = "MRB是什麼"

# Step 1：retrieve
docs = retriever.retrieve(query, top_k=10)

print("\n==== RETRIEVE ====")
for d in docs[:5]:
    print("-", d["text"][:80])

# Step 2：rerank
ranked = reranker.rerank(query, docs)

print("\n==== RERANK ====")
for d in ranked[:5]:
    print("-", d["text"][:80])