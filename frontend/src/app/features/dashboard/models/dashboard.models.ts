export type SyncStatus = 'synced' | 'syncing' | 'offline';

export interface TaskTodayItem {
  id: string;
  title: string;
  due_at: string | null;
  priority: string | null;
}

export interface HabitTodayItem {
  id: string;
  name: string;
  completed: boolean;
}

export interface GoalProgressItem {
  id: string;
  title: string;
  percent: number;
}

export interface RunningProgress {
  weekly_km: number;
  goal_km: number;
  last_run: string | null;
}

export interface CalendarPreviewItem {
  id: string;
  title: string;
  starts_at: string;
}

export interface NotificationItem {
  id: string;
  message: string;
  created_at: string;
}

export interface ActivityItem {
  type: string;
  label: string;
  at: string;
}

export interface QuickActionItem {
  id: string;
  label: string;
  route: string | null;
  enabled: boolean;
}

export interface DashboardSummary {
  sync_status: SyncStatus;
  pending_sync_count: number;
  tasks_today: TaskTodayItem[];
  habits_today: HabitTodayItem[];
  goals_progress: GoalProgressItem[];
  running_progress: RunningProgress | null;
  calendar_preview: CalendarPreviewItem[];
  notifications: NotificationItem[];
  recent_activity: ActivityItem[];
  quick_actions: QuickActionItem[];
}
