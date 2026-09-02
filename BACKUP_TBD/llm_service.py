# core/llm_service.py

from openai import OpenAI
from settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL

_client = None


def get_llm_client():
    """
    建立 Nemotron client。
    只建一次，後面重複使用。
    """
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=NVIDIA_API_KEY,
            base_url=NVIDIA_BASE_URL,
        )
    return _client


def build_context_block(docs: list[dict]) -> str:
    """
    把檢索到的文件片段組成 prompt 用的 context。
    """
    blocks = []

    for i, doc in enumerate(docs, start=1):
        pages = ",".join(str(p) for p in doc.get("pages", [])) if doc.get("pages") else "N/A"
        block = (
            f"[{i}] source={doc.get('source')} pages={pages}\n"
            f"{doc.get('text')}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def answer_with_nemotron(question: str, docs: list[dict]) -> str:
    client = get_llm_client()
    context_text = build_context_block(docs)

    response = client.chat.completions.create(
        model=NVIDIA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是企業製造 WI 專家。\n\n"
                    "請根據文件回答問題。\n\n"
                    "輸出格式：\n"
                    "1. 優先用條列整理（步驟 / 操作）\n"
                    "2. 每句話後加來源 [1]\n"
                    "3. 如果文件不足，可以合理補充\n"
                    "4. 使用繁體中文\n"
                )
            },
            {
                "role": "user",
                "content": (
                    f"問題：\n{question}\n\n"
                    f"文件內容：\n{context_text}"
                )
            }
        ],
        max_tokens=2000,
        temperature=0.3,
    )

    return response.choices[0].message.content