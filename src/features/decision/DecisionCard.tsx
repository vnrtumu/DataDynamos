import { CheckCircle2, Flag, HelpCircle } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { formatMs } from "@/lib/format";
import { ConfidenceMeter } from "@/features/decision/ConfidenceMeter";
import { CheckTrace } from "@/features/decision/CheckTrace";
import type { Decision, DecisionResult } from "@/lib/types";

const DECISION_META: Record<
  Decision,
  {
    label: string;
    tone: "approve" | "flag" | "review";
    icon: typeof CheckCircle2;
  }
> = {
  approve: { label: "Approve", tone: "approve", icon: CheckCircle2 },
  flag: { label: "Flag", tone: "flag", icon: Flag },
  needs_review: { label: "Needs review", tone: "review", icon: HelpCircle },
};

const TONE_BG: Record<string, string> = {
  approve: "border-approve/40 bg-approve/[0.06]",
  flag: "border-flag/40 bg-flag/[0.06]",
  review: "border-review/40 bg-review-muted/40",
};

const TONE_BADGE: Record<string, string> = {
  approve: "bg-approve text-approve-foreground",
  flag: "bg-flag text-flag-foreground",
  review: "bg-review text-review-foreground",
};

export function DecisionCard({ decision }: { decision: DecisionResult }) {
  const meta = DECISION_META[decision.decision];
  const Icon = meta.icon;
  const overridden =
    decision.llm_decision != null &&
    decision.llm_decision !== decision.decision;

  return (
    <div className="space-y-5">
      <div
        className={cn("space-y-4 rounded-2xl border p-5", TONE_BG[meta.tone])}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex size-12 items-center justify-center rounded-xl",
              TONE_BADGE[meta.tone],
            )}
          >
            <Icon className="size-6" />
          </div>
          <div>
            <div className="text-2xl font-semibold tracking-tight">
              {meta.label}
            </div>
            <div className="font-mono text-xs text-muted-foreground">
              {decision.provider} · {decision.model} ·{" "}
              {formatMs(decision.latency_ms)}
            </div>
          </div>
        </div>

        <ConfidenceMeter value={decision.confidence} tone={meta.tone} />

        {overridden && (
          <p className="rounded-lg border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
            Code reconciliation overrode the model (it proposed{" "}
            <span className="font-medium">{decision.llm_decision}</span>) — a
            hard rule cannot be overruled, only explained.
          </p>
        )}

        {decision.reasons.length > 0 && (
          <ul className="space-y-1.5">
            {decision.reasons.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span
                  className={cn(
                    "mt-1.5 size-1.5 shrink-0 rounded-full",
                    TONE_BADGE[meta.tone],
                  )}
                />
                <span className="text-foreground/90">{r}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Rule checks
        </h3>
        <CheckTrace checks={decision.checks} />
      </div>

      {decision.citations.length > 0 && (
        <div className="space-y-2">
          <Separator />
          <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Citations
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {decision.citations.map((c) => (
              <span
                key={c.field}
                className="rounded-md border bg-muted/40 px-2 py-1 font-mono text-xs"
              >
                {c.field}{" "}
                <span className="text-muted-foreground">· {c.source}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
