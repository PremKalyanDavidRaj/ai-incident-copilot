# AI Incident Copilot

A local AI application that finds investigation guidance in fictional
incident runbooks and verifies model-selected quotations against source text.

Built with Python, FastAPI, Sentence Transformers, BM25, and Ollama.

## Demo workflow

1. Describe an incident in the browser.
2. Check semantic similarity against the runbook collection.
3. Combine keyword and semantic retrieval using reciprocal rank fusion.
4. Select the highest-ranked runbook.
5. Ask a local model to extract investigation and interpretation quotes.
6. Validate the response schema, source IDs, and quoted text.
7. Display verified quotes with source filenames and line references.

The application does not execute operational actions or confirm root causes.

## Features

- Six fictional incident runbooks.
- BM25 keyword search and embedding-based semantic search.
- Hybrid retrieval with reciprocal rank fusion.
- Local generation using Qwen2.5 1.5B through Ollama.
- Structured JSON output with Pydantic validation.
- Quote verification that ignores whitespace differences.
- Provisional relevance gate before generation.
- FastAPI endpoints and a browser interface.
- Automated quote-validation and API tests.

## Requirements

- Python 3.13, used during local development.
- Ollama with the `qwen2.5:1.5b` model.
- Internet access for initial dependency and model downloads.

The browser workflow was exercised locally on an Apple M3 MacBook Air
with 8 GB RAM. This is not a performance benchmark.

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/create_sample_docs.py
ollama pull qwen2.5:1.5b
```

The embedding model downloads on first use.

Start Ollama in one terminal if it is not already running:

```bash
ollama serve
```

Start the API in another terminal:

```bash
source .venv/bin/activate
python -m uvicorn src.api:app --host 127.0.0.1 --port 8004
```

Keep both services running.

- Browser interface: http://127.0.0.1:8004/demo
- API documentation: http://127.0.0.1:8004/docs
- Health endpoint: http://127.0.0.1:8004/health

The health endpoint checks retrieval readiness, not Ollama availability.

## Example request

```bash
curl -sS http://127.0.0.1:8004/investigate \
  -H "Content-Type: application/json" \
  -d '{"question":"Checkout returns 503 after deployment and readiness returns 404. What should I investigate?"}'
```

Successful evidence responses include quotes, source IDs, filenames,
and line ranges. Low-similarity requests return no evidence without
calling the generation model.

## Tests

```bash
python -m pytest tests/test_evidence.py tests/test_api.py -q
```

Observed local result: 18 passed.

Tests cover quote matching, fabricated quotes, unknown or mismatched
sources, duplicate removal, request validation, and API error handling.

API tests use a fake service. They do not evaluate live model quality.

## Development observations

The browser and API were exercised with a checkout-readiness incident.
The service returned source-verified investigation guidance.

An unrelated cake-baking question was rejected before generation.

A provisional semantic-similarity threshold of 0.23 was chosen using
six relevant and six unrelated development questions:

- Relevant examples: approximately 0.374–0.822.
- Unrelated examples: approximately 0.041–0.091.

These examples were used to select the threshold, not as an independent
test set. Similarity is not a relevance probability.

## Limitations

- All runbooks and incident examples are fictional.
- Exact quote matching does not prove relevance, completeness, or applicability.
- The small local model can select incomplete or unhelpful evidence.
- Only the highest-ranked runbook is used for evidence extraction.
- Extraction is restricted to Investigation and Interpretation sections.
- The relevance threshold needs broader evaluation, including unsupported
  technical incidents and ambiguous questions.
- Requests are serialized within one service process to limit memory pressure.
- Authentication, bounded request queues, and production load testing
  are not implemented. The demo binds to localhost.
- No production incident outcomes or root-cause accuracy have been measured.

## Earlier generation experiment

`src/answer.py` contains an experimental free-text answer path.
During development it produced unsupported claims, missing citations,
and unnecessary abstentions.

The browser/API uses the structured evidence service instead.
That service verifies quoted text but still requires human review.

## Project layout

- `src/search.py`: keyword retrieval and document chunking.
- `src/semantic_search.py`: embedding-based retrieval.
- `src/hybrid_search.py`: rank fusion.
- `src/evidence_answer.py`: extraction CLI and quote validation.
- `src/service.py`: reusable evidence workflow.
- `src/api.py`: HTTP endpoints.
- `static/index.html`: browser interface.
- `data/documents/`: fictional runbooks.
- `tests/`: automated validation and API tests.
