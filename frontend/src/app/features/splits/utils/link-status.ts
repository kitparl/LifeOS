import { SplitGroupView } from '../models/split.models';

/** "5h 12m left", "Link ended" or "Link expired" — for the group header. */
export function linkStatusLabel(group: Pick<SplitGroupView, 'is_open' | 'ended_at' | 'expires_at'>, now: number): string {
  if (group.ended_at) return 'Link ended';
  const remainingMs = new Date(group.expires_at).getTime() - now;
  if (!group.is_open || remainingMs <= 0) return 'Link expired';
  const totalMinutes = Math.max(1, Math.floor(remainingMs / 60_000));
  const days = Math.floor(totalMinutes / (24 * 60));
  const hours = Math.floor((totalMinutes % (24 * 60)) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `${days}d ${hours}h left`;
  if (hours > 0) return `${hours}h ${minutes}m left`;
  return `${minutes}m left`;
}
