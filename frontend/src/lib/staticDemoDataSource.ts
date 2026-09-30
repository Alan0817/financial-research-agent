import type {
  DemoCapabilities,
  DemoPresentationResult,
  EvidenceFamily,
  ScenarioListResponse,
} from "../types/api";
import { DemoApiError } from "./demoError";


const STATIC_MANIFEST_SCHEMA_VERSION = "showcase-manifest-v1";


interface StaticShowcaseManifest {
  schema_version: string;
  presentation_schema_version: string;
  evidence_families: EvidenceFamily[];
  scenarios: ScenarioListResponse["scenarios"];
}


export function getDemoMode(): "static" {
  return "static";
}


export function createDemoDataSource(): StaticShowcaseDataSource {
  return new StaticShowcaseDataSource();
}


class StaticShowcaseDataSource {
  private manifest: StaticShowcaseManifest | null = null;

  async getCapabilities(): Promise<DemoCapabilities> {
    const manifest = await this.getManifest();
    return {
      showcase_available: manifest.scenarios.length > 0,
      live_mode_enabled: false,
      presentation_schema_version: manifest.presentation_schema_version,
      evidence_families: manifest.evidence_families,
      showcase_scenario_count: manifest.scenarios.length,
    };
  }

  async getShowcaseScenarios(): Promise<ScenarioListResponse> {
    const manifest = await this.getManifest();
    return { scenarios: manifest.scenarios };
  }

  getShowcaseScenario(scenarioId: string): Promise<DemoPresentationResult> {
    const assetPath = `showcase/results/${encodeURIComponent(scenarioId)}.json`;
    return getStaticJson<DemoPresentationResult>(assetPath);
  }

  async runLiveResearch(): Promise<DemoPresentationResult> {
    throw new DemoApiError("Live research is intentionally unavailable in the public static showcase.");
  }

  private async getManifest(): Promise<StaticShowcaseManifest> {
    if (this.manifest) {
      return this.manifest;
    }

    const manifest = await getStaticJson<StaticShowcaseManifest>("showcase/manifest.json");
    if (manifest.schema_version !== STATIC_MANIFEST_SCHEMA_VERSION) {
      throw new DemoApiError("The reviewed showcase assets use an unsupported manifest version.");
    }

    this.manifest = manifest;
    return manifest;
  }
}


async function getStaticJson<T>(assetPath: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(staticAssetUrl(assetPath));
  } catch {
    throw new DemoApiError("The reviewed showcase assets could not be loaded.");
  }

  if (!response.ok) {
    throw new DemoApiError("The reviewed showcase assets could not be loaded.");
  }

  return response.json() as Promise<T>;
}


function staticAssetUrl(assetPath: string): string {
  const baseUrl = import.meta.env.BASE_URL;
  return `${baseUrl}${assetPath}`;
}
