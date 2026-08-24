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

export interface WritingIssue {
  location: string;
  problem_type: string;
  severity: string;
  original_text: string;
  explanation: string;
  suggestion: string;
}

export interface WritingEvaluation {
  id: string;
  writing_id: string;
  evaluation_key: string;
  provider: string;
  model: string;
  model_version: string | null;
  prompt_version: string;
  rubric_version: string;
  evaluation_version: string;
  overall_score: number;
  dimensions: Record<string, number>;
  strengths: string[];
  issues: WritingIssue[];
  suggestions: string[];
  metrics: Record<string, number>;
  already_strong: boolean;
  truncated: boolean;
  truncation_note: string | null;
  cached: boolean;
  created_at: string;
}

export interface WritingRewrite {
  id: string;
  writing_id: string;
  rewrite_key: string;
  provider: string;
  model: string;
  prompt_version: string;
  suggested_text: string;
  why_better: string[];
  key_changes: string[];
  truncated: boolean;
  truncation_note: string | null;
  cached: boolean;
  created_at: string;
}

export const DIMENSION_LABELS: Record<string, string> = {
  grammar: 'Grammar',
  punctuation: 'Punctuation',
  spelling: 'Spelling',
  clarity: 'Clarity',
  readability: 'Readability',
  vocabulary: 'Vocabulary',
  sentenceVariety: 'Sentence Variety',
  coherence: 'Coherence',
  structure: 'Structure',
  conciseness: 'Conciseness',
  tone: 'Tone',
  intentAlignment: 'Intent Alignment',
  audienceAppropriateness: 'Audience Appropriateness',
};
