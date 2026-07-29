// Small display formatters shared across the UI.

/** 842 -> "842 ms", 1840 -> "1.84 s". */
export function formatMs(ms?: number): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

/** 0.873 -> "87%". null -> "—". */
export function formatPct(v?: number | null): string {
  if (v == null) return "—";
  return `${Math.round(v * 100)}%`;
}

/** ISO timestamp -> "May 31, 2026". Invalid/unparseable input -> "". */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Tailwind text color for a 0-1 confidence value. */
export function confidenceTone(v?: number | null): string {
  if (v == null) return "text-muted-foreground";
  if (v >= 0.8) return "text-approve";
  if (v >= 0.5) return "text-review";
  return "text-flag";
}
