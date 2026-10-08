"""Search fictional incident runbooks using BM25 keyword retrieval."""

import argparse
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ROOT / "data" / "documents"

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "why", "what", "how", "my", "our", "it", "its",
    "to", "of", "and", "or", "in", "on", "for",
}


def tokenize(text):
    # Keep error codes and identifiers such as POOL_ACQUIRE_TIMEOUT.
    words = re.findall(r"[a-z0-9_]+", text.casefold())
    return [word for word in words if word not in STOPWORDS]


def load_chunks(directory=DOCUMENTS):
    """Split Markdown at section headings, retaining source line numbers."""
    chunks = []

    for path in sorted(directory.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines:
            continue

        title = lines[0].lstrip("# ").strip()
        boundaries = [0] + [
            index
            for index, line in enumerate(lines)
            if index > 0 and line.startswith("## ")
        ] + [len(lines)]

        for start, end in zip(boundaries, boundaries[1:]):
            text = "\n".join(lines[start:end]).strip()
            if not text:
                continue

            chunks.append({
                "source": path.name,
                "title": title,
                "start_line": start + 1,
                "end_line": end,
                "text": text,
            })

    if not chunks:
        raise ValueError(
            "No documents found. Run: python scripts/create_sample_docs.py"
        )

    return chunks


class KeywordSearch:
    def __init__(self, directory=DOCUMENTS):
        self.chunks = load_chunks(directory)

        # Include the document title so sections retain service context.
        self.tokens = [
            tokenize(chunk["title"] + "\n" + chunk["text"])
            for chunk in self.chunks
        ]
        self.index = BM25Okapi(self.tokens)

    def search(self, query, top_k=3):
        if not query.strip():
            raise ValueError("Enter a non-empty search query.")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10.")

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self.index.get_scores(query_tokens)
        ranked = sorted(
            range(len(self.chunks)),
            key=lambda index: (-float(scores[index]), index),
        )

        results = []
        for index in ranked:
            if scores[index] <= 0:
                continue

            results.append({
                **self.chunks[index],
                "score": float(scores[index]),
            })
            if len(results) == top_k:
                break

        return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Incident question or error code")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    try:
        results = KeywordSearch().search(args.query, args.top_k)
    except ValueError as error:
        parser.exit(1, f"Error: {error}\n")

    if not results:
        print("No keyword matches found.")
        return

    for rank, result in enumerate(results, start=1):
        citation = (
            f"{result['source']}:"
            f"L{result['start_line']}-L{result['end_line']}"
        )
        print(f"\n{rank}. {result['title']}")
        print(f"Source: {citation}")
        print(f"BM25 score: {result['score']:.3f}")
        print(result["text"])

    print("\nRetrieved evidence only; no AI-generated diagnosis yet.")


if __name__ == "__main__":
    main()
