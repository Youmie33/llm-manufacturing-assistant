from core.utils.query_utils import expand_query
from core.router.source_router import SourceRouter


class Retriever:
    def __init__(self, embedder, vector_store):
        # embedding 模組（負責 query / source 語意向量）
        self.embedder = embedder

        # vector DB（Qdrant）
        self.vector_store = vector_store

        # 🔥 新增：文件路由器
        self.source_router = SourceRouter(embedder)

    def retrieve(self, query, top_k=10, mode="fact"):
        print("🚀 Retriever 啟動")

        # =========================
        # 1️⃣ query expansion
        # =========================
        queries = expand_query(query)

        if not queries:
            queries = [query]

        # =========================
        # 2️⃣ 是否做 source routing
        # =========================
        candidate_sources = None

        if mode == "procedure":
            all_sources = self.vector_store.get_all_sources()

            candidate_sources = self.source_router.select_sources(
                query=query,
                sources=all_sources,
                top_k=2   # 🔥 不要太多
            )

            print("🎯 候選文件:")
            for src in candidate_sources:
                print(" -", src)

        else:
            print("📌 FACT 模式 → 不限來源")

        all_docs = []

        # =========================
        # 3️⃣ retrieval
        # =========================
        for q in queries:
            query_vec = self.embedder.encode(q)

            vector_docs = self.vector_store.search(
                query_vector=query_vec,
                limit=top_k * 3,
                sources=candidate_sources
            ) or []

            keyword_docs = self.vector_store.keyword_search(
                query=q,
                limit=top_k * 3,
                sources=candidate_sources
            ) or []

            all_docs.extend(vector_docs)
            all_docs.extend(keyword_docs)

        # =========================
        # 4️⃣ 去重
        # =========================
        seen = set()
        unique_docs = []

        for d in all_docs:
            key = d.get("text", "")[:120]

            if key not in seen:
                seen.add(key)
                unique_docs.append(d)

        print(f"👉 去重後 docs: {len(unique_docs)}")

        # =========================
        # 5️⃣ 粗排（keyword score）
        # =========================
        unique_docs = sorted(
            unique_docs,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        return unique_docs[:top_k]