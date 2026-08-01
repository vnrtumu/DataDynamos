import React from "react";
import {
  Check,
  Loader2,
  MinusCircle,
  RotateCw,
  ScanLine,
  ScanText,
  Sparkles,
  Gavel,
  X,
  Cpu,
  Bot,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatMs } from "@/lib/format";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import {
  STAGE_LABEL,
  STAGE_ORDER,
  type StageKey,
  type StageStatus,
} from "@/features/pipeline/usePipeline";
import type { OcrEngine } from "@/lib/types";

const STAGE_ICON: Record<StageKey, React.ElementType> = {
  prescan: ScanLine,
  ocr: ScanText,
  structure: Sparkles,
  decide: Gavel,
};

function engineDisplayName(engine: OcrEngine): string {
  switch (engine) {
    case "paddleocr":
      return "PaddleOCR (PP-OCRv4)";
    case "pytesseract":
      return "PyTesseract (v5.3 CPU)";
    case "docling":
      return "Docling (Deep Layout)";
    case "qwen-vl":
      return "Qwen3-VL (Vision AI)";
    default:
      return engine;
  }
}

function StatusGlyph({ status }: { status: StageStatus }) {
  if (status === "running") return <Loader2 className="size-4 animate-spin" />;
  if (status === "done") return <Check className="size-4" />;
  if (status === "error") return <X className="size-4" />;
  if (status === "blocked") return <MinusCircle className="size-4" />;
  return null;
}

export function Stepper() {
  const {
    perStageStatus,
    perStageTiming,
    runStage,
    document,
    activeEngine,
    ocr,
    structure,
    decision,
  } = usePipelineContext();
  const anyRunning = Object.values(perStageStatus).some((s) => s === "running");

  return (
    <div className="w-full space-y-2">
      {/* Active Pipeline Configuration Summary Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-muted/30 px-3.5 py-1.5 text-xs text-muted-foreground">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1 font-semibold text-foreground">
            <Cpu className="size-3.5 text-sky-400" />
            Active OCR Engine:
            <span className="font-mono text-sky-400 font-bold ml-1">
              {ocr?.engine_name ? engineDisplayName(ocr.engine_name as OcrEngine) : engineDisplayName(activeEngine)}
            </span>
          </span>
          <span className="text-muted-foreground/40">•</span>
          <span className="flex items-center gap-1 font-semibold text-foreground">
            <Sparkles className="size-3.5 text-purple-400" />
            Structuring Model:
            <span className="font-mono text-purple-400 font-bold ml-1">
              {structure?.model ? structure.model : "LangExtract (DeepSeek-v4)"}
            </span>
          </span>
          <span className="text-muted-foreground/40">•</span>
          <span className="flex items-center gap-1 font-semibold text-foreground">
            <Bot className="size-3.5 text-emerald-400" />
            Decision Engine:
            <span className="font-mono text-emerald-400 font-bold ml-1">
              {decision?.model ? decision.model : "NPI & ICD-10 Rule Agent"}
            </span>
          </span>
        </div>

        {document?.doc_type && (
          <div className="flex items-center gap-1">
            <ShieldCheck className="size-3.5 text-emerald-400" />
            <span className="font-mono text-[11px] uppercase bg-card px-2 py-0.5 rounded border text-foreground font-semibold">
              {document.doc_type}
            </span>
          </div>
        )}
      </div>

      {/* Stage Cards Flow */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {STAGE_ORDER.map((stage) => {
          const status = perStageStatus[stage];
          const Icon = STAGE_ICON[stage];
          const timing = perStageTiming[stage];

          let engineSpec = "";
          if (stage === "prescan") {
            engineSpec = "OpenCV Deskew & Quality";
          } else if (stage === "ocr") {
            engineSpec = ocr?.engine_name
              ? engineDisplayName(ocr.engine_name as OcrEngine)
              : engineDisplayName(activeEngine);
          } else if (stage === "structure") {
            engineSpec = structure?.model ? `LangExtract (${structure.model})` : "LangExtract Schema Extractor";
          } else if (stage === "decide") {
            engineSpec = decision?.model ? `Rule Agent (${decision.model})` : "NPI & ICD-10 Rule Guardrails";
          }

          return (
            <div
              key={stage}
              className={cn(
                "relative flex flex-col justify-between gap-2 rounded-xl border p-3.5 transition-all shadow-2xs",
                status === "running" && "border-sky-500/50 bg-sky-500/5 ring-1 ring-sky-500/30",
                status === "done" && "border-emerald-500/40 bg-emerald-500/[0.04]",
                status === "error" && "border-rose-500/50 bg-rose-500/[0.05]",
                (status === "idle" || status === "blocked") && "bg-card/70 border-border/70 text-muted-foreground"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <div
                    className={cn(
                      "flex size-9 shrink-0 items-center justify-center rounded-lg border",
                      status === "running" && "border-sky-500/50 bg-sky-500/10 text-sky-400",
                      status === "done" && "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
                      status === "error" && "border-rose-500/50 bg-rose-500/10 text-rose-400",
                      (status === "idle" || status === "blocked") && "border-border bg-muted/50 text-muted-foreground"
                    )}
                  >
                    <Icon className="size-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-foreground">
                        {STAGE_LABEL[stage]}
                      </span>
                      <span
                        className={cn(
                          status === "done" && "text-emerald-400",
                          status === "error" && "text-rose-400",
                          status === "running" && "text-sky-400",
                          status === "blocked" && "text-muted-foreground"
                        )}
                      >
                        <StatusGlyph status={status} />
                      </span>
                    </div>
                    <div className="text-[10px] font-mono text-muted-foreground">
                      {status === "running"
                        ? "processing…"
                        : status === "done"
                        ? formatMs(timing)
                        : status === "blocked"
                        ? "skipped"
                        : status === "error"
                        ? "failed"
                        : "ready"}
                    </div>
                  </div>
                </div>

                {document && (status === "done" || status === "error") && !anyRunning && (
                  <button
                    onClick={() => runStage(stage)}
                    title={`Re-run ${STAGE_LABEL[stage]}`}
                    className="flex size-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    <RotateCw className="size-3" />
                  </button>
                )}
              </div>

              {/* Active Engine / Model Sub-Badge */}
              <div className="mt-1 rounded-md border bg-muted/40 px-2 py-1 text-[11px] font-medium flex items-center justify-between">
                <span className="truncate text-muted-foreground">{engineSpec}</span>
                {status === "done" && (
                  <span className="text-[10px] text-emerald-400 font-semibold shrink-0 ml-1">
                    PASS
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
