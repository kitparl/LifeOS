export type MarkdownEmphasis = 'bold' | 'italic';

export interface TextEdit {
  value: string;
  selectionStart: number;
  selectionEnd: number;
}

/** Marker length per emphasis: `**bold**`, `*italic*`, `***both***`. */
const MARKER_LENGTH: Record<MarkdownEmphasis, number> = { bold: 2, italic: 1 };

function countStars(text: string, from: number, step: 1 | -1): number {
  let count = 0;
  for (let i = from; i >= 0 && i < text.length && text[i] === '*'; i += step) count++;
  return count;
}

/**
 * Toggles Markdown bold/italic around the selection, like Cmd/Ctrl+B and Cmd/Ctrl+I
 * in a rich editor. The selection stays on the inner text so pressing the shortcut
 * again removes the markers.
 */
export function toggleMarkdownEmphasis(
  value: string,
  selectionStart: number,
  selectionEnd: number,
  emphasis: MarkdownEmphasis,
): TextEdit {
  const markerLength = MARKER_LENGTH[emphasis];
  const surrounding = Math.min(countStars(value, selectionStart - 1, -1), countStars(value, selectionEnd, 1));
  // 1 = italic, 2 = bold, 3 = both.
  const isActive = emphasis === 'bold' ? surrounding >= 2 : surrounding % 2 === 1;

  if (isActive) {
    return {
      value: value.slice(0, selectionStart - markerLength) + value.slice(selectionStart, selectionEnd) + value.slice(selectionEnd + markerLength),
      selectionStart: selectionStart - markerLength,
      selectionEnd: selectionEnd - markerLength,
    };
  }
  const marker = '*'.repeat(markerLength);
  return {
    value: value.slice(0, selectionStart) + marker + value.slice(selectionStart, selectionEnd) + marker + value.slice(selectionEnd),
    selectionStart: selectionStart + markerLength,
    selectionEnd: selectionEnd + markerLength,
  };
}
