"""JSON-safe types returned by the client-neutral demo presentation layer."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DemoPresentationResult:
    """A bounded projection of one completed financial-analysis request."""

    schema_version: str
    mode: str
    answer: str
    tools_used: list[str]
    evidence_families: list[str]
    trace: list[dict]
    quantitative_evidence: list[dict]
    sec_evidence: list[dict]
    web_evidence: list[dict]
    sec_citations: list[dict]
    web_sources: list[dict]
    limitations: list[dict]
    metadata: dict

    def to_dict(self) -> dict:
        """Return a standard JSON-compatible representation."""
        return asdict(self)
