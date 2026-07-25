/**
 * Client-side DashboardWidget interface for future drag-and-drop layouts.
 * Mirrors the server WidgetDescriptor registry.
 */
export interface DashboardWidget {
  id: string;
  title: string;
  icon: string;
  type: 'kpi' | 'chart' | 'list' | 'placeholder';
  endpoint: string;
  refreshInterval: number;
  component: string;
}

export const ANALYTICS_WIDGET_REGISTRY: DashboardWidget[] = [
  {
    id: 'life_score',
    title: 'Life Score',
    icon: 'sparkles',
    type: 'kpi',
    endpoint: '/analytics/dashboard',
    refreshInterval: 60,
    component: 'KpiCard',
  },
  {
    id: 'todays_tasks',
    title: "Today's Tasks",
    icon: 'list-todo',
    type: 'kpi',
    endpoint: '/analytics/dashboard',
    refreshInterval: 60,
    component: 'KpiCard',
  },
  {
    id: 'task_completion',
    title: 'Task Completion',
    icon: 'chart-column',
    type: 'chart',
    endpoint: '/analytics/dashboard/productivity',
    refreshInterval: 120,
    component: 'DonutChart',
  },
  {
    id: 'goal_progress',
    title: 'Goal Progress',
    icon: 'target',
    type: 'chart',
    endpoint: '/analytics/dashboard/goals',
    refreshInterval: 120,
    component: 'ProgressRing',
  },
  {
    id: 'habit_heatmap',
    title: 'Habit Heatmap',
    icon: 'flame',
    type: 'chart',
    endpoint: '/analytics/dashboard/habits',
    refreshInterval: 120,
    component: 'Heatmap',
  },
  {
    id: 'mood_trend',
    title: 'Mood Trend',
    icon: 'smile',
    type: 'chart',
    endpoint: '/analytics/dashboard/journal',
    refreshInterval: 120,
    component: 'LineChart',
  },
  {
    id: 'ai_insights',
    title: 'AI Insights',
    icon: 'sparkles',
    type: 'placeholder',
    endpoint: '/analytics/dashboard/ai',
    refreshInterval: 300,
    component: 'AiInsightsPanel',
  },
];
