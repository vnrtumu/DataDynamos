# DataDynamos Working Prototype Demo Script & Walkthrough (03_Demo.mp4)

**Platform**: DataDynamos Intelligent Healthcare Claims Processing Engine  
**Target Duration**: 10 Minutes  
**Submission File**: `03_Demo.mp4`  

---

## 🎬 Live Demonstration Timed Agenda

### Minute 0:00 - 1:30 | Executive Introduction & Architectural Overview
- **Visual**: Datamatics Hackathon Dashboard & Architecture view.
- **Narrative**: Introduction to Team DataDynamos solution for processing 100M claim pages/year at $0.000375/page average cost.
- **Highlight**: 7-stage processing pipeline and multi-engine OCR orchestration.

### Minute 1:30 - 3:30 | Document Ingestion & Automatic Tier Classification
- **Visual**: Uploading a CMS-1500 claim form (`cms1500_sample.png`) and a UB-04 institutional claim form.
- **Narrative**: Demonstrating Stage 1 OpenCV pre-scan (deskew, resolution normalization) and Stage 2 AI format classification.

### Minute 3:30 - 5:30 | Multi-Engine OCR & Bounding Box Grounding Overlay
- **Visual**: Interactive Page Viewer tab switching between OCR Text, JSON Structure, and Image Bounding Box overlay.
- **Narrative**: Highlighting PaddleOCR/PyTesseract speed (~1.2s), spatial bounding box overlays, and structured OCR JSON feeding into LLMs.

### Minute 5:30 - 7:30 | LLM Field Extraction & Deterministic Rule Engine Audit
- **Visual**: Structured tab displaying extracted fields (Patient Name, NPI, Diagnosis Codes, Total Charges) and Decision Check Trace.
- **Narrative**: Demonstrating 10-digit NPI Luhn checksum, ICD-10 format validation, and UB-04 `revenue_charges_balance` math check.

### Minute 7:30 - 8:30 | Stage 7 Self-Learning HITL Feedback Memory Loop
- **Visual**: Clicking a field value in Stage 7 HITL Review, submitting an operator correction note, and showing persistent learned prompt memory.
- **Narrative**: Demonstrating continuous zero-retraining learning without re-training ML weights.

### Minute 8:30 - 10:00 | Rule Defining Settings & Executive Benchmark Dashboards
- **Visual**: Navigating to Rule Defining Settings, exploring the Rule Audit Meanings Glossary, and opening the Deliverables & Architecture benchmark dashboard.
- **Narrative**: Financial cost breakdown, STP throughput metrics, and closing summary of why Team DataDynamos should win.

---
*Created for Datamatics AI Engineering Hackathon 2026 Submission*
