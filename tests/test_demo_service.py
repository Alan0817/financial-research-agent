import json

import pytest

from agent.types import FinancialAnalysisResult
from demo.presentation import MAX_SEC_EXCERPT_LENGTH, MAX_WEB_SNIPPET_LENGTH
from demo.service import DemoPresentationService


class FakeAgent:
    def __init__(self, result):
        self.result = result
        self.prompts = []

    def run(self, prompt):
        self.prompts.append(prompt)
        return self.result


def result(answer="Answer", trace=None, limitations=None):
    return FinancialAnalysisResult(
        answer=answer,
        tools_used=[],
        trace=trace or [{"event": "final_response"}],
        limitations=limitations or [],
    )


def tool_events(name, arguments, payload, round_number=1):
    return [
        {
            "event": "tool_requested",
            "name": name,
            "arguments": arguments,
            "round": round_number,
        },
        {
            "event": "tool_completed",
            "name": name,
            "result": payload,
            "round": round_number,
        },
    ]


def sec_item(text="Custody risk evidence."):
    return {
        "rank": 1,
        "score": 0.8,
        "chunk_id": "chunk-mstr-1",
        "document_id": "document-mstr-10k",
        "ticker": "MSTR",
        "company": "Strategy Inc.",
        "document_type": "10-K",
        "filing_date": "2026-02-19",
        "period_end": "2025-12-31",
        "section": "PART I ITEM 1A",
        "section_title": "Risk Factors",
        "text": text,
        "source": "SEC",
        "source_url": "https://www.sec.gov/Archives/example",
    }


def web_item(snippet="Recent development."):
    return {
        "rank": 1,
        "title": "NVIDIA update",
        "url": "https://example.com/nvidia",
        "snippet": snippet,
        "source": "Example News",
        "published_at": None,
    }


def present(agent_result, mode="showcase"):
    agent = FakeAgent(agent_result)
    response = DemoPresentationService(agent, mode=mode).run("Prompt")
    assert agent.prompts == ["Prompt"]
    json.dumps(response.to_dict())
    return response.to_dict()


def test_conceptual_answer_has_no_evidence_or_tool_events():
    response = present(result(answer="RSI measures momentum."))

    assert response["schema_version"] == "demo-presentation-v1"
    assert response["mode"] == "showcase"
    assert response["answer"] == "RSI measures momentum."
    assert response["tools_used"] == []
    assert response["evidence_families"] == []
    assert response["trace"] == [{"event": "final_response"}]


def test_quantitative_result_remains_structured():
    payload = {
        "symbol": "NVDA",
        "market": {"observations": 100, "latest_ohlcv": {"Close": 123.45}},
        "technical_analysis": {"rsi": 55.2},
        "lstm_prediction": {"status": "not_applicable"},
        "risk": {"sharpe_ratio": 1.2},
        "limitations": [{"code": "model_symbol_applicability", "applicable": False}],
    }
    trace = tool_events(
        "analyze_market",
        {"symbol": "NVDA", "start_date": "2026-01-01", "end_date": "2026-06-30"},
        payload,
    ) + [{"event": "final_response"}]

    response = present(result(trace=trace))

    assert response["evidence_families"] == ["quantitative"]
    assert response["quantitative_evidence"][0]["result"]["market"]["observations"] == 100
    assert response["trace"][1]["result_summary"]["lstm_status"] == "not_applicable"


def test_sec_result_preserves_provenance_and_citation():
    payload = {"status": "ok", "result_count": 1, "results": [sec_item()]}
    trace = tool_events(
        "search_financial_documents",
        {"query": "Bitcoin custody risk", "ticker": "MSTR", "section": "Risk Factors"},
        payload,
    )

    response = present(result(trace=trace))

    evidence = response["sec_evidence"][0]
    assert response["evidence_families"] == ["document"]
    assert evidence["chunk_id"] == "chunk-mstr-1"
    assert evidence["section_title"] == "Risk Factors"
    assert evidence["source_url"] == "https://www.sec.gov/Archives/example"
    assert evidence["excerpt"] == "Custody risk evidence."
    assert response["sec_citations"][0]["document_type"] == "10-K"


def test_web_result_preserves_source_url_and_null_publication_date():
    payload = {"status": "ok", "result_count": 1, "results": [web_item()]}
    trace = tool_events("search_web", {"query": "NVIDIA latest", "max_results": 5}, payload)

    response = present(result(trace=trace))

    assert response["evidence_families"] == ["web"]
    assert response["web_evidence"][0]["url"] == "https://example.com/nvidia"
    assert response["web_evidence"][0]["published_at"] is None
    assert response["web_sources"] == [
        {
            "title": "NVIDIA update",
            "url": "https://example.com/nvidia",
            "source": "Example News",
            "published_at": None,
        }
    ]


