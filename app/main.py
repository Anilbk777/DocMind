from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from dotenv import load_dotenv


from app.utils.logging import LoggerFactory
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers.upload_router import router as upload_router
from app.api.routers.chat_router import router as chat_router

load_dotenv()
logger = LoggerFactory.get_logger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Create a shared ThreadPoolExecutor for heavy file parsing tasks
    logger.info("Initializing application ThreadPoolExecutor...")
    app.state.thread_executor = ThreadPoolExecutor(
        max_workers=5, thread_name_prefix="ingestion_worker"
    )
    logger.info("Server is fully warmed up and ready to accept requests.")
    yield
    logger.info("Shutting down worker thread pool safely...")
    app.state.thread_executor.shutdown(wait=True)


app = FastAPI(title="Local RAG Development Server", lifespan=app_lifespan)
app.include_router(upload_router)
app.include_router(chat_router)

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
