"""Deterministic projection of agent traces into safe presentation artifacts."""

from __future__ import annotations

import re
from typing import Any

from .types import DemoPresentationResult


SCHEMA_VERSION = "demo-presentation-v1"
MAX_ANSWER_LENGTH = 12_000
MAX_ARGUMENT_TEXT_LENGTH = 500
MAX_SEC_EXCERPT_LENGTH = 1_200
MAX_WEB_SNIPPET_LENGTH = 800
MAX_LIMITATION_TEXT_LENGTH = 1_000
MAX_COLLECTION_ITEMS = 10

QUANTITATIVE_TOOLS = {
    "analyze_market",
    "get_market_data",
    "get_risk_metrics",
}

TRACE_ARGUMENT_FIELDS = {
    "analyze_market": ("symbol", "start_date", "end_date"),
    "get_market_data": ("symbol", "start_date", "end_date"),
    "get_risk_metrics": ("returns",),
    "search_financial_documents": (
        "query",
        "top_k",
        "ticker",
        "document_type",
        "section",
        "filing_date_from",
        "filing_date_to",
    ),
    "search_web": ("query", "max_results"),
}

SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "credential",
    "environment",
    "password",
    "secret",
    "token",
)

INTERNAL_KEY_PARTS = (
    "artifact_path",
    "call_id",
    "filesystem",
    "provider_request",
    "raw_response",
    "sdk",
)

LOCAL_PATH_PATTERN = re.compile(r"^(?:[A-Za-z]:[\\/]|/|file:)")
WINDOWS_PATH_PATTERN = re.compile(r"\b[A-Za-z]:[\\/][^\s]+")
UNIX_PATH_PATTERN = re.compile(
    r"(?<![:\w])/(?:home|mnt|tmp|var|private|workspace|Users)(?:/[^\s]*)?"
)
RELATIVE_PATH_PATTERN = re.compile(r"(?<![\w/])(?:src|data)/[^\s]+")


def present_financial_analysis_result(result, mode: str) -> DemoPresentationResult:
    """Build a stable public projection from one completed agent result."""
    normalized_mode = _validate_mode(mode)
    answer = _clip_text(getattr(result, "answer", ""), MAX_ANSWER_LENGTH)
    trace = getattr(result, "trace", [])
    trace_events = trace if isinstance(trace, list) else []

    presentation_trace = []
    quantitative_evidence = []
    sec_evidence = []
    web_evidence = []
    tools_used = []
    completion_count = 0

    for event in trace_events:
        if not isinstance(event, dict):
            continue
        projected_event = _present_trace_event(event)
        if projected_event is not None:
            presentation_trace.append(projected_event)

        if event.get("event") == "tool_requested":
            name = event.get("name")
            if isinstance(name, str) and name not in tools_used:
                tools_used.append(name)
            continue

        if event.get("event") != "tool_completed":
            continue

        completion_count += 1
        name = event.get("name")
        payload = event.get("result")
        if not isinstance(name, str) or not isinstance(payload, dict):
            continue

        if name in QUANTITATIVE_TOOLS:
            quantitative_evidence.append(_present_quantitative_evidence(name, payload))
        elif name == "search_financial_documents":
            sec_evidence.extend(_present_sec_evidence(payload))
        elif name == "search_web":
            web_evidence.extend(_present_web_evidence(payload))

    sec_evidence = sec_evidence[:MAX_COLLECTION_ITEMS]
    web_evidence = web_evidence[:MAX_COLLECTION_ITEMS]
    limitations = _present_limitations(getattr(result, "limitations", []))

    evidence_families = []
    if quantitative_evidence:
        evidence_families.append("quantitative")
    if sec_evidence or _completed_tool(trace_events, "search_financial_documents"):
        evidence_families.append("document")
    if web_evidence or _completed_tool(trace_events, "search_web"):
        evidence_families.append("web")

    return DemoPresentationResult(
        schema_version=SCHEMA_VERSION,
        mode=normalized_mode,
        answer=answer,
        tools_used=tools_used,
        evidence_families=evidence_families,
        trace=presentation_trace,
        quantitative_evidence=quantitative_evidence,
        sec_evidence=sec_evidence,
        web_evidence=web_evidence,
        sec_citations=_sec_citations(sec_evidence),
        web_sources=_web_sources(web_evidence),
        limitations=limitations,
        metadata={
            "trace_event_count": len(presentation_trace),
            "tool_completion_count": completion_count,
        },
    )


def _validate_mode(mode: str) -> str:
    if not isinstance(mode, str) or not mode.strip():
        raise ValueError("mode must be a non-empty string.")
    return mode.strip()


