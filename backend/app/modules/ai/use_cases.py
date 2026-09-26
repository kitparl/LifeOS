"""Code-constant registry of AI use cases.

A use case declares what the product supports (id, name, required capability). Which
models are allowed comes from the cached catalogs of the user's connected providers.
Adding a use case: add a constant + entry here, then call AiGateway from the domain service.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.ai.adapters.base import CAPABILITY_CHAT


@dataclass(frozen=True)
class UseCase:
    id: str
    display_name: str
    capability: str


USE_CASE_WRITING_FEEDBACK = "communication.writing_feedback"
USE_CASE_RAG_CHAT = "ai.rag_chat"
USE_CASE_REPORTS = "reports.ai_briefing"
USE_CASE_ANALYTICS_INSIGHTS = "analytics.insights"

_USE_CASES: tuple[UseCase, ...] = (
    UseCase(USE_CASE_WRITING_FEEDBACK, "Writing Feedback", CAPABILITY_CHAT),
    UseCase(USE_CASE_RAG_CHAT, "Dashboard AI Chat", CAPABILITY_CHAT),
    UseCase(USE_CASE_REPORTS, "Reports & Briefings", CAPABILITY_CHAT),
    UseCase(USE_CASE_ANALYTICS_INSIGHTS, "Analytics Insights", CAPABILITY_CHAT),
)
USE_CASES: dict[str, UseCase] = {uc.id: uc for uc in _USE_CASES}


def get_use_case(use_case: str) -> UseCase | None:
    return USE_CASES.get(use_case)
