from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from core.ingest.parser import parse_pdf, detect_doc_type
from core.ingest.cleaner import clean_lines
from core.ingest.pipeline import chunk_document
from core.ingest.semantic_chunker import semantic_merge_chunks


def process_document(file_path: str) -> List[Dict]:
    # 1. parse
    lines = parse_pdf(file_path)

    # 2. detect document type
    doc_type = detect_doc_type(lines)
    print(f"📘 Detected doc type: {doc_type}")

    # 3. clean
    cleaned = clean_lines(lines, doc_type=doc_type)

    # 4. structure-aware chunking
    chunks = chunk_document(cleaned, doc_type=doc_type, source=file_path)

    # 5. semantic merge（保留）
    chunks = semantic_merge_chunks(chunks)

    # 6. final filter
    filtered_chunks: List[Dict] = []
    for c in chunks:
        txt = c["text"]

        # spot_wi：至少要有 4.x section
        if c["doc_type"] == "spot_wi":
            if not re_search_any([r"4\.\d+"], txt):
                continue

        # wi5000：至少要有章節或 step
        elif c["doc_type"] == "wi5000":
            if not re_search_any([r"^\d+、", r"\d+-\d+"], txt):
                continue

        # general / mrb / temp_humidity
        else:
            if not re_search_any([r"\d+\.\d+"], txt):
                continue

        filtered_chunks.append(c)

    chunks = filtered_chunks

    print("\n========== CHUNK PREVIEW ==========")
    for i, c in enumerate(chunks[:5], start=1):
        print(f"\n--- Chunk {i} ---")
        print(f"Section: {c.get('section', '')}")
        if c.get("steps"):
            print(f"Steps: {c['steps']}")
        print(f"Text: {c['text'][:500]}")

    return chunks


def process_file(file_path: str) -> List[Dict]:
    """
    保留舊名稱，避免你原本其他地方呼叫 process_file 時壞掉
    """
    return process_document(file_path)


def re_search_any(patterns, text: str) -> bool:
    import re
    return any(re.search(p, text) for p in patterns)


if __name__ == "__main__":
    docs_dir = Path("data/docs")
    if not docs_dir.exists():
        raise FileNotFoundError(f"Folder not found: {docs_dir}")

    pdf_files = sorted(docs_dir.glob("*.pdf"))
    print(f"🔥 TOTAL FILES: {len(pdf_files)}")

    all_chunks: List[Dict] = []
    for pdf_file in pdf_files:
        print(f"\n📄 Processing: {pdf_file}")
        chunks = process_document(str(pdf_file))
        all_chunks.extend(chunks)

    print(f"\n✅ Total chunks after processing: {len(all_chunks)}")