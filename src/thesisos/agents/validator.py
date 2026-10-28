"""Node 6: Independent Numeric, Citation, and Contradiction Validator."""
import re
from typing import List
from thesisos.agents.state import WorkflowState
from thesisos.filings.citations import verify_text_citations


def validate_ai_synthesis(state: WorkflowState) -> WorkflowState:
    """
    Cross-check optional AI narrative against:
      1. Indexed SourceRecords ([SRC_..., p.X] tags and page numbers).
      2. Deterministic calculation engine numbers.
      3. Directional consistency with reported growth/valuation.
    Flags issues explicitly rather than silently rewriting numbers.
    """
    flags: List[str] = []
    narrative = state.optional_ai_narrative
    if not narrative:
        state.validation_passed = True
        state.validation_flags = []
        return state

    # 1. Verify citations exist and page numbers match
    cit_audit = verify_text_citations(narrative, state.retrieved_sources)
    if cit_audit.total_citations_found == 0:
        flags.append("MISSING_CITATION: AI response contains zero [SRC_..., p.X] source citations.")
    if not cit_audit.is_valid:
        if cit_audit.invalid_or_missing_sources:
            flags.append(f"UNVERIFIED_SOURCE_ID: Hallucinated citation IDs {cit_audit.invalid_or_missing_sources}.")
        if cit_audit.page_mismatch_citations:
            flags.append(f"PAGE_NUMBER_MISMATCH: {cit_audit.page_mismatch_citations}.")

    # 2. Check for unsupported financial figures following 'Rs' or '₹'
    allowed_numbers = set()
    for val in state.latest_metrics.values():
        if isinstance(val, (int, float)) and val == val:
            allowed_numbers.add(round(float(val), 1))
            allowed_numbers.add(round(float(val), 0))
    if state.dcf_output:
        allowed_numbers.add(round(state.dcf_output.fair_value_per_share_inr, 2))
        allowed_numbers.add(round(state.dcf_output.fair_value_per_share_inr, 0))
        allowed_numbers.add(round(state.dcf_output.enterprise_value_cr, 1))
        allowed_numbers.add(round(state.dcf_output.equity_value_cr, 1))

    # Also allow numbers explicitly present inside indexed source passages
    for s in state.retrieved_sources:
        for num_match in re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", s.extracted_passage):
            try:
                v = float(num_match.replace(",", ""))
                allowed_numbers.add(round(v, 1))
                allowed_numbers.add(round(v, 0))
            except ValueError:
                pass

    claimed_currency_nums = re.findall(r"(?:Rs\.?|₹)\s*(\d[\d,]*(?:\.\d+)?)", narrative, flags=re.IGNORECASE)
    for raw_num in claimed_currency_nums:
        val = float(raw_num.replace(",", ""))
        if not any(abs(val - allowed) <= 1.0 for allowed in allowed_numbers):
            flags.append(
                f"UNSUPPORTED_FINANCIAL_VALUE: Claimed figure '₹{raw_num}' does not match any verified metric or source passage."
            )

    # 3. Check directional contradiction (e.g. claiming revenue contracted when revenue_growth > 0)
    rev_g = state.latest_metrics.get("revenue_growth")
    if isinstance(rev_g, float) and rev_g > 0:
        if re.search(r"revenue\s+(declined|contracted|fell|dropped)", narrative, flags=re.IGNORECASE):
            flags.append(
                f"CONTRADICTORY_CLAIM: AI narrative states revenue declined, contradicting verified YoY growth of {rev_g*100:+.1f}%."
            )

    state.validation_flags = flags
    state.validation_passed = len(flags) == 0
    return state
