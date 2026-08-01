import { useState } from "react";
import { SlidersHorizontal, RefreshCw, Cpu, Sparkles, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import type { DocType, OcrEngine } from "@/lib/types";

const DOC_TIERS: { value: DocType; label: string }[] = [
  { value: "cms1500", label: "Tier A (CMS-1500 Single)" },
  { value: "cms1500_multi", label: "Tier B (CMS-1500 Multi)" },
  { value: "ub04", label: "Tier C (UB-04 Form)" },
  { value: "unstructured_claim", label: "Tier D (Unstructured Claim)" },
];

const OCR_ENGINES: { value: OcrEngine; label: string }[] = [
  { value: "paddleocr", label: "PaddleOCR (PP-OCRv4)" },
  { value: "pytesseract", label: "PyTesseract (v5.3 CPU)" },
  { value: "docling", label: "Docling (Deep Layout)" },
  { value: "qwen-vl", label: "Qwen3-VL (Vision AI)" },
];

const LLM_MODELS = [
  { value: "deepseek-v4", label: "DeepSeek-v4 Flash" },
  { value: "gpt-4o", label: "GPT-4o Multimodal" },
  { value: "claude-3.5-sonnet", label: "Claude 3.5 Sonnet" },
  { value: "qwen-2.5-72b", label: "Qwen 2.5 72B" },
];

export function ModelOverridesToolbar() {
  const { docType, setDocType, activeEngine, setActiveEngine, reRunPipeline, perStageStatus } = usePipelineContext();
  const [selectedLlm, setSelectedLlm] = useState("deepseek-v4");
  const [isReRunning, setIsReRunning] = useState(false);

  const isPipelineRunning = Object.values(perStageStatus).includes("running");

  const handleReRun = async () => {
    setIsReRunning(true);
    try {
      await reRunPipeline("ocr", activeEngine, docType);
    } finally {
      setIsReRunning(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-sky-500/20 bg-card/90 p-3 shadow-xs backdrop-blur-xs">
      <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
        <SlidersHorizontal className="size-4 text-sky-400" />
        <span>Pipeline Model Benchmark Switcher</span>
        <Badge variant="outline" className="text-[10px] font-mono bg-sky-500/10 text-sky-400 border-sky-500/30">
          Post-Processing Live Test
        </Badge>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        {/* Tier Selector */}
        <div className="flex items-center gap-1.5 bg-muted/40 px-2.5 py-1 rounded-lg border text-xs">
          <Shield className="size-3.5 text-emerald-400" />
          <span className="text-[11px] text-muted-foreground font-medium">Tier:</span>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value as DocType)}
            disabled={isPipelineRunning || isReRunning}
            className="bg-transparent text-xs font-semibold text-foreground focus:outline-none cursor-pointer"
          >
            {DOC_TIERS.map((t) => (
              <option key={t.value} value={t.value} className="bg-popover text-foreground">
                {t.label}
              </option>
            ))}
          </select>
        </div>

        {/* OCR Engine Selector */}
        <div className="flex items-center gap-1.5 bg-muted/40 px-2.5 py-1 rounded-lg border text-xs">
          <Cpu className="size-3.5 text-sky-400" />
          <span className="text-[11px] text-muted-foreground font-medium">OCR:</span>
          <select
            value={activeEngine}
            onChange={(e) => setActiveEngine(e.target.value as OcrEngine)}
            disabled={isPipelineRunning || isReRunning}
            className="bg-transparent text-xs font-semibold text-foreground focus:outline-none cursor-pointer"
          >
            {OCR_ENGINES.map((eng) => (
              <option key={eng.value} value={eng.value} className="bg-popover text-foreground">
                {eng.label}
              </option>
            ))}
          </select>
        </div>

        {/* LLM Model Selector */}
        <div className="flex items-center gap-1.5 bg-muted/40 px-2.5 py-1 rounded-lg border text-xs">
          <Sparkles className="size-3.5 text-purple-400" />
          <span className="text-[11px] text-muted-foreground font-medium">LLM:</span>
          <select
            value={selectedLlm}
            onChange={(e) => setSelectedLlm(e.target.value)}
            disabled={isPipelineRunning || isReRunning}
            className="bg-transparent text-xs font-semibold text-foreground focus:outline-none cursor-pointer"
          >
            {LLM_MODELS.map((m) => (
              <option key={m.value} value={m.value} className="bg-popover text-foreground">
                {m.label}
              </option>
            ))}
          </select>
        </div>

        {/* Re-run Pipeline Button */}
        <Button
          size="sm"
          onClick={handleReRun}
          disabled={isPipelineRunning || isReRunning}
          className="gap-1.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs shadow-sm"
        >
          <RefreshCw className={`size-3.5 ${isPipelineRunning || isReRunning ? "animate-spin" : ""}`} />
          {isPipelineRunning || isReRunning ? "Running Pipeline…" : "Re-run Pipeline"}
        </Button>
      </div>
    </div>
  );
}
