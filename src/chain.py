"""LangChain RAG chain: retrieve → format context → generate with Claude."""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_chroma import Chroma

from src.config import LLM_MODEL, ANTHROPIC_API_KEY, SYSTEM_PROMPT
from src.utils import format_docs


def build_chain(vectorstore: Chroma):
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6},
    )

    llm = ChatAnthropic(
        model=LLM_MODEL,
        anthropic_api_key=ANTHROPIC_API_KEY,
        streaming=True,
        max_tokens=2048,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{chat_history}\n\nบริบทจากแนวทางเวชปฏิบัติ:\n{context}\n\nคำถาม: {question}"),
    ])

    def retrieve_and_format(inputs: dict) -> dict:
        question = inputs["question"]
        docs = retriever.invoke(question)
        return {
            "context": format_docs(docs),
            "question": question,
            "chat_history": inputs.get("chat_history", ""),
            "_docs": docs,
        }

    chain = (
        RunnableLambda(retrieve_and_format)
        | {
            "answer": (
                {
                    "context": lambda x: x["context"],
                    "question": lambda x: x["question"],
                    "chat_history": lambda x: x["chat_history"],
                }
                | prompt
                | llm
                | StrOutputParser()
            ),
            "docs": lambda x: x["_docs"],
        }
    )

    return chain


def build_streaming_chain(vectorstore: Chroma):
    """Returns a chain that streams only the answer tokens, plus a separate retriever for docs."""
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6},
    )

    llm = ChatAnthropic(
        model=LLM_MODEL,
        anthropic_api_key=ANTHROPIC_API_KEY,
        streaming=True,
        max_tokens=2048,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{chat_history}\n\nบริบทจากแนวทางเวชปฏิบัติ:\n{context}\n\nคำถาม: {question}"),
    ])

    answer_chain = (
        {
            "context": RunnablePassthrough(),
            "question": RunnablePassthrough(),
            "chat_history": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return retriever, answer_chain
