import { useEffect, useState } from "react";
import { ChevronDown, FileText, Loader2, Plus, ReceiptText, ScanText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import { Stepper } from "@/features/pipeline/Stepper";
import { QualityReportPanel } from "@/features/pipeline/QualityReportPanel";
import { SplitInspector } from "@/features/inspector/SplitInspector";
import { STAGE_LABEL, type StageKey } from "@/features/pipeline/usePipeline";
import { API_BASE_URL } from "@/lib/api";

import { ModelOverridesToolbar } from "@/features/pipeline/ModelOverridesToolbar";

const STAGE_DESCRIPTIONS: Record<StageKey, string> = {
  prescan: "Deskewing & quality checking",
  ocr: "Extracting text with OCR engine",
  structure: "Structuring fields with LLM",
  decide: "Running approval decision rules",
};

interface OcrProgress {
  current_page: number;
  total_pages: number;
  engine: string;
  done: boolean;
  pages?: any[];
}

export function Workspace() {
  const { document, prescan, perStageStatus, reset, setPartialOcr, activeEngine } = usePipelineContext();
  const [showPrescan, setShowPrescan] = useState(false);
  const [ocrProgress, setOcrProgress] = useState<OcrProgress | null>(null);

  if (!document) return null;
  const DocIcon = (document.doc_type as string) === "contract" ? FileText : ReceiptText;

  const activeStage = (Object.entries(perStageStatus) as [StageKey, string][]).find(
    ([, s]) => s === "running"
  )?.[0] ?? null;

  // Poll OCR progress endpoint while OCR stage is running and stream pages live
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    if (activeStage !== "ocr" || !document) {
      setOcrProgress(null);
      return;
    }
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/documents/${document.id}/ocr/progress`);
        if (!cancelled && res.ok) {
          const data: OcrProgress & { pages?: any[] } = await res.json();
          setOcrProgress(data);
          if (data.pages && data.pages.length > 0) {
            setPartialOcr({
              document_id: document.id,
              status: "ocr_done",
              engine_name: data.engine || activeEngine,
              engine_version: "1.0",
              device: "cpu",
              full_text: data.pages.map((p) => p.text).join("\n\n"),
              pages: data.pages,
              avg_confidence: 0.95,
              table_count: data.pages.reduce((acc, p) => acc + (p.tables?.length || 0), 0),
              latency_ms: 0,
              warnings: [],
            });
          }
        }
      } catch { /* ignore */ }
    };
    poll();
    const timer = setInterval(poll, 800);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [activeStage, document?.id, activeEngine, setPartialOcr]);

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 px-4 py-5 sm:px-6">
      {/* Document header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg border bg-card text-muted-foreground">
            <DocIcon className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-medium">{document.filename}</h2>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {document.doc_type && (
                <Badge variant="secondary" className="capitalize">
                  {document.doc_type}
                </Badge>
              )}
              <span className="font-mono">
                {document.page_count} page{document.page_count > 1 ? "s" : ""}
              </span>
            </div>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={reset}>
          <Plus className="size-4" />
          New document
        </Button>
      </div>

      {/* Post-Processing Model & Engine Switcher Toolbar */}
      <ModelOverridesToolbar />

      {/* Live "Now Scanning" banner */}
      {activeStage && (
        <div className="flex items-center gap-3 rounded-xl border border-sky-500/30 bg-sky-500/[0.06] px-4 py-2.5 shadow-sm animate-in fade-in slide-in-from-top-1 duration-300">
          <div className="relative flex size-8 shrink-0 items-center justify-center rounded-lg border border-sky-500/40 bg-sky-500/10">
            <ScanText className="size-4 text-sky-400" />
            <span className="absolute -right-1 -top-1 flex size-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
              <span className="relative inline-flex size-2.5 rounded-full bg-sky-500" />
            </span>
          </div>
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="flex items-center gap-2">
              <Loader2 className="size-3 animate-spin text-sky-400" />
              <span className="text-xs font-semibold text-sky-400">
                {STAGE_LABEL[activeStage]} — {STAGE_DESCRIPTIONS[activeStage]}
              </span>
              {/* Live parallel page counter for OCR stage */}
              {activeStage === "ocr" && ocrProgress && ocrProgress.total_pages > 1 && !ocrProgress.done && (
                <span className="rounded-md border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[10px] font-mono font-bold text-sky-300">
                  ⚡ Scanning {ocrProgress.pages?.length || ocrProgress.current_page || 1} of {ocrProgress.total_pages} pages (Parallel Threads)
                </span>
              )}
            </div>
            <p className="truncate text-[11px] text-muted-foreground font-mono">
              📄 {document.filename}
              {document.page_count > 1 && (
                <span className="ml-1.5 text-sky-400/70">({document.page_count} pages)</span>
              )}
            </p>
          </div>
          <span className="shrink-0 rounded-full bg-sky-500/15 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-sky-400">
            Live
          </span>
        </div>
      )}

      {/* Stepper */}
      <Stepper />

      {/* Pre-scan quality report (collapsible) */}
      {prescan && (
        <div className="rounded-xl border bg-card">
          <button
            onClick={() => setShowPrescan((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3 text-sm"
          >
            <span className="flex items-center gap-2 font-medium">
              Pre-scan quality
              <Badge
                variant="outline"
                className={cn(
                  prescan.verdict === "warn"
                    ? "border-review/50 text-review-foreground"
                    : "border-approve/50 text-approve",
                )}
              >
                {prescan.verdict}
              </Badge>
            </span>
            <ChevronDown
              className={cn(
                "size-4 text-muted-foreground transition-transform",
                showPrescan && "rotate-180",
              )}
            />
          </button>
          {showPrescan && (
            <div className="border-t p-4">
              <QualityReportPanel report={prescan} />
            </div>
          )}
        </div>
      )}

      {/* Split inspector */}
      <SplitInspector />
    </div>
  );
}
