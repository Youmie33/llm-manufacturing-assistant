# core/json_parser.py

import json
import re


def extract_json(text: str):
    """
    從 LLM 回應中強制抽出 JSON
    """

    try:
        return json.loads(text)
    except:
        pass

    # 抓 {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    # fallback
    return {
        "summary": text,
        "steps": [],
        "notes": []
    }