import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api import auth, employees, org, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        from app.services.langchain_service import ingest_hr_documents
        count = await asyncio.wait_for(ingest_hr_documents(), timeout=120)
        print(f"Ingested {count} SCB HR policy document chunks into vector store.")
    except Exception as e:
        print(f"HR document ingestion skipped (Ollama may not be running): {e}")
    yield
    await engine.dispose()


app = FastAPI(title="HRChatBot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://44.192.6.64:3000", "http://44.192.6.64:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(org.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
