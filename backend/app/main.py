from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base, engine


def _run_migrations() -> None:
    """给旧库补齐新增列（SQLite ALTER TABLE ADD COLUMN，幂等）。"""
    inspector = inspect(engine)
    if "records" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("records")}
    additions = {
        "ref_low": "ALTER TABLE records ADD COLUMN ref_low FLOAT",
        "ref_high": "ALTER TABLE records ADD COLUMN ref_high FLOAT",
        "source": "ALTER TABLE records ADD COLUMN source VARCHAR(80)",
    }
    pending = [sql for col, sql in additions.items() if col not in existing]
    if pending:
        with engine.begin() as conn:
            for sql in pending:
                conn.execute(text(sql))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    yield


app = FastAPI(title="Chronicle API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
