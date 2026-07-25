"""Server-side DashboardWidget registry for future drag-and-drop dashboards."""

from app.modules.analytics_dashboard.schemas import WidgetDescriptor

WIDGET_REGISTRY: list[WidgetDescriptor] = [
    WidgetDescriptor(
        id="life_score",
        title="Life Score",
        icon="sparkles",
        type="kpi",
        endpoint="/analytics/dashboard",
        refresh_interval=60,
        component="KpiCard",
    ),
    WidgetDescriptor(
        id="todays_tasks",
        title="Today's Tasks",
        icon="list-todo",
        type="kpi",
        endpoint="/analytics/dashboard",
        refresh_interval=60,
        component="KpiCard",
    ),
    WidgetDescriptor(
        id="task_completion",
        title="Task Completion",
        icon="chart-column",
        type="chart",
        endpoint="/analytics/dashboard/productivity",
        refresh_interval=120,
        component="DonutChart",
    ),
    WidgetDescriptor(
        id="goal_progress",
        title="Goal Progress",
        icon="target",
        type="chart",
        endpoint="/analytics/dashboard/goals",
        refresh_interval=120,
        component="ProgressRing",
    ),
    WidgetDescriptor(
        id="habit_heatmap",
        title="Habit Heatmap",
        icon="flame",
        type="chart",
        endpoint="/analytics/dashboard/habits",
        refresh_interval=120,
        component="Heatmap",
    ),
    WidgetDescriptor(
        id="mood_trend",
        title="Mood Trend",
        icon="smile",
        type="chart",
        endpoint="/analytics/dashboard/journal",
        refresh_interval=120,
        component="LineChart",
    ),
    WidgetDescriptor(
        id="ai_insights",
        title="AI Insights",
        icon="sparkles",
        type="placeholder",
        endpoint="/analytics/dashboard/ai",
        refresh_interval=300,
        component="AiInsightsPanel",
    ),
    WidgetDescriptor(
        id="upcoming_events",
        title="Upcoming Events",
        icon="calendar-days",
        type="list",
        endpoint="/analytics/dashboard",
        refresh_interval=60,
        component="EventList",
    ),
]


def list_widgets() -> list[WidgetDescriptor]:
    return list(WIDGET_REGISTRY)
