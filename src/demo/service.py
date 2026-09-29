"""Client-neutral facade that runs the existing financial-analysis agent."""

from .presentation import present_financial_analysis_result
from .types import DemoPresentationResult


class DemoPresentationService:
    """Run an injected agent and return a safe presentation result."""

    def __init__(self, agent, mode: str = "live"):
        if not hasattr(agent, "run"):
            raise TypeError("agent must provide run(prompt).")
        self._agent = agent
        self._mode = mode

    def run(self, prompt: str) -> DemoPresentationResult:
        """Run one existing agent request without changing its execution path."""
        result = self._agent.run(prompt)
        return present_financial_analysis_result(result, mode=self._mode)
