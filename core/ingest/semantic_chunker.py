from __future__ import annotations

from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer


model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def cosine_similarity(a, b) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def is_valid_chunk(text: str) -> bool:
    if not text:
        return False
    if len(text.strip()) < 80:
        return False
    return True


def semantic_merge_chunks(chunks: List[Dict], threshold: float = 0.84) -> List[Dict]:
    """
    只合併「相鄰」且「同 section」的 chunk
    """
    if len(chunks) <= 1:
        return chunks

    merged: List[Dict] = []
    i = 0

    while i < len(chunks):
        current = dict(chunks[i])
        current_text = current["text"]

        if not is_valid_chunk(current_text):
            merged.append(current)
            i += 1
            continue

        current_vec = model.encode(current_text)
        j = i + 1

        while j < len(chunks):
            nxt = chunks[j]
            next_text = nxt["text"]

            # section 不同，不合併
            if current.get("section", "") != nxt.get("section", ""):
                break

            if not is_valid_chunk(next_text):
                break

            next_vec = model.encode(next_text)
            sim = cosine_similarity(current_vec, next_vec)

            if sim >= threshold:
                current_text += "\n" + next_text
                current["text"] = current_text

                # step / steps 保留
                existing_steps = list(current.get("steps", []))
                next_steps = list(nxt.get("steps", []))
                current["steps"] = list(dict.fromkeys(existing_steps + next_steps))

                if not current.get("step") and nxt.get("step"):
                    current["step"] = nxt["step"]

                current_vec = model.encode(current_text)
                j += 1
            else:
                break

        merged.append(current)
        i = j

    print(f"🧠 Semantic merged: {len(chunks)} → {len(merged)}")
    return merged