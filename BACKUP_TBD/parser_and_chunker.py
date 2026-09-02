# core/parser_and_chunker.py

from pathlib import Path
from typing import List, Dict, Any
from unstructured.partition.auto import partition
from settings import TARGET_CHARS
from bs4 import BeautifulSoup
import re


# =========================
# 基礎工具
# =========================

def is_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def is_english(text):
    return bool(re.search(r'[a-zA-Z]', text))


# =========================
# Header 判斷（🔥重點）
# =========================

def is_header_block(text: str) -> bool:
    keywords = [
        "File Name", "File Number", "Version",
        "Page", "Formulate date",
        "Excellence Optoelectronics",
        "聯嘉光電股份有限公司",
        "Document No",
        "Issued Date"
    ]
    hit = sum(1 for k in keywords if k in text)
    return hit >= 2


# =========================
# 清洗層
# =========================

def fix_spacing(text: str) -> str:
    text = text.strip()

    # 英文拆字
    if re.match(r"^(\w\s+){3,}\w$", text):
        text = text.replace(" ", "")

    # 中文拆字
    text = re.sub(r'(?<=\u4e00)\s+(?=\u4e00)', '', text)

    text = re.sub(r"\s+", " ", text)
    return text


def is_gibberish(text: str) -> bool:
    t = text.strip()

    if len(t) <= 6 and not is_chinese(t):
        return True

    if re.match(r"^(\w\s+){2,}\w$", t):
        return True

    return False


def fix_reversed_word(word):
    if len(word) > 6 and not re.search(r'[aeiouAEIOU]', word[:3]):
        return word[::-1]
    return word


def clean_text(text: str) -> str:
    text = text.strip()

    # 🔥 Header → 直接跳過（不進 chunk）
    if is_header_block(text):
        return ""

    if is_gibberish(text):
        return ""

    # 修括號
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)

    # 修反轉英文
    text = " ".join(fix_reversed_word(w) for w in text.split())

    return text


# =========================
# 結構判斷（⚠️ 保留章節編號）
# =========================

def is_section_header(text: str) -> bool:
    return bool(re.match(r"^\d+(\.\d+)+", text.strip()))


def is_incomplete_sentence(text: str) -> bool:
    return not re.search(r"[。.!?)]$", text.strip())


# =========================
# 表格處理
# =========================

def html_table_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")

    table = []
    for row in rows:
        cols = [col.get_text(" ", strip=True) for col in row.find_all(["td", "th"])]
        if cols:
            table.append(cols)

    if not table:
        return ""

    md = "| " + " | ".join(table[0]) + " |\n"
    md += "| " + " | ".join(["---"] * len(table[0])) + " |\n"

    for row in table[1:]:
        md += "| " + " | ".join(row) + " |\n"

    return md


# =========================
# Merge + Stitch
# =========================

def merge_bilingual(lines: List[str]) -> List[str]:
    merged = []
    i = 0

    while i < len(lines):
        current = lines[i]

        if i + 1 < len(lines):
            nxt = lines[i + 1]

            if is_chinese(current) and is_english(nxt) and not is_chinese(nxt):
                merged.append(f"{current} ({nxt})")
                i += 2
                continue

            if is_english(current) and is_chinese(nxt):
                merged.append(f"{nxt} ({current})")
                i += 2
                continue

        merged.append(current)
        i += 1

    return merged


def stitch_lines(lines: List[str]) -> List[str]:
    stitched = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if not buffer:
            buffer = line
            continue

        # 未結束句
        if is_incomplete_sentence(buffer):
            buffer += " " + line
            continue

        # 英文補句（限制長度避免污染）
        if is_english(line) and not is_chinese(line) and len(line) < 120:
            buffer += " " + line
            continue

        # 被切壞句
        if re.match(r"^[^A-Za-z\u4e00-\u9fff]", line):
            buffer += " " + line
            continue

        # 章節切割（🔥避免污染）
        if is_section_header(line):
            if len(buffer) > 80:
                stitched.append(buffer)
                buffer = line
                continue

        stitched.append(buffer)
        buffer = line

    if buffer:
        stitched.append(buffer)

    return stitched


# =========================
# Chunk 主流程
# =========================

def chunk_elements(elements, source_name: str) -> List[Dict[str, Any]]:
    raw_texts = []

    for el in elements:
        meta = getattr(el, "metadata", None)
        table_html = getattr(meta, "text_as_html", None) if meta else None

        text = html_table_to_markdown(table_html) if table_html else getattr(el, "text", "")
        text = fix_spacing(text)

        if text:
            raw_texts.append(text)

    merged = merge_bilingual(raw_texts)
    stitched = stitch_lines(merged)

    chunks = []
    buffer = []
    buffer_len = 0
    seen = set()
    current_section = None

    def flush():
        nonlocal buffer, buffer_len

        if not buffer:
            return

        text = "\n".join(buffer).strip()

        if text in seen:
            return

        seen.add(text)

        print("\n🧩 CHUNK >>>", text[:200])

        chunks.append({
            "text": text,
            "source": source_name,
            "section_header": current_section
        })

        buffer = []
        buffer_len = 0

    for text in stitched:
        text = clean_text(text)
        if not text:
            continue

        # 保留章節（🔥重要）
        if is_section_header(text):
            current_section = text

        # 接續句
        if buffer and is_incomplete_sentence(buffer[-1]):
            buffer[-1] += " " + text
            buffer_len += len(text)
            continue

        # 避免句中切斷
        if buffer_len + len(text) > TARGET_CHARS and not is_incomplete_sentence(buffer[-1]):
            flush()

        buffer.append(text)
        buffer_len += len(text)

    flush()
    return chunks


# =========================
# 外部接口
# =========================

def partition_document(file_path: str):
    return partition(filename=file_path)


def load_and_chunk_file(file_path: str) -> List[Dict[str, Any]]:
    path = Path(file_path)
    elements = partition_document(str(path))
    return chunk_elements(elements, source_name=path.name)