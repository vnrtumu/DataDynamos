import React, { useState } from "react";
import {
  ArrowRight,
  ScanLine,
  Sparkles,
  ShieldCheck,
  Cpu,
  Bot,
  Zap,
  SlidersHorizontal,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import { Dropzone } from "@/features/upload/Dropzone";
import { DocTypeToggle } from "@/features/upload/DocTypeToggle";
import { EngineSelect } from "@/features/upload/EngineSelect";
import { LlmSelect } from "@/features/upload/LlmSelect";
import { DocumentLibrary } from "@/features/upload/DocumentLibrary";

const STAGES = [
  { label: "1. Auto-Classifier", hint: "Tier A–D Detection" },
  { label: "2. CV Pre-scan", hint: "Deskew & Denoise" },
  { label: "3. Smart OCR", hint: "Auto-Routed Engine" },
  { label: "4. Rule Engine", hint: "NPI / ICD-10 / CPT" },
  { label: "5. Decision", hint: "Auto-Approve / HITL" },
];

export function UploadView() {
  const {
    docType,
    activeEngine,
    activeLlmModel,
    setDocType,
    setActiveEngine,
    setLlmModel,
    ingestFile,
    ingesting,
  } = usePipelineContext();

  const [showAdvanced, setShowAdvanced] = useState(true);

  return (
    <div className="mx-auto flex h-full w-full max-w-6xl flex-col items-center gap-6 px-4 py-6 sm:px-6 overflow-y-auto">
      {/* Hero Title Header */}
      <div className="flex shrink-0 w-full max-w-3xl flex-col items-center gap-3 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border bg-emerald-500/10 border-emerald-500/30 px-3.5 py-1 text-xs font-medium text-emerald-400 shadow-xs">
          <Bot className="size-3.5 text-emerald-400" />
          100% Automated Zero-Intervention Pipeline Enabled
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-balance sm:text-4xl">
          Autonomous Healthcare Claims Ingestion & Approval
        </h1>
        <p className="max-w-xl text-sm text-muted-foreground text-balance">
          Drop any scanned claim form or bill. The system automatically detects the Document Format Tier and routes to the optimal OCR engine with zero manual setup.
        </p>
      </div>

      {/* Main Ingestion Card */}
      <Card className="w-full shrink-0 border-border/70 shadow-sm">
        <CardHeader className="pb-3 border-b bg-muted/20">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Zap className="size-4 text-emerald-400" /> Direct Claims Drag & Drop Ingestion
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvanced((v) => !v)}
              className="text-xs gap-1.5"
            >
              <SlidersHorizontal className="size-3.5" />
              {showAdvanced ? "Hide Manual Overrides" : "Advanced Manual Overrides"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          {/* Advanced Manual Overrides Panel */}
          {showAdvanced && (
            <div className="rounded-xl border bg-muted/20 p-4 space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="font-semibold text-xs text-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <SlidersHorizontal className="size-3.5 text-sky-400" />
                  Manual Pipeline Engine & Model Overrides
                </div>
                <span className="text-[11px] text-muted-foreground">
                  (Default: AI Auto-Classification & Auto-Routing)
                </span>
              </div>

              {/* 1. Document Format Tier */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">
                  1. Target Document Format Tier:
                </label>
                <DocTypeToggle value={docType} onChange={setDocType} disabled={ingesting} />
              </div>

              {/* 2. OCR Engine (Stage 3/4) */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Cpu className="size-3.5 text-sky-400" />
                  2. OCR Engine Selection (Stage 3/4):
                </label>
                <EngineSelect value={activeEngine} onChange={setActiveEngine} disabled={ingesting} />
              </div>

              {/* 3. LLM Structuring Model (Stage 5a/5b) */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Sparkles className="size-3.5 text-purple-400" />
                  3. LLM Structuring Model Selection (Stage 5a/5b):
                </label>
                <LlmSelect value={activeLlmModel} onChange={setLlmModel} disabled={ingesting} />
              </div>
            </div>
          )}

          {/* Automated Feature Badges Banner */}
          <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/5 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-xs text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="size-4" /> Autonomous Processing Protocol Active
              </div>
              <Badge variant="outline" className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 font-mono text-[10px]">
                Zero Intervention
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Document format classification (CMS-1500 Tier A/B, UB-04 Tier C, Unstructured Tier D) and OCR engine selection are handled automatically by the AI classifier during upload.
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-foreground bg-card px-2.5 py-1 rounded-md border">
                <ShieldCheck className="size-3 text-emerald-400" /> Auto Tier Classifier
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-foreground bg-card px-2.5 py-1 rounded-md border">
                <Cpu className="size-3 text-sky-400" /> Smart Engine Router
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-foreground bg-card px-2.5 py-1 rounded-md border">
                <Sparkles className="size-3 text-purple-400" /> NPI & ICD-10 Rule Engine
              </span>
            </div>
          </div>

          {/* Primary Dropzone */}
          <Dropzone onFile={ingestFile} disabled={ingesting} />

          {ingesting && (
            <div className="flex items-center justify-center gap-2 rounded-lg border bg-emerald-500/10 border-emerald-500/30 p-3 text-sm text-emerald-400 font-medium">
              <ScanLine className="size-4 animate-pulse" />
              Ingesting claim scan & running automated classification pipeline…
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pipeline Stage Footnote */}
      <div className="flex shrink-0 flex-wrap items-center justify-center gap-x-1.5 gap-y-2 text-xs text-muted-foreground">
        {STAGES.map((s, i) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <span className="rounded-lg border bg-card/80 px-3 py-1 shadow-2xs">
              <span className="font-medium text-foreground">{s.label}</span>
              <span className="ml-1.5 text-muted-foreground text-[11px]">{s.hint}</span>
            </span>
            {i < STAGES.length - 1 && (
              <ArrowRight className="size-3.5 opacity-40" />
            )}
          </div>
        ))}
      </div>

      {/* Document Library */}
      <div className="w-full shrink-0">
        <DocumentLibrary />
      </div>
    </div>
  );
}
