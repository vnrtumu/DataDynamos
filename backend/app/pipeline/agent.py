"""Phase 5 decision stage: structured JSON -> approve | flag | needs_review.

Two providers behind one entrypoint, mirroring the structuring stage:

* ``llm`` — a single OpenRouter call (OpenAI-compatible client), imported lazily so
  the app boots and tests run without the optional ``openai`` dep.
* ``mock`` — deterministic ("approve"), so the offline tests exercise the part that
  matters: code-computed business rules reconciling with — and overriding — the LLM.

The defining rule (TASK + cross-cutting checklist): deterministic checks run in code
and the LLM can never override a hard-failed rule, only explain it. So checks +
citations are built here in code; the LLM supplies qualitative judgment + reasons;
``_reconcile`` combines them under a fixed precedence.
"""

from __future__ import annotations

import json
from time import perf_counter

from app.config import settings
from app.models import Document, DocumentStatus
from app.rules import (
    DecisionContext,
    citations_from_grounding,
    cross_cutting_checks,
    get_citation_paths,
    get_ruleset,
)
from app.schemas import Check, Decision, DecisionResult, StructuredResult

PROVIDERS = {"llm", "mock"}

_VALID_DECISIONS = {"approve", "flag", "needs_review"}


def run_decision(
    doc: Document,
    structured: StructuredResult,
    ctx: DecisionContext,
    provider: str = "",
) -> DecisionResult:
    """Decide a document from its structured fields + quality/confidence context."""
    provider = provider or settings.decision_provider
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown decision provider '{provider}'. Available: {', '.join(sorted(PROVIDERS))}"
        )

    doc_type = structured.doc_type
    fields = structured.fields

    # 1. Authoritative, code-computed checks (rule set + shared confidence/quality gates).
    checks = get_ruleset(doc_type)(fields, ctx) + cross_cutting_checks(ctx)

    # 2. Qualitative judgment from the provider.
    start = perf_counter()
    warnings: list[str] = []
    if provider == "mock":
        llm_decision, llm_conf, llm_reasons = "approve", 0.95, ["mock approval"]
        model = "mock"
    else:
        llm_decision, llm_conf, llm_reasons, llm_warnings = _decide_llm(
            doc_type.value, fields, checks, ctx
        )
        warnings.extend(llm_warnings)
        model = settings.decision_model
    latency_ms = int((perf_counter() - start) * 1000)

    # 3. Reconcile: code wins on hard failures; gates cap at needs_review.
    decision, confidence, reasons = _reconcile(
        checks, llm_decision, llm_conf, llm_reasons, ctx.extraction_confidence
    )

    # 4. Citations from the structuring grounding map.
    citations = citations_from_grounding(structured.grounding_map, get_citation_paths(doc_type))

    status = (
        DocumentStatus.needs_review if decision == "needs_review" else DocumentStatus.decided
    )

    return DecisionResult(
        document_id=doc.id,
        status=status,
        doc_type=doc_type,
        provider=provider,
        model=model,
        decision=decision,
        confidence=confidence,
        reasons=reasons,
        checks=checks,
        citations=citations,
        llm_decision=llm_decision,
        warnings=warnings,
        latency_ms=latency_ms,
    )


# --- reconciliation -----------------------------------------------------------


