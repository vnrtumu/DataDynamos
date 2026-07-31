import React, { useState } from "react";
import {
  Sliders,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Save,
  Sparkles,
  FileCheck,
  Building2,
  FileText,
  ScanLine,
  Scale,
  DollarSign,
  ShieldAlert,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface RulePreset {
  id: string;
  name: string;
  description: string;
  cms1500Max: number;
  ub04Max: number;
  invoiceMax: number;
  contractMax: number;
  npiStrict: boolean;
  icd10Strict: boolean;
  cptStrict: boolean;
  ocrConfWarn: number;
  extractionConfWarn: number;
  bankDetailFlag: boolean;
  duplicateCheck: boolean;
}

const PRESETS: RulePreset[] = [
  {
    id: "standard",
    name: "Standard Payer Policy (Default)",
    description: "Balanced automation with strict NPI and coding validation.",
    cms1500Max: 5000,
    ub04Max: 15000,
    invoiceMax: 10000,
    contractMax: 100000,
    npiStrict: true,
    icd10Strict: true,
    cptStrict: true,
    ocrConfWarn: 80,
    extractionConfWarn: 60,
    bankDetailFlag: false,
    duplicateCheck: true,
  },
  {
    id: "strict",
    name: "Strict Regulatory Compliance",
    description: "Zero-tolerance rules; lower caps and high manual review triggers.",
    cms1500Max: 2500,
    ub04Max: 5000,
    invoiceMax: 5000,
    contractMax: 50000,
    npiStrict: true,
    icd10Strict: true,
    cptStrict: true,
    ocrConfWarn: 90,
    extractionConfWarn: 75,
    bankDetailFlag: true,
    duplicateCheck: true,
  },
  {
    id: "fasttrack",
    name: "Fast-Track Auto-Approve",
    description: "High thresholds and permissive checks for high-volume ingestion.",
    cms1500Max: 15000,
    ub04Max: 30000,
    invoiceMax: 25000,
    contractMax: 250000,
    npiStrict: false,
    icd10Strict: false,
    cptStrict: false,
    ocrConfWarn: 70,
    extractionConfWarn: 50,
    bankDetailFlag: false,
    duplicateCheck: true,
  },
];

export function RuleSettingsView() {
  const [activeCategory, setActiveCategory] = useState<
    "all" | "healthcare" | "invoices" | "contracts" | "preflight"
  >("all");

  // Rule State Values
  const [cms1500Max, setCms1500Max] = useState<number>(5000);
  const [ub04Max, setUb04Max] = useState<number>(15000);
  const [invoiceMax, setInvoiceMax] = useState<number>(10000);
  const [contractMax, setContractMax] = useState<number>(100000);

  const [npiStrict, setNpiStrict] = useState<boolean>(true);
  const [icd10Strict, setIcd10Strict] = useState<boolean>(true);
  const [cptStrict, setCptStrict] = useState<boolean>(true);
  const [signaturesRequired, setSignaturesRequired] = useState<boolean>(true);

  const [mathTolerance, setMathTolerance] = useState<number>(0.01);
  const [bankDetailFlag, setBankDetailFlag] = useState<boolean>(false);
  const [duplicateCheck, setDuplicateCheck] = useState<boolean>(true);

  const [minDpi, setMinDpi] = useState<number>(100);
  const [blurWarn, setBlurWarn] = useState<number>(60);
  const [contrastWarn, setContrastWarn] = useState<number>(30);
  const [ocrConfWarn, setOcrConfWarn] = useState<number>(80);
  const [extractionConfWarn, setExtractionConfWarn] = useState<number>(60);

  const [activePreset, setActivePreset] = useState<string>("standard");

  const applyPreset = (preset: RulePreset) => {
    setActivePreset(preset.id);
    setCms1500Max(preset.cms1500Max);
    setUb04Max(preset.ub04Max);
    setInvoiceMax(preset.invoiceMax);
    setContractMax(preset.contractMax);
    setNpiStrict(preset.npiStrict);
    setIcd10Strict(preset.icd10Strict);
    setCptStrict(preset.cptStrict);
    setOcrConfWarn(preset.ocrConfWarn);
    setExtractionConfWarn(preset.extractionConfWarn);
    setBankDetailFlag(preset.bankDetailFlag);
    setDuplicateCheck(preset.duplicateCheck);

    toast.success(`Applied "${preset.name}" rule configuration preset!`);
  };

  const handleSave = () => {
    toast.success("Document Rule Defining Settings Saved Successfully!", {
      description: "Updated threshold limits and automated decisioning criteria.",
    });
  };

  const handleReset = () => {
    applyPreset(PRESETS[0]);
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6">
      {/* Header Banner */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b pb-6">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border bg-purple-500/10 border-purple-500/30 px-3 py-1 text-xs font-medium text-purple-400 mb-2">
            <Sliders className="size-3.5" />
            Document Policy & Rule Defining Settings Engine
          </div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl text-foreground">
            Rule Defining Settings for Uploaded Claims & Documents
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1 max-w-2xl">
            Configure automated validation thresholds, dollar limits, medical coding verification severity, and pre-flight quality constraints.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={handleReset} className="text-xs gap-1.5">
            <RotateCcw className="size-3.5" />
            Reset Defaults
          </Button>
          <Button size="sm" onClick={handleSave} className="text-xs gap-1.5 bg-brand hover:bg-brand/90 text-brand-foreground shadow-xs">
            <Save className="size-3.5" />
            Save Rules
          </Button>
        </div>
      </div>

      {/* Preset Policy Templates Bar */}
      <Card className="border-purple-500/30 bg-purple-500/5">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
            <Sparkles className="size-4 text-purple-400" />
            Rule Configuration Profiles & Policy Presets
          </CardTitle>
          <CardDescription className="text-xs">
            Select a predefined rule profile or customize individual rule parameters below.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {PRESETS.map((p) => {
            const isSelected = activePreset === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => applyPreset(p)}
                className={`flex flex-col items-start gap-1.5 rounded-xl border p-3.5 text-left transition-all ${
                  isSelected
                    ? "border-purple-500 bg-purple-500/15 ring-1 ring-purple-500 shadow-xs"
                    : "border-border/70 bg-card hover:bg-muted/50"
                }`}
              >
                <div className="flex w-full items-center justify-between">
                  <span className="font-semibold text-xs text-foreground">{p.name}</span>
                  {isSelected && <Badge variant="secondary" className="bg-purple-500/20 text-purple-400 text-[10px]">Active</Badge>}
                </div>
                <p className="text-[11px] text-muted-foreground leading-snug">{p.description}</p>
                <div className="mt-1 text-[10px] font-mono text-purple-300">
                  CMS-1500: ${p.cms1500Max.toLocaleString()} • UB-04: ${p.ub04Max.toLocaleString()}
                </div>
              </button>
            );
          })}
        </CardContent>
      </Card>

      {/* Category Filter Tabs */}
      <div className="flex items-center gap-2 border-b pb-2 overflow-x-auto">
        <Button
          variant={activeCategory === "all" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setActiveCategory("all")}
          className="text-xs gap-1.5"
        >
          <Sliders className="size-3.5 text-brand" />
          All Document Rules
        </Button>
        <Button
          variant={activeCategory === "healthcare" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setActiveCategory("healthcare")}
          className="text-xs gap-1.5"
        >
          <FileCheck className="size-3.5 text-emerald-400" />
          Healthcare Claims (CMS-1500 / UB-04)
        </Button>
        <Button
          variant={activeCategory === "invoices" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setActiveCategory("invoices")}
          className="text-xs gap-1.5"
        >
          <Building2 className="size-3.5 text-sky-400" />
          Commercial Invoices
        </Button>
        <Button
          variant={activeCategory === "contracts" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setActiveCategory("contracts")}
          className="text-xs gap-1.5"
        >
          <FileText className="size-3.5 text-amber-400" />
          Contracts & Legal
        </Button>
        <Button
          variant={activeCategory === "preflight" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setActiveCategory("preflight")}
          className="text-xs gap-1.5"
        >
          <ScanLine className="size-3.5 text-purple-400" />
          Pre-flight Quality Thresholds
        </Button>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* 1. Healthcare Claims Rules (CMS-1500 & UB-04) */}
        {(activeCategory === "all" || activeCategory === "healthcare") && (
          <Card className="border-border/70 shadow-2xs">
            <CardHeader className="pb-3 border-b bg-emerald-500/5">
              <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
                <FileCheck className="size-4 text-emerald-400" />
                Healthcare Claim Processing Rules (Tiers A, B, C)
              </CardTitle>
              <CardDescription className="text-xs">
                Auto-approval dollar limits, NPI Luhn validation, ICD-10 & CPT coding checks.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {/* CMS-1500 Limit */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground flex items-center gap-1.5">
                    <DollarSign className="size-3.5 text-emerald-400" />
                    CMS-1500 Max Auto-Approve Threshold:
                  </label>
                  <span className="font-mono font-semibold text-emerald-400 text-sm">
                    ${cms1500Max.toLocaleString()}
                  </span>
                </div>
                <input
                  type="range"
                  min={1000}
                  max={25000}
                  step={500}
                  value={cms1500Max}
                  onChange={(e) => setCms1500Max(Number(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <p className="text-[11px] text-muted-foreground">
                  Claims with total charges exceeding this amount are routed to HITL manual review.
                </p>
              </div>

              {/* UB-04 Limit */}
              <div className="space-y-1.5 pt-2 border-t">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground flex items-center gap-1.5">
                    <DollarSign className="size-3.5 text-emerald-400" />
                    UB-04 Institutional Max Auto-Approve Threshold:
                  </label>
                  <span className="font-mono font-semibold text-emerald-400 text-sm">
                    ${ub04Max.toLocaleString()}
                  </span>
                </div>
                <input
                  type="range"
                  min={5000}
                  max={50000}
                  step={1000}
                  value={ub04Max}
                  onChange={(e) => setUb04Max(Number(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>

              {/* NPI Luhn Toggle */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div>
                  <div className="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <ShieldCheck className="size-3.5 text-sky-400" />
                    Strict NPI Luhn Algorithm Check
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Enforce 10-digit National Provider Identifier checksum validation (ANSI A3).
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setNpiStrict((v) => !v)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                    npiStrict ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-muted text-muted-foreground border"
                  }`}
                >
                  {npiStrict ? "ENABLED" : "DISABLED"}
                </button>
              </div>

              {/* ICD-10 Verification */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div>
                  <div className="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <CheckCircle2 className="size-3.5 text-purple-400" />
                    Strict ICD-10 & CPT Code Syntax
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Validate diagnosis and procedure codes against medical coding standards.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setIcd10Strict((v) => !v)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                    icd10Strict ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-muted text-muted-foreground border"
                  }`}
                >
                  {icd10Strict ? "ENABLED" : "DISABLED"}
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 2. Commercial Invoices Rules */}
        {(activeCategory === "all" || activeCategory === "invoices") && (
          <Card className="border-border/70 shadow-2xs">
            <CardHeader className="pb-3 border-b bg-sky-500/5">
              <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
                <Building2 className="size-4 text-sky-400" />
                Commercial Invoices & Accounts Payable Rules
              </CardTitle>
              <CardDescription className="text-xs">
                Line item math tolerance, duplicate detection, and high-value approvals.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {/* Invoice Limit */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground flex items-center gap-1.5">
                    <DollarSign className="size-3.5 text-sky-400" />
                    Invoice Max Auto-Approve Limit:
                  </label>
                  <span className="font-mono font-semibold text-sky-400 text-sm">
                    ${invoiceMax.toLocaleString()}
                  </span>
                </div>
                <input
                  type="range"
                  min={1000}
                  max={50000}
                  step={1000}
                  value={invoiceMax}
                  onChange={(e) => setInvoiceMax(Number(e.target.value))}
                  className="w-full accent-sky-500 cursor-pointer"
                />
              </div>

              {/* Math Tolerance */}
              <div className="space-y-1.5 pt-2 border-t">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground">
                    Line Item Total Calculation Allowance:
                  </label>
                  <span className="font-mono font-semibold text-foreground text-xs">
                    ±${mathTolerance.toFixed(2)}
                  </span>
                </div>
                <input
                  type="range"
                  min={0.00}
                  max={1.00}
                  step={0.01}
                  value={mathTolerance}
                  onChange={(e) => setMathTolerance(Number(e.target.value))}
                  className="w-full accent-sky-500 cursor-pointer"
                />
              </div>

              {/* Bank Detail Flag */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div>
                  <div className="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <ShieldAlert className="size-3.5 text-amber-400" />
                    Flag on New Bank Account Details
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Force review if wire/bank routing details are detected.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setBankDetailFlag((v) => !v)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                    bankDetailFlag ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" : "bg-muted text-muted-foreground border"
                  }`}
                >
                  {bankDetailFlag ? "FLAG" : "IGNORE"}
                </button>
              </div>

              {/* Duplicate Check */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div>
                  <div className="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <AlertTriangle className="size-3.5 text-red-400" />
                    Duplicate Invoice Number Safeguard
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Check prior processed claims database for matching invoice numbers.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setDuplicateCheck((v) => !v)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                    duplicateCheck ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-muted text-muted-foreground border"
                  }`}
                >
                  {duplicateCheck ? "ENABLED" : "DISABLED"}
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 3. Contracts Rules */}
        {(activeCategory === "all" || activeCategory === "contracts") && (
          <Card className="border-border/70 shadow-2xs">
            <CardHeader className="pb-3 border-b bg-amber-500/5">
              <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
                <FileText className="size-4 text-amber-400" />
                Legal Contracts & Agreements Rules
              </CardTitle>
              <CardDescription className="text-xs">
                Value thresholds, governing jurisdiction checks, signature requirements.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {/* Contract Review Threshold */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground flex items-center gap-1.5">
                    <Scale className="size-3.5 text-amber-400" />
                    Contract Value Review Threshold:
                  </label>
                  <span className="font-mono font-semibold text-amber-400 text-sm">
                    ${contractMax.toLocaleString()}
                  </span>
                </div>
                <input
                  type="range"
                  min={10000}
                  max={500000}
                  step={10000}
                  value={contractMax}
                  onChange={(e) => setContractMax(Number(e.target.value))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
              </div>

              {/* Signatures Required */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div>
                  <div className="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <CheckCircle2 className="size-3.5 text-amber-400" />
                    Mandatory Dual Signature Verification
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Require detected signatures on file for both parties.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSignaturesRequired((v) => !v)}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                    signaturesRequired ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" : "bg-muted text-muted-foreground border"
                  }`}
                >
                  {signaturesRequired ? "REQUIRED" : "OPTIONAL"}
                </button>
              </div>

              {/* Approved Governing Law */}
              <div className="pt-2 border-t space-y-1.5">
                <div className="text-xs font-medium text-foreground">
                  Allowed Governing Law Jurisdictions:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {["Delaware", "New York", "California", "England & Wales"].map((jurisdiction) => (
                    <Badge key={jurisdiction} variant="outline" className="bg-amber-500/10 text-amber-300 border-amber-500/30 text-[11px]">
                      {jurisdiction}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 4. Pre-flight Quality Rules */}
        {(activeCategory === "all" || activeCategory === "preflight") && (
          <Card className="border-border/70 shadow-2xs">
            <CardHeader className="pb-3 border-b bg-purple-500/5">
              <CardTitle className="text-sm font-semibold flex items-center gap-2 text-foreground">
                <ScanLine className="size-4 text-purple-400" />
                Pre-flight Document Scan Quality Rules
              </CardTitle>
              <CardDescription className="text-xs">
                Minimum image DPI, blur, contrast, and OCR confidence warnings.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {/* Min DPI */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground">
                    Minimum Effective DPI Floor:
                  </label>
                  <span className="font-mono font-semibold text-purple-400 text-xs">
                    {minDpi} DPI
                  </span>
                </div>
                <input
                  type="range"
                  min={72}
                  max={300}
                  step={10}
                  value={minDpi}
                  onChange={(e) => setMinDpi(Number(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>

              {/* OCR Confidence Warning */}
              <div className="space-y-1.5 pt-2 border-t">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground">
                    OCR Confidence Threshold Warning:
                  </label>
                  <span className="font-mono font-semibold text-purple-400 text-xs">
                    {ocrConfWarn}%
                  </span>
                </div>
                <input
                  type="range"
                  min={50}
                  max={95}
                  step={5}
                  value={ocrConfWarn}
                  onChange={(e) => setOcrConfWarn(Number(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>

              {/* Structuring Extraction Confidence Warning */}
              <div className="space-y-1.5 pt-2 border-t">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-medium text-foreground">
                    LLM Extraction Confidence Warning Floor:
                  </label>
                  <span className="font-mono font-semibold text-purple-400 text-xs">
                    {extractionConfWarn}%
                  </span>
                </div>
                <input
                  type="range"
                  min={40}
                  max={90}
                  step={5}
                  value={extractionConfWarn}
                  onChange={(e) => setExtractionConfWarn(Number(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Footer Info Box */}
      <div className="rounded-xl border border-border/70 bg-card p-4 flex items-start gap-3 text-xs text-muted-foreground shadow-xs">
        <Info className="size-4 text-brand shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-foreground">Automated Rule Engine Protocol:</span> Rules defined on this page govern the zero-intervention claim processing pipeline. Hard severity rule failures automatically route uploaded documents to Human-in-the-Loop (HITL) review.
        </div>
      </div>
    </div>
  );
}
