import { ItineraryDay } from '../models/travel.models';

/**
 * The full `{day_id: [item_id, ...]}` layout after moving one item — what the backend's batched
 * reorder endpoint expects (one request per drag; it rejects lost or duplicated items).
 */
export function moveItem(
  days: readonly ItineraryDay[],
  from: { dayId: string; index: number },
  to: { dayId: string; index: number },
): Record<string, string[]> {
  const layout: Record<string, string[]> = {};
  for (const day of days) layout[day.id] = day.items.map((i) => i.id);
  const source = layout[from.dayId];
  const target = layout[to.dayId];
  if (!source || !target || from.index < 0 || from.index >= source.length) return layout;
  const [moved] = source.splice(from.index, 1);
  target.splice(Math.min(Math.max(to.index, 0), target.length), 0, moved);
  return layout;
}
