import html
import streamlit as st
from core.pipeline.rag_pipeline import RAGPipeline


# ===============================
# 初始化
# ===============================
@st.cache_resource
def load_pipeline():
    return RAGPipeline()


pipeline = load_pipeline()

st.set_page_config(
    page_title="WI 文件 AI 助手",
    page_icon="📘",
    layout="wide",
)

# ===============================
# Session State
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_docs" not in st.session_state:
    st.session_state.last_docs = []

if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ===============================
# 小工具
# ===============================
def safe_text(value):
    if value is None:
        return ""
    return str(value)


def format_pages(pages):
    if not pages:
        return "N/A"
    return ", ".join(str(p) for p in pages)


def render_doc_card(doc, idx):
    source = safe_text(doc.get("source", ""))
    text = safe_text(doc.get("text", ""))
    pages = format_pages(doc.get("pages", []))
    score = doc.get("score", None)
    section = safe_text(doc.get("section", ""))

    meta_parts = []
    if section:
        meta_parts.append(f"Section: {section}")
    meta_parts.append(f"Pages: {pages}")
    if score is not None:
        try:
            meta_parts.append(f"Score: {float(score):.4f}")
        except Exception:
            meta_parts.append(f"Score: {score}")

    meta_line = " | ".join(meta_parts)

    st.markdown(f"### [{idx}] {source if source else '未知來源'}")
    st.caption(meta_line)

    escaped_text = html.escape(text)
    st.markdown(
        f"""
        <div style="
            height: 220px;
            overflow-y: auto;
            padding: 12px;
            border: 1px solid rgba(128,128,128,0.35);
            border-radius: 12px;
            background: rgba(17, 24, 39, 0.55);
            white-space: pre-wrap;
            line-height: 1.55;
            font-size: 13px;
        ">{escaped_text}</div>
        """,
        unsafe_allow_html=True,
    )


# ===============================
# Sidebar
# ===============================
with st.sidebar:
    st.title("⚙️ 控制台")
    st.markdown("目前模式：`Modular RAG Demo`")

    if st.button("🗑️ 清空對話", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_docs = []
        st.session_state.last_query = ""
        st.rerun()

    st.divider()

    st.markdown("### 使用方式")
    st.markdown(
        """
        1. 在下方輸入問題  
        2. 左側看回答  
        3. 右側看參考文件
        """
    )

    st.divider()
    st.caption("Powered by RAG + Qdrant + Reranker + LLM")


# ===============================
# Header
# ===============================
st.title("📘 WI 文件 AI 助手")
st.caption("企業文件問答 / 檢索 / 來源追溯 Demo")


# ===============================
# 主畫面
# ===============================
col_chat, col_docs = st.columns([1.7, 1.1], gap="large")

# -------------------------------
# 💬 聊天區
# -------------------------------
with col_chat:
    st.subheader("💬 對話區")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("請輸入問題...")

    if prompt:
        st.session_state.last_query = prompt

        # user
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # assistant
        with st.chat_message("assistant"):
            with st.spinner("檢索與生成中..."):
                result = pipeline.ask(prompt)

                answer = result.get("answer")
                docs = result.get("docs", [])
                scores = result.get("scores", {})

                # 🔥 防呆（關鍵）
                if not isinstance(answer, str) or not answer.strip():
                    answer = "⚠️ 系統沒有產生有效回答"

                # 額外防呆：如果模型把推理字樣吐出來，直接擋掉
                if answer.startswith("We need to") or "Let's parse" in answer:
                    answer = "⚠️ 模型回傳了中間推理內容，請再試一次。"
                
                st.markdown(answer)

                # 🔥 評分顯示（超加分）
                if scores:
                    with st.expander("📊 查看評分"):
                        st.json(scores)

                # 存給右側
                st.session_state.last_docs = docs

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })


# -------------------------------
# 📄 文件區
# -------------------------------
with col_docs:
    st.subheader("📄 參考文件")

    docs = st.session_state.last_docs

    if not docs:
        st.info("尚未顯示參考文件")
    else:
        st.caption(f"最近一次查詢：{st.session_state.last_query}")
        for i, doc in enumerate(docs, start=1):
            render_doc_card(doc, i)
            st.markdown("---")