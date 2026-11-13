"""Reproducible Day 06 ingestion, indexing and benchmark entry point."""
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .ingestion import load_pdf
from .store import PgVectorStore


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"))
    started = time.perf_counter()

    pages = load_pdf(
        Path("data/openstax_computer_science.pdf"),
        "openstax-computer-science",
        "data/openstax_computer_science.pdf",
    )

    embedder = MyEmbedder()
    store = PgVectorStore(
        os.environ["DATABASE_URL"],
        embedder.dimensions,
    )
    store.create_schema()

    chunks_a = [
        chunk
        for page in pages
        for chunk in fixed_size(page, size=500, overlap=50)
    ]
    print(f"Embedding Strategy A: {len(chunks_a)} chunks")
    vectors_a = embedder.embed_documents([chunk.text for chunk in chunks_a])
    store.upsert("A", chunks_a, vectors_a)
    print("Stored Strategy A")

    chunks_b = [
        chunk
        for page in pages
        for chunk in by_paragraph(page, max_size=800)
    ]
    print(f"Embedding Strategy B: {len(chunks_b)} chunks")
    vectors_b = embedder.embed_documents([chunk.text for chunk in chunks_b])
    store.upsert("B", chunks_b, vectors_b)
    print("Stored Strategy B")

    # C intentionally shares B's chunks/vectors and differs only at search time.
    store.upsert("C", chunks_b, vectors_b)
    print("Stored Strategy C")

    elapsed = round(time.perf_counter() - started, 2)
    print(f"Indexing elapsed_seconds={elapsed}")

    from scripts.run_benchmark import main as run_benchmark

    run_benchmark()


if __name__ == "__main__":
    main()
