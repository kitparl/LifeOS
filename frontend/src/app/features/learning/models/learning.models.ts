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
  updated_at: string;
}
