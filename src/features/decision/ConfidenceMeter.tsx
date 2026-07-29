import { cn } from "@/lib/utils";
import { formatPct } from "@/lib/format";

export function ConfidenceMeter({
  value,
  tone,
}: {
  value: number;
  tone: "approve" | "flag" | "review";
}) {
  const pct = Math.round(value * 100);
  const bar =
    tone === "approve"
      ? "bg-approve"
      : tone === "flag"
        ? "bg-flag"
        : "bg-review";
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Confidence</span>
        <span className="font-mono font-medium">{formatPct(value)}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-all duration-700", bar)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
