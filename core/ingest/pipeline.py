from __future__ import annotations

import re
from typing import Dict, List


def _flush_chunk(
    chunks: List[Dict],
    section: str | None,
    lines: List[str],
    steps: List[str],
    doc_type: str,
    source: str,
) -> None:
    if not section:
        return
    if not lines:
        return

    text = "\n".join(lines).strip()
    if not text:
        return

    chunks.append(
        {
            "source": source,
            "doc_type": doc_type,
            "section": section,
            "step": steps[0] if steps else "",
            "steps": list(dict.fromkeys(steps)),
            "text": text,
        }
    )


def _is_spot_section_heading(line: str) -> bool:
    """
    現貨元件檢驗 WI 的 section heading 判斷
    只把短標題當 section，例如：
    4.1 標籤檢查：
    4.4 X-ray 分析：
    不把長句內文誤判成 section
    """
    if not re.match(r"^4\.\d+\b", line):
        return False

    if len(line) > 90:
        return False

    if re.search(r"[:：]\s*$", line):
        return True

    heading_keywords = [
        "檢查",
        "檢驗",
        "量測",
        "分析",
        "驗證",
        "inspection",
        "measurement",
        "analysis",
        "check",
        "test",
    ]
    low = line.lower()
    return any(k in line or k in low for k in heading_keywords)


def _chunk_spot_wi(cleaned_lines: List[str], source: str, doc_type: str) -> List[Dict]:
    chunks: List[Dict] = []

    in_process = False
    current_section: str | None = None
    current_lines: List[str] = []
    current_steps: List[str] = []

    for line in cleaned_lines:
        if not in_process:
            if re.match(r"^4(\.0)?\s*作業程序", line) or line.startswith("4 作業程序"):
                in_process = True
            continue

        if _is_spot_section_heading(line):
            _flush_chunk(
                chunks,
                current_section,
                current_lines,
                current_steps,
                doc_type,
                source,
            )

            current_section = re.match(r"^4\.\d+\b", line).group()
            current_lines = [line]
            current_steps = []
            continue

        if current_section is None:
            continue

        step_match = re.match(r"^([1-6]\.\d+)\b", line)
        if step_match:
            current_steps.append(step_match.group(1))

        current_lines.append(line)

    _flush_chunk(
        chunks,
        current_section,
        current_lines,
        current_steps,
        doc_type,
        source,
    )

    return chunks


def _is_primary_heading_general(line: str) -> bool:
    """
    一般文件 / MRB / 溫濕度文件 的主 section 判斷
    """
    if re.match(r"^\d+\.0\b", line):
        return True

    if re.match(r"^[4-9]\.\d+\b", line):
        return True

    return False


def _chunk_general(cleaned_lines: List[str], source: str, doc_type: str) -> List[Dict]:
    chunks: List[Dict] = []

    current_section: str | None = None
    current_lines: List[str] = []
    current_steps: List[str] = []

    for line in cleaned_lines:
        if _is_primary_heading_general(line):
            _flush_chunk(
                chunks,
                current_section,
                current_lines,
                current_steps,
                doc_type,
                source,
            )

            current_section = re.match(r"^\d+\.\d+\b", line).group()
            current_lines = [line]
            current_steps = []
            continue

        if current_section is None:
            continue

        step_match = re.match(r"^(\d+\.\d+)\b", line)
        if step_match:
            current_steps.append(step_match.group(1))

        current_lines.append(line)

    _flush_chunk(
        chunks,
        current_section,
        current_lines,
        current_steps,
        doc_type,
        source,
    )

    return chunks


def _chunk_wi5000(cleaned_lines: List[str], source: str, doc_type: str) -> List[Dict]:
    chunks: List[Dict] = []

    current_section: str | None = None
    current_lines: List[str] = []
    current_steps: List[str] = []

    for line in cleaned_lines:
        # 章節，例如：1、WI-5000量測機開機前準備
        if re.match(r"^\d+、", line):
            _flush_chunk(
                chunks,
                current_section,
                current_lines,
                current_steps,
                doc_type,
                source,
            )

            current_section = re.match(r"^\d+、", line).group().replace("、", "")
            current_lines = [line]
            current_steps = []
            continue

        if current_section is None:
            continue

        # step，例如：1-1 / 2-3
        step_match = re.match(r"^(\d+-\d+)\b", line)
        if step_match:
            current_steps.append(step_match.group(1))

        current_lines.append(line)

    _flush_chunk(
        chunks,
        current_section,
        current_lines,
        current_steps,
        doc_type,
        source,
    )

    return chunks


def chunk_document(cleaned_lines: List[str], doc_type: str, source: str = "") -> List[Dict]:
    if doc_type == "spot_wi":
        chunks = _chunk_spot_wi(cleaned_lines, source, doc_type)
    elif doc_type == "wi5000":
        chunks = _chunk_wi5000(cleaned_lines, source, doc_type)
    else:
        chunks = _chunk_general(cleaned_lines, source, doc_type)

    print(f"🔵 Chunks: {len(chunks)}")
    return chunks