import asyncio
from functools import lru_cache
from typing import AsyncGenerator

from langchain_ollama import ChatOllama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

from app.config import settings

_GREETINGS = frozenset({
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "good day", "thanks", "thank you", "hi there", "hello there", "hey there",
    "morning", "afternoon", "evening", "yo", "sup",
})


# ── LLM / Embedding / Vector Store ──

@lru_cache
def get_llm():
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.0,
        num_predict=512,
        num_ctx=2048,
        num_thread=8,
        keep_alive="10m",
    )


class _ONNXEmbeddings(Embeddings):
    def __init__(self):
        self._ef = ONNXMiniLM_L6_V2()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._ef(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._ef([text])[0]


@lru_cache
def get_embeddings() -> Embeddings:
    return _ONNXEmbeddings()


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
            "You are HR assistant. User is {user_name} ({user_role}, {user_department}).\n"
            "Answer in 4-5 sentences.\n\n"
            "{salary_rule}\n\n"
            "ORG CHANGES:\n"
            "- Only admins can change reporting lines (use [ACTION: UPDATE_MANAGER employee=\"Full Name\" new_manager=\"Full Name\"]).\n"
            "- Non-admins: refuse.\n\n"
            "HR Policy:\n{context}\n\n"
            "Org Data:\n{org_context}"
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
    salary_rule: str = "can view their own salary only.",
    current_user_id: str = "",
    current_user_role: str = "",
) -> str:
    tokens = []
    async for token in ask_hr_policy_stream(
        question, session_id,
        user_name, user_role, user_department,
        org_context, salary_rule,
        current_user_id, current_user_role,
    ):
        tokens.append(token)
    return "".join(tokens)


async def ask_hr_policy_stream(
    question: str,
    session_id: str,
    user_name: str = "Unknown",
    user_role: str = "Unknown",
    user_department: str = "Unknown",
    org_context: str = "",
    salary_rule: str = "can view their own salary only.",
    current_user_id: str = "",
    current_user_role: str = "",
) -> AsyncGenerator[str, None]:
    q = question.strip().lower().rstrip(".!?").strip()
    if q in _GREETINGS:
        context = ""
    else:
        try:
            retriever = get_retriever()
            docs = await retriever.ainvoke(question)
            context = format_docs(docs)
        except Exception:
            context = ""

    input_data = {
        "input": question,
        "context": context or "No specific HR policy documents found for this query.",
        "org_context": org_context or "No organization data available.",
        "user_name": user_name,
        "user_role": user_role,
        "user_department": user_department,
        "salary_rule": salary_rule,
    }
    config = {"configurable": {"session_id": session_id}}
    chain = get_conversational_chat()

    stream = chain.astream(input_data, config=config)
    buffer = ""
    try:
        while True:
            chunk = await asyncio.wait_for(
                stream.__anext__(),
                timeout=settings.OLLAMA_STREAM_TIMEOUT,
            )
            if chunk.content:
                buffer += chunk.content
                for boundary in (". ", "! ", "? "):
                    if boundary in buffer:
                        parts = buffer.split(boundary, 1)
                        yield parts[0] + boundary.strip()
                        buffer = parts[1]
                        break
    except StopAsyncIteration:
        if buffer.strip():
            yield buffer
        return
    except asyncio.TimeoutError:
        if buffer.strip():
            yield buffer
        yield "\n\n[Request timed out. Please try a simpler question or try again later.]"


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
