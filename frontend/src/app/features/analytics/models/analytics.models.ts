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
  finance_net?: number;
  modules?: AnalyticsModuleCount[];
}

export interface AnalyticsCharts {
  tasks_by_status?: AnalyticsChartPoint[];
  expenses_by_category?: AnalyticsChartPoint[];
  learning_by_type?: AnalyticsChartPoint[];
}
