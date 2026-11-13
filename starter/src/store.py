import json
from typing import Any

import psycopg

from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")

        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        strategy TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self.dimensions}) NOT NULL,
                        PRIMARY KEY (strategy, chunk_id)
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_document_chunks_strategy
                    ON document_chunks(strategy)
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata
                    ON document_chunks USING GIN(metadata)
                    """
                )

            connection.commit()

    def upsert(
        self,
        strategy: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")

        for vector in vectors:
            if len(vector) != self.dimensions:
                raise ValueError(
                    f"Expected vector dimension {self.dimensions}, "
                    f"got {len(vector)}"
                )

        if not chunks:
            return

        document_ids = {chunk.document_id for chunk in chunks}

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                for document_id in document_ids:
                    chunk_ids = [
                        chunk.chunk_id
                        for chunk in chunks
                        if chunk.document_id == document_id
                    ]

                    cursor.execute(
                        """
                        DELETE FROM document_chunks
                        WHERE strategy = %s
                          AND document_id = %s
                          AND NOT (chunk_id = ANY(%s))
                        """,
                        (strategy, document_id, chunk_ids),
                    )

                rows = []

                for chunk, vector in zip(chunks, vectors):
                    rows.append(
                        (
                            strategy,
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.source,
                            chunk.page,
                            chunk.text,
                            json.dumps(chunk.metadata),
                            json.dumps(vector),
                        )
                    )

                cursor.executemany(
                    """
                    INSERT INTO document_chunks (
                        strategy,
                        chunk_id,
                        document_id,
                        source,
                        page,
                        text,
                        metadata,
                        embedding
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s::jsonb,
                        %s::vector
                    )
                    ON CONFLICT (strategy, chunk_id)
                    DO UPDATE SET
                        document_id = EXCLUDED.document_id,
                        source = EXCLUDED.source,
                        page = EXCLUDED.page,
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    rows,
                )

            connection.commit()

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(query_vector) != self.dimensions:
            raise ValueError(
                f"Expected query dimension {self.dimensions}, "
                f"got {len(query_vector)}"
            )

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        allowed_filters = {
            "chapter",
            "category",
            "language",
            "section",
            "year",
            "document_type",
        }

        filters = filters or {}

        unknown_filters = set(filters) - allowed_filters
        if unknown_filters:
            raise ValueError(
                f"Unsupported metadata filters: {sorted(unknown_filters)}"
            )

        where_conditions = ["strategy = %s"]
        parameters: list[Any] = [strategy]

        for key, value in filters.items():
            where_conditions.append("metadata ->> %s = %s")
            parameters.extend([key, str(value)])

        where_sql = " AND ".join(where_conditions)
        vector_text = json.dumps(query_vector)

        sql = f"""
            SELECT
                chunk_id,
                document_id,
                source,
                page,
                text,
                metadata,
                1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        query_parameters = [vector_text, *parameters, vector_text, top_k]

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, query_parameters)
                rows = cursor.fetchall()

        return [
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "source": row[2],
                "page": row[3],
                "text": row[4],
                "metadata": row[5],
                "score": float(row[6]),
            }
            for row in rows
        ]
