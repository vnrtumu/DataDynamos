import { Columns2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { formatMs, formatPct, confidenceTone } from "@/lib/format";
import type { OCRResult } from "@/lib/types";

function EngineColumn({ ocr, page }: { ocr: OCRResult; page: number }) {
  const current = ocr.pages.find((p) => p.page === page) ?? ocr.pages[0];
  const multi = ocr.pages.length > 1;
  return (
    <div className="flex min-w-0 flex-1 flex-col gap-2 rounded-xl border bg-card p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge className="bg-brand text-brand-foreground font-mono">
          {ocr.engine_name}
        </Badge>
        <Badge variant="outline" className="font-mono">
          {formatMs(ocr.latency_ms)}
        </Badge>
        <Badge
          variant="outline"
          className={cn("font-mono", confidenceTone(ocr.avg_confidence))}
        >
          {ocr.avg_confidence == null
            ? "no conf"
            : `conf ${formatPct(ocr.avg_confidence)}`}
        </Badge>
        <Badge variant="outline" className="font-mono">
          {ocr.table_count}T
        </Badge>
        {multi && current && (
          <Badge variant="outline" className="font-mono">
            p{current.page}/{ocr.pages.length}
          </Badge>
        )}
      </div>
      <ScrollArea className="h-[48vh] rounded-lg border bg-muted/30">
        <pre className="p-3 font-mono text-[11px] leading-relaxed whitespace-pre-wrap">
          {current?.text || "(no text)"}
        </pre>
      </ScrollArea>
    </div>
  );
}

export function EngineComparison({
  ocrByEngine,
  page,
  onRun,
  running,
}: {
  ocrByEngine: Record<string, OCRResult>;
  page: number;
  onRun: () => void;
  running: boolean;
}) {
  const engines = Object.keys(ocrByEngine);
  const ready = engines.length >= 2;

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Run both engines and compare the selected page's text, confidence, and
          latency side by side.
        </p>
        <Button size="sm" variant="outline" onClick={onRun} disabled={running}>
          {running ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Columns2 className="size-4" />
          )}
          {ready ? "Re-run both" : "Run both engines"}
        </Button>
      </div>
      {engines.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
          No OCR results yet.
        </div>
      ) : (
        <div className="flex flex-1 gap-3">
          {engines.map((e) => (
            <EngineColumn key={e} ocr={ocrByEngine[e]} page={page} />
          ))}
        </div>
      )}
    </div>
  );
}
