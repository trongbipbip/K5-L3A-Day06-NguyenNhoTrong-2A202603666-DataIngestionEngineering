"""Run the fixed dev/test benchmark against the three stored strategies."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.embeddings import MyEmbedder
from src.evaluation import evaluate_query, summarize
from src.store import PgVectorStore


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"))

    questions = json.loads(
        Path("benchmark/questions.json").read_text(encoding="utf-8")
    )
    if len(questions) != 20:
        raise ValueError("Benchmark must contain exactly 20 questions")

    embedder = MyEmbedder()
    store = PgVectorStore(
        os.environ["DATABASE_URL"],
        embedder.dimensions,
    )

    query_vectors = embedder.embed_documents(
        [question["question"] for question in questions]
    )

    traces: list[dict] = []

    for strategy in ["A", "B", "C"]:
        for question, query_vector in zip(questions, query_vectors):
            applied_filter = question.get("filter") if strategy == "C" else None
            hits = store.search(
                strategy,
                query_vector,
                top_k=3,
                filters=applied_filter,
            )

            trace = evaluate_query(question, hits)
            trace["strategy"] = strategy
            trace["applied_filter"] = applied_filter
            traces.append(trace)

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    with (results_dir / "benchmark_traces.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for trace in traces:
            handle.write(json.dumps(trace, ensure_ascii=False) + "\n")

    summary = summarize(traces)
    (results_dir / "benchmark_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("trace_file=results/benchmark_traces.jsonl")
    print("summary_file=results/benchmark_summary.json")


if __name__ == "__main__":
    main()
