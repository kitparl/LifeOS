"""Registry of modules that contribute dated items to the Timeline.

Adding a new dated module = one entry here + one ``_<key>`` collector in
``TimelineService`` (and a presentation entry in the frontend source map).
"""

from app.modules.timeline.schemas import TimelineSource

TIMELINE_SOURCES: tuple[TimelineSource, ...] = (
    TimelineSource(key="calendar", label="Calendar", default_enabled=True),
    TimelineSource(key="running", label="Running", default_enabled=True),
    TimelineSource(key="travel", label="Travel", default_enabled=True),
    TimelineSource(key="tasks", label="Tasks", default_enabled=True),
    TimelineSource(key="journal", label="Journal", default_enabled=True),
    TimelineSource(key="finance", label="Loan EMIs", default_enabled=True),
    TimelineSource(key="wishlist", label="Wishlist wins", default_enabled=True),
    # Routine blocks repeat every day — useful but noisy, so opt-in.
    TimelineSource(key="routines", label="Routines", default_enabled=False),
)

# Calendar rows mirrored from another module (CalendarSyncService.source_module)
# belong to that module's timeline source, so toggling e.g. Running hides races too.
CALENDAR_SOURCE_MODULE_MAP: dict[str, str] = {
    "running": "running",
    "travel": "travel",
    "routine": "routines",
}
