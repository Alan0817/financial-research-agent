"""Client-neutral presentation helpers for financial-analysis results."""

from .service import DemoPresentationService
from .showcase import ShowcaseScenarioCatalog
from .types import DemoPresentationResult

__all__ = [
    "DemoPresentationResult",
    "DemoPresentationService",
    "ShowcaseScenarioCatalog",
]
