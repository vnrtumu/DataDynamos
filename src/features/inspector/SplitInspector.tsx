import { useMemo, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { rectsForField } from "@/lib/grounding";
import { usePipelineContext } from "@/features/pipeline/PipelineContext";
import { PageViewer } from "@/features/inspector/PageViewer";
import { OcrTextPanel } from "@/features/inspector/OcrTextPanel";
import { StructuredPanel } from "@/features/inspector/StructuredPanel";
import { EngineComparison } from "@/features/inspector/EngineComparison";
import { DecisionCard } from "@/features/decision/DecisionCard";

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
    <div className="grid flex-1 gap-4 lg:grid-cols-2">
      {/* Left: source document */}
      <div className="min-h-0">
        <PageViewer
          pages={document.pages}
          page={displayPage}
          rects={rects}
          alignment={highlight?.alignment ?? null}
          onPageChange={setActivePage}
        />
      </div>

      {/* Right: inspector tabs */}
      <div className="flex min-h-0 flex-col">
        <Tabs
          defaultValue="structured"
          className="flex min-h-0 flex-1 flex-col"
        >
          <TabsList>
            <TabsTrigger value="ocr">OCR text</TabsTrigger>
            <TabsTrigger value="structured">Structured</TabsTrigger>
            <TabsTrigger value="decision">Decision</TabsTrigger>
            <TabsTrigger value="compare">Compare</TabsTrigger>
          </TabsList>

          <TabsContent value="ocr" className="min-h-0 flex-1">
            {ocr ? (
              <OcrTextPanel ocr={ocr} page={displayPage} />
            ) : perStageStatus.ocr === "running" ? (
              <Pending label="Running OCR…" />
            ) : (
              <Empty label="OCR has not run yet." />
            )}
          </TabsContent>

          <TabsContent value="structured" className="min-h-0 flex-1">
            {structure ? (
              <StructuredPanel
                structure={structure}
                onHoverField={setHoveredField}
              />
            ) : perStageStatus.structure === "running" ? (
              <Pending label="Structuring with LangExtract…" />
            ) : (
              <Empty label="Structuring has not run yet." />
            )}
          </TabsContent>

          <TabsContent
            value="decision"
            className="min-h-0 flex-1 overflow-auto"
          >
            {decision ? (
              <DecisionCard decision={decision} />
            ) : perStageStatus.decide === "running" ? (
              <Pending label="Agent is deciding…" />
            ) : (
              <Empty label="No decision yet." />
            )}
          </TabsContent>

          <TabsContent value="compare" className="min-h-0 flex-1">
            <EngineComparison
              ocrByEngine={ocrByEngine}
              page={displayPage}
              onRun={runEngineComparison}
              running={perStageStatus.ocr === "running"}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
