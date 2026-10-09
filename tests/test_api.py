import httpx
import pytest
from fastapi.testclient import TestClient

from src import api


class FakeService:
    def __init__(self):
        self.error = None
        self.questions = []

    def investigate(self, question):
        self.questions.append(question)
        if self.error is not None:
            raise self.error

        return {
            "status": "evidence_found",
            "semantic_similarity": 0.8,
            "relevance_threshold": 0.23,
            "selected_source": "example.md",
            "evidence": [{
                "source_id": "S1",
                "quote": "Compare the configured readiness path.",
                "source": "example.md",
                "start_line": 1,
                "end_line": 3,
            }],
            "generation_called": True,
            "note": "Synthetic test fixture.",
        }


@pytest.fixture
def client_and_service(monkeypatch):
    service = FakeService()
    monkeypatch.setattr(api, "EvidenceService", lambda: service)
    with TestClient(api.app) as client:
        yield client, service


def test_root_redirects_to_docs(client_and_service):
    client, _ = client_and_service
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_health(client_and_service):
    client, _ = client_and_service
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["retrieval_loaded"] is True


def test_investigation_response(client_and_service):
    client, service = client_and_service
    response = client.post(
        "/investigate",
        json={"question": "  Why is checkout returning 503?  "},
    )
    assert response.status_code == 200
    assert service.questions == ["Why is checkout returning 503?"]
    body = response.json()
    assert body["status"] == "evidence_found"
    assert body["evidence"][0]["source"] == "example.md"


@pytest.mark.parametrize("payload", [
    {},
    {"question": ""},
    {"question": "   "},
    {"question": "x" * 1001},
    {"question": "Check readiness", "unexpected": True},
])
def test_invalid_input_never_calls_service(client_and_service, payload):
    client, service = client_and_service
    response = client.post("/investigate", json=payload)
    assert response.status_code == 422
    assert service.questions == []


@pytest.mark.parametrize("error,status", [
    (httpx.ConnectError("connection refused"), 503),
    (httpx.ReadTimeout("timed out"), 504),
    (ValueError("invalid model quote"), 502),
])
def test_service_failure_withholds_evidence(
    client_and_service, error, status
):
    client, service = client_and_service
    service.error = error

    response = client.post(
        "/investigate",
        json={"question": "Check readiness failures"},
    )
    assert response.status_code == status
    assert "detail" in response.json()
    assert "evidence" not in response.json()
