"""Citation parsing and chat history formatting."""

import re
from langchain_core.documents import Document

CITE_RE = re.compile(r'\[แหล่งที่มา:\s*([^\]\s,]+)[,\s]+หน้า\s+(\d+)\]')


def parse_citations(text: str) -> list[dict]:
    """Extract unique citations from generated answer text."""
    seen = set()
    citations = []
    for source, page in CITE_RE.findall(text):
        key = (source, page)
        if key not in seen:
            seen.add(key)
            citations.append({"source": source, "page": int(page)})
    return citations


def format_docs(docs: list[Document]) -> str:
    """Format retrieved documents as context string with citation markers."""
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        parts.append(f"[แหล่งที่มา: {source} หน้า {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def format_chat_history(messages: list[dict]) -> str:
    """Convert Streamlit message list to a plain-text history string for the prompt."""
    lines = []
    for msg in messages:
        role = "ผู้ใช้" if msg["role"] == "user" else "ผู้ช่วย"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)
