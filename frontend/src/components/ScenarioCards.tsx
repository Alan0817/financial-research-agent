import { ArrowUpRight, ChevronRight } from "lucide-react";

import { EvidenceBadge } from "./EvidenceBadge";
import type { ShowcaseScenario } from "../types/api";


interface ScenarioCardsProps {
  scenarios: ShowcaseScenario[];
  selectedScenarioId: string | null;
  onSelect: (scenarioId: string) => void;
}


export function ScenarioCards({
  scenarios,
  selectedScenarioId,
  onSelect,
}: ScenarioCardsProps) {
  return (
    <div className="scenario-grid" aria-label="Reviewed showcase scenarios">
      {scenarios.map((scenario) => {
        const isSelected = scenario.scenario_id === selectedScenarioId;

        return (
          <button
            className={`scenario-card ${isSelected ? "scenario-card--selected" : ""}`}
            key={scenario.scenario_id}
            onClick={() => onSelect(scenario.scenario_id)}
            type="button"
            aria-pressed={isSelected}
          >
            <span className="scenario-card__topline">
              <span className="scenario-category">{scenario.category.replaceAll("_", " ")}</span>
              <ChevronRight aria-hidden="true" size={18} />
            </span>
            <span className="scenario-card__title">{scenario.title}</span>
            <span className="scenario-card__description">{scenario.short_description}</span>
            <span className="scenario-card__families">
              {scenario.expected_evidence_families.length > 0 ? (
                scenario.expected_evidence_families.map((family) => (
                  <EvidenceBadge family={family} key={family} />
                ))
              ) : (
                <span className="muted-label">No tool call required</span>
              )}
            </span>
            <span className="scenario-card__action">
              View reviewed example <ArrowUpRight aria-hidden="true" size={15} />
            </span>
          </button>
        );
      })}
    </div>
  );
}
