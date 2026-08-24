"""Deterministic writing metrics (no LLM)."""

from __future__ import annotations

import re
from collections import Counter


_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")


def compute_deterministic_metrics(content: str) -> dict:
    text = content or ""
    words = _WORD_RE.findall(text)
    word_count = len(words)
    char_count = len(text)
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()] if text.strip() else []
    paragraph_count = len(paragraphs)

    sentence_parts = [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]
    sentence_count = len(sentence_parts) if text.strip() else 0

    avg_sentence_length = round(word_count / sentence_count, 2) if sentence_count else 0.0
    long_sentence_count = sum(1 for s in sentence_parts if len(_WORD_RE.findall(s)) > 30)

    lower_words = [w.lower() for w in words]
    counts = Counter(lower_words)
    repeated_word_count = sum(1 for _, c in counts.items() if c >= 3)
    unique_word_ratio = round(len(set(lower_words)) / word_count, 3) if word_count else 0.0

    punctuation_count = sum(1 for ch in text if ch in ".,;:!?\"'()-")
    comma_count = text.count(",")
    semicolon_count = text.count(";")
    question_count = text.count("?")
    exclamation_count = text.count("!")

    return {
        "wordCount": word_count,
        "characterCount": char_count,
        "sentenceCount": sentence_count,
        "paragraphCount": paragraph_count,
        "averageSentenceLength": avg_sentence_length,
        "longSentenceCount": long_sentence_count,
        "repeatedWordCount": repeated_word_count,
        "uniqueWordRatio": unique_word_ratio,
        "punctuationCount": punctuation_count,
        "commaCount": comma_count,
        "semicolonCount": semicolon_count,
        "questionCount": question_count,
        "exclamationCount": exclamation_count,
    }
