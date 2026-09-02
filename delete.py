from qdrant_client import QdrantClient
from settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

client.delete_collection(collection_name=QDRANT_COLLECTION)

print("🔥 collection 已刪除")