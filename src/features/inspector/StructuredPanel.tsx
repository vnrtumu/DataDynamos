import { CornerDownRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { formatPct } from "@/lib/format";
import { buildFieldTree, displayValue, type FieldLeaf } from "@/lib/fields";
import type { Alignment, Grounding, StructuredResult } from "@/lib/types";
import { CostSummaryCard } from "@/components/CostSummaryCard";

function alignmentDot(grounding: Grounding | null | undefined): {
  cls: string;
  title: string;
} {
  const a: Alignment | null | undefined = grounding?.alignment;
  if (a === "exact") return { cls: "bg-approve", title: "exact source match" };
  if (a === "partial")
    return { cls: "bg-review", title: "partial source match" };
  return { cls: "bg-muted-foreground/30", title: "no source location" };
}

function ConfidencePill({ value }: { value: number }) {
  return (
    <span
      className={cn(
        "rounded-full px-1.5 py-0.5 font-mono text-[10px] font-medium",
        value >= 0.8
          ? "bg-approve/10 text-approve"
          : value >= 0.5
            ? "bg-review-muted text-review-foreground"
            : "bg-flag/10 text-flag",
      )}
    >
      {formatPct(value)}
    </span>
  );
}

function Leaf({
  leaf,
  onHover,
  indent,
}: {
  leaf: FieldLeaf;
  onHover: (path: string | null) => void;
  indent?: boolean;
}) {
  const dot = alignmentDot(leaf.fv.grounding);
  const groundable =
    leaf.fv.grounding?.alignment &&
    leaf.fv.grounding.alignment !== "ungrounded";
  return (
    <div
      onMouseEnter={() => onHover(leaf.path)}
      onMouseLeave={() => onHover(null)}
      className={cn(
        "flex items-center justify-between gap-3 rounded-lg px-3 py-2 transition-colors",
        groundable
          ? "cursor-pointer hover:bg-brand/[0.06]"
          : "hover:bg-muted/50",
        indent && "ml-4",
      )}
    >
      <div className="flex min-w-0 items-center gap-2">
        {indent && (
          <CornerDownRight className="size-3 shrink-0 text-muted-foreground/50" />
        )}
        <span className="text-sm text-muted-foreground">{leaf.label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "truncate text-right font-mono text-sm",
            leaf.fv.value === null
              ? "text-muted-foreground/60 italic"
              : "text-foreground",
          )}
        >
          {displayValue(leaf.fv.value)}
        </span>
        {leaf.fv.value !== null && (
          <ConfidencePill value={leaf.fv.confidence} />
        )}
        <span
          className={cn("size-2 shrink-0 rounded-full", dot.cls)}
          title={dot.title}
        />
      </div>
    </div>
  );
}

export function StructuredPanel({
  result,
  onHoverField,
}: {
  result: StructuredResult;
  onHoverField: (path: string | null) => void;
}) {
  const tree = buildFieldTree(result.fields);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-medium text-muted-foreground">Provider:</span>
          <span className="font-mono">{result.provider}</span>
          <span className="text-muted-foreground">•</span>
          <span className="font-medium text-muted-foreground">Model:</span>
          <span className="font-mono">{result.model}</span>
        </div>
        <div className="flex items-center gap-2">
          {result.fallback_used && (
            <Badge variant="outline" className="border-review/40 text-review-foreground">
              Table fallback
            </Badge>
          )}
          <Badge variant="outline">
            {formatPct(result.extraction_confidence)} confidence
          </Badge>
        </div>
      </div>

      {/* Cost & Accuracy Summary Card */}
      <CostSummaryCard cost={result.cost_summary ?? undefined} accuracy={result.accuracy_metrics ?? undefined} />

      {/* Stage 7 HITL Review & Learning Feedback Loop */}
      <div className="flex items-center justify-between gap-2 rounded-lg border border-purple-500/30 bg-purple-500/5 px-3 py-2 text-xs">
        <div className="flex items-center gap-1.5 text-purple-400 font-medium">
          <span>Stage 7 HITL Queue: Review & Feedback Feed</span>
        </div>
        <button
          type="button"
          onClick={async () => {
            try {
              const res = await fetch(`/documents/${result.document_id}/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  corrections: result.fields,
                  notes: "User verified structured fields in Stage 7 HITL Queue",
                }),
              });
              if (res.ok) {
                alert("Stage 7 HITL Feedback Saved! LLM learning memory updated with correction rules for future documents.");
              }
            } catch (e) {
              console.error(e);
            }
          }}
          className="rounded-md bg-purple-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-purple-500 transition-colors shadow-xs"
        >
          Submit HITL Feedback & Update Learning Memory
        </button>
      </div>

      <ScrollArea className="flex-1 rounded-xl border">
        <div className="divide-y">
          {tree.map((node) => {
            if (node.kind === "leaf") {
              return (
                <Leaf key={node.path} leaf={node} onHover={onHoverField} />
              );
            }
            if (node.kind === "object") {
              return (
                <div key={node.path} className="py-1">
                  <div className="px-3 pt-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    {node.label}
                  </div>
                  {node.children.map((c) => (
                    <Leaf key={c.path} leaf={c} onHover={onHoverField} indent />
                  ))}
                </div>
              );
            }
            // list
            return (
              <div key={node.path} className="space-y-2 px-3 py-3">
                <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  {node.label}
                </div>
                {node.rows.length === 0 ? (
                  <p className="text-sm text-muted-foreground/60 italic">—</p>
                ) : node.variant === "scalars" ? (
                  <div className="space-y-0.5">
                    {node.rows.map((row) =>
                      row.map((leaf) => (
                        <Leaf
                          key={leaf.path}
                          leaf={leaf}
                          onHover={onHoverField}
                        />
                      )),
                    )}
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {node.columns.map((c) => (
                          <TableHead key={c} className="text-xs">
                            {c}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {node.rows.map((row, ri) => (
                        <TableRow
                          key={ri}
                          onMouseEnter={() =>
                            row[0] && onHoverField(row[0].path)
                          }
                          onMouseLeave={() => onHoverField(null)}
                          className="cursor-pointer"
                        >
                          {row.map((leaf) => (
                            <TableCell
                              key={leaf.path}
                              className="font-mono text-xs"
                            >
                              {displayValue(leaf.fv.value)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
