import React, { useState, useEffect } from "react";
import { CornerDownRight, Pencil, Check, X, Sparkles, CheckCircle2, Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
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
import { buildFieldTree, displayValue, isFieldValue, type FieldLeaf } from "@/lib/fields";
import type { Alignment, Grounding, StructuredResult } from "@/lib/types";
import { CostSummaryCard } from "@/components/CostSummaryCard";
import { submitHitlFeedback } from "@/lib/api";

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

function ConfidencePill({ value, isEdited }: { value: number; isEdited?: boolean }) {
  if (isEdited) {
    return (
      <span className="rounded-full bg-emerald-500/20 px-1.5 py-0.5 font-mono text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
        100% (Human Corrected)
      </span>
    );
  }
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
  onUpdateValue,
  indent,
}: {
  leaf: FieldLeaf;
  onHover: (path: string | null) => void;
  onUpdateValue: (path: string, newValue: string) => void;
  indent?: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState<string>(
    leaf.fv.value === null || leaf.fv.value === undefined ? "" : String(leaf.fv.value)
  );

  useEffect(() => {
    setEditValue(leaf.fv.value === null || leaf.fv.value === undefined ? "" : String(leaf.fv.value));
  }, [leaf.fv.value]);

  const dot = alignmentDot(leaf.fv.grounding);
  const groundable =
    leaf.fv.grounding?.alignment &&
    leaf.fv.grounding.alignment !== "ungrounded";

  const handleSave = () => {
    onUpdateValue(leaf.path, editValue);
    setIsEditing(false);
  };

  const isEdited = Boolean((leaf.fv as Record<string, unknown>).isEdited);

  return (
    <div
      onMouseEnter={() => onHover(leaf.path)}
      onMouseLeave={() => onHover(null)}
      className={cn(
        "group flex items-center justify-between gap-3 rounded-lg px-3 py-2 transition-colors",
        groundable
          ? "cursor-pointer hover:bg-brand/[0.06]"
          : "hover:bg-muted/50",
        indent && "ml-4",
      )}
    >
      <div className="flex min-w-0 items-center gap-1.5">
        {indent && (
          <CornerDownRight className="size-3 text-muted-foreground/40 shrink-0" />
        )}
        <span className="text-sm text-muted-foreground">{leaf.label}</span>
      </div>

      <div className="flex items-center gap-2">
        {isEditing ? (
          <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSave();
                if (e.key === "Escape") setIsEditing(false);
              }}
              autoFocus
              className="h-7 min-w-[140px] rounded-md border border-purple-500 bg-background px-2 font-mono text-xs text-foreground shadow-2xs focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
            <button
              type="button"
              onClick={handleSave}
              className="rounded-md bg-emerald-500/20 p-1 text-emerald-400 hover:bg-emerald-500/30 transition-colors"
              title="Save updated value"
            >
              <Check className="size-3.5" />
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="rounded-md bg-muted p-1 text-muted-foreground hover:bg-muted/80 transition-colors"
              title="Cancel editing"
            >
              <X className="size-3.5" />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-1.5">
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditing(true);
                }}
                className={cn(
                  "truncate text-right font-mono text-sm cursor-pointer hover:underline hover:text-purple-400 transition-colors",
                  leaf.fv.value === null
                    ? "text-muted-foreground/60 italic"
                    : "text-foreground font-medium",
                )}
                title="Click to edit value"
              >
                {displayValue(leaf.fv.value)}
              </span>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditing(true);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
                title="Edit field value"
              >
                <Pencil className="size-3 text-purple-400" />
              </button>
            </div>

            {leaf.fv.value !== null && (
              <ConfidencePill value={leaf.fv.confidence} isEdited={isEdited} />
            )}
            <span
              className={cn("size-2 shrink-0 rounded-full", dot.cls)}
              title={dot.title}
            />
          </>
        )}
      </div>
    </div>
  );
}

