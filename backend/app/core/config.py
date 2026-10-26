import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "AI-Powered Text-to-SQL System"
    API_V1_STR: str = "/api"
    
    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "text2sql_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Google Gemini AI Model Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    # RAG (retrieval-augmented prompting) settings. All can be overridden in .env.
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    RAG_EMBEDDING_DIM: int = 768
    RAG_EMBED_TIMEOUT: float = 10.0          # seconds per embedding request (online path)
    RAG_EMBED_MAX_RETRIES: int = 2           # keep low online so a quota error cannot stall a request
    RAG_VECTOR_BACKEND: str = "chroma"       # "chroma" or "memory"
    RAG_STORE_PATH: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rag_store"))
    RAG_SCHEMA_ENABLED: bool = True          # retrieves only the relevant tables (min-tables 1 = always, even for the 11-table demo DB)
    RAG_SCHEMA_MIN_TABLES: int = 1
    RAG_SCHEMA_TOP_K: int = 4
    RAG_SCHEMA_MAX_TABLES: int = 6
    RAG_EXAMPLES_ENABLED: bool = True        # falls back to built-in examples until the index is built
    RAG_EXAMPLES_TOP_K: int = 4
    # which example sources may be retrieved: "project" = this app's own examples only;
    # "project,spider" also allows Spider pairs from unrelated databases
    RAG_EXAMPLE_SOURCES: str = "project"
    # Prompt annotations: table descriptions + allowed values of small-choice text columns
    SCHEMA_DESCRIPTIONS: bool = True
    SCHEMA_VALUE_HINTS: bool = True
    SCHEMA_HINT_MAX_VALUES: int = 12
    SCHEMA_INCLUDE_KEYS: bool = True         # add PRIMARY KEY / FOREIGN KEY info to the prompt schema

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

settings = Settings()
