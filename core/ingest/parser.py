from __future__ import annotations

from pathlib import Path
import re
from typing import List

import pdfplumber


def parse_pdf(pdf_path: str) -> List[str]:
    """
    從 PDF 直接抽取文字層
    回傳逐行文字
    """
    lines: List[str] = []

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(str(pdf_file)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1.5, y_tolerance=3, layout=False)
            if not text:
                continue

            for raw in text.splitlines():
                line = raw.strip()
                if line:
                    lines.append(line)

    print(f"🟡 Extracted lines: {len(lines)}")
    return lines


def detect_doc_type(lines: List[str]) -> str:
    """
    依文件內容判斷文件類型，後面 chunk 策略會用到
    """
    sample = "\n".join(lines[:150]).lower()

    if "wi-5000" in sample:
        return "wi5000"

    if "mrb" in sample and ("qa33" in sample or "material review board" in sample):
        return "mrb"

    if (
        "temperature and humidity" in sample
        or "溫、濕度" in sample
        or "溫溼度" in sample
        or "溫、溼度" in sample
    ):
        return "temp_humidity"

    if "現貨" in sample and "檢驗作業指導書" in sample:
        return "spot_wi"

    return "general"


# 保留舊名稱，避免其他地方還在 import ocr_pdf
def ocr_pdf(pdf_path: str) -> List[str]:
    return parse_pdf(pdf_path)