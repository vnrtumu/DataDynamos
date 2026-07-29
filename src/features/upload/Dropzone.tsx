import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

const ACCEPT = ".pdf,.png,.jpg,.jpeg,.tif,.tiff";

export function Dropzone({
  onFile,
  disabled,
}: {
  onFile: (file: File) => void;
  disabled?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const pick = useCallback(() => {
    if (!disabled) inputRef.current?.click();
  }, [disabled]);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files?.[0];
      if (file) onFile(file);
    },
    [onFile, disabled],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      onClick={pick}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && pick()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cn(
        "group relative flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed px-8 py-14 text-center transition-all outline-none",
        "focus-visible:ring-[3px] focus-visible:ring-ring/50",
        disabled
          ? "cursor-not-allowed opacity-60"
          : "cursor-pointer hover:border-brand/60 hover:bg-brand/[0.03]",
        dragging
          ? "border-brand bg-brand/5 scale-[1.01]"
          : "border-border bg-muted/30",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = "";
        }}
      />
      <div
        className={cn(
          "flex size-14 items-center justify-center rounded-full border bg-background transition-colors",
          dragging
            ? "border-brand text-brand"
            : "text-muted-foreground group-hover:text-brand",
        )}
      >
        <UploadCloud className="size-7" />
      </div>
      <div className="space-y-1">
        <p className="text-base font-medium text-foreground">
          {dragging ? "Drop to ingest" : "Drag & drop a document"}
        </p>
        <p className="text-sm text-muted-foreground">
          or <span className="font-medium text-brand">browse</span> — PDF, PNG,
          JPG or TIFF
        </p>
      </div>
    </div>
  );
}
