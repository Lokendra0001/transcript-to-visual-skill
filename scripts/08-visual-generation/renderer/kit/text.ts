// Text measurement for Step 08 compositions, using the browser's own font engine
// (run only inside the renderer page).
let ctx: CanvasRenderingContext2D | null = null;

/** Width in px of `text` drawn with a CSS font shorthand, e.g. "800 22px Inter". */
export function textWidth(text: string, font: string): number {
  ctx ??= document.createElement('canvas').getContext('2d');
  if (!ctx) throw new Error('canvas 2d context unavailable');
  ctx.font = font;
  return ctx.measureText(text).width;
}

/** Greedy word wrap. Throws when one word alone is wider than maxWidth, so overflow is never hidden. */
export function wrapText(text: string, font: string, maxWidth: number): string[] {
  const lines: string[] = [];
  let line = '';
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const next = line ? `${line} ${word}` : word;
    if (textWidth(next, font) <= maxWidth) { line = next; continue; }
    if (!line) throw new Error(`word wider than ${maxWidth}px: "${word}"`);
    lines.push(line);
    line = word;
    if (textWidth(word, font) > maxWidth) throw new Error(`word wider than ${maxWidth}px: "${word}"`);
  }
  if (line) lines.push(line);
  return lines;
}
