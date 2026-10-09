import pytest

from src.evidence_answer import EvidenceBrief, EvidenceItem, verify_quotes


TEXT = (
    "Compare the configured readiness path with the application's health route."
)

SOURCES = {
    "S3": {
        "source": "checkout-readiness.md",
        "start_line": 10,
        "end_line": 15,
        "text": "## Investigation\n" + TEXT,
    }
}


def make_brief(source_id="S3", quote=TEXT):
    return EvidenceBrief(
        evidence=[EvidenceItem(source_id=source_id, quote=quote)]
    )


def test_accepts_matching_quote():
    result = verify_quotes(make_brief(), SOURCES)
    assert len(result) == 1
    assert result[0][0] == "S3"
    assert result[0][1] == TEXT


def test_accepts_whitespace_differences():
    quote = TEXT.replace("readiness path", "readiness\n  path")
    result = verify_quotes(make_brief(quote=quote), SOURCES)
    assert result[0][1] == TEXT


def test_rejects_unknown_source():
    with pytest.raises(ValueError, match="Unknown source"):
        verify_quotes(make_brief(source_id="S99"), SOURCES)


def test_rejects_fabricated_quote():
    with pytest.raises(ValueError, match="Quote does not match"):
        verify_quotes(
            make_brief(quote="The database is definitely unavailable."),
            SOURCES,
        )


def test_rejects_quote_attached_to_wrong_source():
    sources = {
        **SOURCES,
        "S5": {
            **SOURCES["S3"],
            "text": "A 503 alone does not establish this cause.",
        },
    }
    with pytest.raises(ValueError, match="Quote does not match"):
        verify_quotes(make_brief(source_id="S5"), sources)


def test_removes_duplicate_quotes():
    item = EvidenceItem(source_id="S3", quote=TEXT)
    brief = EvidenceBrief(evidence=[item, item])
    assert len(verify_quotes(brief, SOURCES)) == 1


def test_empty_selection_returns_no_evidence():
    assert verify_quotes(EvidenceBrief(evidence=[]), SOURCES) == []
