"""Nodes 1 & 2: Data Quality Auditor and Financial Statement / Forensic Auditor."""
import pandas as pd
from thesisos.agents.state import WorkflowState
from thesisos.data.normalize import pivot_canonical_statements
from thesisos.data.validation import audit_financial_dataset
from thesisos.finance.forensic import evaluate_forensic_alerts
from thesisos.finance.metrics import (
    compute_financial_metrics_table,
    compute_summary_cagrs,
    compute_valuation_multiples,
)
from thesisos.finance.working_capital import append_working_capital_metrics


def run_financial_auditor_node(
    state: WorkflowState,
    facts_df: pd.DataFrame,
    sources_df: pd.DataFrame,
) -> tuple[WorkflowState, pd.DataFrame]:
    """Execute Node 1 (Data Quality Audit) and Node 2 (Financial Ratio & Forensic Audit)."""
    cid = state.company_meta["company_id"]
    state.dq_report = audit_financial_dataset(facts_df, sources_df, company_id=cid, scope=state.scope)

    if facts_df.empty:
        return state, pd.DataFrame()

    wide_df = pivot_canonical_statements(facts_df, expected_scope=state.scope)
    metrics_df = compute_financial_metrics_table(wide_df)
    metrics_df = append_working_capital_metrics(metrics_df)

    state.latest_metrics = metrics_df.iloc[-1].to_dict()
    state.cagrs = compute_summary_cagrs(metrics_df)
    state.multiples = compute_valuation_multiples(
        metrics_df.iloc[-1], float(state.company_meta["reference_price_inr"])
    )
    state.forensic_alerts = evaluate_forensic_alerts(metrics_df, facts_df)
    return state, metrics_df
