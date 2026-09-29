import type { EvidenceFamily } from "../types/api";
import { evidenceFamilyLabels } from "../lib/format";


interface EvidenceBadgeProps {
  family: EvidenceFamily;
}


export function EvidenceBadge({ family }: EvidenceBadgeProps) {
  return <span className={`evidence-badge evidence-badge--${family}`}>{evidenceFamilyLabels[family]}</span>;
}
