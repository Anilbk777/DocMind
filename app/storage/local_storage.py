import asyncio
import aiofiles
from pathlib import Path
from app.storage.base_storage import BaseStorageService
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class LocalStorageService(BaseStorageService):
    def __init__(self, base_dir: str = "media"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file_bytes(
        self, file_name: str, file_bytes: bytes, folder: str
    ) -> str:
        target_dir = self.base_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / file_name

        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_bytes)

            logger.info(f"File bytes successfully stored locally at: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Local file write failure: {str(e)}")
            raise e

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

    async def delete_file(self, file_path: str) -> bool:
        try:
            # 1. Resolve to an absolute path to unpack any symlinks or '../' hacks
            target_path = Path(file_path).resolve()
            logger.info(
                f"Requested local file deletion for resolved path: {target_path}"
            )

            # 2. Security Boundary Check: Ensure the target path is strictly inside the base directory
            if self.base_dir not in target_path.parents:
                logger.error(
                    f"Security Alert! Path traversal attempt blocked. "
                    f"Target path '{target_path}' is outside root storage '{self.base_dir}'."
                )
                return False

            # 3. Check physical existence and safely unlink inside a worker thread
            if target_path.exists() and target_path.is_file():
                await asyncio.to_thread(target_path.unlink)
                logger.info(f"Successfully deleted local file: {target_path}")
                return True

            logger.warning(
                f"File deletion skipped: File not found at path '{target_path}'."
            )
            return False

        except Exception as e:
            logger.error(f"Failed to delete local file '{file_path}': {str(e)}")
            return False
