export interface MoodEntry {
  id: string;
  log_date: string;
  stress: number;
  confidence: number;
  motivation: number;
  happiness: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface MoodUpsert {
  stress: number;
  confidence: number;
  motivation: number;
  happiness: number;
  notes?: string | null;
}

export interface MoodStats {
  days: number;
  avg_stress: number;
  avg_confidence: number;
  avg_motivation: number;
  avg_happiness: number;
  recent: MoodEntry[];
}

export const MOOD_METRICS = [
  { key: 'stress' as const, label: 'Stress', low: 'Low', high: 'High' },
  { key: 'confidence' as const, label: 'Confidence', low: 'Low', high: 'High' },
  { key: 'motivation' as const, label: 'Motivation', low: 'Low', high: 'High' },
  { key: 'happiness' as const, label: 'Happiness', low: 'Low', high: 'High' },
];
