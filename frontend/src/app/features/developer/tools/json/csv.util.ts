function parseCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',') {
      row.push(field);
      field = '';
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(field);
      field = '';
      rows.push(row);
      row = [];
    } else {
      field += ch;
    }
  }
  if (field !== '' || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows.filter((r) => !(r.length === 1 && r[0] === ''));
}

export function csvToJson(csv: string): unknown[] {
  const rows = parseCsvRows(csv);
  if (rows.length === 0) return [];
  const [header, ...dataRows] = rows;
  if (header.some((h) => h.trim() === '')) {
    throw new Error('CSV header row has an empty column name.');
  }
  return dataRows
    .filter((row) => row.some((cell) => cell !== ''))
    .map((row) => {
      const obj: Record<string, string> = {};
      header.forEach((h, i) => {
        obj[h] = row[i] ?? '';
      });
      return obj;
    });
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) return '"' + value.replace(/"/g, '""') + '"';
  return value;
}

export function jsonToCsv(json: unknown): string {
  const arr = Array.isArray(json) ? json : [json];
  if (arr.length === 0) return '';
  if (!arr.every((item) => item !== null && typeof item === 'object' && !Array.isArray(item))) {
    throw new Error('JSON → CSV expects an array of flat objects (or a single object).');
  }
  const headerSet = new Set<string>();
  arr.forEach((item) => Object.keys(item as object).forEach((k) => headerSet.add(k)));
  const headers = Array.from(headerSet);
  const lines = [headers.map(csvEscape).join(',')];
  for (const item of arr) {
    const record = item as Record<string, unknown>;
    lines.push(headers.map((h) => csvEscape(record[h] === undefined || record[h] === null ? '' : String(record[h]))).join(','));
  }
  return lines.join('\n');
}
