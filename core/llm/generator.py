from openai import OpenAI
from settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL


class Generator:
    def __init__(self):
        self.client = OpenAI(
            api_key=NVIDIA_API_KEY,
            base_url=NVIDIA_BASE_URL,
        )
        self.model = NVIDIA_MODEL

    # =========================
    # 判斷問題類型
    # =========================
    def detect_mode(self, question):
        keywords = ["怎麼", "如何", "流程", "步驟", "操作", "設定"]
        return "procedure" if any(k in question for k in keywords) else "qa"

    # =========================
    # Context 清洗
    # =========================
    def build_context_block(self, docs):
        blocks = []
        total_len = 0
        MAX_TOTAL = 3000

        for i, doc in enumerate(docs, start=1):
            text = doc.get("text", "")
            if not isinstance(text, str):
                text = str(text)

            text = text.strip()

            # 🔥 強化過濾
            if any(k in text for k in [
                "Classification", "Page", "Approval", "版本",
                "機密", "Confidential", "Low speed", "guide", ".pdf"
            ]):
                continue

            if len(text) < 30:
                continue

            if total_len > MAX_TOTAL:
                break

            blocks.append(f"[{i}] {text}")
            total_len += len(text)

        return "\n\n".join(blocks)

    # =========================
    # 🔥🔥🔥 核心：超強 reasoning parser
    # =========================
    def extract_from_reasoning(self, reasoning):
        if not reasoning:
            return None

        text = reasoning.strip()

        # 找開始位置
        markers = [
            "Let's compile steps:",
            "Let’s compile steps:",
            "Preparation:",
            "步驟：",
            "answer:"
        ]

        for m in markers:
            if m in text:
                text = text.split(m, 1)[-1]

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        steps = []
        started = False

        for line in lines:
            # 過濾推理句
            if any(line.startswith(x) for x in [
                "We need", "Let's", "Let’s", "From [", "Thus", "Also"
            ]):
                continue

            # 1. 2. 3.
            if line.startswith(tuple(f"{i}." for i in range(1, 30))):
                started = True
                steps.append(line)
                continue

            # - bullet
            if line.startswith("- "):
                started = True
                steps.append(line[2:].strip())
                continue

            # 接續上一行
            if started and steps:
                if not all(ord(c) < 128 for c in line):
                    steps[-1] += " " + line

        # 清洗
        cleaned = []
        idx = 1

        for s in steps:
            s = s.strip()

            # 英文比例過高 → 丟掉
            ascii_count = sum(1 for c in s if ord(c) < 128)
            if ascii_count > len(s) * 0.6:
                continue

            if len(s) < 10:
                continue

            cleaned.append(f"{idx}. {s}")
            idx += 1

        # 🔥 最低步驟數限制（超關鍵）
        if len(cleaned) < 5:
            return None

        return "answer:\n" + "\n".join(cleaned)

    # =========================
    # 主流程
    # =========================
    def generate(self, question, docs):
        context_text = self.build_context_block(docs)

        if len(context_text) > 4000:
            context_text = context_text[:4000]

        mode = self.detect_mode(question)

        if mode == "procedure":
            system_prompt = (
                "你是企業製造 WI 文件專家。\n\n"
                "請將文件中與操作相關的步驟整理為條列式流程。\n\n"

                "規則：\n"
                "1. 使用文件內容\n"
                "2. 允許重組順序\n"
                "3. 使用繁體中文\n\n"

                "輸出：\n"
                "answer:\n"
                "1. ...\n"
                "2. ...\n"
                "..."
            )
        else:
            system_prompt = "請用繁體中文回答問題，不要推理。"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"問題：{question}\n\n文件內容：\n{context_text}"}
                ],
                max_tokens=700,
                temperature=1.0,
                top_p=0.95,
                
                #extra_body= {
                #    "thinking": {"type": "disabled"}
                #}
                    
            )

            msg = response.choices[0].message
            content = getattr(msg, "content", None)
            reasoning = getattr(msg, "reasoning", None)

            print("DEBUG content =", repr(content))
            print("DEBUG reasoning =", repr(reasoning))

            # 🔥 Nemotron 專用處理
            if not content and reasoning:
                print("⚠️ reasoning → parsing")
                content = self.extract_from_reasoning(reasoning)

            if not content:
                return "⚠️ 模型沒有產生有效回答"

            return content.strip()

        except Exception as e:
            print("❌ LLM error:", e)
            return "⚠️ 系統錯誤"