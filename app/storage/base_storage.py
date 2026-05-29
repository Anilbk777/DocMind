from fastapi import UploadFile
from abc import ABC, abstractmethod


class BaseStorageService(ABC):
    @abstractmethod
    async def upload_file(self, file: UploadFile, folder: str) -> str:
        pass

    @abstractmethod
    async def upload_file_bytes(self, file_name: str, file_bytes: bytes, folder: str) -> str:
        pass

    @abstractmethod
    async def get_documents(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        pass
