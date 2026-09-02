print("🚨🚨🚨 我是現在這個 main.py")# main.py 或 api.py（你現在用哪個啟動就放哪個）

from fastapi import FastAPI
from pydantic import BaseModel
from core.pipeline.rag_pipeline import RAGService
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

# 啟動時確認有載入正確檔案
print(" API 啟動成功（確認用）")

# 建立 FastAPI app
app = FastAPI(
    title="MES WI RAG Service",
    version="1.0.0"
)

# 設定 HTML template 資料夾（給 UI 用）
templates = Jinja2Templates(directory="templates")

# 初始化 RAG（⚠️ 這行很重要）
rag = RAGService()

# rag = None  #  不要開這個，會讓系統完全沒有回應


# =========================
# Request Model（前端傳進來的資料格式）
# =========================
class AskRequest(BaseModel):
    question: str  # 前端會傳 { "question": "xxx" }


# =========================
# UI 頁面
# =========================
@app.get("/", response_class=HTMLResponse)
def ui(request: Request):
    """
    回傳 index.html（聊天畫面）
    """
    return templates.TemplateResponse("index.html", {
        "request": request
    })


# =========================
# 健康檢查 API
# =========================
@app.get("/health")
def health():
    """
    用來確認 API 是否正常運作
    """
    return {"status": "ok"}


# =========================
# 核心：問答 API
# =========================
@app.post("/ask")
def ask(req: AskRequest):
    print("🔥 有進到 /ask")

    try:
        result = rag.ask(req.question)
        print("👉 RAG結果:", result)

        return result

    except Exception as e:
        print("❌ 錯誤:", str(e))

        return {
            "summary": "系統錯誤",
            "steps": [],
            "notes": [str(e)]
        }


# =========================
# Debug API
# =========================
@app.get("/debug")
def debug():
    """
    用來確認你現在跑的是不是這個檔案
    """
    return {"msg": "yes this is my api"}