import { useMemo, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { rectsForField } from "@/lib/grounding";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import { PageViewer } from "@/features/inspector/PageViewer";
import { OcrTextPanel } from "@/features/inspector/OcrTextPanel";
import { OcrJsonPanel } from "@/features/inspector/OcrJsonPanel";
import { StructuredPanel } from "@/features/inspector/StructuredPanel";
import { EngineComparison } from "@/features/inspector/EngineComparison";
import { DecisionCard } from "@/features/decision/DecisionCard";
import { ModelRationalePanel } from "@/features/inspector/ModelRationalePanel";

function Pending({ label }: { label: string }) {
  return (
    <div className="space-y-3 p-1">
      <Skeleton className="h-6 w-40" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-2/3" />
      <p className="pt-2 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div className="flex h-40 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
      {label}
    </div>
  );
}

export function SplitInspector() {
  const {
    document,
    ocr,
    ocrByEngine,
    structure,
    decision,
    perStageStatus,
    runEngineComparison,
  } = usePipelineContext();

  const [hoveredField, setHoveredField] = useState<string | null>(null);
  const [activePage, setActivePage] = useState(1);

  const highlight = useMemo(() => {
    if (!hoveredField || !structure || !ocr) return null;
    return rectsForField(hoveredField, structure.grounding_map, ocr);
  }, [hoveredField, structure, ocr]);

  if (!document) return null;

  const displayPage = highlight?.page ?? activePage;
  const rects =
    highlight && highlight.page === displayPage ? highlight.rects : [];

  return (
    <div className="grid flex-1 items-start gap-6 lg:grid-cols-2">
      {/* Left: sticky source document, bounded to viewport */}
      <div className="sticky top-14 flex flex-col" style={{ height: "calc(100vh - 3.5rem)" }}>
        <PageViewer
          pages={document.pages}
          page={displayPage}
          rects={rects}
          alignment={highlight?.alignment ?? null}
          onPageChange={setActivePage}
        />
      </div>

      {/* Right: inspector tabs */}
      <div className="flex flex-col gap-4">
        <Tabs defaultValue="structured" className="w-full">
          <TabsList className="grid grid-cols-6 w-full">
            <TabsTrigger value="ocr">OCR text</TabsTrigger>
            <TabsTrigger value="ocr-json">JSON Structure</TabsTrigger>
            <TabsTrigger value="structured">Structured</TabsTrigger>
            <TabsTrigger value="decision">Decision</TabsTrigger>
            <TabsTrigger value="compare">Compare</TabsTrigger>
            <TabsTrigger value="rationale" className="text-sky-400 font-semibold text-xs truncate">Why OCR & LLM?</TabsTrigger>
          </TabsList>

          <TabsContent value="ocr" className="mt-3">
            {ocr ? (
              <OcrTextPanel ocr={ocr} page={displayPage} />
            ) : perStageStatus.ocr === "running" ? (
              <Pending label="Running OCR…" />
            ) : (
              <Empty label="OCR has not run yet." />
            )}
          </TabsContent>

          <TabsContent value="ocr-json" className="mt-3">
            {ocr ? (
              <OcrJsonPanel ocr={ocr} page={displayPage} />
            ) : perStageStatus.ocr === "running" ? (
              <Pending label="Generating OCR JSON payload..." />
            ) : (
              <Empty label="OCR has not run yet." />
            )}
          </TabsContent>

          <TabsContent value="structured" className="mt-3">
            {structure ? (
              <StructuredPanel
                result={structure}
                onHoverField={setHoveredField}
              />
            ) : perStageStatus.structure === "running" ? (
              <Pending label="Structuring with LangExtract…" />
            ) : (
              <Empty label="Structuring has not run yet." />
            )}
          </TabsContent>

          <TabsContent value="decision" className="mt-3">
            {decision ? (
              <DecisionCard decision={decision} />
            ) : perStageStatus.decide === "running" ? (
              <Pending label="Agent is deciding…" />
            ) : (
              <Empty label="No decision yet." />
            )}
          </TabsContent>

          <TabsContent value="compare" className="mt-3">
            <EngineComparison
              ocrByEngine={ocrByEngine}
              page={displayPage}
              onRun={runEngineComparison}
              running={perStageStatus.ocr === "running"}
            />
          </TabsContent>

          <TabsContent value="rationale" className="mt-3">
            <ModelRationalePanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
