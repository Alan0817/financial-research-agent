"""Tests for the validated static showcase export boundary."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from demo.export_showcase import MANIFEST_SCHEMA_VERSION, export_showcase
from demo.scenarios import SHOWCASE_SCENARIOS
from demo.showcase import ShowcaseScenarioCatalog
from demo.types import DemoPresentationResult


EXPECTED_SCENARIO_IDS = [
    "concept-rsi",
    "nvda-quantitative",
    "mstr-sec-custody",
    "nvidia-current-developments",
    "mstr-sec-and-web",
    "btc-market-analysis",
]


def test_export_writes_catalog_metadata_and_all_available_results(tmp_path):
    export_showcase(tmp_path)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    exported_names = sorted(path.stem for path in (tmp_path / "results").glob("*.json"))

    assert manifest["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert [item["scenario_id"] for item in manifest["scenarios"]] == EXPECTED_SCENARIO_IDS
    assert exported_names == sorted(EXPECTED_SCENARIO_IDS)
    assert "fixture_name" not in manifest["scenarios"][0]


def test_exported_results_deserialize_to_the_public_presentation_schema(tmp_path):
    export_showcase(tmp_path)

    for scenario_id in EXPECTED_SCENARIO_IDS:
        payload = json.loads((tmp_path / "results" / "{}.json".format(scenario_id)).read_text())
        result = DemoPresentationResult(**payload)

        assert result.schema_version == "demo-presentation-v1"
        assert result.mode == "showcase"


def test_export_uses_catalog_validation_before_writing_assets(tmp_path):
    source_catalog = ShowcaseScenarioCatalog()
    invalid_fixture_directory = tmp_path / "fixtures"
    invalid_fixture_directory.mkdir()
    (invalid_fixture_directory / "concept-rsi.json").write_text("not JSON", encoding="utf-8")
    invalid_catalog = ShowcaseScenarioCatalog(
        fixture_directory=invalid_fixture_directory,
        scenarios=(source_catalog.get_scenario("concept-rsi"),),
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        export_showcase(tmp_path / "export", catalog=invalid_catalog)

    assert not (tmp_path / "export" / "manifest.json").exists()


def test_export_is_deterministic_and_removes_stale_generated_results(tmp_path):
    export_showcase(tmp_path)
    first_export = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(tmp_path.rglob("*.json"))
    }
    stale_result = tmp_path / "results" / "removed-scenario.json"
    stale_result.write_text("{}\n", encoding="utf-8")

    export_showcase(tmp_path)
    second_export = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(tmp_path.rglob("*.json"))
    }

    assert not stale_result.exists()
    assert second_export == first_export


def test_export_skips_unavailable_metadata_without_publishing_a_result(tmp_path):
    unavailable = replace(
        SHOWCASE_SCENARIOS[0],
        showcase_available=False,
        fixture_name=None,
        captured_at=None,
    )
    catalog = ShowcaseScenarioCatalog(scenarios=(unavailable,))

    export_showcase(tmp_path, catalog=catalog)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenarios"] == []
    assert list((tmp_path / "results").glob("*.json")) == []


def test_exporter_does_not_import_provider_or_network_modules():
    source_path = Path(__file__).resolve().parents[1] / "src" / "demo" / "export_showcase.py"
    source = source_path.read_text(encoding="utf-8")

