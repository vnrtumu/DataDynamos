import { Table2, TriangleAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { formatMs, formatPct, confidenceTone } from "@/lib/format";
import type { OCRResult } from "@/lib/types";

// Shows the OCR text for the page currently selected in the left page viewer
// (SplitInspector's displayPage). Paging on the left swaps the text shown here.
export function OcrTextPanel({ ocr, page }: { ocr: OCRResult; page: number }) {
  const current = ocr.pages.find((p) => p.page === page) ?? ocr.pages[0];
  const multi = ocr.pages.length > 1;
  const tables = current?.tables ?? [];

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
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
        {multi && current && (
          <Badge variant="outline" className="font-mono">
            page {current.page}/{ocr.pages.length}
          </Badge>
        )}
      </div>

      {ocr.warnings.length > 0 && (
        <div className="space-y-1 rounded-lg border border-review/40 bg-review-muted/30 p-3 text-xs text-review-foreground">
          {ocr.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <TriangleAlert className="mt-0.5 size-3 shrink-0" />
              {w}
            </div>
          ))}
        </div>
      )}

      <ScrollArea className="flex-1 rounded-xl border bg-muted/30">
        <div className="space-y-4 p-4">
          <pre className="font-mono text-xs leading-relaxed whitespace-pre-wrap text-foreground">
            {current?.text || "(no text extracted on this page)"}
          </pre>
          {tables.map((t, i) => (
            <div key={i} className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">
                Table · {t.n_rows}×{t.n_cols}
              </p>
              <pre className="overflow-x-auto rounded-md border bg-card p-3 font-mono text-xs">
                {t.markdown}
              </pre>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
