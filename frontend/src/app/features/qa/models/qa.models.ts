export interface QAVersion {
  id: string;
  version_number: number;
  answer: string;
  created_at: string;
}

export interface QAListItem {
  id: string;
  question: string;
  current_answer: string;
  tags: string[];
  updated_at: string;
}

export interface QAEntry {
  id: string;
  question: string;
  current_answer: string;
  tags: string[];
  linked_goal_id: string | null;
  linked_journal_id: string | null;
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
  versions: QAVersion[];
}
