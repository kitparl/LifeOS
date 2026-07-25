export type GoalCategory =
  | 'career'
  | 'running'
  | 'finance'
  | 'learning'
  | 'personal'
  | 'health';

export type GoalStatus = 'active' | 'archived' | 'completed';

export type GoalPeriod = 'weekly' | 'monthly' | 'yearly' | 'custom';

export interface Milestone {
  id: string;
  title: string;
  completed: boolean;
  sort_order: number;
  created_at: string;
  completed_at: string | null;
}

export interface Goal {
  id: string;
  title: string;
  description: string | null;
  category: GoalCategory;
  status: GoalStatus;
  period: GoalPeriod;
  progress: number;
  notes: string | null;
  target_date: string | null;
  period_start: string | null;
  period_end: string | null;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  milestones: Milestone[];
  is_missed?: boolean;
}

export interface GoalListItem {
  id: string;
  title: string;
  category: GoalCategory;
  status: GoalStatus;
  period: GoalPeriod;
  progress: number;
  target_date: string | null;
  period_start?: string | null;
  period_end?: string | null;
  updated_at: string;
  milestone_count: number;
  completed_milestones: number;
  is_missed?: boolean;
}

export interface GoalCreate {
  title: string;
  description?: string | null;
  category: GoalCategory;
  period?: GoalPeriod;
  progress?: number;
  notes?: string | null;
  target_date?: string | null;
  period_start?: string | null;
  period_end?: string | null;
}

export interface GoalUpdate {
  title?: string;
  description?: string | null;
  category?: GoalCategory;
  status?: GoalStatus;
  period?: GoalPeriod;
  progress?: number;
  notes?: string | null;
  target_date?: string | null;
  period_start?: string | null;
  period_end?: string | null;
}

export const GOAL_CATEGORIES: { value: GoalCategory; label: string }[] = [
  { value: 'career', label: 'Career' },
  { value: 'running', label: 'Running' },
  { value: 'finance', label: 'Finance' },
  { value: 'learning', label: 'Learning' },
  { value: 'personal', label: 'Personal' },
  { value: 'health', label: 'Health' },
];

export const GOAL_PERIODS: { value: GoalPeriod; label: string }[] = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'custom', label: 'Custom' },
];
