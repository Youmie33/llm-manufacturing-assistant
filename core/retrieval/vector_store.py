from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION
from core.utils.query_utils import expand_query
from qdrant_client.models import Filter, FieldCondition, MatchValue


class QdrantStore:
    def __init__(self):
        print("🔥 初始化 QdrantStore")
        self.client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=60
        )

    # =========================
    # 🔍 Vector Search
    # =========================
    def search(self, query_vector, limit=5, sources=None):
        print("🔥🔥🔥 進入 Qdrant search")
        print("👉 vector長度:", len(query_vector))

        query_filter = None

        # 🔥 限定來源（Source Router 用）
        if sources:
            query_filter = Filter(
                should=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=src)
                    )
                    for src in sources
                ]
            )

        results = self.client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            query_filter=query_filter,
            limit=limit
        )

        docs = []
        for point in results.points:
            payload = point.payload or {}
            docs.append({
                "text": payload.get("text", ""),
                "source": payload.get("source", ""),
                "pages": payload.get("pages", []),
                "chunk_index": payload.get("chunk_index", 0),
                "score": getattr(point, "score", 0)
            })

        print("👉 回傳 docs:", len(docs))
        return docs

    # =========================
    # 🔍 Keyword Search（簡化版）
    # =========================
    def keyword_search(self, query, limit=5, sources=None):
        print("🔍 keyword search:", query)

        results, _ = self.client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=500,  # 🔥 降低負擔
            with_payload=True,
            with_vectors=False
        )

        terms = expand_query(query)
        docs = []

        for point in results:
            payload = point.payload or {}
            text = payload.get("text", "")
            source = payload.get("source", "")

            if sources and source not in sources:
                continue

            hit_count = 0
            for term in terms:
                if term and (term in text or term in source):
                    hit_count += 1

            if hit_count > 0:
                docs.append({
                    "text": text,
                    "source": source,
                    "pages": payload.get("pages", []),
                    "chunk_index": payload.get("chunk_index", 0),
                    "score": hit_count
                })

        # 🔥🔥🔥 這段你一定要加
        docs = sorted(docs, key=lambda x: x["score"], reverse=True)

        print(f"👉 keyword 命中: {len(docs)}")
        return docs[:limit]   
        
    # =========================
    # 📚 取得所有文件名稱
    # =========================
    def get_all_sources(self):
        results, _ = self.client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=5000,
            with_payload=True,
            with_vectors=False
        )

        sources = set()

        for point in results:
            payload = point.payload or {}
            source = payload.get("source", "")
            if source:
                sources.add(source)

        sources = sorted(list(sources))
        print(f"📚 source 數量: {len(sources)}")
        return sources

    # =========================
    # 📄 🔥 取得整份文件（超重要）
    # =========================
    def get_chunks_by_source(self, source):
        print(f"📂 Loading full document: {source}")

        results, _ = self.client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=5000,
            with_payload=True,
            with_vectors=False
        )

        docs = []
        for point in results:
            payload = point.payload or {}

            if payload.get("source") == source:
                docs.append({
                    "text": payload.get("text", ""),
                    "source": payload.get("source", ""),
                    "pages": payload.get("pages", []),
                    "chunk_index": payload.get("chunk_index", 0)
                })

        # 🔥 保證流程順序
        docs = sorted(docs, key=lambda x: x["chunk_index"])

        print(f"📚 Loaded {len(docs)} chunks")
        return docs

    # =========================
    # 🏗️ Collection + Index
    # =========================
    def ensure_collection(self, vector_size: int):
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]

        if QDRANT_COLLECTION not in names:
            from qdrant_client.models import VectorParams, Distance

            self.client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )

            print(f"✅ 建立 collection: {QDRANT_COLLECTION}")
        else:
            print(f"✅ collection 已存在: {QDRANT_COLLECTION}")

        # 🔥 確保 index
        self._ensure_payload_index()

    def _ensure_payload_index(self):
        try:
            from qdrant_client.models import PayloadSchemaType

            self.client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="source",
                field_schema=PayloadSchemaType.KEYWORD
            )

            print("✅ source index 確保完成")

        except Exception as e:
            print("ℹ️ index 可能已存在:", e)

    # =========================
    # 📥 Upsert（寫入資料）
    # =========================
    def upsert_chunks(self, chunks, vectors):
        from qdrant_client.models import PointStruct
        import uuid

        BATCH_SIZE = 100

        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk.get("text", ""),
                        "source": chunk.get("source", ""),
                        "pages": chunk.get("pages", []),
                        "chunk_index": idx  # 🔥🔥🔥 關鍵
                    }
                )
            )

        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]

            print(f"🚀 上傳 batch {i} ~ {i + len(batch)}")

            self.client.upsert(
                collection_name=QDRANT_COLLECTION,
                points=batch
            )

        print(f"✅ 已寫入 Qdrant: {len(points)} 筆")