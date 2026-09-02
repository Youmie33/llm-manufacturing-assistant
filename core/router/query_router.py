from core.router.llm_router import LLMRouter
class QueryRouter:
    def __init__(self, embedder=None):
        self.embedder = embedder
        self.llm_router = LLMRouter()

    def route(self, query: str, sources=None):
        query_lower = query.lower()

        # =========================
        # 🟢 Rule-based（快）
        # =========================

        fact_keywords = ["什麼", "哪些", "項目", "內容", "包含"]
        procedure_keywords = ["流程", "步驟", "操作", "怎麼", "如何"]

        # 👉 明確 fact
        for kw in fact_keywords:
            if kw in query_lower:
                return {"mode": "fact"}

        # 👉 明確 procedure
        for kw in procedure_keywords:
            if kw in query_lower:
                return {"mode": "procedure"}

        # =========================
        # 🔥 不確定 → 用 LLM
        # =========================
        print("🤖 使用 LLM Router 判斷")

        mode = self.llm_router.classify(query)

        return {"mode": mode}