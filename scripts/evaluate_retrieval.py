"""Compare retrieval methods on a small development question set."""

import hashlib
import json
import time
from pathlib import Path

from src.hybrid_search import HybridSearch, fuse_rankings
from src.semantic_search import MODEL_NAME

ROOT = Path(__file__).resolve().parents[1]


def summarize(results, expected_source):
    # Positions refer to returned passages; several may share a runbook.
    matching_ranks = [
        rank
        for rank, result in enumerate(results, start=1)
        if result["source"] == expected_source
    ]
    first_rank = matching_ranks[0] if matching_ranks else None

    return {
        "hit_at_1": int(first_rank == 1),
        "hit_at_3": int(first_rank is not None),
        "reciprocal_rank_at_3": (
            1.0 / first_rank if first_rank is not None else 0.0
        ),
        "sources": [result["source"] for result in results],
    }


def main():
    cases_path = ROOT / "data/evaluation/retrieval_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if not cases:
        raise ValueError("The evaluation set is empty.")

    print("Loading retrieval models once...", flush=True)
    engine = HybridSearch()

    known_sources = {chunk["source"] for chunk in engine.keyword.chunks}
    for case in cases:
        if case["expected_source"] not in known_sources:
            raise ValueError(
                f"Missing expected document: {case['expected_source']}"
            )

    # Warm up inference before measuring query processing.
    engine.semantic.search("warmup", top_k=1)

    measurements = {"keyword": [], "semantic": [], "hybrid": []}
    details = []

    for case in cases:
        query = case["query"]

        started = time.perf_counter()
        keyword = engine.keyword.search(query, top_k=10)
        keyword_ms = (time.perf_counter() - started) * 1000

        started = time.perf_counter()
        semantic = engine.semantic.search(query, top_k=10)
        semantic_ms = (time.perf_counter() - started) * 1000

        started = time.perf_counter()
        hybrid = fuse_rankings(
            {"keyword": keyword, "semantic": semantic},
            top_k=3,
        )
        fusion_ms = (time.perf_counter() - started) * 1000

        outputs = {
            "keyword": (keyword[:3], keyword_ms),
            "semantic": (semantic[:3], semantic_ms),
            # Hybrid executes both retrievers sequentially.
            "hybrid": (
                hybrid,
                keyword_ms + semantic_ms + fusion_ms,
            ),
        }

        case_result = {**case, "methods": {}}
        for name, (results, latency) in outputs.items():
            row = summarize(results, case["expected_source"])
            row["latency_ms"] = round(latency, 3)
            measurements[name].append(row)
            case_result["methods"][name] = row

        details.append(case_result)

    summary = {}
    for name, rows in measurements.items():
        summary[name] = {
            metric: round(
                sum(row[metric] for row in rows) / len(rows), 4
            )
            for metric in [
                "hit_at_1",
                "hit_at_3",
                "reciprocal_rank_at_3",
                "latency_ms",
            ]
        }

    document_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "data/documents").glob("*.md"))
    }

    report = {
        "scope": (
            "Development evaluation: 12 authored questions over six "
            "fictional runbooks. Checks source-document relevance, "
            "not passage sufficiency or generated-answer correctness."
        ),
        "cases": len(cases),
        "embedding_model": MODEL_NAME,
        "candidate_count_per_method": 10,
        "rrf_constant": 60,
        "cases_sha256": hashlib.sha256(
            cases_path.read_bytes()
        ).hexdigest(),
        "document_sha256": document_hashes,
        "latency_note": (
            "Single local measurements after warmup; excludes model "
            "loading and indexing. Hybrid time sums both retrieval "
            "times and fusion. Not a production latency benchmark."
        ),
        "summary": summary,
        "details": details,
    }

    output = ROOT / "reports/retrieval_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    print("\nSaved reports/retrieval_evaluation.json")


if __name__ == "__main__":
    main()
