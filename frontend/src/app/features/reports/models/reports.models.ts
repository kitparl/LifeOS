export interface ReportSection {
  title: string;
  body: string;
}

export interface PeriodReport {
  sections?: ReportSection[];
  ai_summary?: string | null;
}

export interface ReviewResponse {
  content?: string;
}
