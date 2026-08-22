export interface QAVersion {
  id: string;
  version_number: number;
  answer: string;
  created_at: string;
}

export interface QAListItem {
  id: string;
  question: string;
  current_answer: string | null;
  type: string | null;
  tags: string[];
  is_deep_personal: boolean;
  created_at: string;
  updated_at: string;
}

export interface QAEntry {
  id: string;
  question: string;
  current_answer: string;
  type: string | null;
  tags: string[];
  is_deep_personal: boolean;
  linked_goal_id: string | null;
  linked_journal_id: string | null;
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
  versions: QAVersion[];
}

export interface QAListResult {
  items: QAListItem[];
  total: number;
}

export type QAViewMode = 'all' | 'month' | 'deep';
export type QASortBy = 'created_at' | 'updated_at';

export interface QAListOptions {
  search?: string;
  type?: string;
  tag?: string;
  deep_personal?: boolean;
  sort_by?: QASortBy;
  limit?: number;
  offset?: number;
  include_answer?: boolean;
}
