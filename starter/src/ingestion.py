from pathlib import Path
import re
import unicodedata

from pypdf import PdfReader

from .models import DocumentPage


def chapter_for_page(page_number: int) -> str | None:
    """Map physical PDF pages to the book chapter.

    The PDF has ten front-matter pages before the printed page numbers begin.
    These ranges are derived from the book's contents pages and are kept
    explicit so the benchmark's chapter filters are reproducible.
    """
    ranges = [
        (1, 19, 48),
        (2, 49, 98),
        (3, 99, 152),
        (4, 153, 202),
        (5, 203, 248),
        (6, 249, 306),
        (7, 307, 368),
        (8, 369, 438),
        (9, 439, 510),
        (10, 511, 568),
        (11, 569, 668),
        (12, 669, 764),
        (13, 765, 820),
        (14, 821, 920),
    ]

    for chapter, first_page, last_page in ranges:
        if first_page <= page_number <= last_page:
            return str(chapter)

    return None


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace while preserving paragraphs."""
    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract every physical PDF page and retain page metadata."""
    reader = PdfReader(str(path))
    pages: list[DocumentPage] = []

    for page_number, pdf_page in enumerate(reader.pages, start=1):
        try:
            raw_text = pdf_page.extract_text() or ""
            text = normalize_text(raw_text)

            status = "ok" if text else "empty"

            pages.append(
                DocumentPage(
                    document_id=document_id,
                    source=source,
                    page=page_number,
                    text=text,
                    metadata={
                        "extraction_status": status,
                        "language": "en",
                        "category": "computer-science",
                        "chapter": chapter_for_page(page_number),
                    },
                )
            )
        except Exception as exc:
            pages.append(
                DocumentPage(
                    document_id=document_id,
                    source=source,
                    page=page_number,
                    text="",
                    metadata={
                        "extraction_status": "error",
                        "error": str(exc),
                        "language": "en",
                        "category": "computer-science",
                        "chapter": chapter_for_page(page_number),
                    },
                )
            )

    return pages
