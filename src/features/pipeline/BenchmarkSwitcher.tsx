import React, { useState } from "react";
import {
  SlidersHorizontal,
  ShieldCheck,
  Cpu,
  Sparkles,
  RotateCw,
  Loader2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import type { DocType, OcrEngine } from "@/lib/types";
import type { LlmModelOption } from "@/features/upload/LlmSelect";

const TIER_OPTIONS: { value: DocType; label: string }[] = [
  { value: "cms1500", label: "Tier A (CMS-1500 Single)" },
  { value: "cms1500_multi", label: "Tier B (CMS-1500 Multi)" },
  { value: "ub04", label: "Tier C (UB-04 Form)" },
  { value: "unstructured_claim", label: "Tier D (Unstructured Claim)" },
];

const OCR_OPTIONS: { value: OcrEngine; label: string }[] = [
  { value: "paddleocr", label: "PaddleOCR (PP-OCRv4)" },
  { value: "pytesseract", label: "PyTesseract (v5.3 CPU)" },
  { value: "docling", label: "Docling (Deep Layout)" },
  { value: "qwen-vl", label: "Qwen3-VL (Vision AI)" },
];

const LLM_OPTIONS: { value: LlmModelOption; label: string }[] = [
  { value: "deepseek-v4", label: "DeepSeek-v4 Flash" },
  { value: "gpt-4o", label: "GPT-4o Multimodal" },
  { value: "claude-3.5-sonnet", label: "Claude 3.5 Sonnet" },
  { value: "qwen-2.5-72b", label: "Qwen 2.5 72B" },
  { value: "small-vision-vlm", label: "Small Vision Model" },
];

export function BenchmarkSwitcher() {
  const {
    document,
    docType,
    activeEngine,
    activeLlmModel,
    setDocType,
    setActiveEngine,
    setLlmModel,
    reRunPipeline,
    perStageStatus,
  } = usePipelineContext();

  const [loading, setLoading] = useState(false);

  const isRunning =
    loading ||
    Object.values(perStageStatus).some((status) => status === "running");

  const handleReRun = async () => {
    if (!reRunPipeline || isRunning) return;
    setLoading(true);
    try {
      await reRunPipeline();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full rounded-2xl border border-sky-500/20 bg-card/70 p-3 sm:p-4 shadow-sm backdrop-blur-xs space-y-3">
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2.5">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="size-4 text-sky-400" />
          <span className="text-xs sm:text-sm font-semibold tracking-tight text-foreground">
            Pipeline Model Benchmark Switcher
          </span>
        </div>
        <Badge
          variant="outline"
          className="bg-sky-500/10 text-sky-400 border-sky-500/30 text-[11px] font-medium px-2.5 py-0.5 rounded-full"
        >
          Post-Processing Re-Eval & Model Compare
        </Badge>
      </div>

      {/* Select Controls & Re-run Button */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {/* Tier Select */}
        <div className="flex items-center gap-1.5 rounded-lg border bg-background px-2.5 py-1 text-xs shadow-2xs">
          <ShieldCheck className="size-3.5 text-emerald-400 shrink-0" />
          <span className="font-medium text-muted-foreground">Tier:</span>
          <Select
            value={docType}
            onValueChange={(val) => setDocType(val as DocType)}
            disabled={isRunning}
          >
            <SelectTrigger className="h-7 border-none bg-transparent p-0 text-xs font-semibold focus:ring-0 focus:outline-none shadow-none gap-1">
              <SelectValue placeholder="Select Tier" />
            </SelectTrigger>
            <SelectContent>
              {TIER_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value} className="text-xs">
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* OCR Engine Select */}
        <div className="flex items-center gap-1.5 rounded-lg border bg-background px-2.5 py-1 text-xs shadow-2xs">
          <Cpu className="size-3.5 text-sky-400 shrink-0" />
          <span className="font-medium text-muted-foreground">OCR:</span>
          <Select
            value={activeEngine}
            onValueChange={(val) => setActiveEngine(val as OcrEngine)}
            disabled={isRunning}
          >
            <SelectTrigger className="h-7 border-none bg-transparent p-0 text-xs font-semibold focus:ring-0 focus:outline-none shadow-none gap-1">
              <SelectValue placeholder="Select OCR Engine" />
            </SelectTrigger>
            <SelectContent>
              {OCR_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value} className="text-xs">
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* LLM Model Select */}
        <div className="flex items-center gap-1.5 rounded-lg border bg-background px-2.5 py-1 text-xs shadow-2xs">
          <Sparkles className="size-3.5 text-purple-400 shrink-0" />
          <span className="font-medium text-muted-foreground">LLM:</span>
          <Select
            value={activeLlmModel}
            onValueChange={(val) => setLlmModel(val as LlmModelOption)}
            disabled={isRunning}
          >
            <SelectTrigger className="h-7 border-none bg-transparent p-0 text-xs font-semibold focus:ring-0 focus:outline-none shadow-none gap-1">
              <SelectValue placeholder="Select LLM Model" />
            </SelectTrigger>
            <SelectContent>
              {LLM_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value} className="text-xs">
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Re-run Pipeline Button */}
        <Button
          size="sm"
          onClick={handleReRun}
          disabled={isRunning || !document}
          className="ml-auto bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs px-3.5 h-8 gap-1.5 shadow-xs transition-all"
        >
          {isRunning ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <RotateCw className="size-3.5" />
          )}
          Re-run Pipeline
        </Button>
      </div>
    </div>
  );
}
