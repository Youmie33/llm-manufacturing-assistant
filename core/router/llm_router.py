from openai import OpenAI
from settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL


class LLMRouter:
    def __init__(self):
        self.client = OpenAI(
            api_key=NVIDIA_API_KEY,
            base_url=NVIDIA_BASE_URL
        )

    def classify(self, query: str) -> str:
        """
        判斷 query 類型：
        - fact
        - procedure
        """

        prompt = f"""
請判斷以下問題的類型，只能回答一個詞：

fact = 查詢知識點 / 項目 / 定義
procedure = 查詢流程 / 操作步驟

問題：
{query}

請只回答：fact 或 procedure
"""

        try:
            response = self.client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            result = response.choices[0].message.content.strip().lower()

            if "procedure" in result:
                return "procedure"
            else:
                return "fact"

        except Exception as e:
            print("❌ LLM Router error:", e)
            return "fact"