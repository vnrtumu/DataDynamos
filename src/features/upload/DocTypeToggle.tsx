import React from "react";
import {
  ShieldCheck,
  Layers,
  Building2,
  FileCode2,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { DocType } from "@/lib/types";

interface Option {
  value: DocType;
  label: string;
  badge: string;
  badgeClass: string;
  icon: React.ElementType;
}

const OPTIONS: Option[] = [
  {
    value: "cms1500",
    label: "CMS-1500 (Single)",
    badge: "Tier A",
    badgeClass: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    icon: ShieldCheck,
  },
  {
    value: "cms1500_multi",
    label: "CMS-1500 (Multi)",
    badge: "Tier B",
    badgeClass: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    icon: Layers,
  },
  {
    value: "ub04",
    label: "UB-04 Form",
    badge: "Tier C",
    badgeClass: "bg-purple-500/15 text-purple-400 border-purple-500/30",
    icon: Building2,
  },
  {
    value: "unstructured_claim",
    label: "Unstructured Claim",
    badge: "Tier D",
    badgeClass: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    icon: FileCode2,
  },
];

export function DocTypeToggle({
  value,
  onChange,
  disabled,
}: {
  value: DocType;
  onChange: (t: DocType) => void;
  disabled?: boolean;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {OPTIONS.map((opt) => {
        const Icon = opt.icon;
        const selected = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(opt.value)}
            className={cn(
              "relative flex flex-col items-start gap-1 rounded-xl border p-2.5 text-left transition-all",
              "hover:border-brand/50 hover:bg-brand/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              selected
                ? "border-brand bg-brand/10 ring-1 ring-brand shadow-xs"
                : "bg-card/60 text-muted-foreground border-border/70",
              disabled && "pointer-events-none opacity-50"
            )}
          >
            <div className="flex w-full items-center justify-between gap-1">
              <span
                className={cn(
                  "rounded-md border px-1.5 py-0.5 text-[10px] font-semibold tracking-wide uppercase",
                  opt.badgeClass
                )}
              >
                {opt.badge}
              </span>
              {selected && (
                <div className="flex size-4 items-center justify-center rounded-full bg-brand text-brand-foreground">
                  <Check className="size-2.5" />
                </div>
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Icon
                className={cn(
                  "size-4 shrink-0",
                  selected ? "text-brand" : "text-muted-foreground"
                )}
              />
              <span
                className={cn(
                  "text-xs font-medium leading-tight truncate",
                  selected ? "text-foreground font-semibold" : "text-muted-foreground"
                )}
              >
                {opt.label}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
