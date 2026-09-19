export type VocabLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
export type VocabType = 'WORD' | 'PHRASAL_VERB' | 'COLLOCATION' | 'COMMON_EXPRESSION' | 'FUNCTIONAL_PHRASE';
export type SetType = 'daily' | 'manual';
export type SetStatus = 'active' | 'accepted';
export type DailyState = 'NO_ACTIVE_SET' | 'ACTIVE' | 'ACTIVE_NEXT_SET' | 'WAITING_FOR_NEXT_MIDNIGHT';

export interface VocabularyCard {
  id: string;
  term: string;
  type: VocabType;
  level: VocabLevel;
  part_of_speech: string;
  simple_meaning: string;
  example: string;
  pronunciation: string | null;
}

export interface VocabularySetItem {
  position: number;
  was_changed: boolean;
  vocabulary: VocabularyCard;
}

export interface VocabularySet {
  id: string;
  set_type: SetType;
  set_date: string;
  status: SetStatus;
  created_at: string;
  accepted_at: string | null;
  items: VocabularySetItem[];
}

export interface DailySetResponse {
  state: DailyState;
  current_set: VocabularySet | null;
  progress_count: number;
  progress_total: number;
  end_of_dataset: boolean;
}

export interface VocabularyDetail {
  id: string;
  term: string;
  type: VocabType;
  level: VocabLevel;
  part_of_speech: string;
  simple_meaning: string;
  meaning_in_context: string | null;
  example: string;
  example_context: string | null;
  usage_note: string | null;
  communication_intents: string[];
  topics: string[];
  common_collocations: string[];
  synonyms: string[];
  antonyms: string[];
  commonness: string;
  formality: string;
  pronunciation: string | null;
  learning_priority: string;
}

export interface VocabularyDetailResponse {
  vocabulary: VocabularyDetail;
  is_bookmarked: boolean;
  mastery_level: number;
  times_reviewed: number;
  example_count: number;
}

export interface BookmarkResponse {
  id: string;
  created_at: string;
  vocabulary: VocabularyCard;
}

export interface BookmarkPage {
  items: BookmarkResponse[];
  total: number;
}

export interface PersonalExample {
  id: string;
  vocabulary_id: string;
  sentence: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HistoryEntry {
  set_id: string;
  set_date: string;
  set_type: SetType;
  status: SetStatus;
  item_count: number;
  items: VocabularyCard[];
}

export interface HistoryPage {
  items: HistoryEntry[];
  total: number;
}

export interface VocabularyPage {
  items: VocabularyCard[];
  total: number;
}

export interface VocabularyProgress {
  vocabulary_learned: number;
  total_available_vocabulary: number;
  current_level: string | null;
  todays_progress_count: number;
  todays_progress_total: number;
  bookmarks_count: number;
  needs_revision_count: number;
  current_streak_days: number;
}

export interface SearchFilters {
  q?: string;
  level?: VocabLevel;
  type?: VocabType;
  topic?: string;
}

export type GameType =
  | 'meaning_quiz'
  | 'synonym_quiz'
  | 'antonym_quiz'
  | 'fill_in_blank'
  | 'example_completion'
  | 'word_matching'
  | 'meaning_matching';

export type GameSource = 'today' | 'specific_day' | 'all_learned' | 'bookmarked' | 'needs_revision' | 'level';

export interface GameVocabularyItem {
  id: string;
  term: string;
  type: VocabType;
  level: VocabLevel;
  part_of_speech: string;
  simple_meaning: string;
  example: string;
  synonyms: string[];
  antonyms: string[];
}

export interface GameVocabularyPage {
  items: GameVocabularyItem[];
  total: number;
}

export interface GameSessionResponse {
  id: string;
  game_type: string;
  source: string;
  total_questions: number;
  score: number;
  started_at: string;
  completed_at: string | null;
}

export interface GameAnswerResponse {
  id: string;
  is_correct: boolean;
  mastery_level: number;
}

export interface GameHistoryPage {
  items: GameSessionResponse[];
  total: number;
}
