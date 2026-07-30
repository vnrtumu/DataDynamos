import React from "react";
import { DollarSign, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface CostAccuracyBadgeProps {
  costPerDoc?: number;
  costPerMillion?: number;
  accuracyValue?: number;
  tier?: string;
  className?: string;
}

export function CostAccuracyBadge({
  costPerDoc = 0.0003,
  costPerMillion = 300,
  accuracyValue = 95.0,
  tier = "Tier A",
  className = "",
}: CostAccuracyBadgeProps) {
  const getAccuracyColor = (acc: number) => {
    if (acc >= 95) return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    if (acc >= 85) return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    return "bg-rose-500/15 text-rose-400 border-rose-500/30";
  };

  return (
    <div className={`flex flex-wrap items-center gap-2 text-xs ${className}`}>
      {/* Tier Badge */}
      <Badge variant="outline" className="bg-brand/10 text-brand border-brand/30 font-medium">
        <ShieldCheck className="mr-1 size-3" />
        {tier}
      </Badge>

      {/* Accuracy Badge */}
      <Badge variant="outline" className={`font-mono font-medium ${getAccuracyColor(accuracyValue)}`}>
        <CheckCircle2 className="mr-1 size-3" />
        {accuracyValue.toFixed(1)}% Accuracy
      </Badge>

      {/* Cost Badge */}
      <Badge variant="outline" className="border-sky-500/30 bg-sky-500/10 text-sky-400 font-mono font-medium">
        <DollarSign className="mr-0.5 size-3" />${costPerDoc.toFixed(4)}/pg (${costPerMillion.toFixed(0)}/1M)
      </Badge>
    </div>
  );
}
