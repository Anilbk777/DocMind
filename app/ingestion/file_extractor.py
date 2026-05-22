import io
from abc import ABC, abstractmethod

import pdfplumber
from docx import Document as DocxDocument
from typing import Type

from app.utils.exceptions import FileExtractionError


class IExtractor(ABC):
    """
    Interface definition for all custom stream extractors.
    """

    @abstractmethod
    def extract(self, file_bytes: bytes) -> str:
        """Process stream data into a continuous plain text string."""
        pass


class PDFExtractor(IExtractor):
    def extract(self, file_bytes: bytes) -> str:
        try:
            stream = io.BytesIO(file_bytes)
            text_pages = []

            with pdfplumber.open(stream) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_pages.append(page_text)

            return "\n".join(text_pages)

        except Exception as e:
            raise FileExtractionError(
                f"Failed parsing PDF stream layout via pdfplumber: {str(e)}"
            )


class DocxExtractor(IExtractor):
    def extract(self, file_bytes: bytes) -> str:
        try:
            stream = io.BytesIO(file_bytes)
            doc = DocxDocument(stream)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise FileExtractionError(f"Failed parsing DOCX structural nodes: {str(e)}")


class TxtExtractor(IExtractor):
    def extract(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError as e:
            try:
                return file_bytes.decode("latin-1", errors="ignore")
            except Exception:
                raise FileExtractionError(
                    f"Text encoding identification failed: {str(e)}"
                )


# Registry Mapping Extensions to Extractor Classes (Open for extension, Closed for modification)
EXTRACTOR_REGISTRY: dict[str, Type[IExtractor]] = {
    ".pdf": PDFExtractor,
    ".docx": DocxExtractor,
    ".txt": TxtExtractor,
}
