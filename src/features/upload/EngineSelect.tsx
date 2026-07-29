import { ScanText, Layers } from "lucide-react";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { OcrEngine } from "@/lib/types";

const ENGINES: { value: OcrEngine; label: string; icon: typeof ScanText }[] = [
  { value: "docling", label: "Docling", icon: Layers },
  { value: "qwen-vl", label: "Qwen3-VL", icon: ScanText },
];

export function EngineSelect({
  value,
  onChange,
  disabled,
}: {
  value: OcrEngine;
  onChange: (e: OcrEngine) => void;
  disabled?: boolean;
}) {
  return (
    <ToggleGroup
      type="single"
      variant="outline"
      spacing={0}
      value={value}
      disabled={disabled}
      onValueChange={(v) => v && onChange(v as OcrEngine)}
      className="w-full *:flex-1"
    >
      {ENGINES.map(({ value: v, label, icon: Icon }) => (
        <ToggleGroupItem key={v} value={v} aria-label={label}>
          <Icon className="size-4" />
          {label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}
