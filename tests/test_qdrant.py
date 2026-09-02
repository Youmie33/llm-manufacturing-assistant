# test_qdrant.py

from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY

# 建立 Qdrant client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY or None,
    timeout=60
)

# 列出目前所有 collections
print("Qdrant collections:")
print(client.get_collections())