def _present_trace_event(event: dict) -> dict | None:
    event_type = event.get("event")
    if event_type == "tool_requested":
        name = event.get("name")
        if not isinstance(name, str):
            return None
        return {
            "event": "tool_requested",
            "round": _safe_round(event.get("round")),
            "tool_name": name,
            "arguments": _present_arguments(name, event.get("arguments")),
        }

    if event_type == "tool_completed":
        name = event.get("name")
        if not isinstance(name, str):
            return None
        result = event.get("result")
        return {
            "event": "tool_completed",
            "round": _safe_round(event.get("round")),
            "tool_name": name,
            "status": _completion_status(result),
            "result_summary": _present_result_summary(name, result),
        }

    if event_type == "final_response":
        return {"event": "final_response"}

    return None


def _safe_round(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _present_arguments(name: str, arguments: Any) -> dict:
    if not isinstance(arguments, dict):
        return {}

    fields = TRACE_ARGUMENT_FIELDS.get(name, ())
    projected = {}
    for field in fields:
        if field not in arguments:
            continue
        value = arguments[field]
        if field == "returns" and isinstance(value, list):
            projected["returns_count"] = len(value)
            continue
        projected[field] = _sanitize_value(value, MAX_ARGUMENT_TEXT_LENGTH)
    return projected


def _completion_status(result: Any) -> str:
    if not isinstance(result, dict):
        return "unavailable"
    status = result.get("status")
    if isinstance(status, str) and status:
        return status
    return "ok"


def _present_result_summary(name: str, result: Any) -> dict:
    if not isinstance(result, dict):
        return {"status": "unavailable"}

    status = _completion_status(result)
    if name == "search_financial_documents":
        return {
            "status": status,
            "result_count": _safe_count(result.get("result_count")),
            "filters": _present_document_filters(result.get("filters")),
        }
    if name == "search_web":
        return {
            "status": status,
            "result_count": _safe_count(result.get("result_count")),
        }
    if name == "analyze_market":
        market = result.get("market")
        lstm = result.get("lstm_prediction")
        summary = {
            "status": status,
            "symbol": _sanitize_value(result.get("symbol"), MAX_ARGUMENT_TEXT_LENGTH),
        }
        if isinstance(market, dict):
            summary["observations"] = _safe_count(market.get("observations"))
        if isinstance(lstm, dict) and isinstance(lstm.get("status"), str):
            summary["lstm_status"] = lstm["status"]
        return summary
    if name == "get_market_data":
        return {
            "status": status,
            "symbol": _sanitize_value(result.get("symbol"), MAX_ARGUMENT_TEXT_LENGTH),
            "observations": _safe_count(result.get("observations")),
        }
    if name == "get_risk_metrics":
        return {
            "status": status,
            "observations": _safe_count(result.get("observations")),
        }
    return {"status": status}


def _safe_count(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _present_document_filters(filters: Any) -> dict:
    if not isinstance(filters, dict):
        return {}
    return {
        field: _sanitize_value(filters[field], MAX_ARGUMENT_TEXT_LENGTH)
        for field in (
            "ticker",
            "document_type",
            "section",
            "filing_date_from",
            "filing_date_to",
        )
        if field in filters
    }


def _present_quantitative_evidence(name: str, result: dict) -> dict:
    if name == "analyze_market":
        fields = (
            "symbol",
            "period",
            "market",
            "technical_analysis",
            "lstm_prediction",
            "risk",
            "limitations",
        )
    elif name == "get_market_data":
        fields = (
            "symbol",
            "requested_date_range",
            "available_date_range",
            "observations",
            "latest_ohlcv",
            "recent_returns",
        )
    else:
        fields = (
            "observations",
            "annualization_factor",
            "annualized_volatility",
            "sharpe_ratio",
            "maximum_drawdown",
            "cumulative_return",
            "assumptions",
        )

    return {
        "tool_name": name,
        "result": {
            field: _sanitize_value(result[field], MAX_SEC_EXCERPT_LENGTH)
            for field in fields
            if field in result
        },
    }


def _present_sec_evidence(payload: dict) -> list[dict]:
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    evidence = []
    for item in results[:MAX_COLLECTION_ITEMS]:
        if not isinstance(item, dict):
            continue
        evidence.append(
            {
                "rank": _safe_count(item.get("rank")),
                "score": _safe_number(item.get("score")),
                "chunk_id": _sanitize_value(item.get("chunk_id"), MAX_ARGUMENT_TEXT_LENGTH),
                "document_id": _sanitize_value(item.get("document_id"), MAX_ARGUMENT_TEXT_LENGTH),
                "ticker": _sanitize_value(item.get("ticker"), MAX_ARGUMENT_TEXT_LENGTH),
                "company": _sanitize_value(item.get("company"), MAX_ARGUMENT_TEXT_LENGTH),
                "document_type": _sanitize_value(item.get("document_type"), MAX_ARGUMENT_TEXT_LENGTH),
                "filing_date": _sanitize_value(item.get("filing_date"), MAX_ARGUMENT_TEXT_LENGTH),
                "period_end": _sanitize_value(item.get("period_end"), MAX_ARGUMENT_TEXT_LENGTH),
                "section": _sanitize_value(item.get("section"), MAX_ARGUMENT_TEXT_LENGTH),
                "section_title": _sanitize_value(item.get("section_title"), MAX_ARGUMENT_TEXT_LENGTH),
                "source": _sanitize_value(item.get("source"), MAX_ARGUMENT_TEXT_LENGTH),
                "source_url": _safe_url(item.get("source_url")),
                "excerpt": _clip_text(item.get("text"), MAX_SEC_EXCERPT_LENGTH),
            }
        )
    return evidence


def _present_web_evidence(payload: dict) -> list[dict]:
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    evidence = []
    for item in results[:MAX_COLLECTION_ITEMS]:
        if not isinstance(item, dict):
            continue
        evidence.append(
            {
                "rank": _safe_count(item.get("rank")),
                "title": _clip_text(item.get("title"), MAX_ARGUMENT_TEXT_LENGTH),
                "url": _safe_url(item.get("url")),
                "snippet": _clip_text(item.get("snippet"), MAX_WEB_SNIPPET_LENGTH),
                "source": _sanitize_value(item.get("source"), MAX_ARGUMENT_TEXT_LENGTH),
                "published_at": _sanitize_value(item.get("published_at"), MAX_ARGUMENT_TEXT_LENGTH),
            }
        )
    return evidence


def _safe_number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _safe_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if candidate.startswith("https://") or candidate.startswith("http://"):
        return _clip_url(candidate, MAX_ARGUMENT_TEXT_LENGTH)
    return None


def _sec_citations(evidence: list[dict]) -> list[dict]:
    citations = []
    seen = set()
    for item in evidence:
        identity = (item.get("chunk_id"), item.get("source_url"))
        if identity in seen:
            continue
        seen.add(identity)
        citations.append(
            {
                field: item.get(field)
                for field in (
                    "chunk_id",
                    "document_id",
                    "ticker",
                    "company",
                    "document_type",
                    "filing_date",
                    "section",
                    "section_title",
                    "source",
                    "source_url",
                )
            }
        )
    return citations


def _web_sources(evidence: list[dict]) -> list[dict]:
    sources = []
    seen = set()
    for item in evidence:
        url = item.get("url")
        if not isinstance(url, str) or url in seen:
            continue
        seen.add(url)
        sources.append(
            {
                field: item.get(field)
                for field in ("title", "url", "source", "published_at")
            }
        )
    return sources


def _present_limitations(limitations: Any) -> list[dict]:
    if not isinstance(limitations, list):
        return []
    return [
        _sanitize_value(item, MAX_LIMITATION_TEXT_LENGTH)
        for item in limitations
        if isinstance(item, dict)
    ]


def _completed_tool(trace: list[Any], tool_name: str) -> bool:
    return any(
        isinstance(event, dict)
        and event.get("event") == "tool_completed"
        and event.get("name") == tool_name
        for event in trace
    )


def _sanitize_value(value: Any, text_limit: int, depth: int = 0):
    if depth > 8:
        return "[truncated]"
    if isinstance(value, str):
        if LOCAL_PATH_PATTERN.match(value.strip()):
            return "[redacted]"
        return _clip_text(value, text_limit)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return [
            _sanitize_value(item, text_limit, depth + 1)
            for item in value[:MAX_COLLECTION_ITEMS]
        ]
    if isinstance(value, dict):
        return {
            str(key): _sanitize_value(item, text_limit, depth + 1)
            for key, item in value.items()
            if _is_safe_key(key)
        }
    return None


def _is_safe_key(key: Any) -> bool:
    normalized = str(key).lower()
    return not any(part in normalized for part in SENSITIVE_KEY_PARTS + INTERNAL_KEY_PARTS)


def _clip_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    value = _redact_local_paths(value)
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + "..."


def _clip_url(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + "..."


def _redact_local_paths(value: str) -> str:
    value = WINDOWS_PATH_PATTERN.sub("[redacted]", value)
    value = UNIX_PATH_PATTERN.sub("[redacted]", value)
    return RELATIVE_PATH_PATTERN.sub("[redacted]", value)
