"""
Thai Clinical Guideline Assistant — Streamlit app.
Run: streamlit run app.py
"""

import os

import streamlit as st
from pathlib import Path

from src.retriever import load_vectorstore, get_relevant_docs
from src.chain import build_streaming_chain
from src.utils import parse_citations, format_docs, format_chat_history
from src.config import CHROMA_DB_PATH, DISEASE_DISPLAY

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Thai CPG Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Password gate (set APP_PASSWORD in .env to enable) ───────────────────────
_app_password = os.getenv("APP_PASSWORD", "")
if _app_password:
    if not st.session_state.get("authenticated"):
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == _app_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()

# ── Load resources (cached so they survive Streamlit reruns) ──────────────────
@st.cache_resource(show_spinner="กำลังโหลดฐานข้อมูลแนวทางเวชปฏิบัติ...")
def load_resources():
    if not Path(CHROMA_DB_PATH).exists():
        return None, None
    vectorstore = load_vectorstore()
    retriever, answer_chain = build_streaming_chain(vectorstore)
    return vectorstore, answer_chain

vectorstore, answer_chain = load_resources()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 Thai CPG Assistant")
    st.caption("ผู้ช่วยแนวทางเวชปฏิบัติไทย")
    st.divider()

    with st.expander("📚 แนวทางเวชปฏิบัติที่ใช้", expanded=True):
        for disease_key, display_name in DISEASE_DISPLAY.items():
            st.markdown(f"- **{display_name}**")

    st.divider()

    if st.session_state.last_sources:
        st.markdown("**📄 แหล่งข้อมูลที่ใช้ตอบ**")
        seen = set()
        for doc in st.session_state.last_sources:
            src = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "?")
            key = (src, page)
            if key in seen:
                continue
            seen.add(key)
            with st.expander(f"📖 {src} — หน้า {page}"):
                st.caption(doc.page_content[:500] + ("..." if len(doc.page_content) > 500 else ""))

    st.divider()
    st.caption("⚠️ ข้อมูลนี้เป็นแนวทางเวชปฏิบัติทั่วไป ไม่ใช่คำแนะนำทางการแพทย์เฉพาะบุคคล กรุณาปรึกษาแพทย์")

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🏥 ผู้ช่วยแนวทางเวชปฏิบัติไทย")
st.caption("Thai Clinical Practice Guideline Assistant · เบาหวาน · ไขมัน · ความดัน")

if vectorstore is None:
    st.error(
        "⚠️ ไม่พบฐานข้อมูล ChromaDB กรุณาเรียกใช้งาน ingestion pipeline ก่อน:\n\n"
        "```bash\npython -m src.ingest\n```"
    )
    st.stop()

# Example questions
with st.expander("💡 ตัวอย่างคำถาม / Example questions", expanded=False):
    examples = [
        "ค่าเป้าหมาย HbA1c สำหรับผู้ป่วยเบาหวานชนิดที่ 2 ควรอยู่ที่เท่าไหร่?",
        "ความดันโลหิตเป้าหมายในผู้ป่วยความดันโลหิตสูงคือเท่าไหร่?",
        "เมื่อไหร่ควรเริ่มยา statin ในผู้ป่วยไขมันในเลือดสูง?",
        "ผู้ป่วยเบาหวานที่มีความดันโลหิตสูงควรได้รับยาอะไร?",
        "What are the LDL-C targets for high cardiovascular risk patients?",
    ]
    cols = st.columns(2)
    for i, example in enumerate(examples):
        if cols[i % 2].button(example, key=f"ex_{i}", use_container_width=True):
            st.session_state.pending_question = example
            st.rerun()

st.divider()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input — also picks up button-triggered questions
typed = st.chat_input("ถามคำถามเกี่ยวกับแนวทางเวชปฏิบัติ...")
active_prompt = typed or st.session_state.pending_question
if active_prompt:
    st.session_state.pending_question = None
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    with st.chat_message("assistant"):
        docs = get_relevant_docs(vectorstore, active_prompt)
        st.session_state.last_sources = docs

        from src.utils import format_docs
        context = format_docs(docs)
        history = format_chat_history(st.session_state.messages[:-1])

        stream_placeholder = st.empty()
        full_answer = ""

        try:
            stream = answer_chain.stream({
                "context": context,
                "question": active_prompt,
                "chat_history": history,
            })
            for chunk in stream:
                full_answer += chunk
                stream_placeholder.markdown(full_answer + "▌")

            stream_placeholder.markdown(full_answer)

            # Show out-of-scope banner
            if "ไม่พบ" in full_answer or "not found" in full_answer.lower():
                st.info("💡 ลองถามในรูปแบบอื่น หรือใช้คำศัพท์ทางการแพทย์ เช่น ชื่อยา ค่าทางห้องปฏิบัติการ")

        except Exception as e:
            full_answer = f"เกิดข้อผิดพลาด: {e}"
            stream_placeholder.error(full_answer)

        st.session_state.messages.append({"role": "assistant", "content": full_answer})
        st.rerun()
