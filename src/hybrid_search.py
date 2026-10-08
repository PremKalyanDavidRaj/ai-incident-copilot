"""Combine BM25 and semantic retrieval using reciprocal rank fusion."""

import argparse

from src.search import DOCUMENTS, KeywordSearch
from src.semantic_search import SemanticSearch


def passage_key(result):
    return (
        result["source"],
        result["start_line"],
        result["end_line"],
    )


def fuse_rankings(rankings, top_k=3, rank_constant=60):
    """Each retrieval method contributes 1 / (constant + rank)."""
    combined = {}

    for method, results in rankings.items():
        seen = set()

        for rank, result in enumerate(results, start=1):
            key = passage_key(result)

            # Count each passage at most once per retrieval method.
            if key in seen:
                continue
            seen.add(key)

            if key not in combined:
                combined[key] = {
                    "source": result["source"],
                    "title": result["title"],
                    "start_line": result["start_line"],
                    "end_line": result["end_line"],
                    "text": result["text"],
                    "rrf_score": 0.0,
                    "ranks": {},
                }

            combined[key]["rrf_score"] += 1.0 / (
                rank_constant + rank
            )
            combined[key]["ranks"][method] = rank

    return sorted(
        combined.values(),
        key=lambda item: (-item["rrf_score"], passage_key(item)),
    )[:top_k]


class HybridSearch:
    def __init__(self, directory=DOCUMENTS):
        self.keyword = KeywordSearch(directory)
        self.semantic = SemanticSearch(directory)

        # Both methods must operate on exactly the same source passages.
        if self.keyword.chunks != self.semantic.chunks:
            raise ValueError(
                "Documents changed while loading. Restart the search."
            )

    def search(self, query, top_k=3):
        if not query.strip():
            raise ValueError("Enter a non-empty search query.")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10.")

        # Retrieve more candidates than we ultimately display.
        rankings = {
            "keyword": self.keyword.search(query, top_k=10),
            "semantic": self.semantic.search(query, top_k=10),
        }

        return fuse_rankings(rankings, top_k=top_k)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Incident question")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    print("Loading hybrid search...", flush=True)

    try:
        results = HybridSearch().search(args.query, args.top_k)
    except ValueError as error:
        parser.exit(1, f"Error: {error}\n")

    for rank, result in enumerate(results, start=1):
        citation = (
            f"{result['source']}:"
            f"L{result['start_line']}-L{result['end_line']}"
        )
        print(f"\n{rank}. {result['title']}")
        print(f"Source: {citation}")
        print(f"RRF score: {result['rrf_score']:.5f}")
        print(f"Retrieval ranks: {result['ranks']}")
        print(result["text"])

    print(
        "\nRetrieved evidence only. RRF scores are not confidence "
        "probabilities, and unrelated queries can still return results."
    )


if __name__ == "__main__":
    main()
