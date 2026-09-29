"""Small request and metadata models for FastAPI validation and OpenAPI."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Minimal non-sensitive service health response."""

    status: str


class CapabilitiesResponse(BaseModel):
    """Public capability summary for a portfolio client."""

    showcase_available: bool
    live_mode_enabled: bool
    presentation_schema_version: str
    evidence_families: list[str]
    showcase_scenario_count: int


class ResearchRequest(BaseModel):
    """The single client-controlled input accepted by the live endpoint."""

    model_config = ConfigDict(extra="forbid")

    prompt: str
