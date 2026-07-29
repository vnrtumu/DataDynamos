// Hover-to-highlight: resolve a structured field path through grounding_map to the
// OCRBlock bbox(es) whose text overlaps the grounded snippet/offsets, so we can draw
// a box on the rasterized page image.
import type { Alignment, Grounding, OCRBlock, OCRResult } from "@/lib/types";

/** A rectangle in page-natural pixel space, top-left origin. */
export interface HighlightRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface FieldHighlight {
  page: number;
  rects: HighlightRect[];
  alignment: Alignment | null;
}

/** Whitespace/case-tolerant normalization for fuzzy containment matching. */
export function normalizeForMatch(s: string): string {
  return s
    .toLowerCase()
    .replace(/\s+/g, " ")
    .replace(/[^\w .,/$%@-]/g, "")
    .trim();
}

function rectFromBlock(b: OCRBlock): HighlightRect {
  const [x0, y0, x1, y1] = b.bbox;
  return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
}

/**
 * Blocks on the grounded page whose text overlaps the grounding. Primary match
 * is normalized snippet/text containment (a snippet may span several blocks);
 * the fallback walks blocks by accumulated text length to cover the char range.
 */
export function blocksForGrounding(g: Grounding, ocr: OCRResult): OCRBlock[] {
  if (g.page == null) return [];
  const page = ocr.pages.find((p) => p.page === g.page);
  if (!page) return [];

  // Primary: snippet-based containment.
  const snippet = g.snippet ? normalizeForMatch(g.snippet) : "";
  if (snippet.length >= 2) {
    const hits = page.blocks.filter((b) => {
      const t = normalizeForMatch(b.text);
      if (!t) return false;
      return t.includes(snippet) || snippet.includes(t);
    });
    if (hits.length) return hits;
  }

  // Fallback: walk blocks accumulating page-local char offsets and intersect
  // with [char_start, char_end). Offsets index OCRResult.full_text, so rebase
  // to this page by subtracting the page's start offset within full_text.
  if (g.char_start != null && g.char_end != null) {
    const pageStart = pageStartOffset(ocr, g.page);
    if (pageStart != null) {
      const localStart = g.char_start - pageStart;
      const localEnd = g.char_end - pageStart;
      const hits: OCRBlock[] = [];
      let cursor = 0;
      for (const b of page.blocks) {
        const bStart = cursor;
        const bEnd = cursor + b.text.length;
        if (bStart < localEnd && bEnd > localStart) hits.push(b);
        cursor = bEnd + 1; // blocks joined by a separator char
      }
      if (hits.length) return hits;
    }
  }
  return [];
}

/** Start offset of `page` within OCRResult.full_text ("\n\n".join of page texts). */
function pageStartOffset(ocr: OCRResult, page: number): number | null {
  let offset = 0;
  for (const p of ocr.pages) {
    if (p.page === page) return offset;
    offset += p.text.length + 2; // "\n\n" joiner
  }
  return null;
}

/** Resolve a field path to its source rectangles (in natural pixel space). */
export function rectsForField(
  fieldPath: string,
  groundingMap: Record<string, Grounding>,
  ocr: OCRResult | null,
): FieldHighlight | null {
  if (!ocr) return null;
  const g = groundingMap[fieldPath];
  if (!g || g.page == null || g.alignment === "ungrounded") return null;
  const blocks = blocksForGrounding(g, ocr);
  if (!blocks.length) return null;
  return {
    page: g.page,
    rects: blocks.map(rectFromBlock),
    alignment: g.alignment,
  };
}

/** Scale natural-pixel rects to the rendered <img> CSS size. */
export function scaleRects(
  rects: HighlightRect[],
  natural: { width: number; height: number },
  displayed: { width: number; height: number },
): HighlightRect[] {
  if (!natural.width || !natural.height) return [];
  const sx = displayed.width / natural.width;
  const sy = displayed.height / natural.height;
  return rects.map((r) => ({
    x: r.x * sx,
    y: r.y * sy,
    width: r.width * sx,
    height: r.height * sy,
  }));
}
