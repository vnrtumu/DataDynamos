import { useState } from "react";
import { CornerDownRight, CheckCircle2, Download, Loader2 } from "lucide-react";
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
import { buildFieldTree, displayValue, type FieldLeaf } from "@/lib/fields";
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
  editedValue,
  onEdit,
}: {
  leaf: FieldLeaf;
  onHover: (path: string | null) => void;
  indent?: boolean;
  editedValue?: any;
  onEdit?: (path: string, val: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const valToDisplay = editedValue !== undefined ? editedValue : leaf.fv.value;
  const [valInput, setValInput] = useState(String(valToDisplay ?? ""));

  const dot = alignmentDot(leaf.fv.grounding);
  const groundable =
    leaf.fv.grounding?.alignment &&
    leaf.fv.grounding.alignment !== "ungrounded";

  const originalValStr = String(leaf.fv.value ?? "").trim();

  const handleSave = () => {
    if (onEdit) {
      if (valInput.trim() === originalValStr) {
        onEdit(leaf.path, undefined as any);
      } else {
        onEdit(leaf.path, valInput.trim());
      }
    }
    setIsEditing(false);
  };

  return (
    <div
      onMouseEnter={() => onHover(leaf.path)}
      onMouseLeave={() => onHover(null)}
      className={cn(
        "group flex items-center justify-between gap-2 rounded-md px-2 py-1 text-xs transition-colors",
        groundable ? "cursor-pointer hover:bg-brand/5" : "hover:bg-muted/40",
      )}
    >
      <div className="flex min-w-0 max-w-[220px] items-center gap-1.5 shrink-0">
        {indent && (
          <CornerDownRight className="size-3 text-muted-foreground/40 shrink-0" />
        )}
        <span
          className={cn("size-1.5 rounded-full shrink-0", dot.cls)}
          title={dot.title}
        />
        <span
          className="font-mono text-[11px] text-muted-foreground truncate max-w-[180px]"
          title={leaf.label}
        >
          {leaf.label}
        </span>
      </div>
      <div className="flex min-w-0 flex-1 items-center justify-end gap-2 overflow-hidden">
        {isEditing ? (
          <div className="flex items-center gap-1 w-full max-w-[280px]">
            <input
              type="text"
              value={valInput}
              onChange={(e) => setValInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              className="h-6 w-full rounded border bg-background px-1.5 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-sky-500"
              autoFocus
            />
            <button
              type="button"
              onClick={handleSave}
              className="rounded bg-sky-500 px-1.5 py-0.5 text-[10px] font-bold text-white hover:bg-sky-400 shrink-0"
            >
              Save
            </button>
          </div>
        ) : (
          <div
            onClick={() => setIsEditing(true)}
            className="flex min-w-0 max-w-[260px] items-center gap-1.5 cursor-pointer rounded px-1 py-0.5 hover:bg-sky-500/10 transition-colors overflow-hidden"
            title={String(valToDisplay ?? "")}
          >
            <span
              className={cn(
                "font-medium truncate text-right text-xs",
                editedValue !== undefined ? "text-sky-400 font-bold" : "text-foreground"
              )}
            >
              {displayValue(valToDisplay)}
            </span>
            <span className="text-[10px] text-muted-foreground/60 group-hover:text-sky-400 shrink-0">✏️</span>
          </div>
        )}
        <ConfidencePill value={leaf.fv.confidence} />
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
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [editedFields, setEditedFields] = useState<Record<string, any>>({});
  const [operatorNotes, setOperatorNotes] = useState("");

  const handleFieldEdit = (path: string, val: string | undefined) => {
    setEditedFields((prev) => {
      const next = { ...prev };
      if (val === undefined) {
        delete next[path];
      } else {
        next[path] = val;
      }
      return next;
    });
    setSubmitted(false);
  };

  const handleExportJson = () => {
    const mergedFields = { ...result.fields, ...editedFields };
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(mergedFields, null, 2));
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
      const mergedFields = { ...result.fields, ...editedFields };
      const res = await submitHitlFeedback(result.document_id, {
        corrections: mergedFields,
        notes: operatorNotes || "Operator verified and corrected structured fields in Stage 7 HITL Queue",
      });
      setSubmitted(true);
      toast.success("Stage 7 HITL Feedback & Learning Rule Saved!", {
        description: res.message || "Operator guidance stored in feedback memory.",
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
      <div className="flex flex-col gap-2 rounded-lg border border-purple-500/30 bg-purple-500/5 p-3 text-xs">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-purple-400 font-semibold">
            <span>Stage 7 HITL Queue: Interactive Operator Review & Learning Loop</span>
          </div>
          <button
            type="button"
            disabled={submitting || submitted}
            onClick={handleSubmitFeedback}
            className={cn(
              "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold text-white transition-all shadow-xs cursor-pointer shrink-0",
              submitted
                ? "bg-emerald-600 hover:bg-emerald-600 cursor-default"
                : "bg-purple-600 hover:bg-purple-500 active:scale-95",
              submitting && "opacity-75 pointer-events-none"
            )}
          >
            {submitting ? (
              <>
                <Loader2 className="size-3.5 animate-spin" />
                Updating Learning Memory…
              </>
            ) : submitted ? (
              <>
                <CheckCircle2 className="size-3.5" />
                Rule Memory Updated
              </>
            ) : (
              "Submit HITL Feedback & Update Learning Memory"
            )}
          </button>
        </div>

        {/* Operator Guidance & Learning Note Input */}
        <input
          type="text"
          value={operatorNotes}
          onChange={(e) => setOperatorNotes(e.target.value)}
          placeholder="Type operator correction guidance notes (e.g. 'Insured ID Box 1a corrected to 933299471')…"
          className="w-full rounded-md border border-purple-500/30 bg-card px-2.5 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-purple-500"
        />
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
                  editedValue={editedFields[node.path]}
                  onEdit={handleFieldEdit}
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
                      indent
                      editedValue={editedFields[c.path]}
                      onEdit={handleFieldEdit}
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
                          editedValue={editedFields[leaf.path]}
                          onEdit={handleFieldEdit}
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
      </div>
    </div>
  );
}
