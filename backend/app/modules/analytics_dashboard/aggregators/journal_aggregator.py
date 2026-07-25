"""Journal and mood analytics aggregations."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics_dashboard.aggregators import utc_today, window_start, word_count
from app.modules.analytics_dashboard.schemas import (
    JournalAnalytics,
    PlaceholderField,
    SeriesPoint,
    TimeSeries,
)
from app.modules.journal.models import JournalEntry
from app.modules.mood.models import MoodEntry


async def writing_streak(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(JournalEntry.entry_date).where(JournalEntry.user_id == user_id)
    )
    dates = {d for (d,) in result.all()}
    if not dates:
        return 0
    today = utc_today()
    streak = 0
    cursor = today
    # Allow yesterday start if nothing today yet
    if cursor not in dates:
        cursor = today - timedelta(days=1)
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


async def mood_score_avg(db: AsyncSession, user_id: str, range_days: int = 30) -> float | None:
    start = window_start(range_days)
    result = await db.execute(
        select(MoodEntry).where(MoodEntry.user_id == user_id, MoodEntry.log_date >= start)
    )
    entries = list(result.scalars().all())
    if not entries:
        return None
    scores = []
    for e in entries:
        # stress inverted (1..5 assumed); higher happiness/confidence/motivation is better
        stress_inv = max(1, 6 - int(e.stress))
        scores.append((int(e.happiness) + int(e.confidence) + int(e.motivation) + stress_inv) / 4.0)
    # Normalize assuming 1–5 scale → 0–100
    avg = sum(scores) / len(scores)
    return round((avg - 1) / 4 * 100, 1)


async def build_journal_analytics(db: AsyncSession, user_id: str, range_days: int) -> JournalAnalytics:
    today = utc_today()
    start = window_start(range_days, today)

    journal_rows = await db.execute(
        select(JournalEntry).where(
            JournalEntry.user_id == user_id, JournalEntry.entry_date >= start
        )
    )
    entries = list(journal_rows.scalars().all())

    freq_map: dict[str, float] = defaultdict(float)
    word_map: dict[str, float] = defaultdict(float)
    total_words = 0
    for e in entries:
        key = e.entry_date.isoformat()
        freq_map[key] += 1
        wc = word_count(e.content, e.gratitude, e.wins, e.lessons)
        word_map[key] += wc
        total_words += wc

    freq_points: list[SeriesPoint] = []
    word_points: list[SeriesPoint] = []
    cursor = start
    while cursor <= today:
        key = cursor.isoformat()
        freq_points.append(SeriesPoint(label=key, value=freq_map.get(key, 0.0)))
        word_points.append(SeriesPoint(label=key, value=word_map.get(key, 0.0)))
        cursor += timedelta(days=1)

    mood_rows = await db.execute(
        select(MoodEntry).where(MoodEntry.user_id == user_id, MoodEntry.log_date >= start)
    )
    moods = list(mood_rows.scalars().all())
    by_metric: dict[str, dict[str, float]] = {
        "happiness": {},
        "confidence": {},
        "motivation": {},
        "stress": {},
    }
    for m in moods:
        key = m.log_date.isoformat()
        by_metric["happiness"][key] = float(m.happiness)
        by_metric["confidence"][key] = float(m.confidence)
        by_metric["motivation"][key] = float(m.motivation)
        by_metric["stress"][key] = float(m.stress)

    mood_trend: list[TimeSeries] = []
    for metric, values in by_metric.items():
        points = [
            SeriesPoint(label=d, value=values[d]) for d in sorted(values.keys())
        ]
        mood_trend.append(TimeSeries(key=metric, label=metric.title(), points=points))

    return JournalAnalytics(
        mood_trend=mood_trend,
        journal_frequency=TimeSeries(
            key="journal_frequency", label="Journal Frequency", points=freq_points
        ),
        word_count_total=total_words,
        word_count_series=TimeSeries(
            key="word_count", label="Word Count", points=word_points
        ),
        writing_streak=await writing_streak(db, user_id),
        sentiment=PlaceholderField(status="coming_soon", message="Sentiment analysis coming soon"),
        emotion=PlaceholderField(status="coming_soon", message="Emotion detection coming soon"),
        range_days=range_days,
    )
