import React from "react";
import { Sparkles, Cpu, Layers, ScanText, Code2, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { OcrEngine } from "@/lib/types";

interface EngineOption {
  value: OcrEngine;
  label: string;
  subLabel: string;
  cost: string;
  icon: React.ElementType;
}

const ENGINES: EngineOption[] = [
  {
    value: "paddleocr",
    label: "PaddleOCR",
    subLabel: "PP-OCRv4 Fast CPU",
    cost: "$0.0002/pg",
    icon: Sparkles,
  },
  {
    value: "pytesseract",
    label: "PyTesseract",
    subLabel: "Tesseract v5.3 CPU",
    cost: "$0.0001/pg",
    icon: Cpu,
  },
  {
    value: "docling",
    label: "Docling",
    subLabel: "Deep Layout Engine",
    cost: "$0.0005/pg",
    icon: Layers,
  },
  {
    value: "qwen-vl",
    label: "Qwen3-VL",
    subLabel: "Vision AI Multimodal",
    cost: "$0.0030/pg",
    icon: ScanText,
  },
];

export function EngineSelect({
  value,
  onChange,
  disabled,
}: {
  value: OcrEngine;
  onChange: (e: OcrEngine) => void;
  disabled?: boolean;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {ENGINES.map((eng) => {
        const Icon = eng.icon;
        const selected = value === eng.value;
        return (
          <button
            key={eng.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(eng.value)}
            className={cn(
              "relative flex flex-col items-start gap-1 rounded-xl border p-2.5 text-left transition-all",
              "hover:border-sky-500/50 hover:bg-sky-500/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              selected
                ? "border-sky-500 bg-sky-500/10 ring-1 ring-sky-500 shadow-xs"
                : "bg-card/60 text-muted-foreground border-border/70",
              disabled && "pointer-events-none opacity-50"
            )}
          >
            <div className="flex w-full items-center justify-between gap-1">
              <Icon
                className={cn(
                  "size-4 shrink-0",
                  selected ? "text-sky-400" : "text-muted-foreground"
                )}
              />
              {selected ? (
                <div className="flex size-4 items-center justify-center rounded-full bg-sky-500 text-sky-950 font-bold">
                  <Check className="size-2.5" />
                </div>
              ) : (
                <span className="text-[10px] font-mono text-muted-foreground/80">
                  {eng.cost}
                </span>
              )}
            </div>

            <div className="mt-1">
              <div
                className={cn(
                  "text-xs font-semibold leading-tight truncate",
                  selected ? "text-foreground" : "text-muted-foreground"
                )}
              >
                {eng.label}
              </div>
              <div className="text-[10px] text-muted-foreground/70 truncate mt-0.5">
                {eng.subLabel}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
