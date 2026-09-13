export function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function isPastDate(dateStr: string): boolean {
  if (!dateStr) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const raceDate = new Date(`${dateStr}T00:00:00`);
  return raceDate < today;
}
