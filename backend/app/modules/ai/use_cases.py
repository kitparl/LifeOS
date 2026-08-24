"""Code-constant catalog of AI use cases and allowed provider/model options."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelOption:
    provider: str
    model: str
    display_name: str


USE_CASE_WRITING_FEEDBACK = "communication.writing_feedback"

USE_CASE_CATALOG: dict[str, list[ModelOption]] = {
    USE_CASE_WRITING_FEEDBACK: [
        ModelOption(
            provider="sarvam",
            model="sarvam-105b",
            display_name="Sarvam · sarvam-105b",
        ),
    ],
}

USE_CASE_DISPLAY_NAMES: dict[str, str] = {
    USE_CASE_WRITING_FEEDBACK: "Writing Feedback",
}


def known_use_cases() -> list[str]:
    return list(USE_CASE_CATALOG.keys())


def options_for(use_case: str) -> list[ModelOption]:
    return list(USE_CASE_CATALOG.get(use_case, []))


def is_valid_option(use_case: str, provider: str, model: str) -> bool:
    return any(o.provider == provider and o.model == model for o in options_for(use_case))


def default_option(use_case: str) -> ModelOption | None:
    opts = options_for(use_case)
    return opts[0] if opts else None