function EditableTableCell({
  leaf,
  onUpdateValue,
}: {
  leaf: FieldLeaf;
  onUpdateValue: (path: string, newValue: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(
    leaf.fv.value === null || leaf.fv.value === undefined ? "" : String(leaf.fv.value)
  );

  const handleSave = () => {
    onUpdateValue(leaf.path, editValue);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-1">
        <input
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSave();
            if (e.key === "Escape") setIsEditing(false);
          }}
          autoFocus
          className="h-6 w-24 rounded border border-purple-500 bg-background px-1.5 font-mono text-xs"
        />
        <button
          type="button"
          onClick={handleSave}
          className="rounded bg-emerald-500/20 p-0.5 text-emerald-400"
        >
          <Check className="size-3" />
        </button>
      </div>
    );
  }

  return (
    <div
      onClick={() => setIsEditing(true)}
      className="group flex items-center justify-between gap-1 cursor-pointer hover:text-purple-400"
    >
      <span>{displayValue(leaf.fv.value)}</span>
      <Pencil className="size-2.5 opacity-0 group-hover:opacity-100 text-purple-400" />
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
  const [fields, setFields] = useState<Record<string, unknown>>(result.fields);
  const [modifiedCount, setModifiedCount] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    setFields(result.fields);
    setModifiedCount(0);
  }, [result]);

  const handleUpdateValue = (path: string, newValue: string) => {
    setFields((prev) => {
      const next = JSON.parse(JSON.stringify(prev));
      const parts = path.split(".");
      let curr = next;
      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        if (/^\d+$/.test(part)) {
          curr = curr[Number(part)];
        } else {
          curr = curr[part];
        }
      }
      const lastKey = parts[parts.length - 1];
      const targetKey = /^\d+$/.test(lastKey) ? Number(lastKey) : lastKey;
      const targetNode = curr[targetKey];

      if (isFieldValue(targetNode)) {
        curr[targetKey] = {
          ...targetNode,
          value: newValue,
          confidence: 1.0,
          isEdited: true,
        };
      } else if (typeof targetNode === "object" && targetNode !== null && "value" in targetNode) {
        curr[targetKey] = {
          ...targetNode,
          value: newValue,
          confidence: 1.0,
          isEdited: true,
        };
      } else {
        curr[targetKey] = {
          value: newValue,
          confidence: 1.0,
          grounding: null,
          isEdited: true,
        };
      }
      return next;
    });

    setModifiedCount((c) => c + 1);
    toast.info(`Updated field value for "${path}"`, {
      description: `New value: "${newValue}" (Confidence updated to 100% Human Corrected)`,
    });
  };

  const tree = buildFieldTree(fields);

  const handleExportJson = () => {
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(fields, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `extracted_claim_${result.document_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    toast.success("Structured fields exported as JSON!");
  };

  const handleSubmitFeedback = async () => {
    setSubmitting(true);
    try {
      const res = await submitHitlFeedback(result.document_id, {
        corrections: fields,
        notes: "User verified and updated structured fields in Stage 7 HITL Queue",
      });
      setSubmitted(true);
      toast.success("Stage 7 HITL Feedback Recorded!", {
        description: res.message || "LLM learning memory updated with human correction rules.",
      });
    } catch (e) {
      toast.error("Feedback Submission Failed", {
        description: e instanceof Error ? e.message : "Could not save HITL feedback.",
      });
    } finally {
      setSubmitting(false);
    }
  };

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
          {modifiedCount > 0 && (
            <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-400 font-mono">
              {modifiedCount} field{modifiedCount > 1 ? "s" : ""} updated
            </Badge>
          )}
          {result.fallback_used && (
            <Badge variant="outline" className="border-review/40 text-review-foreground">
              Table fallback
            </Badge>
          )}
          <Badge variant="outline">
            {formatPct(result.extraction_confidence)} confidence
          </Badge>
          <button
            type="button"
            onClick={handleExportJson}
            className="flex items-center gap-1.5 rounded-md border bg-card px-2.5 py-1 text-[11px] font-semibold text-foreground hover:bg-muted transition-colors cursor-pointer shadow-2xs"
            title="Download extracted fields as JSON"
          >
            <Download className="size-3.5 text-sky-400" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Cost & Accuracy Summary Card */}
      <CostSummaryCard cost={result.cost_summary ?? undefined} accuracy={result.accuracy_metrics ?? undefined} />

      {/* Stage 7 HITL Review & Learning Feedback Loop */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-purple-500/30 bg-purple-500/5 px-3 py-2 text-xs">
        <div className="flex items-center gap-1.5 text-purple-400 font-medium">
          <Sparkles className="size-4 text-purple-400" />
          <span>Stage 7 HITL Queue: Review & Feedback Feed</span>
          <span className="text-[11px] text-muted-foreground hidden sm:inline">(Click any field value to edit)</span>
        </div>
        <button
          type="button"
          disabled={submitting || submitted}
          onClick={handleSubmitFeedback}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold text-white transition-all shadow-xs cursor-pointer",
            submitted
              ? "bg-emerald-600 hover:bg-emerald-600 cursor-default"
              : "bg-purple-600 hover:bg-purple-500 active:scale-95",
            submitting && "opacity-75 pointer-events-none"
          )}
        >
          {submitting ? (
            <>
              <Loader2 className="size-3.5 animate-spin" />
              Recording Feedback…
            </>
          ) : submitted ? (
            <>
              <CheckCircle2 className="size-3.5" />
              HITL Memory Updated
            </>
          ) : (
            <>
              <CheckCircle2 className="size-3.5" />
              Submit HITL Feedback & Update Learning Memory
            </>
          )}
        </button>
      </div>

      <div className="rounded-xl border shadow-2xs">
        <div className="divide-y">
          {tree.map((node) => {
            if (node.kind === "leaf") {
              return (
                <Leaf
                  key={node.path}
                  leaf={node}
                  onHover={onHoverField}
                  onUpdateValue={handleUpdateValue}
                />
              );
            }
            if (node.kind === "object") {
              return (
                <div key={node.path} className="py-1">
                  <div className="px-3 pt-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    {node.label}
                  </div>
                  {node.children.map((c) => (
                    <Leaf
                      key={c.path}
                      leaf={c}
                      onHover={onHoverField}
                      onUpdateValue={handleUpdateValue}
                      indent
                    />
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
                          onUpdateValue={handleUpdateValue}
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
                              <EditableTableCell
                                leaf={leaf}
                                onUpdateValue={handleUpdateValue}
                              />
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
      </div>
    </div>
  );
}
