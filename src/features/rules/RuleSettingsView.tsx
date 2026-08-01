import React, { useState, useMemo } from "react";
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
  BookOpen,
  Search,
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

interface RuleGlossaryItem {
  name: string;
  code: string;
  category: "healthcare" | "invoices" | "contracts" | "preflight";
  severity: "hard" | "review" | "advisory";
  summary: string;
  explanation: string;
}

const RULE_GLOSSARY: RuleGlossaryItem[] = [
  // Healthcare - CMS-1500
  {
    name: "Patient Identity Match",
    code: "patient_identity_match [ANSI A1]",
    category: "healthcare",
    severity: "hard",
    summary: "Cross-references Box 2 Patient Name & Box 3 Date of Birth against active payer patient registry.",
    explanation: "Ensures the patient listed on the claim is an active covered beneficiary under the policy. Mismatches prevent paying claims under fraudulent or misspelled patient profiles.",
  },
  {
    name: "Insured ID Active",
    code: "insured_id_active [ANSI A2]",
    category: "healthcare",
    severity: "hard",
    summary: "Validates Box 1a Insured's Policy ID format and active coverage on date of service.",
    explanation: "Checks that the primary insurance policy number is active on the specific date medical services were provided. Fails if policy is lapsed, cancelled, or invalid.",
  },
  {
    name: "Insurance Type Selection Match",
    code: "insurance_type_match [ANSI A3]",
    category: "healthcare",
    severity: "review",
    summary: "Confirms Box 1 coverage type selection (Medicare, Medicaid, TRICARE, Commercial) aligns with policy.",
    explanation: "Audits whether the primary payer designated on the claim matches the patient's enrolled plan type.",
  },
  {
    name: "Billing Provider NPI Checksum",
    code: "billing_npi_nppes_active [ANSI B1]",
    category: "healthcare",
    severity: "hard",
    summary: "Validates Box 33a Billing Provider 10-digit NPI using Luhn check digit algorithm (80840 US prefix).",
    explanation: "Ensures the billing organization or physician possesses an active, legitimate NPI registered in the National Plan & Provider Enumeration System (NPPES).",
  },
  {
    name: "Rendering Provider NPI Checksum",
    code: "rendering_npi_nppes_active [ANSI B2]",
    category: "healthcare",
    severity: "hard",
    summary: "Validates Box 24J Rendering Physician 10-digit NPI via Luhn check digit algorithm.",
    explanation: "Verifies that the individual practitioner who rendered the medical treatment has a valid, unrevoked NPI license.",
  },
  {
    name: "Tax ID & NPI Entity Match",
    code: "tax_id_npi_match [ANSI B3]",
    category: "healthcare",
    severity: "review",
    summary: "Cross-references Box 25 Provider Federal Tax ID / EIN with the billing NPI organizational entity.",
    explanation: "Audits whether the tax identification number provided matches IRS records for the billing provider's registered business entity.",
  },
  {
    name: "Provider Billing Address Match",
    code: "provider_address_match [ANSI B4]",
    category: "healthcare",
    severity: "review",
    summary: "Confirms Box 33 Billing Provider Address matches contracted practice location records.",
    explanation: "Protects against billing fraud by verifying that payments are remitted to an authorized, contracted clinic or hospital address.",
  },
  {
    name: "ICD-10 Diagnosis Code Audit",
    code: "icd10_valid [ANSI C1]",
    category: "healthcare",
    severity: "hard",
    summary: "Audits Box 21 diagnosis codes against standard ICD-10-CM formatting rules (e.g. E11.9, G31.84).",
    explanation: "Verifies that all listed medical condition codes conform to valid ICD-10 clinical diagnosis standards.",
  },
  {
    name: "CPT/HCPCS Procedure Code Audit",
    code: "cpt_hcpcs_valid [ANSI C2]",
    category: "healthcare",
    severity: "review",
    summary: "Validates Box 24D 5-character CPT/HCPCS procedure codes format.",
    explanation: "Confirms medical procedures, treatments, or surgeries billed on service lines represent valid 5-digit CPT/HCPCS medical codes.",
  },
  {
    name: "Diagnosis Pointer Linkage",
    code: "diagnosis_pointer_valid [ANSI C3]",
    category: "healthcare",
    severity: "review",
    summary: "Verifies Box 24E diagnosis pointers correctly link line-item CPT procedure codes back to Box 21 diagnosis codes A–L.",
    explanation: "Audits medical necessity by proving that each billed procedure is explicitly justified by a corresponding diagnosed medical condition.",
  },
  {
    name: "Place of Service (POS) Alignment",
    code: "place_of_service_valid [ANSI C4]",
    category: "healthcare",
    severity: "review",
    summary: "Confirms Box 24B Place of Service code (e.g. 11 Office, 21 Hospital) matches procedure guidelines.",
    explanation: "Ensures the setting where treatment was provided (e.g. outpatient clinic vs inpatient hospital) is appropriate for the billed procedure code.",
  },
  {
    name: "CMS-1500 Total Charge Balance Math",
    code: "charge_balance [ANSI D2]",
    category: "healthcare",
    severity: "hard",
    summary: "Calculates sum of (Box 24F Line Charges x Units) and verifies it equals Box 28 Total Charge.",
    explanation: "Fails if the sum of individual line item charges does not equal the claimed Total Charge on the CMS-1500 form.",
  },
  {
    name: "CMS-1500 Balance Due Math",
    code: "balance_due_math [ANSI D3]",
    category: "healthcare",
    severity: "hard",
    summary: "Verifies Box 30 Balance Due equals Box 28 Total Charge minus Box 29 Amount Paid.",
    explanation: "Checks financial arithmetic to ensure patient co-pays or prior payments are correctly deducted from the remaining balance due.",
  },
  {
    name: "Signature on File (SOF) Release",
    code: "signature_on_file [ANSI E1]",
    category: "healthcare",
    severity: "review",
    summary: "Verifies Box 12 & 13 Signature on File (SOF) assignment of benefits release indicators are on record.",
    explanation: "Confirms the patient has signed a legal release authorizing medical records disclosure and direct payment to the provider.",
  },
  {
    name: "Prior Authorization Approval",
    code: "prior_authorization_valid [ANSI E2]",
    category: "healthcare",
    severity: "review",
    summary: "Confirms Box 23 Prior Authorization pre-approval number is active and approved.",
    explanation: "Verifies high-cost specialized treatments or surgeries received pre-service insurance approval prior to billing.",
  },

  // Healthcare - UB-04
  {
    name: "Revenue Charges Balance Audit",
    code: "revenue_charges_balance",
    category: "healthcare",
    severity: "hard",
    summary: "Calculates sum of itemized revenue line charges (Boxes 42–47) and verifies equality to Box 47 line 23 Total Charges.",
    explanation: "A critical institutional financial check. Ensures the sum of itemized hospital room, pharmacy, and supply charges equals the total claimed charges on UB-04 forms.",
  },
  {
    name: "Attending Physician NPI Checksum",
    code: "attending_npi_checksum",
    category: "healthcare",
    severity: "hard",
    summary: "Runs 10-digit Luhn checksum validation on Box 76 Attending Physician NPI.",
    explanation: "Ensures the supervising hospital physician responsible for patient care has a valid, active NPI.",
  },
  {
    name: "Federal Tax ID 9-Digit Format",
    code: "federal_tax_id_format",
    category: "healthcare",
    severity: "review",
    summary: "Audits Box 5 Federal Tax ID for standard 9-digit EIN formatting.",
    explanation: "Verifies hospital or facility tax identification format for IRS 1099 compliance.",
  },
  {
    name: "Institutional Patient & Health Plan ID",
    code: "institutional_patient_id",
    category: "healthcare",
    severity: "hard",
    summary: "Verifies both Patient Name (Box 8) and Health Plan ID (Box 60) are present on institutional claim forms.",
    explanation: "Fails if hospital claim forms are submitted missing primary patient identity or health plan membership details.",
  },

  // Invoices
  {
    name: "Invoice Subtotal + Tax Math Balance",
    code: "total_math",
    category: "invoices",
    severity: "hard",
    summary: "Verifies Subtotal + Tax = Total Charges (within +/- $0.01 tolerance).",
    explanation: "Audits commercial invoice line arithmetic. Prevents paying vendor invoices with calculation errors or hidden fees.",
  },
  {
    name: "Duplicate Invoice Number Safeguard",
    code: "duplicate_invoice_no",
    category: "invoices",
    severity: "hard",
    summary: "Queries historical database to block processing if the invoice number was already paid or processed.",
    explanation: "A key accounts payable control that blocks double payments by detecting duplicate invoice numbers across previously processed vendors.",
  },
  {
    name: "Invoice Auto-Approve Threshold Cap",
    code: "auto_approve_threshold",
    category: "invoices",
    severity: "review",
    summary: "Routes commercial invoices with total charges exceeding dollar cap (e.g. $10,000) to HITL manual review.",
    explanation: "Enforces financial delegation of authority rules by requiring manager sign-off for large enterprise purchases.",
  },
  {
    name: "Purchase Order (PO) Presence",
    code: "po_present",
    category: "invoices",
    severity: "advisory",
    summary: "Checks if a Purchase Order (PO) reference number is present on the invoice.",
    explanation: "Flags non-PO invoices to ensure accounts payable teams can match billing to approved procurement requisitions.",
  },

  // Contracts
  {
    name: "Mandatory Signature Execution Audit",
    code: "signatures_present",
    category: "contracts",
    severity: "hard",
    summary: "Fails if executed signatures for both contracting parties are missing from the document.",
    explanation: "Ensures legal contracts are fully executed and legally binding before archiving or activating terms.",
  },
  {
    name: "Auto-Renewal Without Notice Risk",
    code: "auto_renew_without_notice",
    category: "contracts",
    severity: "hard",
    summary: "Flags contracts that auto-renew automatically without specifying a required cancellation notice window.",
    explanation: "Protects against surprise recurring financial commitments by identifying evergreen clauses lacking cancellation notice windows.",
  },
  {
    name: "Standard Termination Clause Presence",
    code: "termination_clause_present",
    category: "contracts",
    severity: "review",
    summary: "Verifies the presence of a standard termination/exit clause in the contract text.",
    explanation: "Ensures the organization retains legal rights to terminate agreements for cause or convenience.",
  },
  {
    name: "Limitation of Liability Cap Audit",
    code: "liability_cap_present",
    category: "contracts",
    severity: "review",
    summary: "Checks for the presence of a Limitation of Liability clause to limit financial exposure.",
    explanation: "Identifies contracts with uncapped financial liability exposure so legal counsel can negotiate liability caps.",
  },
  {
    name: "Approved Governing Law Jurisdiction",
    code: "governing_law_allowed",
    category: "contracts",
    severity: "review",
    summary: "Confirms governing jurisdiction matches approved list (Delaware, New York, California, England & Wales).",
    explanation: "Prevents entering contracts governed by unfamiliar or unfavorable legal jurisdictions.",
  },

  // Pre-flight Quality
  {
    name: "AI Extraction Confidence Warning",
    code: "extraction_confidence",
    category: "preflight",
    severity: "review",
    summary: "Triggers manual review if overall AI field extraction confidence falls below warning floor (e.g. 60%).",
    explanation: "Acts as a safety net against noisy OCR by flagging low-confidence extractions before business rules run.",
  },
  {
    name: "Pre-flight Scan Quality Verdict",
    code: "prescan_quality",
    category: "preflight",
    severity: "review",
    summary: "Ensures scanned document passes minimum DPI, blur, deskew, and contrast quality checks.",
    explanation: "Prevents processing severely blurred or illegible scans that would lead to inaccurate data extraction.",
  },
];

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
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Filter glossary items based on category and search query
  const filteredGlossary = useMemo(() => {
    return RULE_GLOSSARY.filter((item) => {
      const matchCategory =
        activeCategory === "all" || item.category === activeCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchSearch =
        !q ||
        item.name.toLowerCase().includes(q) ||
        item.code.toLowerCase().includes(q) ||
        item.summary.toLowerCase().includes(q) ||
        item.explanation.toLowerCase().includes(q);
      return matchCategory && matchSearch;
    });
  }, [activeCategory, searchQuery]);

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

      {/* Rule Audit Meanings & Specifications Dictionary */}
      <Card className="border-border/80 shadow-sm mt-4">
        <CardHeader className="pb-3 border-b bg-muted/30">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <CardTitle className="text-base font-bold flex items-center gap-2 text-foreground">
                <BookOpen className="size-4 text-purple-400" />
                Automated Financial & Compliance Audit Rule Meanings Glossary
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                Complete technical specification, severity levels, and business meanings for all automated audit checks in the system.
              </CardDescription>
            </div>
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-2.5 size-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search rule names, codes, or terms..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border bg-background pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-4 sm:p-6">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredGlossary.map((item) => (
              <div
                key={item.code}
                className="flex flex-col justify-between rounded-xl border border-border/70 bg-card p-4 transition-all hover:border-purple-500/40 hover:shadow-2xs"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="font-semibold text-xs text-foreground leading-snug">
                      {item.name}
                    </span>
                    <Badge
                      variant="outline"
                      className={`text-[10px] shrink-0 font-mono ${
                        item.severity === "hard"
                          ? "border-rose-500/40 bg-rose-500/10 text-rose-400"
                          : item.severity === "review"
                          ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
                          : "border-sky-500/40 bg-sky-500/10 text-sky-300"
                      }`}
                    >
                      {item.severity.toUpperCase()} FAIL
                    </Badge>
                  </div>
                  <div className="font-mono text-[10px] text-purple-300 bg-purple-500/10 rounded px-1.5 py-0.5 w-fit mb-2">
                    {item.code}
                  </div>
                  <p className="text-[11px] text-foreground/90 font-medium leading-relaxed mb-2">
                    {item.summary}
                  </p>
                  <p className="text-[11px] text-muted-foreground leading-relaxed border-t border-dashed pt-2">
                    <span className="font-semibold text-foreground/80">Business Meaning: </span>
                    {item.explanation}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {filteredGlossary.length === 0 && (
            <div className="py-8 text-center text-xs text-muted-foreground">
              No audit rules found matching "{searchQuery}".
            </div>
          )}
        </CardContent>
      </Card>

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
