"""Retrieve incident passages using local sentence embeddings."""

import argparse

import numpy as np
from sentence_transformers import SentenceTransformer

from src.search import DOCUMENTS, load_chunks

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SemanticSearch:
    def __init__(self, directory=DOCUMENTS):
        self.chunks = load_chunks(directory)

        # CPU execution keeps this small baseline portable.
        # First use downloads the model; later runs reuse its cache.
        self.model = SentenceTransformer(MODEL_NAME, device="cpu")

        passages = [
            chunk["title"] + "\n" + chunk["text"]
            for chunk in self.chunks
        ]

        # Fail explicitly if future documents exceed the model limit.
        # This avoids silently truncating evidence.
        for chunk, passage in zip(self.chunks, passages):
            token_ids = self.model.tokenizer(
                passage, truncation=False
            )["input_ids"]

            if len(token_ids) > self.model.max_seq_length:
                raise ValueError(
                    f"Section too long in {chunk['source']}, "
                    f"starting at line {chunk['start_line']}. "
                    "Split it into smaller sections."
                )

        self.embeddings = self.model.encode(
            passages,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def search(self, query, top_k=3):
        query = query.strip()

        if not query:
            raise ValueError("Enter a non-empty search query.")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10.")

        tokens = self.model.tokenizer(
            query, truncation=False
        )["input_ids"]
        if len(tokens) > self.model.max_seq_length:
            raise ValueError("Query is too long. Use a shorter question.")

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        # Dot product equals cosine similarity for normalized vectors.
        scores = self.embeddings @ query_embedding
        ranked = np.argsort(-scores, kind="stable")[:top_k]

        return [
            {
                **self.chunks[int(index)],
                "score": float(scores[index]),
            }
            for index in ranked
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Incident question")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    print("Loading embedding model and indexing passages...", flush=True)

    try:
        results = SemanticSearch().search(args.query, args.top_k)
    except ValueError as error:
        parser.exit(1, f"Error: {error}\n")

    for rank, result in enumerate(results, start=1):
        citation = (
            f"{result['source']}:"
            f"L{result['start_line']}-L{result['end_line']}"
        )
        print(f"\n{rank}. {result['title']}")
        print(f"Source: {citation}")
        print(f"Cosine similarity: {result['score']:.3f}")
        print(result["text"])

    print(
        "\nThese are nearest passages, not a verified diagnosis. "
        "An unrelated question can still return results."
    )


if __name__ == "__main__":
    main()
