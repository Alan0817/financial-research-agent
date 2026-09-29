"""Curated metadata for source-controlled financial-agent showcase snapshots."""

from dataclasses import asdict, dataclass


SHOWCASE_SNAPSHOT_NOTICE = (
    "Showcase snapshot — captured from a reviewed agent run. "
    "This example is not live market or web information."
)


@dataclass(frozen=True)
class ShowcaseScenario:
    """Presentation metadata for one selectable showcase card."""

    scenario_id: str
    title: str
    short_description: str
    category: str
    example_question: str
    expected_evidence_families: tuple[str, ...]
    showcase_available: bool
    captured_at: str | None
    snapshot_notice: str
    tags: tuple[str, ...]
    fixture_name: str | None = None

    def to_dict(self) -> dict:
        """Return public scenario-card metadata without fixture internals."""
        data = asdict(self)
        data.pop("fixture_name")
        data["expected_evidence_families"] = list(self.expected_evidence_families)
        data["tags"] = list(self.tags)
        return data


SHOWCASE_SCENARIOS = (
    ShowcaseScenario(
        scenario_id="concept-rsi",
        title="What RSI Measures",
        short_description="A conceptual answer that completes without financial-tool calls.",
        category="conceptual",
        example_question="What is RSI?",
        expected_evidence_families=(),
        showcase_available=True,
        captured_at="2026-09-16T15:38:00Z",
        snapshot_notice=SHOWCASE_SNAPSHOT_NOTICE,
        tags=("conceptual", "no-tools"),
        fixture_name="concept-rsi.json",
    ),
    ShowcaseScenario(
        scenario_id="nvda-quantitative",
        title="Analyze NVIDIA",
        short_description="Structured market, technical, and risk evidence for NVDA.",
        category="quantitative",
        example_question="Analyze NVDA from 2026-01-01 to 2026-06-30.",
        expected_evidence_families=("quantitative",),
        showcase_available=True,
        captured_at="2026-09-16T15:38:00Z",
        snapshot_notice=SHOWCASE_SNAPSHOT_NOTICE,
        tags=("market", "technical-analysis", "risk", "model-boundary"),
        fixture_name="nvda-quantitative.json",
    ),
    ShowcaseScenario(
        scenario_id="mstr-sec-custody",
        title="Bitcoin Custody Risks",
        short_description="MSTR 10-K evidence with section-aware SEC provenance.",
        category="sec",
        example_question="What Bitcoin custody risks does MSTR disclose?",
        expected_evidence_families=("document",),
        showcase_available=True,
        captured_at="2026-09-16T15:38:00Z",
        snapshot_notice=SHOWCASE_SNAPSHOT_NOTICE,
        tags=("sec", "risk-factors", "bitcoin", "provenance"),
        fixture_name="mstr-sec-custody.json",
    ),
    ShowcaseScenario(
        scenario_id="nvidia-current-developments",
        title="NVIDIA Developments Snapshot",
        short_description="A historical web-evidence snapshot with source provenance.",
        category="web",
        example_question="What are the latest developments involving NVIDIA?",
        expected_evidence_families=("web",),
        showcase_available=True,
        captured_at="2026-09-16T15:38:00Z",
        snapshot_notice=SHOWCASE_SNAPSHOT_NOTICE,
        tags=("web", "historical-snapshot", "provenance"),
        fixture_name="nvidia-current-developments.json",
    ),
    ShowcaseScenario(
        scenario_id="mstr-sec-and-web",
        title="MSTR Filing Risks and Developments",
        short_description="Separate SEC and web evidence shown together without conflating sources.",
        category="mixed",
        example_question="Compare recent MSTR Bitcoin developments with filing risks.",
        expected_evidence_families=("document", "web"),
        showcase_available=True,
        captured_at="2026-09-16T15:38:00Z",
        snapshot_notice=SHOWCASE_SNAPSHOT_NOTICE,
        tags=("sec", "web", "bitcoin", "mixed-evidence"),
        fixture_name="mstr-sec-and-web.json",
    ),
    ShowcaseScenario(
        scenario_id="btc-market-analysis",
        title="BTC Market Analysis",
        short_description="Historical market evidence plus the bounded BTC-USD LSTM signal.",
        category="quantitative_ml",
        example_question="Analyze BTC-USD using the ML capability.",
        expected_evidence_families=("quantitative",),
        showcase_available=True,
        captured_at="2026-09-16T06:47:31Z",
        snapshot_notice=SHOWCASE_SNAPSHOT_NOTICE,
        tags=("btc-usd", "lstm", "market", "model-boundary"),
        fixture_name="btc-market-analysis.json",
    ),
)
