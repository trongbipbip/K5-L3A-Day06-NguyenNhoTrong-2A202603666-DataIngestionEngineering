import os
from typing import Protocol

from dotenv import load_dotenv
from openai import OpenAI


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with document vectors."""
        ...


class MyEmbedder:
    """OpenAI embedding implementation without mock fallback."""

    def __init__(
        self,
        model_name: str | None = None,
        batch_size: int = 64,
    ) -> None:
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")

        self.model_name = (
            model_name
            or os.getenv("EMBEDDING_MODEL")
            or "text-embedding-3-small"
        )
        self.dimensions = 1536
        self.batch_size = batch_size
        self.client = OpenAI(api_key=api_key)

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError("Embedding input cannot contain empty text")

        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts,
            encoding_format="float",
        )

        items = sorted(response.data, key=lambda item: item.index)
        vectors = [item.embedding for item in items]

        if len(vectors) != len(texts):
            raise RuntimeError("Embedding response length does not match input")

        if any(len(vector) != self.dimensions for vector in vectors):
            raise RuntimeError(
                f"Expected {self.dimensions}-dimensional vectors"
            )

        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []

        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start + self.batch_size]
            vectors.extend(self._embed_batch(batch))

        return vectors

    def embed_query(self, question: str) -> list[float]:
        vectors = self._embed_batch([question])
        return vectors[0]
