from typing import List, Dict
import re
import numpy as np
from sentence_transformers import SentenceTransformer


class Evaluator:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # =========================
    # 工具
    # =========================
    def _cos_sim(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _split_sentences(self, text):
        if not isinstance(text, str):
            text = str(text)
        return [s.strip() for s in re.split(r"[。！？\n]", text) if s.strip()]

    # =========================
    # 1️⃣ Context Recall（🔥最重要）
    # =========================
    def context_recall(self, contexts: List[Dict]) -> float:
        """
        看有沒有抓到關鍵 SOP（4.x）
        """
        steps_found = set()

        for c in contexts:
            text = c.get("text", "")
            matches = re.findall(r"4\.(\d+)", text)
            steps_found.update(matches)

        expected = {"1", "2", "3", "4", "5", "6"}

        if not steps_found:
            return 0.0

        return len(steps_found & expected) / len(expected)

    # =========================
    # 2️⃣ Answer Relevancy
    # =========================
    def answer_relevancy(self, question: str, answer: str) -> float:
        if not answer:
            return 0.0

        q_emb = self.embedder.encode(question)
        a_emb = self.embedder.encode(answer)

        return float(self._cos_sim(q_emb, a_emb))

    # =========================
    # 3️⃣ Faithfulness（語意版🔥）
    # =========================
    def faithfulness(self, answer: str, contexts: List[Dict]) -> float:
        context_texts = [c.get("text", "") for c in contexts if c.get("text")]

        if not context_texts:
            return 0.0

        sentences = self._split_sentences(answer)

        if not sentences:
            return 0.0

        context_embs = self.embedder.encode(context_texts)

        supported = 0

        for s in sentences:
            s_emb = self.embedder.encode(s)

            sims = [self._cos_sim(s_emb, c_emb) for c_emb in context_embs]

            if max(sims) > 0.6:
                supported += 1

        return supported / len(sentences)

    # =========================
    # 4️⃣ Completeness（流程🔥）
    # =========================
    def completeness(self, flow_steps: List[Dict]) -> float:
        if not flow_steps:
            return 0.0

        steps = [s.get("step", "") for s in flow_steps]

        found = set()

        for step in steps:
            parts = step.split(".")
            if len(parts) >= 2:
                found.add(parts[1])

        expected = {"1", "2", "3", "4", "5", "6"}

        return len(found & expected) / len(expected)

    # =========================
    # 🔥 主評估
    # =========================
    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[Dict],
        flow_steps: List[Dict],
    ) -> Dict:

        recall = self.context_recall(contexts)
        relevancy = self.answer_relevancy(question, answer)
        faith = self.faithfulness(answer, contexts)
        comp = self.completeness(flow_steps)

        return {
            "context_recall": round(recall, 3),
            "answer_relevancy": round(relevancy, 3),
            "faithfulness": round(faith, 3),
            "completeness": round(comp, 3),
        }