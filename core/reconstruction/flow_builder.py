from sentence_transformers import SentenceTransformer
import numpy as np


class FlowBuilder:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def _cos_sim(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # 🔥 清洗 text（關鍵）
    def _clean_text(self, text):
        if not text:
            return ""

        garbage_keywords = [
            "項目", "名稱", "Item", "No", "Page",
            "Classification", "等級", "核准單號",
            "發行日期", "Revision", "版本"
        ]

        for g in garbage_keywords:
            if g in text:
                return ""

        if len(text.strip()) < 30:
            return ""

        if text.count("：") > 5:
            return ""

        if sum(c.isalpha() for c in text) > len(text) * 0.5:
            return ""

        return text.strip()

    def build_flow(self, docs, query=None):
        flow = []

        for d in docs:
            clean_text = self._clean_text(d.get("text", ""))  # ✅ 修正

            if not clean_text:
                continue  # 🔥 空的直接丟掉

            flow.append({
                "text": clean_text,
                "source": d.get("source", ""),
                "chunk_index": d.get("chunk_index", 0),
                "section": d.get("section", ""),
            })

        # 🔹 排序
        flow = sorted(flow, key=lambda x: x["chunk_index"])

        # 🔥 智慧裁切
        if query:
            flow = self._smart_select(flow, query)

        print(f"🔧 Flow steps after smart filter: {len(flow)}")

        return {
            "steps": flow
        }

    def _smart_select(self, flow, query, top_k=12):
        if not flow:
            return []

        clean_flow = []

        for f in flow:
            text = f.get("text", "")

            if not text:
                continue

            # ❌ 過濾表頭
            if any(k in text for k in [
                "Classification", "等級", "核准單號", "發行日期",
                "Page", "頁次", "Formulate", "Revision", "版本"
            ]):
                continue

            if len(text.strip()) < 20:
                continue

            # ✅ 保留流程
            if any(k in text for k in ["4.", "操作", "切割", "修刀", "安裝"]):
                clean_flow.append(f)

        if not clean_flow:
            return flow[:top_k]

        texts = [f["text"] for f in clean_flow]

        try:
            query_emb = self.embedder.encode(query)
            text_embs = self.embedder.encode(texts)

            scored = []
            for i, emb in enumerate(text_embs):
                sim = self._cos_sim(query_emb, emb)
                scored.append((sim, clean_flow[i]))

            scored = sorted(scored, key=lambda x: x[0], reverse=True)

            selected = [item[1] for item in scored[:top_k]]

            # 🔥 排回順序
            selected = sorted(selected, key=lambda x: x["chunk_index"])

            return selected

        except Exception as e:
            print("❌ Smart select error:", e)
            return clean_flow[:top_k]