from core.retrieval.embedder import Embedder
from core.retrieval.vector_store import VectorStore

# 假資料
chunks = [
    {"section": "1.0", "text": "MRB 是處理異常物料的流程"},
    {"section": "2.0", "text": "IQC 負責進料檢驗"},
]

embedder = Embedder()
vectors = embedder.encode([c["text"] for c in chunks])

store = VectorStore()

# 👉 你原本怎麼存就怎麼用
store.add(chunks, vectors)

# 測 query
query = "MRB是什麼"
q_vec = embedder.encode([query])

results = store.search(q_vec, top_k=2)

print("\n==== RETRIEVE RESULT ====")
for r in results:
    print(r)
