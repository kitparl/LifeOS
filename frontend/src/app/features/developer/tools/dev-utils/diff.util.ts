export interface DiffLine {
  type: 'added' | 'removed' | 'unchanged';
  text: string;
}

/** Classic LCS-based line diff. Fine for typical tool-sized inputs (not optimized for huge files). */
export function diffLines(a: string, b: string): DiffLine[] {
  const linesA = a.split('\n');
  const linesB = b.split('\n');
  const n = linesA.length;
  const m = linesB.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = linesA[i] === linesB[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const result: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (linesA[i] === linesB[j]) {
      result.push({ type: 'unchanged', text: linesA[i] });
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      result.push({ type: 'removed', text: linesA[i] });
      i++;
    } else {
      result.push({ type: 'added', text: linesB[j] });
      j++;
    }
  }
  while (i < n) {
    result.push({ type: 'removed', text: linesA[i] });
    i++;
  }
  while (j < m) {
    result.push({ type: 'added', text: linesB[j] });
    j++;
  }
  return result;
}

export interface DiffRow {
  type: 'added' | 'removed' | 'unchanged' | 'changed';
  left?: string;
  right?: string;
}

/** Post-processes a removed-line-immediately-followed-by-added-line into a single "changed" row. */
export function computeDiffRows(a: string, b: string): DiffRow[] {
  const lines = diffLines(a, b);
  const rows: DiffRow[] = [];
  let i = 0;
  while (i < lines.length) {
    const cur = lines[i];
    const next = lines[i + 1];
    if (cur.type === 'removed' && next && next.type === 'added') {
      rows.push({ type: 'changed', left: cur.text, right: next.text });
      i += 2;
      continue;
    }
    if (cur.type === 'removed') {
      rows.push({ type: 'removed', left: cur.text });
      i++;
      continue;
    }
    if (cur.type === 'added') {
      rows.push({ type: 'added', right: cur.text });
      i++;
      continue;
    }
    rows.push({ type: 'unchanged', left: cur.text, right: cur.text });
    i++;
  }
  return rows;
}

export function toUnifiedDiff(a: string, b: string): string {
  return diffLines(a, b)
    .map((l) => (l.type === 'added' ? `+ ${l.text}` : l.type === 'removed' ? `- ${l.text}` : `  ${l.text}`))
    .join('\n');
}
