from app.storage.base_storage import BaseStorageService
from app.storage.local_storage import LocalStorageService
from app.storage.cloud_storage import CloudStorageService
import os


def get_storage_service() -> BaseStorageService:
    storage_provider = os.environ.get("STORAGE_PROVIDER", "local").lower()

    if storage_provider == "local":
        return LocalStorageService()
    elif storage_provider == "cloud":
        return CloudStorageService()
    else:
        raise ValueError(f"Unsupported storage provider: {storage_provider}")
