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

const STAGE_ICON: Record<StageKey, typeof ScanLine> = {
  prescan: ScanLine,
  ocr: ScanText,
  structure: Sparkles,
  decide: Gavel,
};

function StatusGlyph({ status }: { status: StageStatus }) {
  if (status === "running") return <Loader2 className="size-4 animate-spin" />;
  if (status === "done") return <Check className="size-4" />;
  if (status === "error") return <X className="size-4" />;
  if (status === "blocked") return <MinusCircle className="size-4" />;
  return null;
}

export function Stepper() {
  const { perStageStatus, perStageTiming, runStage, document } =
    usePipelineContext();
  const anyRunning = Object.values(perStageStatus).some((s) => s === "running");

  return (
    <div className="flex items-stretch gap-2 overflow-x-auto">
      {STAGE_ORDER.map((stage, i) => {
        const status = perStageStatus[stage];
        const Icon = STAGE_ICON[stage];
        const timing = perStageTiming[stage];
        return (
          <div key={stage} className="flex flex-1 items-center gap-2">
            <div
              className={cn(
                "flex flex-1 items-center gap-3 rounded-xl border px-4 py-3 transition-colors",
                status === "running" && "border-brand/40 bg-brand/5",
                status === "done" && "border-approve/30 bg-approve/[0.04]",
                status === "error" && "border-flag/40 bg-flag/[0.05]",
                (status === "idle" || status === "blocked") && "bg-card",
              )}
            >
              <div
                className={cn(
                  "flex size-9 shrink-0 items-center justify-center rounded-lg border",
                  status === "running" &&
                    "border-brand/50 bg-brand/10 text-brand",
                  status === "done" &&
                    "border-approve/40 bg-approve/10 text-approve",
                  status === "error" && "border-flag/50 bg-flag/10 text-flag",
                  (status === "idle" || status === "blocked") &&
                    "border-border bg-muted text-muted-foreground",
                )}
              >
                <Icon className="size-4" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-medium">
                    {STAGE_LABEL[stage]}
                  </span>
                  <span
                    className={cn(
                      status === "done" && "text-approve",
                      status === "error" && "text-flag",
                      status === "running" && "text-brand",
                      status === "blocked" && "text-muted-foreground",
                    )}
                  >
                    <StatusGlyph status={status} />
                  </span>
                </div>
                <span className="font-mono text-xs text-muted-foreground">
                  {status === "running"
                    ? "running…"
                    : status === "done"
                      ? formatMs(timing)
                      : status === "blocked"
                        ? "skipped"
                        : status === "error"
                          ? "failed"
                          : "—"}
                </span>
              </div>
              {document &&
                (status === "done" || status === "error") &&
                !anyRunning && (
                  <button
                    onClick={() => runStage(stage)}
                    title={`Re-run ${STAGE_LABEL[stage]}`}
                    className="ml-auto flex size-7 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    <RotateCw className="size-3.5" />
                  </button>
                )}
            </div>
            {i < STAGE_ORDER.length - 1 && (
              <div
                className={cn(
                  "h-px w-3 shrink-0 sm:w-5",
                  perStageStatus[STAGE_ORDER[i + 1]] !== "idle"
                    ? "bg-brand/40"
                    : "bg-border",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
