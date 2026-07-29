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
  structure,
  onHoverField,
}: {
  structure: StructuredResult;
  onHoverField: (path: string | null) => void;
}) {
  const tree = buildFieldTree(structure.fields);

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary" className="font-mono">
          {structure.provider} · {structure.model}
        </Badge>
        <Badge
          variant="outline"
          className={cn(
            "font-mono",
            structure.extraction_confidence >= 0.6
              ? "text-approve"
              : "text-review",
          )}
        >
          extraction {formatPct(structure.extraction_confidence)}
        </Badge>
        {structure.fallback_used && (
          <Badge variant="outline">table fallback</Badge>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Hover a field to highlight its source on the page. Dots:{" "}
        <span className="text-approve">exact</span> ·{" "}
        <span className="text-review">partial</span> ·{" "}
        <span className="text-muted-foreground">none</span>.
      </p>

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
