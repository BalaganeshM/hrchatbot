from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./hrchatbot.db"
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    OLLAMA_BASE_URL: str = "http://44.192.6.64:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_EMBEDDING_MODEL: str = "all-minilm"
    OLLAMA_TIMEOUT: int = 120
    OLLAMA_STREAM_TIMEOUT: int = 300
    VECTOR_STORE_PATH: str = "./chroma_db"

    class Config:
        env_file = ".env"


settings = Settings()
