"""Local API for verified incident evidence."""

from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from src.service import EvidenceService


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    question: str = Field(min_length=1, max_length=1000)


class EvidenceResponse(BaseModel):
    source_id: str
    quote: str
    source: str
    start_line: int
    end_line: int


class InvestigationResponse(BaseModel):
    status: Literal[
        "no_relevant_evidence",
        "no_guidance_sections",
        "no_evidence_selected",
        "evidence_found",
    ]
    semantic_similarity: float
    relevance_threshold: float
    selected_source: str | None
    evidence: list[EvidenceResponse]
    generation_called: bool
    note: str


class HealthResponse(BaseModel):
    status: str
    retrieval_loaded: bool
    generation_dependency: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.service = EvidenceService()
    try:
        yield
    finally:
        app.state.service = None


app = FastAPI(
    title="AI Incident Copilot",
    version="0.1.0",
    description=(
        "Retrieves fictional runbook guidance and verifies model-selected "
        "quotes. Does not confirm root causes or execute operational actions."
    ),
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", response_model=HealthResponse)
def health(request: Request):
    loaded = getattr(request.app.state, "service", None) is not None
    if not loaded:
        raise HTTPException(503, "Retrieval service is not ready.")
    return {
        "status": "ok",
        "retrieval_loaded": True,
        "generation_dependency": "Ollama availability is not checked here.",
    }


@app.post("/investigate", response_model=InvestigationResponse)
def investigate(body: InvestigationRequest, request: Request):
    service = getattr(request.app.state, "service", None)
    if service is None:
        raise HTTPException(503, "Retrieval service is not ready.")

    try:
        return service.investigate(body.question)
    except httpx.TimeoutException as error:
        raise HTTPException(
            504, "Local generation timed out. Please retry."
        ) from error
    except httpx.ConnectError as error:
        raise HTTPException(
            503, "Cannot reach Ollama. Start ollama serve."
        ) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            502, "The local generation service failed."
        ) from error
    except ValueError as error:
        raise HTTPException(
            502, "Model output failed validation. Evidence withheld."
        ) from error
