/**
 * Collect File objects from a paste or drop event.
 * Browsers expose clipboard files when copying from Finder/Explorer or screenshots.
 */
export function filesFromClipboard(event: ClipboardEvent): File[] {
  const items = event.clipboardData?.items;
  if (!items?.length) return [];
  const files: File[] = [];
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item.kind !== 'file') continue;
    const file = item.getAsFile();
    if (file) files.push(file);
  }
  // Some browsers also put files on clipboardData.files
  if (!files.length && event.clipboardData?.files?.length) {
    return Array.from(event.clipboardData.files);
  }
  return files;
}

export function filesFromDataTransfer(dt: DataTransfer | null): File[] {
  if (!dt?.files?.length) return [];
  return Array.from(dt.files);
}

/** Match against an HTML accept attribute (e.g. "image/*,application/pdf"). Empty = allow all. */
export function fileMatchesAccept(file: File, accept: string): boolean {
  const rules = accept
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  if (!rules.length || rules.includes('*') || rules.includes('*/*')) return true;

  const type = (file.type || '').toLowerCase();
  const name = file.name.toLowerCase();

  return rules.some((rule) => {
    if (rule.endsWith('/*')) {
      const prefix = rule.slice(0, -1); // "image/"
      return type.startsWith(prefix);
    }
    if (rule.startsWith('.')) {
      return name.endsWith(rule);
    }
    return type === rule;
  });
}

export function filterAccepted(files: File[], accept: string): File[] {
  return files.filter((f) => fileMatchesAccept(f, accept));
}
