# app/main.py
from app.api import routers
import multiprocessing
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.utils.logging import LoggerFactory
from dotenv import load_dotenv
from app.ingestion.rag_components import get_vector_store

load_dotenv()

logger = LoggerFactory.get_logger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.info("Pre-warming embedding model and vector store at startup...")
    app.state.vector_store = get_vector_store()
    logger.info("Embedding model ready. Server is accepting requests.")

    worker_cores = max(1, multiprocessing.cpu_count() - 1)
    app.state.worker_cores = worker_cores
    app.state.process_pool = None

    yield

    if app.state.process_pool is not None:
        logger.info("Shutting down worker process pool...")
        app.state.process_pool.shutdown(wait=True)


app = FastAPI(title="Local RAG Development Server", lifespan=app_lifespan)

app.include_router(routers.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
