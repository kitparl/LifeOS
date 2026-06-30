export interface Notification {
  id: string;
  message: string;
  module: string | null;
  entity_id: string | null;
  route: string | null;
  is_read: boolean;
  channel: string;
  telegram_sent: boolean;
  created_at: string;
}

export interface NotificationSettings {
  telegram_chat_id: string | null;
  telegram_enabled: boolean;
}
