from __future__ import annotations

import re
from typing import List


META_KEYWORDS = [
    "document no",
    "file number",
    "file name",
    "document name",
    "version",
    "issued date",
    "approval no",
    "classification",
    "production unit",
    "proposed unit",
    "formulate date",
    "content pages",
    "revise",
    "revision",
    "review prepare",
    "approve",
    "prepared by",
    "reviewed by",
    "approved by",
    "released reviewed by",
    "g02-dcc",
    "excellence optoelectronics inc",
    "聯嘉光電股份有限公司",
    "聯 嘉 光 電 股 份 有 限 公 司",
    "文件編號",
    "文件名稱",
    "文件名 稱",
    "文件版次",
    "修訂履歷",
    "版 本",
    "核 准 單 號",
    "發 行 日 期",
    "機 密 等 級",
    "擬 案 單 位",
    "製作單位",
    "制訂日期",
    "內容頁次",
]


def _fix_spaced_chinese(text: str) -> str:
    """
    把 '聯 嘉 光 電 股 份 有 限 公 司' 這種拆散中文黏回來
    """
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    return text


def _normalize_line(text: str) -> str:
    text = str(text).replace("\u3000", " ")
    text = _fix_spaced_chinese(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_date_like(text: str) -> bool:
    return bool(
        re.fullmatch(r"\d{4}[./-]\d{1,2}[./-]\d{1,3}", text)
        or re.fullmatch(r"\d{2}\.\d{2}", text)
    )


def _is_metadata_line(text: str) -> bool:
    low = text.lower()

    if not text:
        return True

    if _is_date_like(text):
        return True

    if re.fullmatch(r"\d+\s*/\s*\d+", text):
        return True

    if re.fullmatch(r"\d+\s+of\s+\d+", low):
        return True

    if re.match(r"^g\d{2}-", low):
        return True

    if any(k in low for k in META_KEYWORDS):
        return True

    if re.search(r"page/?total pages", low):
        return True

    if re.search(r"document version", low):
        return True

    if re.search(r"newly established document", low):
        return True

    if re.search(r"revised according to the new coding principles", low):
        return True

    return False


def _split_mixed_numbering(line: str) -> List[str]:
    """
    把同一行裡混在一起的編號拆開
    例如：
    3.4顯微鏡 3.5 X-ray machine
    1、WI-5000... 1-1 ...
    """
    text = line

    # 在各種編號前插入換行
    text = re.sub(r"\s+(?=(\d+\.\d+\.\d+))", "\n", text)
    text = re.sub(r"\s+(?=(\d+\.\d+))", "\n", text)
    text = re.sub(r"\s+(?=(\d+-\d+))", "\n", text)
    text = re.sub(r"\s+(?=(\d+、))", "\n", text)

    # 處理像 "作1-1"、"及1-2" 這種沒有空白的情況
    text = re.sub(r"(?<!\d)(?=(\d+-\d+))", "\n", text)
    text = re.sub(r"(?<!\d)(?=(\d+、))", "\n", text)

    parts = [p.strip() for p in text.split("\n") if p.strip()]
    return parts


def _body_start_index(lines: List[str], doc_type: str) -> int:
    if doc_type == "wi5000":
        for i, line in enumerate(lines):
            if re.match(r"^\d+、", line):
                return i
        return 0

    if doc_type == "spot_wi":
        for i, line in enumerate(lines):
            if re.match(r"^1\s*目", line) or re.match(r"^1\s+目", line):
                return i
        return 0

    for i, line in enumerate(lines):
        if re.match(r"^1\.0\b", line) or re.match(r"^1\.0\s", line):
            return i
    return 0


def _dedupe_consecutive(lines: List[str]) -> List[str]:
    result: List[str] = []
    prev = None
    for line in lines:
        if line == prev:
            continue
        result.append(line)
        prev = line
    return result


def clean_lines(lines: List[str], doc_type: str = "general") -> List[str]:
    """
    清洗 PDF 抽出的原始 lines
    """
    # 1. normalize
    normalized = [_normalize_line(x) for x in lines]
    normalized = [x for x in normalized if x]

    # 2. 先砍 metadata
    filtered: List[str] = []
    for line in normalized:
        if _is_metadata_line(line):
            continue
        filtered.append(line)

    # 3. 切到正文開始
    start_idx = _body_start_index(filtered, doc_type)
    filtered = filtered[start_idx:]

    # 4. 拆混在同一行的 numbering
    split_lines: List[str] = []
    for line in filtered:
        split_lines.extend(_split_mixed_numbering(line))

    # 5. 再過一次 metadata 清洗
    final_lines: List[str] = []
    for line in split_lines:
        line = _normalize_line(line)
        if not line:
            continue
        if _is_metadata_line(line):
            continue
        final_lines.append(line)

    # 6. 去掉連續重複
    final_lines = _dedupe_consecutive(final_lines)

    print(f"🟢 Cleaned lines: {len(final_lines)}")
    print("\n===== FINAL CLEANED =====")
    for i, line in enumerate(final_lines[:20]):
        print(i, line)

    return final_lines