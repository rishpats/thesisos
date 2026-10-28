"""End-to-end 6-node research orchestrator for ThesisOS."""
from typing import Any, Callable, Dict, List, Optional
import pandas as pd
from thesisos.agents.financial_auditor import run_financial_auditor_node
from thesisos.agents.market_researcher import run_valuation_node
from thesisos.agents.risk_analyst import run_disclosure_analyst_node
from thesisos.agents.state import WorkflowState
from thesisos.agents.synthesizer import build_strict_evidence_prompt, call_optional_byok_llm
from thesisos.agents.validator import validate_ai_synthesis
from thesisos.data.sources import SourceRecord
from thesisos.finance.dcf import DCFAssumptions
from thesisos.reports.memo import build_deterministic_research_memo


def execute_research_workflow(
    company_meta: Dict[str, Any],
    scope: str,
    facts_df: pd.DataFrame,
    sources_df: pd.DataFrame,
    corpus: List[SourceRecord],
    dcf_assumptions: DCFAssumptions,
    optional_provider: str = "",
    optional_api_key: str = "",
    http_post_fn: Optional[Callable] = None,
) -> WorkflowState:
    """Run all 6 nodes sequentially and always guarantee a validated deterministic dossier."""
    state = WorkflowState(company_meta=company_meta, scope=scope)

    # Nodes 1 & 2: Data Quality & Financial/Forensic Auditor
    state, metrics_df = run_financial_auditor_node(state, facts_df, sources_df)
    if metrics_df.empty:
        return state

    # Node 3: Disclosure & Filing Analyst
    state = run_disclosure_analyst_node(state, corpus)

    # Node 4: Valuation Engine
    state = run_valuation_node(state, dcf_assumptions)

    # Always generate the Category A Deterministic Dossier first
    state.deterministic_dossier = build_deterministic_research_memo(
        company_meta=company_meta,
        scope=scope,
        metrics_df=metrics_df,
        cagrs=state.cagrs,
        multiples=state.multiples,
        forensic_alerts=state.forensic_alerts,
        dcf_output=state.dcf_output,
        scenarios=state.scenarios,
        reverse_dcf_growth=state.reverse_dcf_growth,
        dq_report=state.dq_report,
        sources=state.retrieved_sources,
    )

    # Node 5 & 6: Optional BYOK LLM Synthesis + Independent Claim Validator
    if optional_api_key.strip():
        prompt = build_strict_evidence_prompt(state)
        narrative, status_msg = call_optional_byok_llm(
            provider=optional_provider,
            api_key=optional_api_key,
            prompt=prompt,
            http_post_fn=http_post_fn,
        )
        state.optional_ai_narrative = narrative
        state.ai_status_message = status_msg
        if narrative:
            state = validate_ai_synthesis(state)

    return state
