export const LEARNING_TYPES = [
  { value: 'book', label: 'Book' },
  { value: 'course', label: 'Course' },
  { value: 'video', label: 'Video' },
  { value: 'coding', label: 'Coding' },
  { value: 'interview_prep', label: 'Interview prep' },
  { value: 'study_plan', label: 'Study plan' },
] as const;

export type LearningType = (typeof LEARNING_TYPES)[number]['value'];

export interface LearningItem {
  id: string;
  item_type: LearningType;
  title: string;
  provider: string | null;
  url: string | null;
  status: string;
  progress: number;
  target_date: string | null;
  notes: string | null;
  track_id?: string | null;
  sort_order?: number;
  slug?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LearningListItem {
  id: string;
  item_type: LearningType;
  title: string;
  provider: string | null;
  status: string;
  progress: number;
  target_date: string | null;
  track_id?: string | null;
  sort_order?: number;
  updated_at: string;
}

export interface LearningResource {
  id: string;
  item_id: string | null;
  concept_id: string | null;
  resource_type: string;
  title: string;
  url: string;
  provider: string | null;
  author: string | null;
  duration_minutes: number | null;
  priority: string;
  sort_order: number;
  is_consumed: boolean;
  notes: string | null;
  last_verified_at: string | null;
}

export interface LearningConcept {
  id: string;
  item_id: string;
  slug: string;
  title: string;
  summary: string | null;
  week_number: number | null;
  estimated_minutes: number | null;
  sort_order: number;
  confidence: number;
  can_explain: boolean;
  failure_modes_known: boolean;
  tradeoffs_known: boolean;
  artifact_url: string | null;
  completed_at: string | null;
  resources?: LearningResource[];
  inherited_resources?: LearningResource[];
}

export interface ConceptNote {
  id: string;
  concept_id: string;
  section_id: string;
  section_title: string;
  snippet: string;
  chapter_id: string;
  chapter_title: string;
  subject_id: string;
  subject_title: string;
  route: string;
  updated_at: string;
}

export interface ConceptNoteCreate {
  section_id?: string | null;
  subject_id?: string | null;
  subject_title?: string | null;
  chapter_id?: string | null;
  chapter_title?: string | null;
  title?: string | null;
  content?: string;
}

export interface LearningPhase {
  id: string;
  track_id: string | null;
  slug: string | null;
  item_type: string;
  title: string;
  status: string;
  progress: number;
  sort_order: number;
  concepts: LearningConcept[];
  resources?: LearningResource[];
}

export interface LearningTrack {
  id: string;
  slug: string;
  title: string;
  description: string | null;
  status: string;
  start_date: string | null;
  target_date: string | null;
  weekly_hours_target: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
  phases?: LearningPhase[];
}

export interface TrackProgress {
  track_id: string;
  percent_complete: number;
  concepts_total: number;
  concepts_gated: number;
  hours_logged: number;
  weekly_hours_target: number;
  pace_hours_this_week: number;
  study_streak_days: number;
}

export interface StudySession {
  id: string;
  item_id: string;
  concept_id: string | null;
  session_date: string;
  minutes: number;
  confidence: number;
  can_explain: boolean;
  artifact_url: string | null;
  notes: string | null;
  created_at: string;
}

export interface SessionStats {
  minutes_this_week: number;
  minutes_total: number;
  concepts_gated: number;
  concepts_total: number;
  pace_vs_target_hours: number | null;
  study_streak_days: number;
}

export interface ConceptUpdate {
  confidence?: number;
  can_explain?: boolean;
  failure_modes_known?: boolean;
  tradeoffs_known?: boolean;
  artifact_url?: string | null;
  summary?: string | null;
}

export interface SessionCreate {
  item_id: string;
  concept_id?: string | null;
  session_date: string;
  minutes: number;
  confidence?: number;
  can_explain?: boolean;
  artifact_url?: string | null;
  notes?: string | null;
}