def _reconcile(
    checks: list[Check],
    llm_decision: Decision,
    llm_conf: float,
    llm_reasons: list[str],
    extraction_confidence: float,
) -> tuple[Decision, float, list[str]]:
    """Combine code checks with the LLM judgment under a fixed precedence."""
    hard_failed = [c for c in checks if c.severity == "hard" and not c.passed]
    review_failed = [c for c in checks if c.severity == "review" and not c.passed]

    reasons = list(llm_reasons)

    if hard_failed:
        # A deterministic hard-rule violation is a certain flag — always trustworthy.
        decision: Decision = "flag"
        reasons = [f"Failed rule: {c.name} — {c.detail}" for c in hard_failed] + reasons
    elif review_failed:
        # A failed quality/business review gate caps at needs_review. This takes
        # precedence over an LLM "flag": with untrustworthy data (low confidence, poor
        # scan) we can't confidently flag either — only a human or a hard rule can.
        decision = "needs_review"
        reasons = [f"Needs review: {c.name} — {c.detail}" for c in review_failed] + reasons
    else:
        # Trustworthy data, no gate tripped: the LLM judgment stands (approve | flag |
        # needs_review).
        decision = llm_decision

    # Confidence propagation: never more confident than the inputs. A failed hard
    # rule is a certain flag, so floor it at 0.9.
    confidence = min(max(llm_conf, 0.0), max(extraction_confidence, 0.0))
    if hard_failed:
        confidence = max(confidence, 0.9)
    return decision, round(confidence, 4), reasons


# --- providers ----------------------------------------------------------------


def _decide_llm(
    doc_type: str, fields: dict, checks: list[Check], ctx: DecisionContext
) -> tuple[Decision, float, list[str], list[str]]:
    """Single OpenRouter call returning {decision, confidence, reasons}.

    On any error (missing key, network, unparsable output) falls back to a cautious
    ``needs_review`` plus a warning — never raises into the request path.
    """
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not set; the llm decision provider needs it.")

    try:
        import openai  # lazy: optional dep

        client = openai.OpenAI(
            api_key=settings.openrouter_api_key, base_url=settings.decision_base_url
        )
        prompt = _build_prompt(doc_type, fields, checks, ctx)
        response = client.chat.completions.create(
            model=settings.decision_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        payload = json.loads(response.choices[0].message.content or "{}")
    except Exception as exc:  # noqa: BLE001 — degrade gracefully, surface as a warning
        return "needs_review", 0.3, ["LLM judgment unavailable"], [f"decision LLM error: {exc}"]

    decision = payload.get("decision")
    if decision not in _VALID_DECISIONS:
        return (
            "needs_review",
            0.3,
            ["LLM returned an unrecognized decision"],
            [f"decision LLM returned invalid decision {decision!r}"],
        )
    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = min(max(confidence, 0.0), 1.0)
    raw_reasons = payload.get("reasons") or []
    reasons = [str(r) for r in raw_reasons] if isinstance(raw_reasons, list) else [str(raw_reasons)]
    return decision, confidence, reasons, []


_SYSTEM_PROMPT = (
    "You are an approvals assistant for contracts and invoices. You are given a "
    "document's extracted fields and the results of deterministic business-rule "
    "checks already computed in code. The code checks are authoritative — do not "
    "contradict a failed check; explain it. Respond ONLY with a JSON object: "
    '{"decision": "approve"|"flag"|"needs_review", "confidence": 0.0-1.0, '
    '"reasons": ["short bullet", ...]}.'
)


def _build_prompt(doc_type: str, fields: dict, checks: list[Check], ctx: DecisionContext) -> str:
    """Compact, deterministic prompt body (values-only fields + the check trace)."""
    check_lines = [
        f"- {c.name} [{c.severity}]: {'PASS' if c.passed else 'FAIL'} — {c.detail}"
        for c in checks
    ]
    return (
        f"Document type: {doc_type}\n"
        f"Extracted fields (values only):\n{json.dumps(_values_only(fields), indent=2)}\n\n"
        f"Deterministic checks:\n" + "\n".join(check_lines) + "\n\n"
        f"Overall extraction confidence: {ctx.extraction_confidence:.2f}\n"
        f"Pre-flight quality verdict: {ctx.prescan_verdict or 'not run'}\n\n"
        "Give your decision, confidence, and concise reasons."
    )


def _values_only(node: object) -> object:
    """Strip FieldValue nodes down to their value for a compact LLM prompt."""
    if isinstance(node, dict):
        if "value" in node and "confidence" in node:
            return node.get("value")
        return {k: _values_only(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_values_only(x) for x in node]
    return node
