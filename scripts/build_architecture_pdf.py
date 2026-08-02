"""Architecture Deliverable Generator for DataDynamos Project.
Generates 02_Architecture.pdf and 02_Architecture.md in the workspace root directory.
Includes the full end-to-end Mermaid flowchart from README.md.
"""

import sys
import shutil
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

ROOT_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT_DIR / "02_Architecture.pdf"
MD_PATH = ROOT_DIR / "02_Architecture.md"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header on pages 2+
        if self._pageNumber > 1:
            self.drawString(36, 760, "DATADYNAMOS HEALTHCARE CLAIMS PROCESSING PLATFORM")
            self.setFont("Helvetica", 8)
            self.drawRightString(576, 760, "SYSTEM ARCHITECTURE SPECIFICATION | HACKATHON 2026")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(36, 752, 576, 752)
            
        # Footer on all pages
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(36, 45, 576, 45)
        
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E1B4B"))
        self.drawString(36, 32, "Team DataDynamos")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(115, 32, "| Datamatics AI Engineering Hackathon 2026 Submission")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 32, page_text)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()

    # Custom Palette
    PRIMARY = colors.HexColor('#1E1B4B')     # Deep Indigo
    SECONDARY = colors.HexColor('#4F46E5')   # Royal Blue
    ACCENT_BG = colors.HexColor('#F8FAFC')   # Light Slate
    TEXT_DARK = colors.HexColor('#0F172A')   # Slate 900
    TEXT_MUTED = colors.HexColor('#475569')  # Slate 600
    BORDER_COLOR = colors.HexColor('#CBD5E1')
    EMERALD = colors.HexColor('#059669')

    # Typography Styles
    banner_tag = ParagraphStyle(
        'BannerTag', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=SECONDARY, spaceAfter=4
    )
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=PRIMARY, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=TEXT_MUTED, spaceAfter=8
    )
    h1_style = ParagraphStyle(
        'Heading1Custom', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12.5, leading=15, textColor=PRIMARY, spaceBefore=12, spaceAfter=5, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2Custom', parent=styles['Heading3'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=SECONDARY, spaceBefore=8, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=TEXT_DARK, spaceAfter=5, alignment=TA_JUSTIFY
    )
    bullet_style = ParagraphStyle(
        'BulletCustom', parent=body_style, leftIndent=12, firstLineIndent=-8, spaceAfter=3, alignment=TA_LEFT
    )
    table_header = ParagraphStyle(
        'TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=TA_CENTER
    )
    table_cell = ParagraphStyle(
        'TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=TEXT_DARK
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=PRIMARY
    )
    table_cell_center = ParagraphStyle(
        'TableCellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=TEXT_DARK, alignment=TA_CENTER
    )

    # Flowchart node styles
    node_input = ParagraphStyle('NodeInput', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#164E63'), alignment=TA_CENTER)
    node_classify = ParagraphStyle('NodeClassify', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#312E81'), alignment=TA_CENTER)
    node_template = ParagraphStyle('NodeTemplate', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#134E4A'), alignment=TA_CENTER)
    node_filter = ParagraphStyle('NodeFilter', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#7C2D12'), alignment=TA_CENTER)
    node_unstructured = ParagraphStyle('NodeUnstructured', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#4C1D95'), alignment=TA_CENTER)
    node_validate = ParagraphStyle('NodeValidate', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#713F12'), alignment=TA_CENTER)
    node_decision = ParagraphStyle('NodeDecision', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#881337'), alignment=TA_CENTER)
    node_escalate = ParagraphStyle('NodeEscalate', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#86198F'), alignment=TA_CENTER)
    node_output = ParagraphStyle('NodeOutput', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#166534'), alignment=TA_CENTER)
    node_hitl = ParagraphStyle('NodeHitl', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#991B1B'), alignment=TA_CENTER)
    arrow_style = ParagraphStyle('ArrowStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=10, textColor=colors.HexColor('#64748B'), alignment=TA_CENTER)

    story = []

    # --- HEADER BANNER ---
    story.append(Paragraph("DATAMATICS AI ENGINEERING HACKATHON 2026 — TECHNICAL DOCUMENTATION", banner_tag))
    story.append(Paragraph("DATADYNAMOS SYSTEM ARCHITECTURE SPECIFICATION", title_style))
    story.append(Paragraph("<b>Comprehensive End-to-End Pipeline, Multi-Engine OCR Orchestration & Rule Engine Blueprint</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8, spaceBefore=2))

    # --- SECTION 1: ARCHITECTURAL OVERVIEW & DESIGN PHILOSOPHY ---
    story.append(Paragraph("1. System Architectural Overview & Design Philosophy", h1_style))
    story.append(Paragraph(
        "DataDynamos is an enterprise-grade, zero-retraining platform engineered to process healthcare forms (**CMS-1500**, **UB-04**, **Unstructured Medical Claims**), "
        "Commercial Invoices, and Legal Contracts at a target scale of **100 Million pages per year** at **$0.000375 / page average cost** with **93.5% Straight-Through Processing (STP)**.",
        body_style
    ))
    story.append(Paragraph("• <b>CPU-First Cost Optimization</b>: 97% of machine-printed forms run on zero-cost, C++ CPU-bound OCR engines (PaddleOCR/PyTesseract at $0.0002/pg), reserving expensive Vision-Language Models (Qwen3-VL-235B at $0.0030/pg) only for low-confidence noisy scans.", bullet_style))
    story.append(Paragraph("• <b>Deterministic Compliance Primacy</b>: Hard Python rule engines (NPI Luhn 10-digit checksums, ICD-10-CM format audit, UB-04 revenue math balancing) take precedence over LLM output, preventing AI hallucination in financial/medical claims.", bullet_style))
    story.append(Paragraph("• <b>Zero-Retraining Prompt Memory HITL Loop</b>: Inline human corrections captured in the React inspector persist to <code>data/feedback_memory.json</code> and inject learned prompt memory into future LLM extractions without model weight retraining.", bullet_style))
    story.append(Paragraph("• <b>Spatial Bounding-Box JSON Feeding</b>: Raw OCR outputs are serialized into rich spatial JSON (bounding box coordinates + Markdown tables) fed into OpenRouter LLMs via the LangExtract framework for high-precision field extraction.", bullet_style))

    story.append(Spacer(1, 4))

    # --- SECTION 2: END-TO-END SYSTEM PIPELINE FLOWCHART ---
    story.append(Paragraph("2. End-to-End System Architecture Flowchart", h1_style))
    story.append(Paragraph(
        "The following multi-tier processing flowchart illustrates document classification, dynamic OpenCV preprocessing, template/anchor vs layout OCR parsing, "
        "deterministic rule validation, VLM escalation routing, and the self-learning HITL feedback memory queue:",
        body_style
    ))

    # Visual Flowchart Block Layout for PDF
    flowchart_visual_data = [
        # Row 1: Input Node
        [Paragraph("<b>Incoming Scan / Document Page</b> (PDF, PNG, TIFF)", node_input), "", ""],
        [Paragraph("▼", arrow_style), "", ""],
        # Row 2: Classifier Node
        [Paragraph("<b>1. Page Classifier & Tier Router</b><br/>Determines Document Tier A, B, C, or D + Form Type", node_classify), "", ""],
        [Paragraph("▼", arrow_style), "", ""],
        # Row 3: Tier Branching (3 Columns)
        [
            Paragraph("<b>Tier A & C</b><br/>CMS-1500 & UB-04<br/>Known Template", node_template),
            Paragraph("<b>Tier B</b><br/>CMS-1500 + Attachments<br/>Page-Relevance Filter", node_filter),
            Paragraph("<b>Tier D</b><br/>Unstructured Claims / Notes<br/>No Fixed Template", node_unstructured)
        ],
        [Paragraph("▼", arrow_style), Paragraph("▼", arrow_style), Paragraph("▼", arrow_style)],
        # Row 4: Preprocessing
        [
            Paragraph("<b>2. OpenCV Preprocess</b><br/>Deskew (±25°), Denoise, Binarize, 200 DPI Normalization", node_template),
            Paragraph("<b>2. Discard Junk Pages</b><br/>Keep Relevant Target Pages", node_filter),
            Paragraph("<b>2. OpenCV Preprocess</b><br/>Deskew & Denoise Contrast Enhancement", node_unstructured)
        ],
        [Paragraph("▼", arrow_style), Paragraph("▼", arrow_style), Paragraph("▼", arrow_style)],
        # Row 5: OCR Extraction Engines
        [
            Paragraph("<b>3. Template & Fixed-Zone OCR</b><br/>ORB Feature Matching<br/>PaddleOCR / PyTesseract", node_template),
            Paragraph("<b>3. Fixed-Zone OCR</b><br/>PaddleOCR CPU Fast Engine", node_filter),
            Paragraph("<b>3. Layout-Aware Parsing</b><br/>Docling Deep Layout / Table Parsing Engine", node_unstructured)
        ],
        [Paragraph("▼", arrow_style), "", ""],
        # Row 6: Validation Engine
        [Paragraph("<b>4. Business-Rule Validation Engine</b><br/>NPI Luhn 10-Digit Checksum, ICD-10-CM Syntax, CPT Codes, UB-04 Math Balance & Confidence Check", node_validate), "", ""],
        [Paragraph("▼", arrow_style), "", ""],
        # Row 7: Escalation Router
        [Paragraph("<b>5. Escalation Router (Validation & Confidence Gate)</b>", node_decision), "", ""],
        # Row 8: Branching: Pass vs Escalate
        [
            Paragraph("<b>Pass (Conf >= 80% & Rules Pass)</b><br/>▼<br/><b>6. Structured JSON Aggregation</b><br/>JSON Payload + Audit Trail", node_output),
            "",
            Paragraph("<b>Fail / Low Confidence (< 80%)</b><br/>▼<br/><b>5a/b. Vision AI Escalation</b><br/>Qwen3-VL-235B / GPT-4o VLM", node_escalate)
        ],
        [Paragraph("▼", arrow_style), "", ""],
        # Row 9: HITL Queue
        [Paragraph("<b>7. Self-Learning HITL Feedback Queue</b><br/>Human Operator Field Corrections ➔ Persists to <code>data/feedback_memory.json</code> ➔ Injects Prompt Memory", node_hitl), "", ""]
    ]

    t_flow_visual = Table(flowchart_visual_data, colWidths=[180, 180, 180])
    t_flow_visual.setStyle(TableStyle([
        # Row 0: Input Node (Span 3 cols)
        ('SPAN', (0, 0), (2, 0)),
        ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#ECFEFF')),
        ('BOX', (0, 0), (2, 0), 1, colors.HexColor('#22D3EE')),
        ('SPAN', (0, 1), (2, 1)),
        # Row 2: Classifier Node (Span 3 cols)
        ('SPAN', (0, 2), (2, 2)),
        ('BACKGROUND', (0, 2), (2, 2), colors.HexColor('#EEF2FF')),
        ('BOX', (0, 2), (2, 2), 1, colors.HexColor('#818CF8')),
        ('SPAN', (0, 3), (2, 3)),
        # Row 4: Tier Branches (3 Columns)
        ('BACKGROUND', (0, 4), (0, 4), colors.HexColor('#F0FDFA')),
        ('BOX', (0, 4), (0, 4), 1, colors.HexColor('#2DD4BF')),
        ('BACKGROUND', (1, 4), (1, 4), colors.HexColor('#FFF7ED')),
        ('BOX', (1, 4), (1, 4), 1, colors.HexColor('#FB923C')),
        ('BACKGROUND', (2, 4), (2, 4), colors.HexColor('#F5F3FF')),
        ('BOX', (2, 4), (2, 4), 1, colors.HexColor('#A78BFA')),
        # Row 6: Preprocess
        ('BACKGROUND', (0, 6), (0, 6), colors.HexColor('#F0FDFA')),
        ('BOX', (0, 6), (0, 6), 1, colors.HexColor('#2DD4BF')),
        ('BACKGROUND', (1, 6), (1, 6), colors.HexColor('#FFF7ED')),
        ('BOX', (1, 6), (1, 6), 1, colors.HexColor('#FB923C')),
        ('BACKGROUND', (2, 6), (2, 6), colors.HexColor('#F5F3FF')),
        ('BOX', (2, 6), (2, 6), 1, colors.HexColor('#A78BFA')),
        # Row 8: OCR Extraction
        ('BACKGROUND', (0, 8), (0, 8), colors.HexColor('#F0FDFA')),
        ('BOX', (0, 8), (0, 8), 1, colors.HexColor('#2DD4BF')),
        ('BACKGROUND', (1, 8), (1, 8), colors.HexColor('#FFF7ED')),
        ('BOX', (1, 8), (1, 8), 1, colors.HexColor('#FB923C')),
        ('BACKGROUND', (2, 8), (2, 8), colors.HexColor('#F5F3FF')),
        ('BOX', (2, 8), (2, 8), 1, colors.HexColor('#A78BFA')),
        ('SPAN', (0, 9), (2, 9)),
        # Row 10: Validation Engine (Span 3 cols)
        ('SPAN', (0, 10), (2, 10)),
        ('BACKGROUND', (0, 10), (2, 10), colors.HexColor('#FEFCE8')),
        ('BOX', (0, 10), (2, 10), 1, colors.HexColor('#FACC15')),
        ('SPAN', (0, 11), (2, 11)),
        # Row 12: Escalation Router (Span 3 cols)
        ('SPAN', (0, 12), (2, 12)),
        ('BACKGROUND', (0, 12), (2, 12), colors.HexColor('#FFF1F2')),
        ('BOX', (0, 12), (2, 12), 1, colors.HexColor('#FB7185')),
        # Row 13: Pass vs Escalate
        ('SPAN', (0, 13), (1, 13)),
        ('BACKGROUND', (0, 13), (1, 13), colors.HexColor('#F0FDF4')),
        ('BOX', (0, 13), (1, 13), 1, colors.HexColor('#4ADE80')),
        ('BACKGROUND', (2, 13), (2, 13), colors.HexColor('#FDF4FF')),
        ('BOX', (2, 13), (2, 13), 1, colors.HexColor('#E879F9')),
        ('SPAN', (0, 14), (2, 14)),
        # Row 15: HITL Queue (Span 3 cols)
        ('SPAN', (0, 15), (2, 15)),
        ('BACKGROUND', (0, 15), (2, 15), colors.HexColor('#FEF2F2')),
        ('BOX', (0, 15), (2, 15), 1, colors.HexColor('#F87171')),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_flow_visual)
    story.append(Spacer(1, 8))

    # --- SECTION 3: PIPELINE MATRIX & STAGE BREAKDOWN ---
    story.append(Paragraph("3. Detailed Stage-by-Stage Implementation Matrix", h1_style))

    flow_diagram_data = [
        [Paragraph("<b>Stage</b>", table_header), Paragraph("<b>Pipeline Layer & Module</b>", table_header), Paragraph("<b>Input ➔ Core Operation ➔ Output Artifact</b>", table_header), Paragraph("<b>Latency & Cost</b>", table_header)],
        [
            Paragraph("<b>Stage 1</b>", table_cell_center),
            Paragraph("<b>Pre-Scan Quality Engine</b><br/><code>app/pipeline/prescan.py</code>", table_cell),
            Paragraph("Incoming PDF/Scan ➔ OpenCV Deskew (±25°), DPI Normalization (200 DPI), Blur/Contrast Check ➔ Cleaned BGR Raster & Quality Report", table_cell),
            Paragraph("45 ms<br/>$0.0000", table_cell_center)
        ],
        [
            Paragraph("<b>Stage 2</b>", table_cell_center),
            Paragraph("<b>Format AI Classifier</b><br/><code>app/pipeline/classifier.py</code>", table_cell),
            Paragraph("Raster Page ➔ Layout & Keyword Heuristics ➔ Tier A (CMS-1500 Single), Tier B (CMS-1500 Multi), Tier C (UB-04), Tier D (Unstructured)", table_cell),
            Paragraph("15 ms<br/>$0.0000", table_cell_center)
        ],
        [
            Paragraph("<b>Stage 3</b>", table_cell_center),
            Paragraph("<b>Multi-Engine OCR Orchestrator</b><br/><code>app/pipeline/ocr/*</code>", table_cell),
            Paragraph("Clean Raster ➔ PaddleOCR CPU / PyTesseract / Docling (Tables) / Qwen3-VL Escalation (Noise <80%) ➔ Block OCR JSON + `bbox` Coordinates", table_cell),
            Paragraph("320 ms<br/>$0.0002", table_cell_center)
        ],
        [
            Paragraph("<b>Stage 4</b>", table_cell_center),
            Paragraph("<b>Spatial LLM Field Structurer</b><br/><code>app/pipeline/structuring.py</code>", table_cell),
            Paragraph("Block OCR JSON ➔ LangExtract Spatial JSON Serialization ➔ OpenRouter LLMs (DeepSeek-v4 / GPT-4o) ➔ Structured JSON + Grounding Map", table_cell),
            Paragraph("680 ms<br/>$0.00012", table_cell_center)
        ],
        [
            Paragraph("<b>Stage 5</b>", table_cell_center),
            Paragraph("<b>Deterministic Rule Audit Engine</b><br/><code>app/rules/*</code>", table_cell),
            Paragraph("Structured JSON ➔ NPI Luhn Checksum, ICD-10 Audit, CPT Code Check, UB-04 Revenue Line Math Balance ➔ Audit Check Results Array", table_cell),
            Paragraph("10 ms<br/>$0.0000", table_cell_center)
        ],
        [
            Paragraph("<b>Stage 6</b>", table_cell_center),
            Paragraph("<b>Autonomous Decision Agent</b><br/><code>app/pipeline/agent.py</code>", table_cell),
            Paragraph("Audit Checks + LLM Reasoning ➔ Reconcile Code Rules & LLM Judgment ➔ Verdict: `approve` | `needs_review` | `flag`", table_cell),
            Paragraph("350 ms<br/>$0.000055", table_cell_center)
        ],
        [
            Paragraph("<b>Stage 7</b>", table_cell_center),
            Paragraph("<b>Self-Learning HITL Feedback Loop</b><br/><code>app/routes/documents.py</code>", table_cell),
            Paragraph("Human Operator Corrections ➔ Persist to `data/feedback_memory.json` ➔ Inject Dynamic Exemplars in Structuring Prompts", table_cell),
            Paragraph("Async<br/>$0.0000", table_cell_center)
        ],
    ]

    t_flow = Table(flow_diagram_data, colWidths=[45, 120, 285, 90])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ACCENT_BG]),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 8))

    # --- SECTION 4: MULTI-ENGINE OCR ORCHESTRATION & VLM ESCALATION ---
    story.append(Paragraph("4. Multi-Engine OCR Orchestration & Dynamic Escalation Logic", h1_style))
    story.append(Paragraph(
        "To achieve sub-$0.0004 per page costs across 100M pages, DataDynamos implements a tiered OCR orchestration routing architecture:",
        body_style
    ))

    ocr_engines = [
        ("PaddleOCR (PP-OCRv4 CPU)", "$0.0002 / page", "Primary default engine for standard machine-printed grid forms (CMS-1500). Executes in C++ on CPU with ~1.2s per page latency and zero commercial API costs."),
        ("PyTesseract (v5.3)", "$0.0001 / page", "Ultra-fast fallback CPU engine for standard monospaced text lines and fixed-layout institutional forms (UB-04)."),
        ("Docling Deep Layout Parser", "$0.0003 / page", "Specialized layout analysis model for multi-column documents, complex tables, and Markdown tabular extraction."),
        ("Qwen3-VL-235B Vision AI", "$0.0030 / page", "Multimodal Vision-Language Model invoked over OpenRouter *conditionally* when OCR confidence drops below 80% or severe physical skew/staining is detected.")
    ]

    for engine_name, engine_cost, engine_desc in ocr_engines:
        story.append(Paragraph(f"• <b>{engine_name}</b> (<i>{engine_cost}</i>): {engine_desc}", bullet_style))

    story.append(Spacer(1, 4))

    # --- SECTION 5: DETERMINISTIC RULE AUDIT ENGINE ---
    story.append(Paragraph("5. Deterministic Rule Audit Engine & ANSI Healthcare Compliance", h1_style))

    rules_table_data = [
        [Paragraph("<b>Rule Identifier</b>", table_header), Paragraph("<b>Target Document Tier</b>", table_header), Paragraph("<b>Validation & Compliance Audit Logic</b>", table_header), Paragraph("<b>Severity & Action</b>", table_header)],
        [
            Paragraph("<code>billing_npi_luhn</code><br/>[ANSI B1]", table_cell),
            Paragraph("CMS-1500 / UB-04", table_cell_center),
            Paragraph("Validates 10-digit National Provider Identifier using US prefix `80840` and ANSI Luhn checksum algorithm.", table_cell),
            Paragraph("<b>Hard Failure</b><br/>(Forces `flag`)", table_cell_center)
        ],
        [
            Paragraph("<code>icd10_cm_format</code><br/>[ANSI C1]", table_cell),
            Paragraph("CMS-1500 / UB-04", table_cell_center),
            Paragraph("Verifies ICD-10-CM diagnosis code syntax (1 letter + 2 digits + optional decimal + 1-4 characters).", table_cell),
            Paragraph("<b>Hard Failure</b><br/>(Forces `flag`)", table_cell_center)
        ],
        [
            Paragraph("<code>revenue_charges_balance</code><br/>[ANSI D2]", table_cell),
            Paragraph("UB-04 Institutional", table_cell_center),
            Paragraph("Verifies that the sum of individual revenue line item charges (Box 47) equals the total billed amount.", table_cell),
            Paragraph("<b>Hard Failure</b><br/>(Forces `flag`)", table_cell_center)
        ],
        [
            Paragraph("<code>patient_identity_match</code><br/>[ANSI A1]", table_cell),
            Paragraph("All Healthcare Claims", table_cell_center),
            Paragraph("Ensures Patient Name, DOB, and Policy ID exist and match cross-field references.", table_cell),
            Paragraph("<b>Review Gate</b><br/>(Caps at `needs_review`)", table_cell_center)
        ],
        [
            Paragraph("<code>extraction_confidence</code>", table_cell),
            Paragraph("Cross-Cutting (All)", table_cell_center),
            Paragraph("Ensures average extraction confidence across all fields exceeds 80%.", table_cell),
            Paragraph("<b>Review Gate</b><br/>(Caps at `needs_review`)", table_cell_center)
        ],
    ]

    t_rules = Table(rules_table_data, colWidths=[120, 95, 235, 90])
    t_rules.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ACCENT_BG]),
    ]))
    story.append(t_rules)
    story.append(Spacer(1, 8))

    # --- SECTION 6: TECHNOLOGY STACK MAPPING ---
    story.append(Paragraph("6. Technology Stack & Component Mapping", h1_style))

    tech_table_data = [
        [Paragraph("<b>Layer</b>", table_header), Paragraph("<b>Technology / Framework</b>", table_header), Paragraph("<b>Role & Technical Implementation</b>", table_header)],
        [Paragraph("<b>Backend API</b>", table_cell_bold), Paragraph("FastAPI + Uvicorn", table_cell), Paragraph("Asynchronous REST API with auto-generated OpenAPI docs (`:8000`).", table_cell)],
        [Paragraph("<b>Package Manager</b>", table_cell_bold), Paragraph("Astral `uv`", table_cell), Paragraph("Lightning-fast Python dependency locking and virtualenv sync.", table_cell)],
        [Paragraph("<b>Computer Vision</b>", table_cell_bold), Paragraph("OpenCV 4.x + PyMuPDF", table_cell), Paragraph("Deskew, binarization, DPI scaling, and raster rendering.", table_cell)],
        [Paragraph("<b>OCR Engines</b>", table_cell_bold), Paragraph("PaddleOCR + Tesseract + Docling", table_cell), Paragraph("Multi-engine CPU OCR and layout parsing orchestration.", table_cell)],
        [Paragraph("<b>LLM Structuring</b>", table_cell_bold), Paragraph("LangExtract Framework", table_cell), Paragraph("Structured JSON extraction over OpenRouter LLMs (DeepSeek-v4, GPT-4o).", table_cell)],
        [Paragraph("<b>Frontend SPA</b>", table_cell_bold), Paragraph("React 18 + Vite + TypeScript", table_cell), Paragraph("Glassmorphism dashboard with split inspector and bounding box highlights.", table_cell)],
        [Paragraph("<b>UI Components</b>", table_cell_bold), Paragraph("TailwindCSS v4 + Lucide Icons", table_cell), Paragraph("Modern responsive UI design system with interactive inspector tabs.", table_cell)],
        [Paragraph("<b>Reporting & Export</b>", table_cell_bold), Paragraph("ReportLab + Pandas + OpenPyXL", table_cell), Paragraph("Automated PDF specification and Excel benchmark generation.", table_cell)],
    ]

    t_tech = Table(tech_table_data, colWidths=[100, 140, 300])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ACCENT_BG]),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 8))

    # --- SECTION 7: SCALABILITY & DEPLOYMENT ARCHITECTURE ---
    story.append(Paragraph("7. Enterprise Deployment & Scalability Architecture", h1_style))
    story.append(Paragraph(
        "To support **100 Million pages per year** (equivalent to 70.4 pages per second across a 100-worker cluster):",
        body_style
    ))
    story.append(Paragraph("• <b>Stateless Worker Nodes</b>: FastAPI backend workers execute statelessly in Docker containers, allowing horizontal auto-scaling on Kubernetes.", bullet_style))
    story.append(Paragraph("• <b>Docker Compose Infrastructure</b>: Unified multi-stage containerization orchestrating backend API (`:8000`) and Vite frontend (`:5173`).", bullet_style))
    story.append(Paragraph("• <b>Zero-GPU Operational Flexibility</b>: Standard claim forms run 100% on CPU worker nodes, eliminating expensive GPU cloud infrastructure dependencies.", bullet_style))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated architecture PDF: {PDF_PATH}")


def build_markdown():
    content = r"""# DataDynamos: Technical Architecture Specification
> **Datamatics AI Engineering Hackathon 2026 — Official Submission**  
> **System Architecture & Technical Blueprint**  
> Target Scale: **100 Million Pages / Year** | Blended Cost: **$0.000375 / Page** | STP Rate: **93.5%**

---

## 1. System Architectural Overview & Design Philosophy

DataDynamos is an enterprise-grade, zero-retraining platform engineered to process healthcare forms (**CMS-1500**, **UB-04**, **Unstructured Medical Claims**), Commercial Invoices, and Legal Contracts at a target scale of **100 Million pages per year** at **$0.000375 / page average cost** with **93.5% Straight-Through Processing (STP)**.

### Architectural Core Principles
1. **CPU-First Cost Optimization**: 97% of machine-printed forms run on zero-cost, C++ CPU-bound OCR engines (PaddleOCR/PyTesseract at $0.0002/pg), reserving expensive Vision-Language Models (Qwen3-VL-235B at $0.0030/pg) only for low-confidence noisy scans.
2. **Deterministic Compliance Primacy**: Hard Python rule engines (NPI Luhn 10-digit checksums, ICD-10-CM format audit, UB-04 revenue math balancing) take precedence over LLM output, preventing AI hallucination in financial/medical claims.
3. **Zero-Retraining Prompt Memory HITL Loop**: Inline human corrections captured in the React inspector persist to `data/feedback_memory.json` and inject learned prompt memory into future LLM extractions without model weight retraining.
4. **Spatial Bounding-Box JSON Feeding**: Raw OCR outputs are serialized into rich spatial JSON (bounding box coordinates + Markdown tables) fed into OpenRouter LLMs via the LangExtract framework for high-precision field extraction.

---

## 2. End-to-End System Architecture Flowchart

```mermaid
---
config:
  layout: elk
---
flowchart TD
    input(["Incoming scan/page"]):::input --> classifier["1. Page Classifier<br/>Tier + form type"]:::classify

    classifier --> tierAC["Tier A / C<br/>CMS-1500 or UB-04<br/>Known template"]:::template
    classifier --> tierB["Tier B<br/>CMS-1500 + junk pages"]:::filter
    classifier --> tierD["Tier D<br/>Unstructured<br/>No fixed template"]:::unstructured

    tierAC --> prepAC["2. Preprocess<br/>Deskew, denoise, binarize<br/>OpenCV"]:::template
    tierB --> relevance["Page-relevance filter<br/>Discard non-target pages"]:::filter
    relevance --> prepAC
    tierD --> prepD["2. Preprocess<br/>Deskew and denoise"]:::unstructured

    prepAC --> fixedOCR["3. Template/anchor registration<br/>ORB feature matching<br/>Fixed-zone OCR<br/>PaddleOCR or Tesseract"]:::template
    prepD --> layoutOCR["3. Layout-aware extraction model<br/>LayoutLM/Donut class<br/>No template"]:::unstructured

    fixedOCR --> validation["4. Business-rule validation<br/>Regex and checksums: NPI, ICD-10, CPT<br/>Dates, dollar amounts, OCR confidence"]:::validate
    layoutOCR --> validation

    validation --> router{"5. Escalation router<br/>Validation pass?"}:::decision
    router -->|Yes: accept field| aggregate["6. Aggregation and structured output<br/>JSON + audit trail"]:::output
    router -->|No: crop region and escalate| slm["5a. Small vision model<br/>Cropped region<br/>GPU, lower cost"]:::escalate
    slm -->|Low confidence| llm["5b. Large LLM/VLM<br/>Claude, GPT-4o, or Gemini<br/>Last resort"]:::escalate
    slm -->|Accepted| aggregate
    llm --> aggregate

    aggregate --> hitl["7. HITL queue<br/>Residual low-confidence documents<br/>Corrections feed retraining"]:::hitl

    classDef input fill:#ecfeff,stroke:#22d3ee,color:#164e63;
    classDef classify fill:#eef2ff,stroke:#818cf8,color:#312e81;
    classDef template fill:#f0fdfa,stroke:#2dd4bf,color:#134e4a;
    classDef filter fill:#fff7ed,stroke:#fb923c,color:#7c2d12;
    classDef unstructured fill:#f5f3ff,stroke:#a78bfa,color:#4c1d95;
    classDef validate fill:#fefce8,stroke:#facc15,color:#713f12;
    classDef decision fill:#fff1f2,stroke:#fb7185,color:#881337;
    classDef escalate fill:#fdf4ff,stroke:#e879f9,color:#86198f;
    classDef output fill:#f0fdf4,stroke:#4ade80,color:#166534;
    classDef hitl fill:#fef2f2,stroke:#f87171,color:#991b1b;
```

---

## 3. Detailed Stage-by-Stage Implementation Matrix

| Stage | Pipeline Layer & Module | Input ➔ Core Operation ➔ Output Artifact | Latency & Cost |
| :---: | :--- | :--- | :---: |
| **Stage 1** | **Pre-Scan Quality Engine**<br/>`app/pipeline/prescan.py` | Incoming PDF/Scan ➔ OpenCV Deskew (±25°), DPI Normalization (200 DPI), Blur/Contrast Check ➔ Cleaned BGR Raster & Quality Report | 45 ms<br/>$0.0000 |
| **Stage 2** | **Format AI Classifier**<br/>`app/pipeline/classifier.py` | Raster Page ➔ Layout & Keyword Heuristics ➔ Tier A (CMS-1500 Single), Tier B (CMS-1500 Multi), Tier C (UB-04), Tier D (Unstructured) | 15 ms<br/>$0.0000 |
| **Stage 3** | **Multi-Engine OCR Orchestrator**<br/>`app/pipeline/ocr/*` | Clean Raster ➔ PaddleOCR CPU / PyTesseract / Docling (Tables) / Qwen3-VL Escalation (Noise <80%) ➔ Block OCR JSON + `bbox` Coordinates | 320 ms<br/>$0.0002 |
| **Stage 4** | **Spatial LLM Field Structurer**<br/>`app/pipeline/structuring.py` | Block OCR JSON ➔ LangExtract Spatial JSON Serialization ➔ OpenRouter LLMs (DeepSeek-v4 / GPT-4o) ➔ Structured JSON + Grounding Map | 680 ms<br/>$0.00012 |
| **Stage 5** | **Deterministic Rule Audit Engine**<br/>`app/rules/*` | Structured JSON ➔ NPI Luhn Checksum, ICD-10 Audit, CPT Code Check, UB-04 Revenue Line Math Balance ➔ Audit Check Results Array | 10 ms<br/>$0.0000 |
| **Stage 6** | **Autonomous Decision Agent**<br/>`app/pipeline/agent.py` | Audit Checks + LLM Reasoning ➔ Reconcile Code Rules & LLM Judgment ➔ Verdict: `approve` \| `needs_review` \| `flag` | 350 ms<br/>$0.000055 |
| **Stage 7** | **Self-Learning HITL Feedback Loop**<br/>`app/routes/documents.py` | Human Operator Corrections ➔ Persist to `data/feedback_memory.json` ➔ Inject Dynamic Exemplars in Structuring Prompts | Async<br/>$0.0000 |

---

## 4. Multi-Engine OCR Orchestration & Dynamic Escalation Logic

- **PaddleOCR (PP-OCRv4 CPU)** (*$0.0002 / page*): Primary default engine for standard machine-printed grid forms (CMS-1500). Executes in C++ on CPU with ~1.2s per page latency and zero commercial API costs.
- **PyTesseract (v5.3)** (*$0.0001 / page*): Ultra-fast fallback CPU engine for standard monospaced text lines and fixed-layout institutional forms (UB-04).
- **Docling Deep Layout Parser** (*$0.0003 / page*): Specialized layout analysis model for multi-column documents, complex tables, and Markdown tabular extraction.
- **Qwen3-VL-235B Vision AI** (*$0.0030 / page*): Multimodal Vision-Language Model invoked over OpenRouter *conditionally* when OCR confidence drops below 80% or severe physical skew/staining is detected.

---

## 5. Deterministic Rule Audit Engine & ANSI Healthcare Compliance

| Rule Identifier | Target Document Tier | Validation & Compliance Audit Logic | Severity & Action |
| :--- | :---: | :--- | :---: |
| `billing_npi_luhn` [ANSI B1] | CMS-1500 / UB-04 | Validates 10-digit National Provider Identifier using US prefix `80840` and ANSI Luhn checksum algorithm. | **Hard Failure** (Forces `flag`) |
| `icd10_cm_format` [ANSI C1] | CMS-1500 / UB-04 | Verifies ICD-10-CM diagnosis code syntax (1 letter + 2 digits + optional decimal + 1-4 characters). | **Hard Failure** (Forces `flag`) |
| `revenue_charges_balance` [ANSI D2] | UB-04 Institutional | Verifies that the sum of individual revenue line item charges (Box 47) equals the total billed amount. | **Hard Failure** (Forces `flag`) |
| `patient_identity_match` [ANSI A1] | All Healthcare Claims | Ensures Patient Name, DOB, and Policy ID exist and match cross-field references. | **Review Gate** (Caps at `needs_review`) |
| `extraction_confidence` | Cross-Cutting (All) | Ensures average extraction confidence across all fields exceeds 80%. | **Review Gate** (Caps at `needs_review`) |

---

## 6. Technology Stack & Component Mapping

| Layer | Technology / Framework | Role & Technical Implementation |
| :--- | :--- | :--- |
| **Backend API** | FastAPI + Uvicorn | Asynchronous REST API with auto-generated OpenAPI docs (`:8000`). |
| **Package Manager** | Astral `uv` | Lightning-fast Python dependency locking and virtualenv sync. |
| **Computer Vision** | OpenCV 4.x + PyMuPDF | Deskew, binarization, DPI scaling, and raster rendering. |
| **OCR Engines** | PaddleOCR + Tesseract + Docling | Multi-engine CPU OCR and layout parsing orchestration. |
| **LLM Structuring** | LangExtract Framework | Structured JSON extraction over OpenRouter LLMs (DeepSeek-v4, GPT-4o). |
| **Frontend SPA** | React 18 + Vite + TypeScript | Glassmorphism dashboard with split inspector and bounding box highlights. |
| **UI Components** | TailwindCSS v4 + Lucide Icons | Modern responsive UI design system with interactive inspector tabs. |
| **Reporting & Export** | ReportLab + Pandas + OpenPyXL | Automated PDF specification and Excel benchmark generation. |

---

## 7. Enterprise Deployment & Scalability Architecture

- **Stateless Worker Nodes**: FastAPI backend workers execute statelessly in Docker containers, allowing horizontal auto-scaling on Kubernetes.
- **Docker Compose Infrastructure**: Unified multi-stage containerization orchestrating backend API (`:8000`) and Vite frontend (`:5173`).
- **Zero-GPU Operational Flexibility**: Standard claim forms run 100% on CPU worker nodes, eliminating expensive GPU cloud infrastructure dependencies.

---

*Submitted by **Team DataDynamos** for the **Datamatics AI Engineering Hackathon 2026**.*
"""
    MD_PATH.write_text(content, encoding="utf-8")
    print(f"Successfully generated architecture Markdown: {MD_PATH}")

if __name__ == "__main__":
    build_pdf()
    build_markdown()
