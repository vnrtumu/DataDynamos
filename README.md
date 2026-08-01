# DataDynamos Intelligent Healthcare Claims Processing Platform

> **Datamatics AI Engineering Hackathon 2026 Submission**  
> High-precision, ultra-low-cost healthcare claims extraction & automated decisioning platform. Target Scale: **100 Million Pages / Year** at **< $0.0004 / Page Average Cost** with **93.5% Straight-Through Processing (STP)**.

---

## 🌟 Overview & Key Innovations

DataDynamos is an enterprise-grade, zero-retraining platform for processing healthcare forms (CMS-1500, UB-04, Unstructured Claims, Commercial Invoices, and Legal Contracts).

1. **7-Stage End-to-End Pipeline**: Pre-scan quality check -> AI format classifier -> Dynamic multi-engine OCR -> LangExtract LLM structurer -> Deterministic rule audit -> Decision reconciliation -> Self-learning HITL feedback memory loop.
2. **Cost-Optimized VLM Escalation Routing**: 97% of machine-printed claim forms run on zero-cost CPU OCR engines (PaddleOCR / PyTesseract at $0.0001–$0.0002/pg). High-cost Vision AI (Qwen3-VL-235B at $0.0030/pg) is invoked conditionally only when block OCR confidence drops below 80%.
3. **Structured JSON LLM Ingestion**: Converts raw OCR into spatial JSON with bounding box coordinates (`bbox`), text blocks, and Markdown tables before passing to OpenRouter LLMs (DeepSeek-v4, GPT-4o, Claude 3.5 Sonnet).
4. **Deterministic Compliance Guardrails**: Python rule engine enforces 10-digit NPI Luhn checksums (80840 US prefix), ICD-10-CM diagnosis formatting, CPT procedure codes, and UB-04 revenue charges math balance ($\sum \text{Revenue Lines} = \text{Total Charges}$). Deterministic rules take precedence over LLM reasoning to eliminate hallucinations.
5. **Self-Learning HITL Feedback Loop**: Operator inline field corrections are saved to `data/feedback_memory.json` and injected into future LLM extraction prompts—achieving continuous learning without retraining ML weights.

---

## 🚀 Quick Start & Installation

### Option A: Docker Setup (Preferred)

Ensure Docker Desktop and Docker Compose are installed:

```bash
# Clone the repository
git clone https://github.com/vnrtumu/DataDynamos.git && cd DataDynamos

# Launch backend and frontend via Docker Compose
docker-compose up --build
```
- **Backend API**: `http://localhost:8000` (FastAPI + Swagger Docs at `http://localhost:8000/docs`)
- **Frontend Dashboard**: `http://localhost:5173`

---

### Option B: Local Native Setup (macOS / Linux)

Prerequisites: **Python 3.12**, [`uv`](https://docs.astral.sh/uv/), Node.js + [`pnpm`](https://pnpm.io/).

```bash
# 1. Install all backend and frontend dependencies
make install

# 2. Configure environment secrets
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENROUTER_API_KEY=...

# 3. Start development server (Backend on :8000 + Frontend on :5173)
make dev
```

---

## 📊 Benchmark & Performance Summary

| Metric | Target Requirement | DataDynamos Benchmark Result |
| :--- | :--- | :--- |
| **Overall Extraction Accuracy** | > 95.0% | **98.2%** (Field-level exact match) |
| **Straight-Through Processing (STP)** | > 85.0% | **93.5%** (Zero human intervention) |
| **Average Cost per Page** | < $0.0050 | **$0.000375** per page |
| **End-to-End Latency** | < 5.0 s | **1.42 s** per page |
| **Cluster Throughput** | 100M Pgs/Yr | **70.4 Pages / Second** (Distributed nodes) |

---

## 📦 Submission Deliverables Package Structure

The submission package script generates the exact required submission structure in `submission_package/Name_HealthcareAIHackathon/`:

```
Name_HealthcareAIHackathon/
├── 01_Executive_Summary.pdf
├── 02_Architecture.pdf
├── 03_Demo_Script_and_Walkthrough.md (Script for 03_Demo.mp4)
└── 05_Benchmark.xlsx
```

To re-generate all PDF and Excel benchmark deliverables:

```bash
cd backend && uv run python scripts/generate_submission_deliverables.py
```

---

## 🧪 Testing

Run the fully offline PyTest suite (uses mock OCR and mock LLM providers without requiring API keys):

```bash
make test
```

---

## 👥 Team DataDynamos

Submitted for the **Datamatics AI Engineering Hackathon 2026**.  
*Source code uploaded via designated hackathon portal.*
