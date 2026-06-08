import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.auth_router import router as auth_router
from app.api.routers.chat_router import router as chat_router
from app.api.routers.upload_router import router as upload_router
from app.core.database import AsyncSessionLocal, engine
from app.utils.exceptions import setup_exception_handlers
from app.utils.logging import LoggerFactory

load_dotenv()
logger = LoggerFactory.get_logger(__name__)

# _cpu_cores: int = os.cpu_count() or 1
# MAX_INGESTION_WORKERS: int = min(_cpu_cores * 2, 10)
_is_production = os.getenv("ENVIRONMENT", "development") == "production"
_cpu_cores: int = os.cpu_count() or 1
MAX_INGESTION_WORKERS: int = 2 if _is_production else min(_cpu_cores * 2, 10)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # logger.info("Creating database tables if not exists...")
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

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
setup_exception_handlers(app)

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(auth_router)

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Chat-Session-ID"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
