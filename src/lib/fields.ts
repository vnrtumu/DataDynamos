// Flatten a StructuredResult.fields dict into a renderable tree whose node paths
// mirror the backend's grounding_map dotted-path scheme (e.g. "line_items.0.amount"),
// so hovering a node emits a path that resolves in grounding_map.
import type { FieldValue } from "@/lib/types";

export interface FieldLeaf {
  kind: "leaf";
  path: string;
  label: string;
  fv: FieldValue;
}

export interface FieldList {
  kind: "list";
  path: string;
  label: string;
  variant: "scalars" | "objects";
  columns: string[]; // object keys (objects variant) or [] (scalars)
  rows: FieldLeaf[][]; // scalars: one leaf per row; objects: one leaf per column
}

export interface FieldObject {
  kind: "object";
  path: string;
  label: string;
  children: FieldLeaf[];
}

export type FieldNode = FieldLeaf | FieldList | FieldObject;

export function isFieldValue(x: unknown): x is FieldValue {
  return (
    typeof x === "object" &&
    x !== null &&
    "value" in x &&
    "confidence" in x &&
    "grounding" in x
  );
}

/** "invoice_no" -> "Invoice No", "po_number" -> "Po Number". */
export function humanize(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function leaf(path: string, label: string, fv: FieldValue): FieldLeaf {
  return { kind: "leaf", path, label, fv };
}

function childPath(prefix: string, key: string | number): string {
  return prefix ? `${prefix}.${key}` : String(key);
}

export function buildFieldTree(fields: Record<string, unknown>): FieldNode[] {
  const nodes: FieldNode[] = [];
  for (const [key, value] of Object.entries(fields)) {
    const path = key;
    const label = humanize(key);

    if (isFieldValue(value)) {
      nodes.push(leaf(path, label, value));
      continue;
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        // Show empty arrays as a list node with no rows (renders "—").
        nodes.push({
          kind: "list",
          path,
          label,
          variant: "scalars",
          columns: [],
          rows: [],
        });
        continue;
      }
      const first = value[0];
      if (isFieldValue(first)) {
        const rows = value.map((item, i) =>
          isFieldValue(item)
            ? [leaf(childPath(path, i), `${label} ${i + 1}`, item)]
            : [],
        );
        nodes.push({
          kind: "list",
          path,
          label,
          variant: "scalars",
          columns: [],
          rows,
        });
      } else if (typeof first === "object" && first !== null) {
        const columns = Object.keys(first as Record<string, unknown>);
        const rows = value.map((item, i) =>
          columns.map((col) => {
            const cell = (item as Record<string, unknown>)[col];
            return leaf(
              childPath(childPath(path, i), col),
              humanize(col),
              isFieldValue(cell)
                ? cell
                : {
                    value: cell as FieldValue["value"],
                    confidence: 0,
                    grounding: null,
                  },
            );
          }),
        );
        nodes.push({
          kind: "list",
          path,
          label,
          variant: "objects",
          columns,
          rows,
        });
      }
      continue;
    }

    if (typeof value === "object" && value !== null) {
      const children: FieldLeaf[] = [];
      for (const [ck, cv] of Object.entries(value as Record<string, unknown>)) {
        if (isFieldValue(cv)) {
          children.push(leaf(childPath(path, ck), humanize(ck), cv));
        }
      }
      nodes.push({ kind: "object", path, label, children });
    }
  }
  return nodes;
}

/** Display string for a FieldValue.value (null -> em dash). */
export function displayValue(v: FieldValue["value"]): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  return String(v);
}
