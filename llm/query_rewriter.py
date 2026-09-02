class QueryRewriter:
    """
    先用簡單版本：
    - 不呼叫 LLM
    - 先做關鍵字擴展
    - 目的是讓 retrieval 比較容易找到 WI / SOP 內容

    之後我們再升級成真正的 LLM Query Rewrite
    """

    def __init__(self):
        self.synonyms = {
            "aoi": ["optical inspection", "defect inspection", "aoi inspection"],
            "spi": ["solder paste inspection", "paste inspection"],
            "ng": ["failure", "defect", "error", "abnormal"],
            "wi": ["work instruction", "instruction"],
            "sop": ["standard operating procedure", "procedure"],
            "流程": ["procedure", "steps", "process flow"],
            "步驟": ["procedure", "steps"],
            "過站": ["process step", "operation", "station"],
            "異常": ["abnormal", "error", "failure"],
            "重工": ["rework"],
            "檢查": ["inspection", "check"],
        }

    def rewrite(self, query: str) -> str:
        query_lower = query.lower()
        expanded_terms = []

        for key, values in self.synonyms.items():
            if key in query_lower or key in query:
                expanded_terms.extend(values)

        # 去重複
        expanded_terms = list(dict.fromkeys(expanded_terms))

        if expanded_terms:
            rewritten_query = f"{query} " + " ".join(expanded_terms)
        else:
            rewritten_query = query

        return rewritten_query.strip()