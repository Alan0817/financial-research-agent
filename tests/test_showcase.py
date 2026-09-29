import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from demo.scenarios import SHOWCASE_SCENARIOS
from demo.showcase import (
    ShowcaseScenarioCatalog,
    ShowcaseUnavailableError,
    validate_showcase_fixture,
)


def fixture_payload(scenario_id="concept-rsi"):
    return ShowcaseScenarioCatalog().load_result(scenario_id).to_dict()


def scenario(scenario_id="concept-rsi"):
    return ShowcaseScenarioCatalog().get_scenario(scenario_id)


def test_catalog_lists_the_six_stable_scenario_cards():
    catalog = ShowcaseScenarioCatalog()

    assert [item.scenario_id for item in catalog.list_scenarios()] == [
        "concept-rsi",
        "nvda-quantitative",
        "mstr-sec-custody",
        "nvidia-current-developments",
        "mstr-sec-and-web",
        "btc-market-analysis",
    ]
    assert "fixture_name" not in catalog.get_scenario("mstr-sec-custody").to_dict()


def test_catalog_loads_valid_fixtures_with_public_schema():
    catalog = ShowcaseScenarioCatalog()

    result = catalog.load_result("mstr-sec-and-web")

    assert result.mode == "showcase"
    assert result.evidence_families == ["document", "web"]
    assert result.sec_citations[0]["source_url"].startswith("https://www.sec.gov/")
    assert result.web_sources[0]["url"].startswith("https://")
    assert "captured_at" in result.metadata
    assert "not live" in result.metadata["snapshot_notice"].lower()
    assert json.dumps(result.to_dict(), sort_keys=True) == json.dumps(result.to_dict(), sort_keys=True)


def test_catalog_rejects_unknown_scenario_id():
    with pytest.raises(KeyError, match="Unknown showcase scenario"):
        ShowcaseScenarioCatalog().get_scenario("missing")


def test_catalog_reports_pending_scenario_without_loading_a_fixture():
    pending = replace(
        scenario(),
        scenario_id="pending",
        showcase_available=False,
        captured_at=None,
        fixture_name=None,
    )
    catalog = ShowcaseScenarioCatalog(scenarios=(pending,))

    with pytest.raises(ShowcaseUnavailableError, match="no reviewed fixture"):
        catalog.load_result("pending")


def test_catalog_rejects_malformed_fixture_json(tmp_path):
    fixture_path = tmp_path / "concept-rsi.json"
    fixture_path.write_text("not json")
    catalog = ShowcaseScenarioCatalog(fixture_directory=tmp_path, scenarios=(scenario(),))

    with pytest.raises(ValueError, match="invalid JSON"):
        catalog.load_result("concept-rsi")


def test_fixture_schema_version_and_evidence_family_must_match_metadata():
    payload = fixture_payload()
    invalid_version = copy.deepcopy(payload)
    invalid_version["schema_version"] = "unknown"

    with pytest.raises(ValueError, match="schema version"):
        validate_showcase_fixture(invalid_version, scenario())

    invalid_evidence = copy.deepcopy(payload)
    invalid_evidence["evidence_families"] = ["web"]

    with pytest.raises(ValueError, match="evidence families"):
        validate_showcase_fixture(invalid_evidence, scenario())

    missing_capture_metadata = copy.deepcopy(payload)
    missing_capture_metadata["metadata"].pop("captured_at")

    with pytest.raises(ValueError, match="captured_at"):
        validate_showcase_fixture(missing_capture_metadata, scenario())


def test_fixture_rejects_unsafe_urls_and_missing_evidence():
    payload = fixture_payload("mstr-sec-custody")
    unsafe_url = copy.deepcopy(payload)
    unsafe_url["sec_evidence"][0]["source_url"] = "file:///private/filing.html"

    with pytest.raises(ValueError, match="unsafe URL"):
        validate_showcase_fixture(unsafe_url, scenario("mstr-sec-custody"))

    missing_evidence = copy.deepcopy(payload)
    missing_evidence["sec_evidence"] = []

    with pytest.raises(ValueError, match="must contain SEC evidence"):
        validate_showcase_fixture(missing_evidence, scenario("mstr-sec-custody"))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("api_key", "secret", "sensitive or internal"),
        ("reason", "/private/model.pth", "local filesystem path"),
    ],
)
def test_fixture_rejects_sensitive_fields_and_local_paths(field, value, message):
    payload = fixture_payload()
    payload["metadata"][field] = value

    with pytest.raises(ValueError, match=message):
        validate_showcase_fixture(payload, scenario())


def test_fixture_rejects_text_exceeding_phase_five_bounds():
    payload = fixture_payload("nvidia-current-developments")
    payload["web_evidence"][0]["snippet"] = "x" * 801

    with pytest.raises(ValueError, match="text limit"):
        validate_showcase_fixture(payload, scenario("nvidia-current-developments"))


def test_all_checked_in_fixtures_validate_and_serialize_deterministically():
    catalog = ShowcaseScenarioCatalog()
    serialized = []
    for item in catalog.list_scenarios():
        if not item.showcase_available:
            continue
        result = catalog.load_result(item.scenario_id)
        serialized.append(json.dumps(result.to_dict(), sort_keys=True))

    assert len(serialized) == 6
    assert serialized == [
        json.dumps(catalog.load_result(item.scenario_id).to_dict(), sort_keys=True)
        for item in catalog.list_scenarios()
        if item.showcase_available
    ]


def test_catalog_definitions_do_not_depend_on_runtime_network_or_provider_modules():
    source = "\n".join(
        [
            (path.read_text())
            for path in (
                Path(__file__).resolve().parents[1] / "src" / "demo" / "showcase.py",
                Path(__file__).resolve().parents[1] / "src" / "demo" / "scenarios.py",
            )
        ]
    )

    assert "import openai" not in source
    assert "import requests" not in source
    assert "google.genai" not in source
    assert len(SHOWCASE_SCENARIOS) == 6
