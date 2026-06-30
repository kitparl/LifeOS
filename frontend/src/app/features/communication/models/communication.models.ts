export type WritingCategory = 'linkedin' | 'blog' | 'essay' | 'notes' | 'hr_answer' | 'technical_answer';
export type SpeakingCategory = 'hr' | 'technical' | 'elevator' | 'mock_interview';

export interface VocabularyWord {
  id: string;
  word: string;
  meaning: string;
  examples: string | null;
  pronunciation: string | null;
  synonyms: string | null;
  mastery: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface WritingPractice {
  id: string;
  title: string;
  content: string;
  category: WritingCategory;
  created_at: string;
  updated_at: string;
}

export interface SpeakingPractice {
  id: string;
  title: string;
  prompt: string;
  response: string | null;
  category: SpeakingCategory;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export const WRITING_CATEGORIES: { value: WritingCategory; label: string }[] = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'blog', label: 'Blog' },
  { value: 'essay', label: 'Essay' },
  { value: 'notes', label: 'Notes' },
  { value: 'hr_answer', label: 'HR Answer' },
  { value: 'technical_answer', label: 'Technical Answer' },
];

export const SPEAKING_CATEGORIES: { value: SpeakingCategory; label: string }[] = [
  { value: 'hr', label: 'HR' },
  { value: 'technical', label: 'Technical' },
  { value: 'elevator', label: 'Elevator Pitch' },
  { value: 'mock_interview', label: 'Mock Interview' },
];
