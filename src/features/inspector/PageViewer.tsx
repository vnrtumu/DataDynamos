import { useEffect, useRef, useState } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { fileUrl } from "@/lib/api";
import { scaleRects, type HighlightRect } from "@/lib/grounding";
import type { Alignment, PageInfo } from "@/lib/types";
import { Button } from "@/components/ui/button";

export function PageViewer({
  pages,
  page,
  rects,
  alignment,
  onPageChange,
}: {
  pages: PageInfo[];
  page: number;
  rects: HighlightRect[]; // natural pixel space, for the current page
  alignment: Alignment | null;
  onPageChange: (page: number) => void;
}) {
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [natural, setNatural] = useState({ width: 0, height: 0 });
  const [displayed, setDisplayed] = useState({ width: 0, height: 0 });
  const [zoomLevel, setZoomLevel] = useState<number>(1.0); // 1.0 = 100%

  const handleZoomIn = () => setZoomLevel((z) => Math.min(5.0, Math.round((z + 0.5) * 100) / 100));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(0.5, Math.round((z - 0.5) * 100) / 100));
  const handleResetZoom = () => setZoomLevel(1.0);

  const handleImageClick = () => {
    setZoomLevel((z) => {
      if (z < 1.8) return 2.0;
      if (z < 3.2) return 3.5;
      if (z < 4.8) return 5.0;
      return 1.0;
    });
  };

  // Track the rendered <img> size so we can scale natural-pixel bboxes onto it.
  useEffect(() => {
    const el = imgRef.current;
    if (!el) return;
    const update = () =>
      setDisplayed({ width: el.clientWidth, height: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [page, zoomLevel]);

  const current = pages.find((p) => p.page === page) ?? pages[0];
  const scaled = scaleRects(rects, natural, displayed);
  const stroke =
    alignment === "partial" ? "border-dashed border-review" : "border-brand";

  return (
    <div className="flex h-full flex-col gap-3 py-4">
      {/* Zoom Control Bar */}
      <div className="flex items-center justify-between rounded-lg border bg-card px-3 py-1.5 shadow-2xs">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
          <Maximize2 className="size-3.5 text-brand" />
          <span>Document Viewer</span>
          <span className="hidden sm:inline text-[11px] text-muted-foreground/70">
            (Click image to zoom)
          </span>
        </div>

        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            disabled={zoomLevel <= 0.5}
            className="h-7 w-7 p-0"
            title="Zoom Out (-25%)"
          >
            <ZoomOut className="size-3.5" />
          </Button>

          <span className="min-w-[42px] text-center text-xs font-mono font-semibold text-foreground">
            {Math.round(zoomLevel * 100)}%
          </span>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            disabled={zoomLevel >= 5.0}
            className="h-7 w-7 p-0"
            title="Zoom In (+50%)"
          >
            <ZoomIn className="size-3.5" />
          </Button>

          <div className="mx-1 h-3 w-px bg-border" />

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleResetZoom}
            disabled={zoomLevel === 1.0}
            className="h-7 w-7 p-0"
            title="Reset Zoom (100%)"
          >
            <RotateCcw className="size-3.5" />
          </Button>
        </div>
      </div>

      {/* Main Image Container: fixed height, scrollable when zoomed */}
      <div
        ref={containerRef}
        className="relative overflow-auto rounded-xl border bg-muted/40 p-4"
        style={{ flex: "1 1 0", minHeight: 0 }}
      >
        <div
          onClick={handleImageClick}
          className={cn(
            "relative mx-auto w-fit transition-all duration-150 ease-out",
            zoomLevel < 5.0 ? "cursor-zoom-in" : "cursor-zoom-out"
          )}
          title={
            zoomLevel < 5.0
              ? `Click to zoom further (${Math.round(zoomLevel * 100)}%)`
              : "Click to reset zoom (100%)"
          }
        >
          <img
            ref={imgRef}
            src={fileUrl(current?.image_url)}
            alt={`Page ${page}`}
            className="rounded-md shadow-sm ring-1 ring-border transition-all duration-150"
            style={
              zoomLevel === 1.0
                ? { maxHeight: "68vh", width: "auto" }
                : {
                    width: `${Math.round(zoomLevel * 100)}%`,
                    maxWidth: "none",
                    maxHeight: "none",
                  }
            }
            onLoad={(e) => {
              const t = e.currentTarget;
              setNatural({ width: t.naturalWidth, height: t.naturalHeight });
              setDisplayed({ width: t.clientWidth, height: t.clientHeight });
            }}
          />
          {scaled.map((r, i) => (
            <div
              key={i}
              className={cn(
                "pointer-events-none absolute rounded-sm border-2 bg-brand/10 transition-all",
                stroke
              )}
              style={{ left: r.x, top: r.y, width: r.width, height: r.height }}
            />
          ))}
        </div>
      </div>

      {pages.length > 1 && (
        <div className="flex shrink-0 gap-2 overflow-x-auto pb-1">
          {pages.map((p) => (
            <button
              key={p.page}
              onClick={() => onPageChange(p.page)}
              className={cn(
                "shrink-0 overflow-hidden rounded-md border-2 transition-colors",
                p.page === page
                  ? "border-brand"
                  : "border-transparent hover:border-border"
              )}
            >
              <img
                src={fileUrl(p.thumbnail_url)}
                alt={`Page ${p.page} thumbnail`}
                className="h-14 w-auto"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
