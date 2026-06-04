from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from dotenv import load_dotenv


from app.utils.logging import LoggerFactory
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers.upload_router import router as upload_router
from app.api.routers.chat_router import router as chat_router
from app.api.routers.auth_router import router as auth_router
from app.core.models import UserModel, ChatSessionModel, ChatMessageModel , DocumentModel
from app.core.database import Base, engine, AsyncSessionLocal
import os

load_dotenv()
logger = LoggerFactory.get_logger(__name__)

_cpu_cores: int = os.cpu_count() or 1
MAX_INGESTION_WORKERS: int = min(_cpu_cores * 2, 10)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.info("Creating database tables if not exists...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    app.state.session_factory = AsyncSessionLocal
    logger.info("Initializing application ThreadPoolExecutor...")
    app.state.thread_executor = ThreadPoolExecutor(
        max_workers=MAX_INGESTION_WORKERS, thread_name_prefix="ingestion_worker"
    )
    logger.info("Server is fully warmed up and ready to accept requests.")
    yield
    logger.info("Shutting down worker thread pool safely...")
    app.state.thread_executor.shutdown(wait=True)
    await engine.dispose()
    logger.info("Database connection closed.")


app = FastAPI(title="Local RAG Development Server", lifespan=app_lifespan)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
