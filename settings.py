# settings.py

import os
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

# ===== Nemotron =====
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")

# ===== Qdrant =====
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "mes_wi_chunks")

# ===== 資料夾 =====
DATA_DIR = "data/docs"

# ===== Chunk 參數 =====
# 這是先求穩定的版本，不要先亂改
TARGET_CHARS = 900
OVERLAP_CHARS = 120

# ===== Retrieval 參數 =====
TOP_K_RETRIEVE = 20
TOP_K_RERANK = 5