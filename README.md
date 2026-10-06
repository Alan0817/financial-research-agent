# Financial Research Agent

> An evidence-grounded, tool-using LLM research system combining quantitative analysis, SEC filing retrieval, current web evidence, and a bounded BTC-specific ML model.

This repository is an evidence-oriented financial research project, not a generic chatbot, automated trading system, or autonomous financial advisor. A provider-neutral LLM layer plans tool use, gathers evidence, and synthesizes a research response. Market calculations, technical indicators, risk metrics, SEC retrieval, BTC-specific LSTM inference, and evidence validation remain application-owned systems with structured results, provenance, traces, and limitations.

**Explore:** [Public Showcase](https://Alan0817.github.io/financial-research-agent/) · [Source Code](https://github.com/Alan0817/financial-research-agent)

The public showcase contains reviewed historical snapshots from real agent runs. It is static by design: examples are not live market or web results, and public Live Research is intentionally not exposed. The full React + FastAPI Live Research application remains available locally or privately.

**Local Live Research example** — *NVDA analysis using deterministic quantitative tools, with structured evidence and an explicit BTC-only model boundary.*

![Local Live Research example](assets/readme/live_research_readme_ready.png)

## What This Project Demonstrates

- Provider-neutral OpenAI and Gemini tool calling through one `FinancialAnalysisAgent` and `ToolRegistry` boundary.
- Quantitative, SEC filing, and current-web evidence routed as separate application-owned systems.
- Section-aware SEC retrieval using dense candidates, BM25, Reciprocal Rank Fusion, and optional cross-encoder reranking.
- A 30-case manually judged SEC retrieval benchmark: Dense Recall@10 `.519`; Hybrid + reranker Recall@10 `.685` on this fixed corpus and label set.
- A 20-case deterministic end-to-end benchmark for routing, evidence families, provenance, capability boundaries, and limitations.
- `183` fully offline automated Python tests, plus structured traces that make observable tool execution inspectable.

In this design, the LLM is responsible for **orchestration and synthesis**. It is not the numerical financial predictor, SEC parser, retriever, or web-search provider. The BTC LSTM is a deliberately bounded `BTC-USD`-only quantitative capability; it does not predict arbitrary equities or drive automated trading.

## Architecture

```mermaid
flowchart TD
    U[User Query] --> A[FinancialAnalysisAgent]
    A --> L[Provider-neutral LLMClient<br/>OpenAI or Gemini]
    L --> R[ToolRegistry]
    R --> Q[Quantitative evidence<br/>market, technical, risk, BTC-only LSTM]
    R --> S[SEC filing evidence<br/>section-aware hybrid retrieval]
    R --> W[Current web evidence<br/>Tavily search]
    Q --> E[Structured evidence<br/>provenance, traces, limitations]
    S --> E
    W --> E
    E --> A
    A --> O[Evidence-grounded research response]
```

Provider adapters translate model tool requests through the same provider-neutral definitions. `ToolRegistry` validates and executes application-owned tools, while JSON-safe traces record observable tool requests, completions, evidence, and structured limitations without exposing provider SDK objects to the agent layer.

## Evidence Routing

| Question type | Intended evidence source |
| --- | --- |
| Historical market behavior | Quantitative tools |
| Technical indicators or risk metrics | Quantitative tools |
| A specific 10-K or 10-Q disclosure | Local SEC retrieval |
| Current, latest, or recent event | Web search |
| Broader research question | A controlled combination of the relevant evidence families |

Keeping these sources separate is intentional. A historical market result is not evidence of a current event; a web snippet is not a substitute for a filing disclosure; and a local filing corpus is not a current-news source.

## Evaluation at a Glance

- `183` fully offline automated Python tests pass.
- The manually judged SEC retrieval benchmark has 30 cases; Dense Recall@10 was `.519` and Hybrid + reranker Recall@10 was `.685` on the fixed benchmark.
- `hybrid` is the default application configuration for the measured latency/coverage trade-off; `hybrid_reranked` is an optional higher-ranking-quality path with additional CPU cost.
- The fixed `financial-agent-e2e-v1` benchmark has 20 deterministic cases covering routing, evidence families, provenance, capability boundaries, and structured limitations.
- Controlled live provider subsets diagnose real routing and retrieval behavior; they are not full live 20-case benchmark runs.

These deterministic measurements assess retrieval placement and evidence handling. They do not prove financial profitability or the factual correctness of every generated sentence.

## Public Showcase and Example Research Workflows

The [Public Showcase](https://Alan0817.github.io/financial-research-agent/) demonstrates reviewed historical agent runs without requiring a backend or provider credentials. Each scenario exposes the answer, structured evidence, provenance, observable tool execution, and limitations without presenting historical snapshots as live information.

| Scenario | Evidence path demonstrated |
| --- | --- |
| Conceptual RSI | No tool is required for a general financial concept. |
| NVDA quantitative analysis | Deterministic market, technical, and risk evidence. |
| MSTR Bitcoin custody | Section-aware SEC filing retrieval with provenance. |
| NVIDIA current developments | Current-information web evidence with source metadata. |
| MSTR SEC + web | Mixed filing and current-web evidence, kept distinct. |
| BTC market analysis | Quantitative evidence plus the bounded `BTC-USD` LSTM capability. |

Representative prompts include `What is RSI?`, `What supply-chain risks does Apple disclose in its filings?`, and `Compare recent MSTR Bitcoin developments with risks disclosed in its SEC filings.` A mixed question can use only the evidence families relevant to the request.

## SEC Filing Retrieval

The current controlled evaluation corpus contains the latest configured `10-K` and `10-Q` filings for `NVDA`, `AAPL`, and `MSTR`. CIK is the stable SEC identity; ticker metadata is retained for filtering and citations. This is a small evaluation corpus, not a production-scale SEC archive.

```mermaid
flowchart TD
    F[Official SEC EDGAR filing] --> C[HTML cleanup and section normalization]
    C --> K[Section-aware chunking with filing metadata]
    K --> D[Dense embeddings and BM25 lexical index]
    D --> H[Metadata filtering and hybrid RRF]
    H --> R[Optional cross-encoder reranking]
    R --> T[search_financial_documents]
```

The pipeline preserves official SEC provenance plus ticker, form, filing-date, reporting-period, and section metadata. Section detection is deterministic and best-effort: unclassified content remains `UNKNOWN`, and tables are retained as text rather than given advanced financial-table interpretation.

`search_financial_documents` returns compact chunk-level evidence with SEC provenance. It supports ticker, document type, section, and filing-date filters. Section filtering uses normalized, case-insensitive exact matching against either the canonical identifier (for example, `PART I ITEM 1A`) or the title (for example, `Risk Factors`).

### Retrieval Benchmark

Phase 3.3 introduced a separate manually judged retrieval benchmark (`phase-3.3-manual-v1`) with positive and negative cases. It records relevance labels at the chunk level, diagnostic ranks, category breakdowns, and failure annotations without an LLM judge. Phase 3.4 then evaluated four retrieval variants on exactly that benchmark.

| Retriever | Hit@5 | Hit@10 | Recall@10 | nDCG@10 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dense | .444 | .556 | .519 | .309 | .247 |
| BM25 | .407 | .593 | .593 | .320 | .235 |
| Hybrid | .444 | .667 | .630 | .354 | .277 |
| Hybrid + reranker | .593 | .704 | .685 | .405 | .315 |

These numbers are benchmark-specific and are not claims of statistical significance or universal retrieval quality. Hybrid improved candidate coverage over dense retrieval in this corpus and is the default application configuration because it offers a practical latency/coverage trade-off. `hybrid_reranked` achieved the strongest fixed-benchmark ranking metrics, but the local cross-encoder adds substantial CPU latency and remains an optional quality mode.

The retrieval stack is local and provider-neutral. It uses exact normalized cosine similarity for dense candidates, a deterministic lowercase word tokenizer for BM25, Reciprocal Rank Fusion rather than raw-score averaging, and optional reranking only over a bounded candidate set.

## Quantitative Analysis and the BTC LSTM

The deterministic `analyze_market(symbol, start_date, end_date)` orchestration keeps DataFrames internal to Python and returns a compact JSON-safe result containing market summary information, project-defined technical indicators, market-return risk metrics, and LSTM status where appropriate.

The BTC LSTM is a legacy experimental ML component retained as a bounded example of integrating a learned model into a broader tool-using research system. Its scope is intentionally narrow:

- Asset applicability: `BTC-USD` only.
- Sequence length: 30 daily observations.
- Model: PyTorch LSTM classifier.
- Output: `probability_up = P(Target = 1)`.
- Target: `Target = 1` when `Future_Return > 0.005`.
- Threshold labels: probability above `0.52` yields raw signal `+1`, below `0.48` yields raw signal `-1`, and otherwise `0`.

Raw signal is not a long/short exposure. The historical backtest deliberately preserves its contrarian convention: exposure is the negated raw signal, and strategy returns use that exposure times the next-day market return. The model and backtest are experimental research artifacts, not deployable trading performance.

## End-to-End Evaluation

The project keeps several evaluation layers separate:

| Evaluation layer | What it measures |
| --- | --- |
| Phase 2 agent evaluation | Tool routing, required calls, duplicate/extra calls, and limitations across provider-neutral traces. |
| Phase 2.8 cross-provider evaluation | The same agent benchmark executed separately against OpenAI and Gemini. |
| Phase 3.3 retrieval analysis | Manually judged chunk ranking, failure diagnostics, and negative-query behavior. |
| Phase 3.4 retrieval ablation | Dense, BM25, hybrid, and hybrid-reranked retrieval behavior on fixed labels. |
| Phase 4.0 E2E evaluation | Routing, evidence availability, provenance, capability boundaries, and planning behavior for the complete research agent. |

The fixed end-to-end benchmark is `financial-agent-e2e-v1` with 20 cases across conceptual, quantitative, SEC, web, quantitative-plus-SEC, quantitative-plus-web, SEC-plus-web, full evidence mix, BTC applicability, and unavailable-capability scenarios. Its deterministic metrics include:

- required-tool recall, missing calls, forbidden calls, and duplicate calls;
- quantitative, document, and web evidence-family coverage;
- structured SEC and web provenance availability;
- document and web retrieval planning diagnostics; and
- structured limitation preservation.

These metrics evaluate routing and evidence handling. They do **not** independently prove factual correctness for every generated sentence, prose quality, investment quality, or provider intelligence. The earlier eight-case cross-provider run likewise measured tool-use behavior and limitations without declaring a provider winner.

### Controlled Live E2E Findings

A controlled OpenAI five-case live subset covered conceptual, quantitative, SEC, web, and SEC-plus-web scenarios. Observed successful behaviors included:

- The conceptual RSI question used no tools.
- NVDA quantitative analysis used the quantitative analysis tool.
- The BTC-only LSTM applicability limitation was preserved for NVDA.
- Mixed SEC-plus-web research used both evidence families when each was available.
- Returned SEC chunks retained real filing provenance.
- The web-search regression run stayed within the intended two-search planning budget.

### Engineering Case Study: Retrieval Contract Failure

A live MSTR custody query initially returned `no_results` because a human-readable section filter such as `Risk Factors` did not match canonical chunk metadata such as `PART I ITEM 1A`. Trace inspection showed that the failure occurred in metadata filtering before ranking, rather than proving that evidence was absent or that embeddings were weak. The retrieval contract was corrected generically to match normalized exact values against either the canonical section identifier or section title, then validated with regression tests and a subsequent live run.

Filing-date planning remains a known limitation: the agent can still infer an overly restrictive SEC filing-date filter even when a user did not explicitly request one. That can truthfully return `no_results` before ranking despite relevant evidence elsewhere in the configured corpus.

## Known Limitations

- The local SEC evaluation corpus is limited to configured NVDA, AAPL, and MSTR filings.
- SEC section detection and table serialization are deterministic best-effort processing, not complete financial-statement interpretation.
- `filing_date` means the actual SEC filing/submission date; it is distinct from the financial reporting period. The agent is instructed to omit filing-date filters unless the user explicitly requests a filing-date restriction, but live evaluation showed that over-restrictive planning can still occur.
- A structured `no_results` response does not prove a fact is false; it reports the configured corpus, query, and filters produced no matching evidence.
- Search-result snippets are not full-page verification. Source and `published_at` metadata depend on what the search provider returns.
- Web search is not a replacement for filing-specific evidence, audited filings, or independent fact verification.
- The BTC LSTM is limited to `BTC-USD`; it does not predict NVDA, AAPL, MSTR, or arbitrary securities.
- The legacy BTC backtest uses one fixed holdout, excludes transaction costs and slippage, has no walk-forward validation, and annualizes with `sqrt(252)` despite BTC trading daily.
- This project is research tooling, not investment advice, production-ready trading infrastructure, or a guarantee of financial outcomes.

## Repository Structure

```text
src/
  agent/              FinancialAnalysisAgent, prompts, and result types
  documents/          SEC client, parser, sections, chunking, storage, ingestion
  evaluation/         Agent, cross-provider, and end-to-end evaluation helpers
  llm/                Provider-neutral client with OpenAI and Gemini adapters
  retrieval/          Dense, BM25, hybrid, reranking, index, and evaluation code
  tools/              Registry and deterministic financial/document tools
  app.py              Application composition helper
  web_search.py       Provider-neutral search interface and Tavily adapter
  backtest.py         Historical BTC backtest entry point
  train.py             Historical BTC LSTM training entry point
tests/                Fully offline unit and integration-style tests
data/                 Local processed BTC data and ignored generated SEC/index artifacts
.env.example          Safe environment-variable template
requirements.txt      Python dependencies
```

## Setup

Create and activate a virtual environment, then install the project dependency set:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Populate only the capabilities you intend to use. Keep `.env` local and never commit credentials.

## Configuration

The current `.env.example` defines the supported configuration surface:

```ini
LLM_PROVIDER=gemini
LLM_MODEL=
# Optional provider-specific fallbacks when LLM_MODEL is unset.
OPENAI_MODEL=
GEMINI_MODEL=
OPENAI_API_KEY=
GEMINI_API_KEY=
RETRIEVAL_BACKEND=hybrid
# Optional local retrieval model overrides.
SEC_EMBEDDING_MODEL=
SEC_RERANKER_MODEL=
# Documented adapter choice; application composition injects the provider.
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=
SEC_USER_AGENT="FinancialResearchAgent your-email@example.com"
```

- `LLM_PROVIDER` selects `openai` or `gemini`; `LLM_MODEL` can override the provider default.
- `OPENAI_MODEL` and `GEMINI_MODEL` are optional provider-specific fallbacks when `LLM_MODEL` is unset.
- `OPENAI_API_KEY` and `GEMINI_API_KEY` are required only for the corresponding live provider.
- `RETRIEVAL_BACKEND` accepts `dense`, `bm25`, `hybrid`, or `hybrid_reranked`. The default is `hybrid`.
- `SEC_EMBEDDING_MODEL` and `SEC_RERANKER_MODEL` are optional local model overrides; leave them unset to use the project defaults.
- `WEB_SEARCH_PROVIDER=tavily` documents the selected adapter in the local template. Current application composition receives an explicitly constructed `TavilyWebSearchProvider`, which needs `TAVILY_API_KEY`; it does not dynamically construct providers from this variable. Without a configured provider, `search_web` is not advertised by the registry.
- `SEC_USER_AGENT` is required for live SEC EDGAR access and should identify the requester in accordance with SEC automated-access expectations.

The SentenceTransformer and optional CrossEncoder are loaded lazily by the selected retrieval backend. `bm25` does not load the dense embedding model, and `hybrid_reranked` is the only mode that loads the cross-encoder.

## Running the System

This repository provides a composition helper rather than an interactive agent CLI. The following direct Python invocation uses the real application boundaries and requires an existing local SEC corpus/index plus the relevant provider credentials:

```bash
PYTHONPATH=src python - <<'PY'
from app import build_financial_analysis_agent
from web_search import TavilyWebSearchProvider

agent = build_financial_analysis_agent(
    provider="openai",
    retrieval_backend="hybrid",
    web_search_provider=TavilyWebSearchProvider(),
)
result = agent.run("What are the latest developments involving NVIDIA?")
print(result.to_dict())
PY
```

To work without current web search, omit `web_search_provider`. The agent then exposes only capabilities that are actually configured. Both forms may make live provider calls; they are not part of the test suite.

### Portfolio Demo API

The FastAPI transport defaults to offline showcase mode and does not construct
the live agent at startup. With `DEMO_LIVE_ENABLED=false`, it works without
provider credentials or local SEC/index artifacts:

```bash
PYTHONPATH=src python -m uvicorn api.app:app --reload
```

The reviewed showcase catalog is available at
`GET /v1/showcase/scenarios`. `POST /v1/research` remains disabled until the
server owner explicitly enables live mode and provides the required local and
provider dependencies. For a separately hosted frontend, set
`DEMO_CORS_ORIGINS` to its explicit origin, such as `http://localhost:5173`.

### Local Live Research

LIVE mode is opt-in and server-owned. The browser submits only a research
question; it cannot select a provider, model, retrieval backend, web-search
provider, API key, or local path. The server loads `.env` through the existing
configuration modules, so set the desired values there before starting the API.

For an OpenAI-backed run, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.
For Gemini, set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`. `LLM_MODEL` can
select a model for either provider; `OPENAI_MODEL` and `GEMINI_MODEL` remain
provider-specific fallbacks.

For local SEC document retrieval, keep `RETRIEVAL_BACKEND=hybrid` (or another
supported configured backend) and ensure the local SEC corpus and compatible
retrieval index exist under `data/financial_documents/`. `SEC_USER_AGENT` is
required only when downloading from SEC EDGAR; it is not required to search an
already-built local corpus. Web evidence is available only when the existing
composition receives `WEB_SEARCH_PROVIDER=tavily` and `TAVILY_API_KEY`.

The BTC-specific LSTM has no environment switch. A live BTC request needs the
local `src/model_weight/lstm_model.pth` artifact and enough available daily
market history for its 30-observation sequence; it remains `BTC-USD` only.
Live market-data tools may independently require their configured external data
source to be reachable.

In one terminal, start the API with live mode enabled. Environment values in
the command override same-named `.env` values for that local process:

```bash
DEMO_LIVE_ENABLED=true \
DEMO_CORS_ORIGINS=http://localhost:5173 \
PYTHONPATH=src \
python -m uvicorn api.app:app --reload
```

In a second terminal, start the frontend:

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:5173`. Confirm `GET /v1/capabilities` reports
`live_mode_enabled: true`; the page will then present separate **Reviewed
Showcase** and **Live Research** modes. Do not enable LIVE mode for a public
demo without intentionally managing provider cost, rate limits, and abuse.

### Portfolio Page

The React and TypeScript portfolio page supports two explicit modes. The Vite
toolchain requires Node.js 18 or newer.

- **Static showcase mode** exports the reviewed Python fixtures through the
  validated catalog and serves them without FastAPI, provider credentials, a
  SEC corpus, or a retrieval index. It is the intended public portfolio mode.
- **API mode** loads the same showcase contract from FastAPI and can expose
  local, server-owned Live Research only when the backend enables it.

Static export data is generated and ignored; the source-controlled authority
remains `src/demo/scenarios.py` and `src/demo/fixtures/`. From the repository
root, prepare and build a static showcase with a base path suitable for a
project-hosted site:

```bash
PYTHONPATH=src python -m demo.export_showcase
cd frontend
VITE_DEMO_MODE=static \
VITE_BASE_PATH=/financial-research-agent/ \
npm run build:static
VITE_DEMO_MODE=static \
VITE_BASE_PATH=/financial-research-agent/ \
npm run preview
```

The base path is configurable; use `VITE_BASE_PATH=/` for root-hosted local
preview. Static builds fail clearly if validated showcase assets have not been
exported.

The reviewed static showcase is deployed through [GitHub Pages](https://Alan0817.github.io/financial-research-agent/). The deployment workflow exports assets through the validated Python catalog and publishes only `frontend/dist` on pushes to `main` or manual dispatch. The public site does not deploy FastAPI or expose Live Research; Live Research remains a local or private, server-owned capability.

### Backend Container and SEC Retrieval Artifacts

The FastAPI backend can run in a Docker container without provider credentials, a SEC corpus/index, or BTC model weights when `DEMO_LIVE_ENABLED=false`. The base image intentionally excludes private/local retrieval artifacts. Live SEC retrieval will later receive a selected, versioned artifact bundle; GCS download and Cloud Run deployment are not part of this phase.

`requirements-runtime.txt` contains only backend serving dependencies and pins
CPU-only PyTorch for the Docker image. `requirements-dev.txt` adds ingestion,
historical plotting, and test dependencies. `requirements.txt` remains the
backward-compatible full local development install through `requirements-dev.txt`.

Pull requests and pushes to `main` run offline Python tests, static frontend
type-check/build validation, a Docker build, showcase-only container smoke tests,
and CPU-only PyTorch checks. This CI workflow does not deploy cloud resources or
enable Live Research.

Build and run the showcase-only backend locally:

```bash
docker build -t financial-research-agent-api .
docker run --rm \
  -p 8000:8080 \
  -e PORT=8080 \
  -e DEMO_LIVE_ENABLED=false \
  financial-research-agent-api
curl http://localhost:8000/healthz
```

Package a validated local SEC corpus and semantic index for later artifact storage:

```bash
PYTHONPATH=src python -m deployment.package_sec_artifacts \
  --corpus-dir data/financial_documents \
  --output dist/sec-artifacts/sec-v1.tar.gz \
  --artifact-version sec-v1

mkdir -p /tmp/sec-artifact
tar -xzf dist/sec-artifacts/sec-v1.tar.gz -C /tmp/sec-artifact
PYTHONPATH=src python -m deployment.validate_sec_artifacts \
  --artifact-dir /tmp/sec-artifact/sec-retrieval-artifact
```

#### Versioned GCS SEC Artifact Releases

SEC corpus releases are versioned separately from the Docker image. A private
GCS bucket is the planned source of truth for published retrieval bundles; an
application release and a corpus release can therefore move independently.
Each immutable version uses deterministic object paths:

```text
gs://<bucket>/sec-artifacts/sec-vN/
    sec-vN.tar.gz
    manifest.json
    sha256.txt
```

The archive remains authoritative: the external `manifest.json` is uploaded
from that archive so release metadata can be inspected before download, and
`sha256.txt` verifies the archive independently of GCS object metadata. Normal
publishing never overwrites a version; changed corpus data is published as a
new version such as `sec-v2`.

Install artifact-distribution tooling separately from the serving image:

```bash
python -m pip install -r requirements-deployment.txt
```

Create a private bucket with uniform bucket-level access. Select a region that
generally matches the future Cloud Run region:

```bash
gcloud storage buckets create gs://<bucket-name> \
  --location=<region> \
  --uniform-bucket-level-access
```

With Application Default Credentials configured outside the repository, upload
and independently download/validate an explicit release:

```bash
PYTHONPATH=src python -m deployment.upload_sec_artifact \
  --archive dist/sec-artifacts/sec-v1.tar.gz \
  --bucket <bucket-name> \
  --version sec-v1

PYTHONPATH=src python -m deployment.download_sec_artifact \
  --bucket <bucket-name> \
  --version sec-v1 \
  --output-dir /tmp/sec-v1
```

`SEC_ARTIFACT_BUCKET`, `SEC_ARTIFACT_PREFIX` (default `sec-artifacts`), and
`SEC_ARTIFACT_VERSION` are optional deployment-tooling environment variables;
they do not affect local application startup. Publisher identities should have
only `storage.objects.get` and `storage.objects.create` access to this bucket,
while a future Cloud Run runtime service account should have read-only object
access. Explicit overwrite requires separately granted update/delete access and
is not part of normal publishing. Bucket object versioning is optional because
explicit paths such as `sec-v1` and `sec-v2` are the project-facing release
mechanism. Retain releases conservatively rather than automatically deleting
active versions.

Future Phase 6.5 behavior, not implemented here, will select an explicit
`SEC_ARTIFACT_VERSION`, download it, verify it, and load it for Cloud Run.


Run the showcase API with an explicit local frontend origin:

```bash
DEMO_CORS_ORIGINS=http://localhost:5173 \
PYTHONPATH=src python -m uvicorn api.app:app --reload
```

In a second terminal, run the Vite frontend in API mode:

```bash
cd frontend
VITE_DEMO_MODE=api VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

The page is available at `http://localhost:5173`. The browser receives no
provider credentials or retrieval configuration; live research remains a
server-owned, opt-in capability.

Historical BTC pipeline entry points remain available. The repository includes the processed BTC dataset; training writes the ignored local model artifact required by the backtest. Refreshing market data is optional and makes a Yahoo Finance network request.

```bash
# Optional: refresh the tracked-input format with live Yahoo Finance data.
PYTHONPATH=src python src/data_downloader.py
# Required before a fresh-clone backtest: writes src/model_weight/lstm_model.pth.
PYTHONPATH=src python src/train.py
# Requires the model artifact produced by training.
PYTHONPATH=src python src/backtest.py
```

Training and backtesting retain their historical research semantics and should not be interpreted as deployment commands.

## Running Tests and Evaluation

Run the offline test suite:

```bash
python -m pytest -q
```

Run the original local dense-retrieval baseline evaluation against an existing corpus/index:

```bash
PYTHONPATH=src python -m retrieval.benchmark \
  --corpus-dir data/financial_documents \
  --index-dir data/financial_documents/semantic_index
```

Run the eight-case cross-provider agent benchmark explicitly for one configured live LLM provider:

```bash
PYTHONPATH=src python -m evaluation.provider_benchmark --provider gemini
PYTHONPATH=src python -m evaluation.provider_benchmark --provider openai --model gpt-5.6-luna
```

Those commands save JSON artifacts to `evaluation_results/` by default. They can make live LLM calls and are intentionally separate from pytest. End-to-end evaluation is exposed through `run_e2e_benchmark()` and `write_e2e_artifact()` in `src/evaluation/e2e.py`, allowing callers to run a selected case subset or the fixed 20-case benchmark with an explicitly composed agent.

## Design Notes

- **Controlled execution boundary:** the LLM chooses from advertised tools, but `ToolRegistry` validates arguments and executes only allowlisted functions.
- **Provider independence:** LLM providers and web-search providers are separate interfaces. Neither OpenAI-hosted search nor Gemini grounding is used as the application’s core web-search tool.
- **Retrieval strategy is application configuration:** the LLM does not choose dense, BM25, hybrid, or reranked retrieval.
- **Evidence is structured first:** tool outputs retain JSON-safe metadata, source URLs, statuses, and limitations so evaluation does not need to infer behavior from prose.
- **Evaluation informs, rather than hides, failures:** observed tool-routing, retrieval, provenance, and planning weaknesses are recorded without tuning benchmark cases or silently fabricating evidence.

The result is a portfolio project focused on building inspectable AI-assisted financial research workflows with explicit evidence boundaries and capability limits.
