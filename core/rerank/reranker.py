from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self):
        # 🔥 model只初始化一次（很重要）
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    def rerank(self, query, docs):
        if not docs:
            return []

        pairs = [(query, d["text"]) for d in docs]

        scores = self.model.predict(pairs)

        # 把score寫回去（之後debug很好用）
        for d, s in zip(docs, scores):
            d["rerank_score"] = float(s)

        docs = sorted(
            docs,
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return docs


# 🔥（保留舊接口，不讓你其他地方炸掉）
_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, docs):
    pairs = [(query, d["text"]) for d in docs]
    scores = _model.predict(pairs)

    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in ranked]