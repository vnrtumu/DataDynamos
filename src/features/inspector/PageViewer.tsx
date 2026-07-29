import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { fileUrl } from "@/lib/api";
import { scaleRects, type HighlightRect } from "@/lib/grounding";
import type { Alignment, PageInfo } from "@/lib/types";

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
  const [natural, setNatural] = useState({ width: 0, height: 0 });
  const [displayed, setDisplayed] = useState({ width: 0, height: 0 });

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
  }, [page]);

  const current = pages.find((p) => p.page === page) ?? pages[0];
  const scaled = scaleRects(rects, natural, displayed);
  const stroke =
    alignment === "partial" ? "border-dashed border-review" : "border-brand";

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="relative flex-1 overflow-auto rounded-xl border bg-muted/40 p-4">
        <div className="relative mx-auto w-fit">
          <img
            ref={imgRef}
            src={fileUrl(current?.image_url)}
            alt={`Page ${page}`}
            className="max-h-[68vh] w-auto rounded-md shadow-sm ring-1 ring-border"
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
                stroke,
              )}
              style={{ left: r.x, top: r.y, width: r.width, height: r.height }}
            />
          ))}
        </div>
      </div>

      {pages.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {pages.map((p) => (
            <button
              key={p.page}
              onClick={() => onPageChange(p.page)}
              className={cn(
                "shrink-0 overflow-hidden rounded-md border-2 transition-colors",
                p.page === page
                  ? "border-brand"
                  : "border-transparent hover:border-border",
              )}
            >
              <img
                src={fileUrl(p.thumbnail_url)}
                alt={`Page ${p.page} thumbnail`}
                className="h-16 w-auto"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
