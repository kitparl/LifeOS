import { ItineraryDay, ItineraryItem, Stop } from '../models/travel.models';

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

/** A day's first and last stop that has a place — only when the day has at least two such stops. */
export function dayEndpoints(day: ItineraryDay): { start: ItineraryItem; end: ItineraryItem } | null {
  const placed = day.items.filter((i) => i.place_id);
  return placed.length >= 2 ? { start: placed[0], end: placed[placed.length - 1] } : null;
}

/**
 * "Day N start" / "Day N end" labels per map stop index. Walks the items exactly like the backend's
 * `stop_sequence` (day order, then position; consecutive repeats of a place share one stop), so a loop
 * such as Kasol → Tosh → Kasol labels the right Kasol pin.
 */
export function stopDayLabels(days: readonly ItineraryDay[], stops: readonly Stop[]): Map<number, string[]> {
  const labels = new Map<number, string[]>();
  const add = (index: number, label: string) => labels.set(index, [...(labels.get(index) ?? []), label]);
  let current = -1;
  for (const day of days) {
    const ends = dayEndpoints(day);
    for (const item of day.items) {
      if (!item.place_id) continue;
      if (current < 0 || stops[current]?.place_id !== item.place_id) current++;
      if (current >= stops.length) return labels;
      if (item === ends?.start) add(current, `Day ${day.day_index + 1} start`);
      if (item === ends?.end) add(current, `Day ${day.day_index + 1} end`);
    }
  }
  return labels;
}
