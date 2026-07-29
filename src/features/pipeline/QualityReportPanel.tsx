import { CheckCircle2, TriangleAlert, RotateCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { fileUrl } from "@/lib/api";
import type { MetricResult, PageQuality, QualityReport } from "@/lib/types";

function MetricChip({
  label,
  metric,
  unit,
}: {
  label: string;
  metric: MetricResult;
  unit?: string;
}) {
  const warn = metric.verdict === "warn";
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "flex items-center justify-between gap-3 rounded-lg border px-3 py-2",
            warn
              ? "border-review/40 bg-review-muted/40"
              : "border-border bg-muted/30",
          )}
        >
          <span className="text-xs text-muted-foreground">{label}</span>
          <span
            className={cn(
              "font-mono text-sm font-medium",
              warn ? "text-review-foreground" : "text-foreground",
            )}
          >
            {Math.round(metric.value)}
            {unit}
          </span>
        </div>
      </TooltipTrigger>
      <TooltipContent>
        {metric.verdict === "warn" ? "Below threshold" : "OK"}
        {metric.threshold != null &&
          ` · threshold ${Math.round(metric.threshold)}${unit ?? ""}`}
      </TooltipContent>
    </Tooltip>
  );
}

function PageBlock({ page }: { page: PageQuality }) {
  return (
    <div className="space-y-3 rounded-xl border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Page {page.page}</span>
        <div className="flex items-center gap-2">
          {page.deskewed && (
            <Badge variant="secondary" className="gap-1">
              <RotateCcw className="size-3" />
              deskewed {page.skew_angle_deg.toFixed(1)}°
            </Badge>
          )}
          <Badge
            variant="outline"
            className={cn(
              page.verdict === "warn"
                ? "border-review/50 text-review-foreground"
                : "border-approve/50 text-approve",
            )}
          >
            {page.verdict}
          </Badge>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <MetricChip label="DPI" metric={page.resolution} />
        <MetricChip label="Sharpness" metric={page.sharpness} />
        <MetricChip label="Contrast" metric={page.contrast} />
        <MetricChip label="Brightness" metric={page.brightness} />
      </div>
      {page.reasons.length > 0 && (
        <ul className="space-y-1 text-xs text-muted-foreground">
          {page.reasons.map((r, i) => (
            <li key={i} className="flex items-start gap-1.5">
              <TriangleAlert className="mt-0.5 size-3 shrink-0 text-review" />
              {r}
            </li>
          ))}
        </ul>
      )}
      {(page.deskewed_url || page.gray_url || page.thresh_url) && (
        <div className="flex gap-2 pt-1">
          {[
            { url: page.image_url, label: "raw" },
            { url: page.deskewed_url, label: "deskewed" },
            { url: page.gray_url, label: "grayscale" },
            { url: page.thresh_url, label: "threshold" },
          ]
            .filter((v) => v.url)
            .map((v) => (
              <figure key={v.label} className="space-y-1">
                <img
                  src={fileUrl(v.url)}
                  alt={v.label}
                  className="h-20 w-auto rounded-md border object-contain"
                />
                <figcaption className="text-center text-[10px] text-muted-foreground">
                  {v.label}
                </figcaption>
              </figure>
            ))}
        </div>
      )}
    </div>
  );
}

export function QualityReportPanel({ report }: { report: QualityReport }) {
  const warn = report.verdict === "warn";
  return (
    <div className="space-y-4">
      <div
        className={cn(
          "flex items-start gap-3 rounded-xl border p-4",
          warn
            ? "border-review/40 bg-review-muted/40"
            : "border-approve/30 bg-approve/[0.04]",
        )}
      >
        {warn ? (
          <TriangleAlert className="mt-0.5 size-5 shrink-0 text-review" />
        ) : (
          <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-approve" />
        )}
        <div className="space-y-1">
          <p className="text-sm font-medium">
            {warn ? "Quality warnings — advisory" : "Quality looks good"}
          </p>
          <p className="text-xs text-muted-foreground">
            {report.reasons.length > 0
              ? report.reasons.join(" · ")
              : "All pages passed the pre-flight checks."}
          </p>
        </div>
      </div>
      <div className="space-y-3">
        {report.pages.map((p) => (
          <PageBlock key={p.page} page={p} />
        ))}
      </div>
    </div>
  );
}
