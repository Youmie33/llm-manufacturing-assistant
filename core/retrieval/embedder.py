from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def encode(self, texts):
        vector = self.model.encode(texts)
        # 保險處理（避免 batch / 單筆問題）
        if len(vector.shape) > 1:
            vector = vector[0]
            
        return vector.tolist()