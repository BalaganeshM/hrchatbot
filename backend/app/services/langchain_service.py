import asyncio
import time
from functools import lru_cache
from typing import AsyncGenerator

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


# ── LLM / Embedding / Vector Store ──

@lru_cache
def get_llm():
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.1,
        num_predict=2048,
        num_ctx=4096,
        num_thread=8,
        keep_alive="10m",
    )


@lru_cache
def get_embeddings():
    return OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_EMBEDDING_MODEL,
    )


@lru_cache
def get_vectorstore():
    return Chroma(
        collection_name="scb_hr_policies",
        embedding_function=get_embeddings(),
        persist_directory=settings.VECTOR_STORE_PATH,
    )


@lru_cache
def get_retriever():
    return get_vectorstore().as_retriever(search_kwargs={"k": 2})


# ── Session History ──

session_histories: dict[str, ChatMessageHistory] = {}
MAX_HISTORY_EXCHANGES = 3


def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in session_histories:
        session_histories[session_id] = ChatMessageHistory()
    history = session_histories[session_id]
    if len(history.messages) > MAX_HISTORY_EXCHANGES * 2:
        history.messages = history.messages[-(MAX_HISTORY_EXCHANGES * 2):]
    return history


def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def _make_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", (
            "You are an SCB HR assistant. User: {user_name}, Role: {user_role}, Dept: {user_department}.\n"
            "Answer elaborately in 4-5 sentences.\n\n"
            "ACCESS RULES:\n"
            "- Admin: can see salary (prefixed with $) of any employee.\n"
            "- Manager: can see salary of their direct/indirect reports only.\n"
            "- Employee: can see their own salary only.\n"
            "For others not authorized, only share name, role, position, department, manager.\n"
            "If asked for unauthorized details, politely refuse.\n\n"
            "ORG CHANGES:\n"
            "- Only admins can change reporting lines.\n"
            "- Non-admins: refuse and suggest contacting an admin.\n"
            "- Admin: to apply, end response with:\n"
            "[ACTION: UPDATE_MANAGER employee=\"Full Name\" new_manager=\"Full Name\"]\n\n"
            "Policy Context:\n{context}\n\n"
            "Organization Data:\n{org_context}"
        )),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])


def get_conversational_chat():
    return RunnableWithMessageHistory(
        _make_prompt() | get_llm(),
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )


# ── Public API ──

async def ask_hr_policy(
    question: str,
    session_id: str,
    user_name: str = "Unknown",
    user_role: str = "Unknown",
    user_department: str = "Unknown",
    org_context: str = "",
    current_user_id: str = "",
    current_user_role: str = "",
) -> str:
    retriever = get_retriever()
    docs = await retriever.ainvoke(question)
    context = format_docs(docs)

    for attempt in range(2):
        try:
            result = await asyncio.wait_for(
                get_conversational_chat().ainvoke(
                    {
                        "input": question,
                        "context": context or "No specific HR policy documents found for this query.",
                        "org_context": org_context or "No organization data available.",
                        "user_name": user_name,
                        "user_role": user_role,
                        "user_department": user_department,
                    },
                    config={"configurable": {"session_id": session_id}},
                ),
                timeout=settings.OLLAMA_TIMEOUT,
            )
            return result.content
        except asyncio.TimeoutError:
            if attempt == 1:
                return "I'm sorry, the request timed out. Please try a simpler question or try again later."
            await asyncio.sleep(1)
    return "I'm sorry, an error occurred. Please try again."


async def ask_hr_policy_stream(
    question: str,
    session_id: str,
    user_name: str = "Unknown",
    user_role: str = "Unknown",
    user_department: str = "Unknown",
    org_context: str = "",
    current_user_id: str = "",
    current_user_role: str = "",
) -> AsyncGenerator[str, None]:
    retriever = get_retriever()
    docs = await retriever.ainvoke(question)
    context = format_docs(docs)

    input_data = {
        "input": question,
        "context": context or "No specific HR policy documents found for this query.",
        "org_context": org_context or "No organization data available.",
        "user_name": user_name,
        "user_role": user_role,
        "user_department": user_department,
    }
    config = {"configurable": {"session_id": session_id}}
    chain = get_conversational_chat()

    for attempt in range(2):
        try:
            start = time.monotonic()
            result = await asyncio.wait_for(
                chain.ainvoke(input_data, config=config),
                timeout=settings.OLLAMA_TIMEOUT,
            )
            elapsed = time.monotonic() - start
            text = result.content
            # adaptive chunking based on actual response speed
            chunk_size = max(1, len(text) // max(1, int(elapsed * 10)))
            chunk_size = min(chunk_size, 8)
            for i in range(0, len(text), chunk_size):
                yield text[i:i + chunk_size]
                await asyncio.sleep(0.003)
            return
        except asyncio.TimeoutError:
            if attempt == 1:
                yield "\n\n[Request timed out. Please try a simpler question or try again later.]"
                return
            await asyncio.sleep(1)


async def ingest_hr_documents(docs_dir: str = "app/hr_docs") -> int:
    loader = DirectoryLoader(docs_dir, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)

    if chunks:
        try:
            get_vectorstore().delete_collection()
        except Exception:
            pass
        new_vs = Chroma(
            collection_name="scb_hr_policies",
            embedding_function=get_embeddings(),
            persist_directory=settings.VECTOR_STORE_PATH,
        )
        new_vs.add_documents(chunks)
        get_vectorstore.cache_clear()

    return len(chunks)
