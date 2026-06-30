export type JournalType = 'morning' | 'night' | 'reflection' | 'gratitude';

export interface JournalEntry {
  id: string;
  entry_date: string;
  entry_type: JournalType;
  title: string | null;
  content: string;
  gratitude: string | null;
  wins: string | null;
  lessons: string | null;
  created_at: string;
  updated_at: string;
}

export interface JournalListItem {
  id: string;
  entry_date: string;
  entry_type: JournalType;
  title: string | null;
  content: string;
  updated_at: string;
}

export interface JournalCreate {
  entry_date: string;
  entry_type?: JournalType;
  title?: string | null;
  content?: string;
  gratitude?: string | null;
  wins?: string | null;
  lessons?: string | null;
}

export interface JournalUpdate {
  entry_date?: string;
  entry_type?: JournalType;
  title?: string | null;
  content?: string;
  gratitude?: string | null;
  wins?: string | null;
  lessons?: string | null;
}

export const JOURNAL_TYPES: { value: JournalType; label: string }[] = [
  { value: 'morning', label: 'Morning' },
  { value: 'night', label: 'Night' },
  { value: 'reflection', label: 'Reflection' },
  { value: 'gratitude', label: 'Gratitude' },
];
