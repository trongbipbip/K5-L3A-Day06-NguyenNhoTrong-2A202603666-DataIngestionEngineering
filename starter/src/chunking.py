from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """Split one page into overlapping fixed-size chunks."""
    if size <= 0:
        raise ValueError("size must be greater than zero")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    if not page.text.strip():
        return []

    chunks: list[Chunk] = []
    step = size - overlap
    start = 0
    chunk_index = 0

    while start < len(page.text):
        end = min(start + size, len(page.text))
        chunk_text = page.text[start:end].strip()

        if chunk_text:
            chunks.append(
                Chunk(
                    chunk_id=(
                        f"{page.document_id}-"
                        f"p{page.page:04d}-"
                        f"fixed-{chunk_index:04d}"
                    ),
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=chunk_text,
                    metadata={
                        **page.metadata,
                        "chunking": "fixed_size",
                        "chunk_size": size,
                        "overlap": overlap,
                    },
                )
            )

        chunk_index += 1

        if end >= len(page.text):
            break

        start += step

    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Group paragraphs and split oversized paragraphs."""
    if max_size <= 0:
        raise ValueError("max_size must be greater than zero")

    if not page.text.strip():
        return []

    raw_paragraphs = [
        paragraph.strip()
        for paragraph in page.text.split("\n\n")
        if paragraph.strip()
    ]

    paragraphs: list[str] = []

    for paragraph in raw_paragraphs:
        if len(paragraph) <= max_size:
            paragraphs.append(paragraph)
            continue

        start = 0
        while start < len(paragraph):
            part = paragraph[start:start + max_size].strip()
            if part:
                paragraphs.append(part)
            start += max_size

    grouped: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"

        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                grouped.append(current)
            current = paragraph

    if current:
        grouped.append(current)

    chunks: list[Chunk] = []

    for index, text in enumerate(grouped):
        chunks.append(
            Chunk(
                chunk_id=(
                    f"{page.document_id}-"
                    f"p{page.page:04d}-"
                    f"paragraph-{index:04d}"
                ),
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=text,
                metadata={
                    **page.metadata,
                    "chunking": "paragraph",
                    "max_size": max_size,
                },
            )
        )

    return chunks
