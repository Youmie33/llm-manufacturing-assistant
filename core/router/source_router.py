import numpy as np
from core.utils.query_utils import expand_query


class SourceRouter:
    def __init__(self, embedder):
        self.embedder = embedder

    def _cosine(self, a, b):
        a = np.array(a)
        b = np.array(b)

        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0

        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def select_sources(self, query, sources, top_k=3):
        """
        根據 query 從所有 source 中挑出最相關文件

        scoring:
        1. lexical overlap（字詞重疊）
        2. semantic similarity（語意相似）
        """

        if not sources:
            return []

        expanded_terms = expand_query(query)
        query_vec = self.embedder.encode(query)

        scored = []

        for source in sources:
            # 🔹 lexical
            lexical_score = 0
            for term in expanded_terms:
                if term and term in source:
                    lexical_score += 1

            # 🔹 semantic
            source_vec = self.embedder.encode(source)
            semantic_score = self._cosine(query_vec, source_vec)

            # 🔥 weighted score
            final_score = lexical_score * 2.0 + semantic_score

            scored.append({
                "source": source,
                "lexical_score": lexical_score,
                "semantic_score": semantic_score,
                "final_score": final_score,
            })

        scored = sorted(scored, key=lambda x: x["final_score"], reverse=True)

        print("📌 Source Router Top Candidates:")
        for item in scored[:top_k]:
            print(
                f" - {item['source']} | lexical={item['lexical_score']} "
                f"| semantic={item['semantic_score']:.4f} "
                f"| final={item['final_score']:.4f}"
            )

        return [item["source"] for item in scored[:top_k]]