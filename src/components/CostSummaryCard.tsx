import React from "react";
import { DollarSign, Cpu, Sparkles, TrendingDown, UserCheck, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface CostSummaryData {
  tier?: string;
  preprocessing_cost?: number;
  ocr_engine_cost?: number;
  vlm_llm_cost?: number;
  total_cost?: number;
  cost_per_million?: number;
  hitl_recommended?: boolean;
  hitl_estimated_cost?: number;
}

export interface AccuracyData {
  overall_accuracy?: number;
  field_accuracy?: number;
  rule_pass_rate?: number;
  ocr_confidence?: number;
  grounded_ratio?: number;
}

interface CostSummaryCardProps {
  cost?: CostSummaryData;
  accuracy?: AccuracyData;
}

export function CostSummaryCard({ cost, accuracy }: CostSummaryCardProps) {
  const defaultCost: CostSummaryData = {
    tier: "Tier A",
    preprocessing_cost: 0.0001,
    ocr_engine_cost: 0.0002,
    vlm_llm_cost: 0.0,
    total_cost: 0.0003,
    cost_per_million: 300.0,
    hitl_recommended: false,
    hitl_estimated_cost: 0.0,
    ...cost,
  };

  const defaultAcc: AccuracyData = {
    overall_accuracy: 95.0,
    field_accuracy: 96.0,
    rule_pass_rate: 100.0,
    ocr_confidence: 94.0,
    grounded_ratio: 92.0,
    ...accuracy,
  };

  return (
    <Card className="border-border/60 bg-card/80 backdrop-blur">
      <CardHeader className="pb-3 pt-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <DollarSign className="size-4 text-emerald-400" />
            Document Cost & Accuracy Summary
          </CardTitle>
          <Badge variant="outline" className="bg-brand/10 text-brand border-brand/30">
            {defaultCost.tier}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-xs">
        {/* Top Highlight Cards */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
            <div className="text-muted-foreground flex items-center gap-1 font-medium">
              <DollarSign className="size-3 text-emerald-400" /> Total Cost / Page
            </div>
            <div className="mt-1 text-lg font-bold text-emerald-400 font-mono">
              ${(defaultCost.total_cost ?? 0.0003).toFixed(4)}
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5">
              ${(defaultCost.cost_per_million ?? 300).toFixed(0)} / 1M Pages
            </div>
          </div>

          <div className="rounded-lg border border-sky-500/20 bg-sky-500/5 p-3">
            <div className="text-muted-foreground flex items-center gap-1 font-medium">
              <CheckCircle2 className="size-3 text-sky-400" /> Extraction Accuracy
            </div>
            <div className="mt-1 text-lg font-bold text-sky-400 font-mono">
              {(defaultAcc.overall_accuracy ?? 95.0).toFixed(1)}%
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5">
              Field Acc: {(defaultAcc.field_accuracy ?? 96.0).toFixed(0)}% | Rules: {(defaultAcc.rule_pass_rate ?? 100).toFixed(0)}%
            </div>
          </div>
        </div>

        {/* Detailed Breakdown */}
        <div className="space-y-2 rounded-lg border bg-muted/30 p-3">
          <div className="font-semibold text-muted-foreground text-[11px] uppercase tracking-wider">
            Cost Component Breakdown
          </div>
          <div className="flex justify-between items-center py-1 border-b border-border/40">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Cpu className="size-3 text-blue-400" /> OpenCV Preprocessing
            </span>
            <span className="font-mono font-medium">${(defaultCost.preprocessing_cost ?? 0.0001).toFixed(4)}</span>
          </div>
          <div className="flex justify-between items-center py-1 border-b border-border/40">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Sparkles className="size-3 text-purple-400" /> OCR Engine Execution
            </span>
            <span className="font-mono font-medium">${(defaultCost.ocr_engine_cost ?? 0.0002).toFixed(4)}</span>
          </div>
          <div className="flex justify-between items-center py-1 border-b border-border/40">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <TrendingDown className="size-3 text-amber-400" /> VLM Escalation Router
            </span>
            <span className="font-mono font-medium">${(defaultCost.vlm_llm_cost ?? 0.0).toFixed(4)}</span>
          </div>
          <div className="flex justify-between items-center py-1 pt-1.5 font-semibold text-foreground">
            <span>Combined Cost per Page</span>
            <span className="font-mono text-emerald-400">${(defaultCost.total_cost ?? 0.0003).toFixed(4)}</span>
          </div>
        </div>

        {/* HITL Recommendation Status */}
        <div className="flex items-center justify-between rounded-lg border p-2.5 bg-card">
          <div className="flex items-center gap-2">
            <UserCheck className={`size-4 ${defaultCost.hitl_recommended ? "text-amber-400" : "text-emerald-400"}`} />
            <div>
              <div className="font-medium text-xs">Human-in-the-Loop (HITL) Status</div>
              <div className="text-[11px] text-muted-foreground">
                {defaultCost.hitl_recommended ? "Escalated for operator verification" : "Straight-Through Processing (STP)"}
              </div>
            </div>
          </div>
          <Badge variant={defaultCost.hitl_recommended ? "destructive" : "secondary"}>
            {defaultCost.hitl_recommended ? "HITL Needed" : "Auto-Approved (STP)"}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
