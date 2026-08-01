import { Table2, TriangleAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatMs, formatPct, confidenceTone } from "@/lib/format";
import type { OCRResult } from "@/lib/types";

// Shows the OCR text for the page currently selected in the left page viewer
// (SplitInspector's displayPage). Paging on the left swaps the text shown here.
export function OcrTextPanel({ ocr, page }: { ocr: OCRResult; page: number }) {
  const current = ocr.pages.find((p) => p.page === page);
  const multi = ocr.pages.length > 1;
  const tables = current?.tables ?? [];

  return (
    <div className="flex flex-col gap-3 h-[calc(100vh-10rem)]">
      <div className="flex flex-wrap items-center gap-2 shrink-0">
        <Badge variant="secondary" className="font-mono">
          {ocr.engine_name} {ocr.engine_version}
        </Badge>
        <Badge variant="outline" className="font-mono">
          {ocr.device}
        </Badge>
        <Badge variant="outline" className="font-mono">
          {formatMs(ocr.latency_ms)}
        </Badge>
        <Badge
          variant="outline"
          className={cn("font-mono", confidenceTone(ocr.avg_confidence))}
        >
          conf {formatPct(ocr.avg_confidence)}
        </Badge>
        {ocr.table_count > 0 && (
          <Badge variant="outline" className="gap-1">
            <Table2 className="size-3" />
            {ocr.table_count} table{ocr.table_count > 1 ? "s" : ""}
          </Badge>
        )}
        {multi && (
          <Badge variant="outline" className="font-mono">
            page {page}
          </Badge>
        )}
      </div>

      {ocr.warnings.length > 0 && (
        <div className="space-y-1 rounded-lg border border-review/40 bg-review-muted/30 p-3 text-xs text-review-foreground shrink-0">
          {ocr.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <TriangleAlert className="mt-0.5 size-3 shrink-0" />
              {w}
            </div>
          ))}
        </div>
      )}

      <div className="flex-1 min-h-0 overflow-y-auto rounded-xl border bg-muted/30 p-4 space-y-4">
        <pre className="font-mono text-xs leading-relaxed whitespace-pre-wrap text-foreground break-words">
          {current
            ? current.text || "(no text extracted on this page)"
            : `(Page ${page} is being scanned / pending OCR...)`}
        </pre>
        {tables.map((t, i) => (
          <div key={i} className="space-y-1.5 w-full">
            <p className="text-xs font-semibold text-sky-400">
              Table · {t.n_rows}×{t.n_cols}
            </p>
            <div className="w-full overflow-x-auto rounded-md border bg-card p-3">
              <pre className="font-mono text-[11px] leading-tight whitespace-pre text-foreground inline-block min-w-max">
                {t.markdown}
              </pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
