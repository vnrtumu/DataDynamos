import { ArrowRight, ScanLine, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import { Dropzone } from "@/features/upload/Dropzone";
import { DocTypeToggle } from "@/features/upload/DocTypeToggle";
import { EngineSelect } from "@/features/upload/EngineSelect";
import { DocumentLibrary } from "@/features/upload/DocumentLibrary";

const STAGES = [
  { label: "Pre-scan", hint: "quality & deskew" },
  { label: "OCR", hint: "Qwen3-VL / Docling" },
  { label: "Structure", hint: "LangExtract" },
  { label: "Decide", hint: "approve / flag" },
];

export function UploadView() {
  const {
    docType,
    activeEngine,
    setDocType,
    setActiveEngine,
    ingestFile,
    ingesting,
  } = usePipelineContext();

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col items-center gap-10 px-6 py-12">
      <div className="flex w-full max-w-2xl flex-col items-center gap-8">
        <div className="space-y-3 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border bg-muted/50 px-3 py-1 text-xs font-medium text-muted-foreground">
            <Sparkles className="size-3.5 text-brand" />
            OCR-to-decision pipeline
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
            From scanned document to a defensible decision
          </h1>
          <p className="mx-auto max-w-md text-sm text-muted-foreground text-balance">
            Upload a contract or invoice. Watch it get pre-scanned, read by OCR,
            structured into fields, and approved or flagged — every field
            traceable to its source.
          </p>
        </div>

        <Card className="w-full">
          <CardContent className="space-y-6">
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Document type
                </label>
                <DocTypeToggle
                  value={docType}
                  onChange={setDocType}
                  disabled={ingesting}
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  OCR engine
                </label>
                <EngineSelect
                  value={activeEngine}
                  onChange={setActiveEngine}
                  disabled={ingesting}
                />
              </div>
            </div>

            <Dropzone onFile={ingestFile} disabled={ingesting} />

            {ingesting && (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <ScanLine className="size-4 animate-pulse text-brand" />
                Ingesting & running the pipeline…
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex flex-wrap items-center justify-center gap-x-1 gap-y-2 text-xs text-muted-foreground">
          {STAGES.map((s, i) => (
            <div key={s.label} className="flex items-center gap-1">
              <span className="rounded-md border bg-card px-2.5 py-1">
                <span className="font-medium text-foreground">{s.label}</span>
                <span className="ml-1.5 text-muted-foreground">{s.hint}</span>
              </span>
              {i < STAGES.length - 1 && (
                <ArrowRight className="size-3.5 opacity-40" />
              )}
            </div>
          ))}
        </div>
      </div>

      <DocumentLibrary />
    </div>
  );
}
