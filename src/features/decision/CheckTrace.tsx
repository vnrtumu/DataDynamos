import { Check, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Check as CheckType, Severity } from "@/lib/types";

const SEVERITY_STYLE: Record<Severity, string> = {
  hard: "border-flag/50 text-flag",
  review: "border-review/50 text-review-foreground",
  advisory: "border-border text-muted-foreground",
};

export function CheckTrace({ checks }: { checks: CheckType[] }) {
  if (checks.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No rule checks recorded.</p>
    );
  }
  return (
    <ul className="space-y-1.5">
      {checks.map((c) => (
        <li
          key={c.name}
          className={cn(
            "flex items-start gap-3 rounded-lg border px-3 py-2",
            c.passed
              ? "border-border bg-card"
              : "border-flag/30 bg-flag/[0.04]",
          )}
        >
          <span
            className={cn(
              "mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full",
              c.passed ? "bg-approve/15 text-approve" : "bg-flag/15 text-flag",
            )}
          >
            {c.passed ? <Check className="size-3" /> : <X className="size-3" />}
          </span>
          <div className="min-w-0 flex-1 space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-medium">{c.name}</span>
              <Badge
                variant="outline"
                className={cn("text-[10px]", SEVERITY_STYLE[c.severity])}
              >
                {c.severity}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">{c.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
