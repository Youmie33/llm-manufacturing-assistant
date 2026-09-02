from core.retrieval.embedder import Embedder
from core.retrieval.vector_store import QdrantStore
from core.retrieval.retriever import Retriever
from core.rerank.reranker import Reranker
from core.llm.generator import Generator
from core.router.router import Router
from core.llm.query_rewriter import QueryRewriter
from core.evaluation.evaluator import Evaluator


class RAGPipeline:
    def __init__(self):
        print("🚀 初始化 RAG Pipeline")

        self.embedder = Embedder()
        self.vector_store = QdrantStore()
        self.vector_store.ensure_collection(vector_size=384)

        self.retriever = Retriever(self.embedder, self.vector_store)
        self.reranker = Reranker()
        self.generator = Generator()
        self.rewriter = QueryRewriter()
        self.router = Router(self.embedder)
        self.evaluator = Evaluator()

    def ask(self, query):
        rewritten_query = self.rewriter.rewrite(query)

        print("原始問題:", query)
        print("改寫後:", rewritten_query)

        docs = []

        # =========================
        # 🧠 Router
        # =========================
        try:
            decision = self.router.route(query)

            if not decision:
                mode = "fact"

            elif isinstance(decision, dict):
                mode = decision.get("mode", "fact")

                if isinstance(mode, dict):
                    mode = mode.get("mode", "fact")

            else:
                mode = str(decision)

        except Exception as e:
            print("❌ Router error:", e)
            mode = "fact"

        print(f"🧠 Query mode: {mode}")

        # =========================
        # 🔍 Retrieval（🔥完整版優化）
        # =========================
        try:
            docs = self.retriever.retrieve(rewritten_query, top_k=12, mode=mode) or []

            if docs:
                docs = self.reranker.rerank(rewritten_query, docs)

                # 🔥 只保留同一文件（關鍵）
                main_source = docs[0].get("source")
                docs = [d for d in docs if d.get("source") == main_source]
                # 🔥 依 chunk_index 排序
                docs = sorted(docs, key=lambda x: x.get("chunk_index", 0))
                # 🔥 控制數量（避免 token 爆）
                docs = docs[:]

                print(f"📄 使用文件: {main_source}")
                print(f"📊 docs 數量: {len(docs)}")

            else:
                print("⚠️ 無檢索結果")


        except Exception as e:
            print("❌ Retrieval error:", e)
            docs = []

        # =========================
        # 🧠 LLM
        # =========================
        answer = "找不到相關資料，請嘗試換個問法。"

        try:
            if docs:
                answer = self.generator.generate(query, docs)

        except Exception as e:
            print("❌ LLM error:", e)
            answer = "系統暫時無法生成回答"

        # =========================
        # 🔥 清洗 docs（給 evaluator 用）
        # =========================
        clean_docs = []

        for d in docs:
            text = d.get("text", "")

            if not isinstance(text, str):
                text = str(text)

            clean_docs.append({
                "text": text,
                "source": d.get("source", "")
            })

        # =========================
        # 📊 Evaluation（Flow已關閉）
        # =========================
        try:
            scores = self.evaluator.evaluate(
                question=query,
                answer=answer,
                contexts=clean_docs,
                flow_steps=None  # 🔥 關鍵（避免 completeness 爆）
            )
        except Exception as e:
            print("❌ Evaluation error:", e)
            scores = {}

        return {
            "answer": answer,
            "docs": docs[:5] if docs else [],
            "scores": scores
        }


# =========================
# 🔧 測試
# =========================
if __name__ == "__main__":
    pipeline = RAGPipeline()

    query = "切割機怎麼操作?"
    result = pipeline.ask(query)

    print("\n================ ANSWER ================\n")
    print(result["answer"])

    print("\n================ SCORES ================\n")
    print(result["scores"])