"""
Ingestion pipeline: PDFs → chunks → embeddings → ChromaDB.
Run once: python -m src.ingest
"""

import os
import sys
from pathlib import Path

import unicodedata

import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from src.config import (
    DATA_PATH,
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    COLLECTION_NAME,
    DISEASE_MAP,
    OPENAI_API_KEY,
)


def extract_pages(pdf_path: Path) -> list[Document]:
    """Extract text per page using PyMuPDF block mode to preserve Thai paragraph structure."""
    docs = []
    disease_name = DISEASE_MAP.get(pdf_path.name, pdf_path.stem)
    pdf = fitz.open(str(pdf_path))
    for page in pdf:
        text = unicodedata.normalize("NFC", page.get_text("text"))
        if not text.strip():
            continue
        docs.append(Document(
            page_content=text,
            metadata={
                "source": pdf_path.name,
                "disease": disease_name,
                "page": page.number + 1,
            }
        ))
    pdf.close()
    return docs


def ingest():
    data_dir = Path(DATA_PATH)
    pdf_files = sorted(data_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        sys.exit(1)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    all_chunks: list[Document] = []
    for pdf_path in pdf_files:
        print(f"Processing {pdf_path.name}...")
        pages = extract_pages(pdf_path)
        chunks = splitter.split_documents(pages)
        print(f"  → {len(pages)} pages, {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Building ChromaDB index...")

    embedding = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embedding,
        persist_directory=CHROMA_DB_PATH,
        collection_name=COLLECTION_NAME,
    )

    print(f"Done. ChromaDB saved to {CHROMA_DB_PATH}")
    print(f"Collection '{COLLECTION_NAME}' contains {vectorstore._collection.count()} vectors.")


if __name__ == "__main__":
    ingest()
