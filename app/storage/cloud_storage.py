import mimetypes
import os
import urllib.parse
from supabase import acreate_client, AsyncClient
from storage3.utils import StorageException  # Bypasses internal SDK parsing bugs
from app.storage.base_storage import BaseStorageService
from app.utils.exceptions import StorageError
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class CloudStorageService(BaseStorageService):
    def __init__(self):
        self.storage_url = os.environ["SUPABASE_URL"]
        self.storage_key = os.environ["SUPABASE_KEY"]
        self.bucket_name = os.environ["SUPABASE_BUCKET"]
        self._client: AsyncClient | None = None

    async def _get_client(self) -> AsyncClient:
        """Initialize the Supabase client asynchronously."""
        try:
            if self._client is None:
                self._client = await acreate_client(self.storage_url, self.storage_key)
            logger.info("Cloud storage client initialized successfully.")
            return self._client
        except Exception as e:
            logger.error(f"Failed to initialize cloud storage client: {str(e)}")
            raise StorageError(
                internal_detail=f"Failed to initialize cloud storage: {str(e)}"
            ) from e

    async def upload_file_bytes(
        self, file_name: str, file_bytes: bytes, folder: str = "documents"
    ) -> str:
        """Upload a file to Supabase Storage."""
        remote_path = f"{folder.strip('/')}/{file_name.strip('/')}"
        mime_type, _ = mimetypes.guess_type(file_name)
        mime_type = mime_type or "application/octet-stream"

        try:
            client = await self._get_client()

            # FIX: "upsert" value must be the string "true", not Python boolean True
            try:
                await client.storage.from_(self.bucket_name).upload(
                    path=remote_path,
                    file=file_bytes,
                    file_options={"content-type": mime_type, "upsert": "true"},
                )
            except Exception as e:
                # SDK crashes on response parsing but upload succeeds
                # only re-raise if it's NOT the dict/text parsing bug
                if "'dict' object has no attribute 'text'" not in str(e):
                    raise

            public_url = await client.storage.from_(self.bucket_name).get_public_url(
                remote_path
            )
            logger.info(
                f"Successfully synced file to cloud storage: {self.bucket_name}/{remote_path}"
            )
            return public_url

        except Exception as e:
            logger.error(f"Supabase cloud upload failed: {str(e)}")
            raise StorageError(
                internal_detail=f"Supabase upload failure: {str(e)}"
            ) from e

    async def get_documents(self) -> list[dict[str, str]]:
        """Get all documents from cloud storage."""
        try:
            target_folder = "documents"
            client = await self._get_client()
            files = await client.storage.from_(self.bucket_name).list(
                path=target_folder
            )
            documents_list = []

            for file_info in files:
                if file_info.get("id") is not None:
                    name = file_info["name"]
                    if name.startswith("."):
                        continue
                    documents_list.append(
                        {
                            "file_name": name,
                            "storage_uri": f"{target_folder}/{name}",
                        }
                    )
            return documents_list

        except Exception as e:
            logger.error(f"Failed to fetch document metadata list: {str(e)}")
            return []

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage.
        """
        try:
            # Check if code accidentally supplied a local Windows absolute file path
            if ":\\" in file_path or file_path.startswith("C:"):
                logger.warning(
                    f"Aborting deletion: '{file_path}' is a local filesystem path, not a cloud asset."
                )
                return False

            cleaned_path = file_path
            if "storage/v1/object/" in file_path:
                url_parts = file_path.split(f"/{self.bucket_name}/")
                if len(url_parts) > 1:
                    cleaned_path = url_parts[1]

            # Converts '%20' back to a standard literal space string
            cleaned_path = urllib.parse.unquote(cleaned_path)

            client = await self._get_client()

            response = await client.storage.from_(self.bucket_name).remove(
                [cleaned_path]
            )

            if not response:
                logger.warning(
                    f"Cloud asset path was not found inside bucket: {cleaned_path}"
                )
                return False

            logger.info(f"Successfully dropped cloud file: {cleaned_path}")
            return True

        except StorageException as error:
            # Catching StorageException prevents the SDK '.text' code failure
            error_msg = error.args[0] if error.args else str(error)
            logger.error(f"Supabase API deletion failure details: {error_msg}")
            return False

        except Exception as e:
            logger.error(f"Failed to delete cloud file target: {str(e)}")
            raise StorageError(
                internal_detail=f"Supabase deletion failure: {str(e)}"
            ) from e