def test_mixed_document_and_web_evidence_is_derived_from_completions():
    document_payload = {"status": "ok", "result_count": 1, "results": [sec_item()]}
    web_payload = {"status": "ok", "result_count": 1, "results": [web_item()]}
    trace = (
        tool_events("search_financial_documents", {"query": "MSTR custody"}, document_payload)
        + tool_events("search_web", {"query": "MSTR recent"}, web_payload, round_number=2)
        + [{"event": "final_response"}]
    )

    response = present(result(trace=trace))

    assert response["evidence_families"] == ["document", "web"]
    assert len(response["sec_evidence"]) == 1
    assert len(response["web_evidence"]) == 1


def test_structured_limitations_are_preserved_without_answer_parsing():
    limitations = [
        {"code": "document_retrieval_no_results", "reason": "No matching chunks."},
        {"code": "lstm_prediction_status", "status": "not_applicable"},
    ]

    response = present(result(answer="No caveats here.", limitations=limitations))

    assert response["limitations"] == limitations


def test_no_results_completion_is_visible_without_fabricated_evidence():
    payload = {
        "status": "no_results",
        "result_count": 0,
        "results": [],
        "filters": {"ticker": "TSLA"},
    }
    trace = tool_events("search_financial_documents", {"query": "TSLA filing evidence"}, payload)

    response = present(result(trace=trace))

    assert response["evidence_families"] == ["document"]
    assert response["sec_evidence"] == []
    assert response["trace"][1]["status"] == "no_results"
    assert response["trace"][1]["result_summary"]["filters"] == {"ticker": "TSLA"}


def test_sec_and_web_text_are_deterministically_clipped():
    sec_text = "s" * (MAX_SEC_EXCERPT_LENGTH + 100)
    web_text = "w" * (MAX_WEB_SNIPPET_LENGTH + 100)
    document_payload = {"status": "ok", "result_count": 1, "results": [sec_item(sec_text)]}
    web_payload = {"status": "ok", "result_count": 1, "results": [web_item(web_text)]}
    trace = tool_events("search_financial_documents", {"query": "MSTR"}, document_payload) + tool_events(
        "search_web",
        {"query": "MSTR current"},
        web_payload,
        round_number=2,
    )

    response = present(result(trace=trace))

    assert len(response["sec_evidence"][0]["excerpt"]) == MAX_SEC_EXCERPT_LENGTH
    assert response["sec_evidence"][0]["excerpt"].endswith("...")
    assert len(response["web_evidence"][0]["snippet"]) == MAX_WEB_SNIPPET_LENGTH
    assert response["web_evidence"][0]["snippet"].endswith("...")


def test_malformed_optional_events_are_safe_and_unrecognized_events_are_ignored():
    trace = [
        "not an event",
        {"event": "tool_requested", "name": "search_web", "arguments": "bad", "round": "one"},
        {"event": "tool_completed", "name": "search_web", "result": ["bad"]},
        {"event": "private_reasoning", "content": "do not expose"},
        {"event": "final_response", "provider_response": {"id": "hidden"}},
    ]

    response = present(result(trace=trace))

    assert response["trace"] == [
        {"event": "tool_requested", "round": None, "tool_name": "search_web", "arguments": {}},
        {
            "event": "tool_completed",
            "round": None,
            "tool_name": "search_web",
            "status": "unavailable",
            "result_summary": {"status": "unavailable"},
        },
        {"event": "final_response"},
    ]


def test_sensitive_and_internal_fields_are_not_projected():
    payload = {
        "status": "ok",
        "result_count": 1,
        "results": [
            {
                **sec_item(),
                "artifact_path": "/private/model.pth",
                "api_key": "secret",
                "provider_call_id": "provider-call",
            }
        ],
        "api_key": "secret",
    }
    trace = tool_events(
        "search_financial_documents",
        {
            "query": "MSTR",
            "ticker": "MSTR",
            "api_key": "secret",
            "artifact_path": "/private/model.pth",
        },
        payload,
    )
    response = present(
        result(
            trace=trace,
            limitations=[
                {
                    "code": "safe",
                    "artifact_path": "/private",
                    "reason": "Missing /private/model.pth and src/model_weight/lstm_model.pth.",
                }
            ],
        )
    )
    encoded = json.dumps(response)

    assert "secret" not in encoded
    assert "artifact_path" not in encoded
    assert "provider-call" not in encoded
    assert "/private" not in encoded
    assert "src/model_weight" not in encoded
    assert response["trace"][0]["arguments"] == {"query": "MSTR", "ticker": "MSTR"}


def test_service_rejects_missing_run_method_and_invalid_mode():
    with pytest.raises(TypeError, match="run"):
        DemoPresentationService(object())

    with pytest.raises(ValueError, match="mode"):
        present(result(), mode=" ")
