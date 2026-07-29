import { FileText, ReceiptText } from "lucide-react";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { DocType } from "@/lib/types";

export function DocTypeToggle({
  value,
  onChange,
  disabled,
}: {
  value: DocType;
  onChange: (t: DocType) => void;
  disabled?: boolean;
}) {
  return (
    <ToggleGroup
      type="single"
      variant="outline"
      spacing={0}
      value={value}
      disabled={disabled}
      onValueChange={(v) => v && onChange(v as DocType)}
      className="w-full *:flex-1"
    >
      <ToggleGroupItem value="invoice" aria-label="Invoice">
        <ReceiptText className="size-4" />
        Invoice
      </ToggleGroupItem>
      <ToggleGroupItem value="contract" aria-label="Contract">
        <FileText className="size-4" />
        Contract
      </ToggleGroupItem>
    </ToggleGroup>
  );
}
