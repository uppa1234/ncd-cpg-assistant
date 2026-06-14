"""ChromaDB vectorstore loader and retriever factory."""

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from src.config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    RETRIEVAL_TOP_K,
    OPENAI_API_KEY,
)


def load_vectorstore() -> Chroma:
    embedding = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embedding,
        collection_name=COLLECTION_NAME,
    )


def get_retriever(vectorstore: Chroma):
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVAL_TOP_K},
    )


def get_relevant_docs(vectorstore: Chroma, query: str):
    return vectorstore.similarity_search(query, k=RETRIEVAL_TOP_K)
