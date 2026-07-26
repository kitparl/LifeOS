export type TaskStatus =
  | 'pending'
  | 'in_progress'
  | 'hold'
  | 'delayed'
  | 'completed'
  | 'cancelled'
  | 'done';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TaskRecurrence = 'none' | 'daily' | 'weekly' | 'monthly';
export type TaskScope = 'owned' | 'assigned_to_me' | 'all';
export type AssignmentStatus =
  | 'pending'
  | 'accepted'
  | 'rejected'
  | 'cancelled'
  | 'reassigned'
  | 'completed';

export interface Subtask {
  id: string;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  completed_at: string | null;
  assigned_to?: string | null;
  assignment_status?: AssignmentStatus | null;
  assignee_username?: string | null;
}

export interface TaskPermissions {
  can_edit: boolean;
  can_assign: boolean;
  can_change_status: boolean;
  can_add_note: boolean;
  can_manage_watchers: boolean;
  can_manage_tags: boolean;
  can_archive: boolean;
  can_delete: boolean;
  role: string;
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
  archived_at?: string | null;
  version?: number;
  assigned_to?: string | null;
  assigned_by?: string | null;
  assignment_status?: AssignmentStatus | null;
  assignment_id?: string | null;
  accepted_at?: string | null;
  rejected_at?: string | null;
  assignee_username?: string | null;
  permissions?: TaskPermissions | null;
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
  goal_id?: string | null;
  subtask_count: number;
  completed_subtasks: number;
  assigned_to?: string | null;
  assignment_status?: AssignmentStatus | null;
  archived_at?: string | null;
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
  assignee_username?: string | null;
  assignee_user_id?: string | null;
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
  version?: number;
  status_reason?: string | null;
}

export interface TaskAssignment {
  id: string;
  task_id: string;
  assignee_user_id: string;
  assigned_by_user_id: string;
  status: AssignmentStatus;
  reason: string | null;
  assigned_at: string;
  accepted_at: string | null;
  rejected_at: string | null;
  cancelled_at: string | null;
  completed_at: string | null;
}

export interface ActivityLogEntry {
  id: string;
  task_id: string;
  actor_user_id: string;
  action: string;
  field: string | null;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export interface StatusHistoryEntry {
  id: string;
  task_id: string;
  from_status: string | null;
  to_status: string;
  changed_by_user_id: string;
  reason: string | null;
  created_at: string;
}

export interface TaskWatcher {
  id: string;
  task_id: string;
  user_id: string;
  username: string | null;
  display_name: string | null;
  created_at: string;
}

export interface TaskNote {
  id: string;
  task_id: string;
  author_user_id: string;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface TaskTag {
  id: string;
  name: string;
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
  { value: 'hold', label: 'Hold' },
  { value: 'delayed', label: 'Delayed' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];

export const TASK_RECURRENCE: { value: TaskRecurrence; label: string }[] = [
  { value: 'none', label: 'None' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];
