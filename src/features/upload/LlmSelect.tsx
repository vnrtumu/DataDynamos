import React from "react";
import { Sparkles, Bot, Cpu, Zap, Check, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export type LlmModelOption =
  | "deepseek-v4"
  | "gpt-4o"
  | "claude-3.5-sonnet"
  | "qwen-2.5-72b"
  | "small-vision-vlm";

interface ModelConfig {
  value: LlmModelOption;
  label: string;
  subLabel: string;
  cost: string;
  icon: React.ElementType;
}

const LLM_MODELS: ModelConfig[] = [
  {
    value: "deepseek-v4",
    label: "DeepSeek-v4 Flash",
    subLabel: "LangExtract Default",
    cost: "$0.00005/pg",
    icon: Sparkles,
  },
  {
    value: "gpt-4o",
    label: "GPT-4o Multimodal",
    subLabel: "OpenAI High Precision",
    cost: "$0.0035/pg",
    icon: Bot,
  },
  {
    value: "claude-3.5-sonnet",
    label: "Claude 3.5 Sonnet",
    subLabel: "Anthropic VLM",
    cost: "$0.0030/pg",
    icon: ShieldCheck,
  },
  {
    value: "qwen-2.5-72b",
    label: "Qwen 2.5 72B",
    subLabel: "OpenSource High Perf",
    cost: "$0.0010/pg",
    icon: Cpu,
  },
  {
    value: "small-vision-vlm",
    label: "Small Vision Model",
    subLabel: "GPU Cropped Region",
    cost: "$0.0002/pg",
    icon: Zap,
  },
];

export function LlmSelect({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (model: LlmModelOption) => void;
  disabled?: boolean;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
      {LLM_MODELS.map((m) => {
        const Icon = m.icon;
        const selected = value === m.value;
        return (
          <button
            key={m.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(m.value)}
            className={cn(
              "relative flex flex-col items-start gap-1 rounded-xl border p-2.5 text-left transition-all",
              "hover:border-purple-500/50 hover:bg-purple-500/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              selected
                ? "border-purple-500 bg-purple-500/10 ring-1 ring-purple-500 shadow-xs"
                : "bg-card/60 text-muted-foreground border-border/70",
              disabled && "pointer-events-none opacity-50"
            )}
          >
            <div className="flex w-full items-center justify-between gap-1">
              <Icon
                className={cn(
                  "size-4 shrink-0",
                  selected ? "text-purple-400" : "text-muted-foreground"
                )}
              />
              {selected ? (
                <div className="flex size-4 items-center justify-center rounded-full bg-purple-500 text-purple-950 font-bold">
                  <Check className="size-2.5" />
                </div>
              ) : (
                <span className="text-[10px] font-mono text-muted-foreground/80">
                  {m.cost}
                </span>
              )}
            </div>

            <div className="mt-1">
              <div
                className={cn(
                  "text-xs font-semibold leading-tight",
                  selected ? "text-foreground font-bold" : "text-foreground/80"
                )}
              >
                {m.label}
              </div>
              <div className="text-[10px] text-muted-foreground leading-tight mt-0.5">
                {m.subLabel}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
