import asyncio
from dataclasses import replace
import json

from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.config import DemoAPIConfig
from demo.showcase import ShowcaseScenarioCatalog


class FakePresentationService:
    def __init__(self, result):
        self.result = result
        self.prompts = []

    def run(self, prompt):
        self.prompts.append(prompt)
        return self.result


def live_result():
    result = ShowcaseScenarioCatalog().load_result("concept-rsi")
    return replace(result, mode="live")


def client_for(config=None, **kwargs):
    return create_app(config=config or DemoAPIConfig(), **kwargs)


def request(app, method, path, **kwargs):
    async def send_request():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send_request())


def test_health_and_showcase_endpoints_do_not_initialize_live_service():
    calls = []

    def live_factory():
        calls.append("called")
        raise AssertionError("Live factory should not be called.")

    app = client_for(presentation_service_factory=live_factory)

    assert request(app, "GET", "/healthz").json() == {"status": "ok"}
    assert request(app, "GET", "/v1/showcase/scenarios").status_code == 200
    assert request(app, "GET", "/v1/showcase/scenarios/concept-rsi").status_code == 200
    assert calls == []


def test_capabilities_report_only_public_demo_state():
    response = request(client_for(), "GET", "/v1/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "showcase_available": True,
        "live_mode_enabled": False,
        "presentation_schema_version": "demo-presentation-v1",
        "evidence_families": ["quantitative", "document", "web"],
        "showcase_scenario_count": 6,
    }


def test_showcase_listing_and_fixture_result_use_catalog_data():
    app = client_for()

    listing = request(app, "GET", "/v1/showcase/scenarios")
    result = request(app, "GET", "/v1/showcase/scenarios/mstr-sec-custody")

    assert listing.status_code == 200
    assert listing.json()["scenarios"][0]["scenario_id"] == "concept-rsi"
    assert "fixture_name" not in listing.json()["scenarios"][0]
    assert result.status_code == 200
    assert result.json()["mode"] == "showcase"
    assert result.json()["sec_citations"][0]["source_url"].startswith("https://www.sec.gov/")


def test_unknown_showcase_scenario_returns_404():
    response = request(client_for(), "GET", "/v1/showcase/scenarios/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Showcase scenario was not found."


def test_live_endpoint_is_disabled_by_default_without_showcase_fallback():
    response = request(client_for(), "POST", "/v1/research", json={"prompt": "Analyze NVDA."})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "live_mode_disabled"


def test_live_endpoint_uses_an_injected_presentation_service():
    service = FakePresentationService(live_result())
    app = client_for(DemoAPIConfig(live_enabled=True), presentation_service=service)

    response = request(app, "POST", "/v1/research", json={"prompt": "  What is RSI?  "})

    assert response.status_code == 200
    assert response.json()["mode"] == "live"
    assert service.prompts == ["What is RSI?"]


def test_live_request_rejects_empty_oversized_and_unexpected_input():
    service = FakePresentationService(live_result())
    app = client_for(
        DemoAPIConfig(live_enabled=True, max_prompt_length=10),
        presentation_service=service,
    )

    assert request(app, "POST", "/v1/research", json={"prompt": "   "}).status_code == 422
    assert request(app, "POST", "/v1/research", json={"prompt": "x" * 11}).status_code == 422
    assert request(
        app,
        "POST",
        "/v1/research",
        json={"prompt": "RSI?", "provider": "openai"},
    ).status_code == 422
    assert service.prompts == []


def test_live_initialization_failure_is_sanitized():
    def failing_factory():
        raise RuntimeError("secret key at /private/index")

    app = client_for(
        DemoAPIConfig(live_enabled=True),
        presentation_service_factory=failing_factory,
    )

    response = request(app, "POST", "/v1/research", json={"prompt": "What is RSI?"})
    encoded = json.dumps(response.json())

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "live_service_unavailable"
    assert "secret" not in encoded
    assert "/private" not in encoded


def test_live_service_failure_is_sanitized():
    class FailingService:
        def run(self, prompt):
            raise RuntimeError("provider call id and /private/path")

    app = client_for(DemoAPIConfig(live_enabled=True), presentation_service=FailingService())

    response = request(app, "POST", "/v1/research", json={"prompt": "What is RSI?"})
    encoded = json.dumps(response.json())

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "live_research_failed"
    assert "provider call" not in encoded
    assert "/private" not in encoded


def test_showcase_responses_contain_no_sensitive_or_internal_fixture_values():
    response = request(client_for(), "GET", "/v1/showcase/scenarios/mstr-sec-and-web")
    encoded = json.dumps(response.json())

    assert response.status_code == 200
    assert "api_key" not in encoded
    assert "artifact_path" not in encoded
    assert "provider_call_id" not in encoded
    assert "file://" not in encoded


def test_cors_is_explicit_and_opt_in():
    configured = client_for(
        DemoAPIConfig(cors_origins=("http://localhost:5173",)),
    )
    preflight = request(
        configured,
        "OPTIONS",
        "/v1/research",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    default = request(
        client_for(),
        "GET",
        "/healthz",
        headers={"Origin": "http://localhost:5173"},
    )

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in default.headers
