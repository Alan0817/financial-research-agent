"""Export validated showcase snapshots as static public assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .presentation import SCHEMA_VERSION
from .scenarios import ShowcaseScenario
from .showcase import ShowcaseScenarioCatalog


MANIFEST_SCHEMA_VERSION = "showcase-manifest-v1"
DEFAULT_OUTPUT_DIRECTORY = Path("frontend") / "public" / "showcase"
RESULTS_DIRECTORY_NAME = "results"


def export_showcase(
    output_directory: Path | str = DEFAULT_OUTPUT_DIRECTORY,
    catalog: ShowcaseScenarioCatalog | None = None,
) -> Path:
    """Write a validated, deterministic static showcase export."""
    output_path = Path(output_directory)
    catalog = catalog or ShowcaseScenarioCatalog()

    available_scenarios = [
        scenario
        for scenario in catalog.list_scenarios()
        if scenario.showcase_available
    ]
    exported_results = _load_validated_results(catalog, available_scenarios)

    results_path = output_path / RESULTS_DIRECTORY_NAME
    results_path.mkdir(parents=True, exist_ok=True)

    expected_result_names = set()
    for scenario, result in exported_results:
        result_name = "{}.json".format(scenario.scenario_id)
        expected_result_names.add(result_name)
        _write_json(results_path / result_name, result)

    _remove_stale_results(results_path, expected_result_names)
    _write_json(output_path / "manifest.json", _build_manifest(available_scenarios))
    return output_path


def _load_validated_results(
    catalog: ShowcaseScenarioCatalog,
    scenarios: list[ShowcaseScenario],
) -> list[tuple[ShowcaseScenario, dict]]:
    """Load all results before writing so invalid input cannot partially publish a run."""
    return [
        (scenario, catalog.load_result(scenario.scenario_id).to_dict())
        for scenario in scenarios
    ]


def _build_manifest(scenarios: list[ShowcaseScenario]) -> dict:
    evidence_families = sorted(
        {
            evidence_family
            for scenario in scenarios
            for evidence_family in scenario.expected_evidence_families
        }
    )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "presentation_schema_version": SCHEMA_VERSION,
        "evidence_families": evidence_families,
        "scenarios": [scenario.to_dict() for scenario in scenarios],
    }


def _remove_stale_results(results_path: Path, expected_result_names: set[str]) -> None:
    """Prevent a removed scenario from remaining in a generated deployment bundle."""
    for result_path in results_path.glob("*.json"):
        if result_path.name not in expected_result_names:
            result_path.unlink()


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Export reviewed showcase assets for a static frontend build."""
    parser = argparse.ArgumentParser(
        description="Export validated Financial Research Agent showcase assets."
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIRECTORY,
        type=Path,
        help="Directory containing manifest.json and results/. Defaults to frontend/public/showcase.",
    )
    arguments = parser.parse_args()
    output_path = export_showcase(arguments.output_dir)
    print("Exported validated showcase assets to {}".format(output_path))


if __name__ == "__main__":
    main()
