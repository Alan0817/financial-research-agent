import type {
  DemoCapabilities,
  DemoPresentationResult,
  ScenarioListResponse,
} from "../types/api";


const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const apiBaseUrl = (configuredBaseUrl || "http://localhost:8000").replace(/\/$/, "");


export class DemoApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DemoApiError";
  }
}


async function getJson<T>(path: string): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}${path}`);
  } catch {
    throw new DemoApiError("The local demo API is unavailable. Start the FastAPI service to load showcase scenarios.");
  }

  return parseResponse<T>(response);
}


async function postJson<T>(path: string, body: Record<string, string>): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new DemoApiError("The local demo API is unavailable. Start the FastAPI service before running live research.");
  }

  return parseResponse<T>(response);
}


async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  const payload = await response.json().catch(() => null);
  const detail = payload && typeof payload === "object" ? payload.detail : null;
  const message =
    typeof detail === "string"
      ? detail
      : detail && typeof detail === "object" && typeof detail.message === "string"
        ? detail.message
        : null;

  if (message) {
    throw new DemoApiError(message);
  }

  throw new DemoApiError(`The demo API returned ${response.status} while loading this resource.`);
}


export function getCapabilities(): Promise<DemoCapabilities> {
  return getJson<DemoCapabilities>("/v1/capabilities");
}


export function getShowcaseScenarios(): Promise<ScenarioListResponse> {
  return getJson<ScenarioListResponse>("/v1/showcase/scenarios");
}


export function getShowcaseScenario(scenarioId: string): Promise<DemoPresentationResult> {
  return getJson<DemoPresentationResult>(`/v1/showcase/scenarios/${encodeURIComponent(scenarioId)}`);
}


export function runLiveResearch(prompt: string): Promise<DemoPresentationResult> {
  return postJson<DemoPresentationResult>("/v1/research", { prompt });
}
