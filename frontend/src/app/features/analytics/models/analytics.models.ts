export interface AnalyticsChartPoint {
  label: string;
  value: number;
}

export interface AnalyticsModuleCount {
  module: string;
  count: number;
}

export interface AnalyticsSummary {
  tasks_completed?: number;
  habits_logged_30d?: number;
  runs_30d?: number;
  journal_entries_30d?: number;
  learning_in_progress?: number;
  /** Still returned by the API; deliberately not surfaced as a metric. */
  finance_net?: number;
  modules?: AnalyticsModuleCount[];
}

export interface AnalyticsCharts {
  tasks_by_status?: AnalyticsChartPoint[];
  expenses_by_category?: AnalyticsChartPoint[];
  learning_by_type?: AnalyticsChartPoint[];
}
