import asyncio
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from app.storage.base_storage import BaseStorageService
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class LocalStorageService(BaseStorageService):
    def __init__(self, base_dir: str = "media"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file: UploadFile, folder: str) -> str:
        target_dir = self.base_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / file.filename

        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    await f.write(chunk)

            logger.info(f"File successfully stored locally at: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Local file write failure: {str(e)}")
            raise e
        finally:
            await file.seek(0)

    async def get_documents(self) -> list[dict[str, str]]:
        """Get all stored documents"""
        try:
            documents_list = []
            target_dir = self.base_dir / "documents"
            logger.info(f"getting documents from target directory: {target_dir}")
            for file_path in target_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    relative_path = file_path.relative_to(self.base_dir).as_posix()
                    full_storage_uri = f"{self.base_dir.name}/{relative_path}"
                    documents_list.append(
                        {
                            "file_name": file_path.name,
                            "storage_uri": full_storage_uri,
                        }
                    )

            logger.info(f"Found {len(documents_list)} documents")
            return documents_list

        except Exception as e:
            logger.error(f"Failed to get documents: {str(e)}")
            return []

    async def delete_file(self, file_name: str) -> bool:
        try:
            target_path = (self.base_dir / "documents" / file_name).resolve()
            if target_path.exists() and target_path.is_file():
                await asyncio.to_thread(target_path.unlink)

                logger.info(f"Deleted local file: {file_name}")
                return True

            logger.warning(f"File not found: {file_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete local file {file_name}: {str(e)} ")
            return False
