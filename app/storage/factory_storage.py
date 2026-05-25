from app.storage.base_storage import BaseStorageService
from app.storage.local_storage import LocalStorageService
import os



def get_storage_service() -> BaseStorageService:
    storage_provider = os.environ.get("STORAGE_PROVIDER", "local").lower()

    if storage_provider == "local":
        return LocalStorageService()
    else:
        raise ValueError(f"Unsupported storage provider: {storage_provider}")
