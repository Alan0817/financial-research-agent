"""Source-controlled loading and validation of showcase presentation snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .presentation import (
    INTERNAL_KEY_PARTS,
    LOCAL_PATH_PATTERN,
    MAX_ANSWER_LENGTH,
    MAX_ARGUMENT_TEXT_LENGTH,
    MAX_COLLECTION_ITEMS,
    MAX_LIMITATION_TEXT_LENGTH,
    MAX_SEC_EXCERPT_LENGTH,
    MAX_WEB_SNIPPET_LENGTH,
    SCHEMA_VERSION,
    SENSITIVE_KEY_PARTS,
)
from .scenarios import SHOWCASE_SCENARIOS, ShowcaseScenario
from .types import DemoPresentationResult


REQUIRED_PRESENTATION_FIELDS = {
    "schema_version",
    "mode",
    "answer",
    "tools_used",
    "evidence_families",
    "trace",
    "quantitative_evidence",
    "sec_evidence",
    "web_evidence",
    "sec_citations",
    "web_sources",
    "limitations",
    "metadata",
}


class ShowcaseUnavailableError(RuntimeError):
    """Raised when metadata exists but no reviewed fixture is available."""


class ShowcaseScenarioCatalog:
    """Load reviewed showcase snapshots without invoking an agent or provider."""

    def __init__(self, fixture_directory: Path | str | None = None, scenarios=SHOWCASE_SCENARIOS):
        self._fixture_directory = (
            Path(fixture_directory)
            if fixture_directory is not None
            else Path(__file__).resolve().parent / "fixtures"
        )
        self._scenarios = {scenario.scenario_id: scenario for scenario in scenarios}
        if len(self._scenarios) != len(scenarios):
            raise ValueError("Showcase scenario IDs must be unique.")

    def list_scenarios(self) -> list[ShowcaseScenario]:
        """Return the stable presentation order for showcase scenario cards."""
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> ShowcaseScenario:
        """Return metadata for one known showcase scenario."""
        if not isinstance(scenario_id, str) or not scenario_id:
            raise KeyError("Showcase scenario ID must be a non-empty string.")
        try:
            return self._scenarios[scenario_id]
        except KeyError as error:
            raise KeyError("Unknown showcase scenario: {!r}.".format(scenario_id)) from error

    def load_result(self, scenario_id: str) -> DemoPresentationResult:
        """Load one reviewed snapshot using the normal public presentation schema."""
        scenario = self.get_scenario(scenario_id)
        if not scenario.showcase_available or not scenario.fixture_name:
            raise ShowcaseUnavailableError(
                "Showcase scenario {!r} has no reviewed fixture.".format(scenario_id)
            )

        fixture_path = self._fixture_directory / scenario.fixture_name
        try:
            payload = json.loads(fixture_path.read_text())
        except FileNotFoundError as error:
            raise ShowcaseUnavailableError(
                "Showcase fixture for {!r} is unavailable.".format(scenario_id)
            ) from error
        except json.JSONDecodeError as error:
            raise ValueError(
                "Showcase fixture for {!r} contains invalid JSON.".format(scenario_id)
            ) from error

        validate_showcase_fixture(payload, scenario)
        return DemoPresentationResult(**payload)


def validate_showcase_fixture(payload: Any, scenario: ShowcaseScenario) -> None:
    """Reject malformed, unsafe, or inconsistent public showcase snapshots."""
    if not isinstance(payload, dict):
        raise ValueError("Showcase fixture must contain a JSON object.")

    missing = sorted(REQUIRED_PRESENTATION_FIELDS.difference(payload))
    if missing:
        raise ValueError("Showcase fixture is missing required fields: {}.".format(", ".join(missing)))
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Showcase fixture has an unsupported schema version.")
    if payload["mode"] != "showcase":
        raise ValueError("Showcase fixture mode must be 'showcase'.")

    _validate_string(payload["answer"], "answer", MAX_ANSWER_LENGTH)
    _validate_string_list(payload["tools_used"], "tools_used")
    _validate_string_list(payload["evidence_families"], "evidence_families")
    _validate_list(payload["trace"], "trace")
    _validate_list(payload["quantitative_evidence"], "quantitative_evidence")
    _validate_list(payload["sec_evidence"], "sec_evidence")
    _validate_list(payload["web_evidence"], "web_evidence")
    _validate_list(payload["sec_citations"], "sec_citations")
    _validate_list(payload["web_sources"], "web_sources")
    _validate_list(payload["limitations"], "limitations")
    if not isinstance(payload["metadata"], dict):
        raise ValueError("Showcase fixture metadata must be an object.")
    _validate_capture_metadata(payload["metadata"])

    expected_families = list(scenario.expected_evidence_families)
    if payload["evidence_families"] != expected_families:
        raise ValueError("Showcase fixture evidence families do not match scenario metadata.")

    _validate_evidence_presence(payload)

    _validate_collection_size(payload)
    _validate_urls(payload["sec_evidence"], "source_url")
    _validate_urls(payload["sec_citations"], "source_url")
    _validate_urls(payload["web_evidence"], "url")
    _validate_urls(payload["web_sources"], "url")
    _validate_text_bounds(payload)
    _validate_safe_values(payload)


def _validate_list(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise ValueError("Showcase fixture field {!r} must be a list.".format(field))


def _validate_string(value: Any, field: str, limit: int) -> None:
    if not isinstance(value, str):
        raise ValueError("Showcase fixture field {!r} must be a string.".format(field))
    if len(value) > limit:
        raise ValueError("Showcase fixture field {!r} exceeds its text limit.".format(field))


def _validate_string_list(value: Any, field: str) -> None:
    _validate_list(value, field)
    if not all(isinstance(item, str) for item in value):
        raise ValueError("Showcase fixture field {!r} must contain strings.".format(field))


def _validate_collection_size(payload: dict) -> None:
    for field in ("quantitative_evidence", "sec_evidence", "web_evidence"):
        if len(payload[field]) > MAX_COLLECTION_ITEMS:
            raise ValueError("Showcase fixture field {!r} exceeds the item limit.".format(field))


def _validate_capture_metadata(metadata: dict) -> None:
    for field in ("captured_at", "capture_source", "snapshot_notice"):
        value = metadata.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Showcase fixture metadata requires {!r}.".format(field))
    if "not live" not in metadata["snapshot_notice"].lower():
        raise ValueError("Showcase fixture snapshot notice must state that it is not live.")


def _validate_evidence_presence(payload: dict) -> None:
    evidence = set(payload["evidence_families"])
    if "quantitative" in evidence and not payload["quantitative_evidence"]:
        raise ValueError("Quantitative showcase fixtures must contain quantitative evidence.")
    if "document" in evidence and not payload["sec_evidence"]:
        raise ValueError("Document showcase fixtures must contain SEC evidence.")
    if "web" in evidence and not payload["web_evidence"]:
        raise ValueError("Web showcase fixtures must contain web evidence.")


def _validate_urls(items: list, field: str) -> None:
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Showcase evidence items must be objects.")
        value = item.get(field)
        if value is not None and (
            not isinstance(value, str)
            or not (value.startswith("https://") or value.startswith("http://"))
        ):
            raise ValueError("Showcase fixture contains an unsafe URL.")


def _validate_text_bounds(payload: dict) -> None:
    for event in payload["trace"]:
        if not isinstance(event, dict):
            raise ValueError("Showcase trace events must be objects.")
        _validate_bounded_strings(event, MAX_ARGUMENT_TEXT_LENGTH)
    for item in payload["sec_evidence"]:
        _validate_string(item.get("excerpt"), "SEC evidence excerpt", MAX_SEC_EXCERPT_LENGTH)
    for item in payload["web_evidence"]:
        _validate_string(item.get("title"), "web evidence title", MAX_ARGUMENT_TEXT_LENGTH)
        _validate_string(item.get("snippet"), "web evidence snippet", MAX_WEB_SNIPPET_LENGTH)
    for limitation in payload["limitations"]:
        if not isinstance(limitation, dict):
            raise ValueError("Showcase limitations must be objects.")
        _validate_bounded_strings(limitation, MAX_LIMITATION_TEXT_LENGTH)


def _validate_bounded_strings(value: Any, limit: int) -> None:
    if isinstance(value, str):
        if len(value) > limit:
            raise ValueError("Showcase fixture contains text exceeding its limit.")
        return
    if isinstance(value, list):
        for item in value:
            _validate_bounded_strings(item, limit)
        return
    if isinstance(value, dict):
        for item in value.values():
            _validate_bounded_strings(item, limit)


def _validate_safe_values(value: Any) -> None:
    if isinstance(value, str):
        if LOCAL_PATH_PATTERN.match(value.strip()):
            raise ValueError("Showcase fixture contains a local filesystem path.")
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_values(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            if any(part in normalized for part in SENSITIVE_KEY_PARTS + INTERNAL_KEY_PARTS):
                raise ValueError("Showcase fixture contains a sensitive or internal field.")
            _validate_safe_values(item)
