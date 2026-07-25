export interface SeriesPoint {
  label: string;
  value: number;
}

export interface TimeSeries {
  key: string;
  label: string;
  points: SeriesPoint[];
}

export interface HeatmapCell {
  date: string;
  value: number;
  completed?: boolean;
}

export interface PlaceholderField {
  status: 'coming_soon' | 'ready';
  value?: unknown;
  message?: string;
}

export interface KpiCard {
  id: string;
  title: string;
  value: number | string;
  unit?: string | null;
  subtitle?: string | null;
  trend?: number | null;
}

export interface AnalyticsOverview {
  life_score: number;
  todays_tasks: number;
  completed_tasks: number;
  goal_progress: number;
  habit_score: number;
  focus_time_hours: number;
  focus_time_label: string;
  journal_streak: number;
  mood_score: number | null;
  upcoming_events: Array<Record<string, unknown>>;
  recent_activity: Array<Record<string, unknown>>;
  kpis: KpiCard[];
  range_days: number;
}

export interface ProductivityAnalytics {
  daily_tasks: TimeSeries;
  weekly_tasks: TimeSeries;
  monthly_tasks: TimeSeries;
  task_completion: SeriesPoint[];
  overdue_tasks: number;
  focus_hours: number;
  deep_work_hours: number;
  focus_label: string;
  category_distribution: SeriesPoint[];
  calendar_heatmap: HeatmapCell[];
  range_days: number;
}

export interface GoalItemAnalytics {
  id: string;
  title: string;
  progress: number;
  status: string;
  remaining_tasks: number;
  milestones_total: number;
  milestones_done: number;
  velocity: number;
  burndown: SeriesPoint[];
  completion_forecast: PlaceholderField;
  risk_indicator: PlaceholderField;
}

export interface GoalAnalytics {
  goals: GoalItemAnalytics[];
  avg_progress: number;
  avg_velocity: number;
  range_days: number;
}

export interface HabitItemAnalytics {
  id: string;
  name: string;
  current_streak: number;
  longest_streak: number;
  consistency_pct: number;
  weekly_completion: number;
  monthly_completion: number;
}

export interface HabitAnalytics {
  habits: HabitItemAnalytics[];
  current_streak_max: number;
  longest_streak_max: number;
  consistency_avg: number;
  weekly_completion_avg: number;
  monthly_completion_avg: number;
  heatmap: HeatmapCell[];
  best_habit: string | null;
  worst_habit: string | null;
  range_days: number;
}

export interface JournalAnalytics {
  mood_trend: TimeSeries[];
  journal_frequency: TimeSeries;
  word_count_total: number;
  word_count_series: TimeSeries;
  writing_streak: number;
  sentiment: PlaceholderField;
  emotion: PlaceholderField;
  range_days: number;
}

export interface AiInsightBlock {
  period: 'daily' | 'weekly' | 'monthly' | 'predictions';
  status: 'coming_soon' | 'ready';
  title: string;
  items: string[];
  message: string;
}

export interface AiInsightsResponse {
  daily: AiInsightBlock;
  weekly: AiInsightBlock;
  monthly: AiInsightBlock;
  predictions: AiInsightBlock;
}

export interface WidgetDescriptor {
  id: string;
  title: string;
  icon: string;
  type: 'kpi' | 'chart' | 'list' | 'placeholder';
  endpoint: string;
  refresh_interval: number;
  component: string;
}

export type AnalyticsTab = 'overview' | 'productivity' | 'goals' | 'habits' | 'journal' | 'ai';
