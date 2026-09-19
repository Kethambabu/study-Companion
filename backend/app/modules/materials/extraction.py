from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import fitz  # PyMuPDF


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    metadata: dict = field(default_factory=dict)


class OCRProvider(ABC):
    """Abstract Base Class for OCR providers handling scanned or image-heavy document pages."""

    @abstractmethod
    def ocr_page(self, image_bytes: bytes) -> str:
        """Performs Optical Character Recognition on raw image bytes."""
        pass


class MockOCRProvider(OCRProvider):
    """Fallback / Mock OCR Provider implementation for testing and image pages."""

    def ocr_page(self, image_bytes: bytes) -> str:
        return "[OCR Extracted Text: Image scan processed by OCR Engine]"


class DocumentExtractor(ABC):
    """Abstract Base Class for Document Extractors."""

    @abstractmethod
    def extract(self, file_bytes: bytes) -> list[ExtractedPage]:
        """Extracts text pages and metadata from document byte stream."""
        pass


class PyMuPDFExtractor(DocumentExtractor):
    """Text and Metadata Extractor leveraging PyMuPDF (fitz) with OCR Provider fallback."""

    def __init__(self, ocr_provider: OCRProvider | None = None):
        self.ocr_provider = ocr_provider or MockOCRProvider()

    def extract(self, file_bytes: bytes) -> list[ExtractedPage]:
        if not file_bytes:
            raise ValueError("Empty file bytes provided for document extraction.")

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document stream: {str(e)}") from e

        extracted_pages: list[ExtractedPage] = []

        try:
            for i, page in enumerate(doc):
                page_num = i + 1
                text = page.get_text("text") or ""
                method = "pymupdf_text"

                # If page text is virtually empty (scanned/image-only PDF page)
                if len(text.strip()) < 10:
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    ocr_text = self.ocr_provider.ocr_page(img_bytes)
                    if ocr_text:
                        text = ocr_text
                        method = "ocr_fallback"

                # Extract page headings/structure
                lines = text.split("\n")
                headings = [line.strip().lstrip("#").strip() for line in lines if line.strip().startswith("#") or (len(line.strip()) < 50 and line.strip().isupper() and len(line.strip()) > 3)]

                words = len(text.split())
                reading_minutes = max(1, round(words / 200)) if words > 0 else 0

                metadata = {
                    "char_count": len(text),
                    "word_count": words,
                    "reading_minutes": reading_minutes,
                    "headings": headings[:5],
                    "extraction_method": method,
                }

                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=text.strip(),
                        metadata=metadata,
                    )
                )
        finally:
            doc.close()

        return extracted_pages
