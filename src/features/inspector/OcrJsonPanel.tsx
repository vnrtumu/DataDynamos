import { useState, useMemo } from "react";
import { FileJson, Copy, Check, Search } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { OCRResult } from "@/lib/types";

export function OcrJsonPanel({ ocr, page }: { ocr: OCRResult; page?: number }) {
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const structuredJson = useMemo(() => {
    const pages = (ocr.pages || []).map((p) => ({
      page_number: p.page,
      text: p.text,
      blocks_count: p.blocks?.length || 0,
      blocks: (p.blocks || []).map((b) => ({
        text: b.text,
        bbox: b.bbox,
        confidence: b.confidence,
        label: b.label || "text",
      })),
      tables_count: p.tables?.length || 0,
      tables: (p.tables || []).map((t) => ({
        markdown: t.markdown,
        n_rows: t.n_rows,
        n_cols: t.n_cols,
      })),
    }));

    const payload = {
      document_id: ocr.document_id,
      ocr_engine: ocr.engine_name,
      engine_version: ocr.engine_version,
      avg_ocr_confidence: ocr.avg_confidence,
      total_pages: pages.length,
      table_count: ocr.table_count,
      full_text: ocr.full_text,
      pages,
    };

    return JSON.stringify(payload, null, 2);
  }, [ocr]);

  const handleCopy = () => {
    navigator.clipboard.writeText(structuredJson);
    setCopied(true);
    toast.success("Structured OCR JSON copied to clipboard!", {
      description: "This exact JSON structure is fed into LLMs during Stage 4 structuring.",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredJsonText = useMemo(() => {
    if (!searchQuery.trim()) return structuredJson;
    const lines = structuredJson.split("\n");
    const matched = lines.filter((l) =>
      l.toLowerCase().includes(searchQuery.toLowerCase())
    );
    return matched.join("\n");
  }, [structuredJson, searchQuery]);

  const totalBlocks = (ocr.pages || []).reduce(
    (acc, p) => acc + (p.blocks?.length || 0),
    0
  );

  return (
    <div className="flex h-full min-h-[500px] flex-col gap-3">
      {/* Header Info Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-sky-500/30 bg-sky-500/5 px-3 py-2 text-xs shadow-2xs">
        <div className="flex items-center gap-2 text-sky-400 font-medium">
          <FileJson className="size-4 text-sky-400" />
          <span>Structured LLM Input Feed (OCR JSON Payload)</span>
          <Badge
            variant="outline"
            className="border-sky-500/40 bg-sky-500/10 text-sky-300 font-mono text-[10px]"
          >
            Engine: {ocr.engine_name}
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-muted-foreground text-[11px] font-mono">
            {ocr.pages?.length || 0} page(s) • {totalBlocks} block(s)
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="h-7 gap-1.5 px-2.5 text-xs font-semibold text-foreground border-sky-500/40 hover:bg-sky-500/10 transition-colors"
          >
            {copied ? (
              <>
                <Check className="size-3.5 text-emerald-400" />
                Copied JSON
              </>
            ) : (
              <>
                <Copy className="size-3.5 text-sky-400" />
                Copy Structured JSON
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Filter / Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 size-3.5 text-muted-foreground" />
        <input
          type="text"
          placeholder="Filter JSON fields, keys, bounding boxes, or text..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border bg-background pl-8 pr-3 py-1.5 font-mono text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-sky-500"
        />
      </div>

      {/* Main Formatted JSON Payload Box */}
      <ScrollArea className="flex-1 rounded-xl border bg-slate-950 p-4 font-mono text-xs text-sky-200/90 shadow-inner">
        <pre className="whitespace-pre-wrap leading-relaxed">
          {filteredJsonText || "(No matching JSON lines found)"}
        </pre>
      </ScrollArea>
    </div>
  );
}
