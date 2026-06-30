export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TaskRecurrence = 'none' | 'daily' | 'weekly' | 'monthly';

export interface Subtask {
  id: string;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  completed_at: string | null;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  category: string | null;
  tags: string[];
  due_date: string | null;
  parent_id: string | null;
  goal_id: string | null;
  recurrence: TaskRecurrence;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  subtasks: Subtask[];
}

export interface TaskListItem {
  id: string;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  category: string | null;
  tags: string[];
  due_date: string | null;
  updated_at: string;
  subtask_count: number;
  completed_subtasks: number;
}

export interface TaskCreate {
  title: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  category?: string | null;
  tags?: string[];
  due_date?: string | null;
  parent_id?: string | null;
  goal_id?: string | null;
  recurrence?: TaskRecurrence;
}

export interface TaskUpdate {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  category?: string | null;
  tags?: string[];
  due_date?: string | null;
  goal_id?: string | null;
  recurrence?: TaskRecurrence;
}

export const TASK_PRIORITIES: { value: TaskPriority; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
];

export const TASK_STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];

export const TASK_RECURRENCE: { value: TaskRecurrence; label: string }[] = [
  { value: 'none', label: 'None' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];
