"""FastAPI transport layer for showcase snapshots and opt-in live research."""

from __future__ import annotations

import logging
import os
from typing import Callable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from demo.presentation import SCHEMA_VERSION
from demo.service import DemoPresentationService
from demo.showcase import ShowcaseScenarioCatalog, ShowcaseUnavailableError
from deployment.runtime_sec_artifacts import RuntimeSecArtifactLoader

from .config import DemoAPIConfig
from .models import (
    CapabilitiesResponse,
    HealthResponse,
    ReadinessResponse,
    ResearchRequest,
)


EVIDENCE_FAMILIES = ["quantitative", "document", "web"]
LOGGER = logging.getLogger(__name__)


def create_app(
    config: DemoAPIConfig | None = None,
    catalog: ShowcaseScenarioCatalog | None = None,
    presentation_service: DemoPresentationService | None = None,
    presentation_service_factory: Callable[[], DemoPresentationService] | None = None,
    sec_artifact_loader: RuntimeSecArtifactLoader | None = None,
) -> FastAPI:
    """Create an API app without eagerly building any live agent dependencies."""
    config = config or DemoAPIConfig.from_environment()
    catalog = catalog or ShowcaseScenarioCatalog()
    sec_artifact_loader = sec_artifact_loader or RuntimeSecArtifactLoader()
    app = FastAPI(title="Financial Research Agent Demo API", version="1.0.0")

    if config.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(config.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    cached_live_service = presentation_service

    def get_live_service() -> DemoPresentationService:
        nonlocal cached_live_service
        if not config.live_enabled:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "live_mode_disabled",
                    "message": "Live research is disabled. Use a reviewed showcase scenario instead.",
                },
            )
        if cached_live_service is not None:
            return cached_live_service

        factory = presentation_service_factory or (
            lambda: _build_live_presentation_service(sec_artifact_loader)
        )
        try:
            cached_live_service = factory()
        except Exception as error:
            LOGGER.error("Live service initialization failed: %s.", type(error).__name__)
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "live_service_unavailable",
                    "message": "Live research is currently unavailable.",
                },
            ) from error
        return cached_live_service

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz():
        return HealthResponse(status="ok")

    @app.get("/readyz", response_model=ReadinessResponse)
    async def readyz():
        artifact_status = sec_artifact_loader.status()
        return ReadinessResponse(
            live_mode_enabled=config.live_enabled,
            live_service_initialized=cached_live_service is not None,
            artifact_mode_enabled=artifact_status["artifact_mode_enabled"],
            artifact_initialized=artifact_status["artifact_initialized"],
            artifact_version=artifact_status["artifact_version"],
        )

    @app.get("/v1/capabilities", response_model=CapabilitiesResponse)
    async def capabilities():
        scenarios = catalog.list_scenarios()
        return CapabilitiesResponse(
            showcase_available=any(item.showcase_available for item in scenarios),
            live_mode_enabled=config.live_enabled,
            presentation_schema_version=SCHEMA_VERSION,
            evidence_families=EVIDENCE_FAMILIES,
            showcase_scenario_count=len(scenarios),
        )

    @app.get("/v1/showcase/scenarios")
    async def list_showcase_scenarios():
        return {"scenarios": [scenario.to_dict() for scenario in catalog.list_scenarios()]}

    @app.get("/v1/showcase/scenarios/{scenario_id}")
    async def get_showcase_scenario(scenario_id: str):
        try:
            return catalog.load_result(scenario_id).to_dict()
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Showcase scenario was not found.") from error
        except ShowcaseUnavailableError as error:
            raise HTTPException(status_code=404, detail="Showcase scenario is not available.") from error
        except ValueError as error:
            raise HTTPException(
                status_code=500,
                detail="Showcase scenario could not be loaded safely.",
            ) from error

    @app.post("/v1/research")
    async def research(request: ResearchRequest):
        prompt = request.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=422, detail="prompt must be a non-empty string.")
        if len(prompt) > config.max_prompt_length:
            raise HTTPException(
                status_code=422,
                detail="prompt exceeds the maximum supported length.",
            )

        service = get_live_service()
        try:
            return service.run(prompt).to_dict()
        except HTTPException:
            raise
        except Exception as error:
            LOGGER.error("Live research request failed: %s.", type(error).__name__)
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "live_research_failed",
                    "message": "Live research could not complete.",
                },
            ) from error

    return app


def _build_live_presentation_service(
    sec_artifact_loader: RuntimeSecArtifactLoader | None = None,
    agent_factory=None,
) -> DemoPresentationService:
    """Build configured live dependencies only after a live request is accepted."""
    from web_search import TavilyWebSearchProvider

    web_search_provider = None
    configured_provider = os.getenv("WEB_SEARCH_PROVIDER", "").strip().lower()
    if configured_provider == "tavily" and os.getenv("TAVILY_API_KEY"):
        web_search_provider = TavilyWebSearchProvider()
    elif configured_provider not in {"", "disabled", "none", "tavily"}:
        raise RuntimeError("Unsupported configured web-search provider.")

    corpus_dir = sec_artifact_loader.load() if sec_artifact_loader is not None else None
    if agent_factory is None:
        from app import build_financial_analysis_agent

        agent_factory = build_financial_analysis_agent
    LOGGER.info("Initializing live financial research agent.")
    agent = agent_factory(
        web_search_provider=web_search_provider,
        corpus_dir=corpus_dir,
    )
    return DemoPresentationService(agent, mode="live")


app = create_app()
