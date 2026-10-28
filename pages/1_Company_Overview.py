"""Page 1: Company Overview, Executive KPIs, Forensic Summary & Data Quality Audit."""
import sys
from pathlib import Path
import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.data.loaders import load_financial_facts, load_sources
from thesisos.data.normalize import pivot_canonical_statements
from thesisos.data.validation import audit_financial_dataset
from thesisos.finance.forensic import evaluate_forensic_alerts
from thesisos.finance.metrics import (
    compute_financial_metrics_table,
    compute_summary_cagrs,
    compute_valuation_multiples,
)
from thesisos.finance.working_capital import append_working_capital_metrics
from thesisos.ui.charts import build_revenue_profit_chart
from thesisos.ui.components import render_footer, render_kpi_card, render_sidebar_and_context

st.set_page_config(page_title="Company Overview | ThesisOS", page_icon="🏢", layout="wide")
company_meta, scope = render_sidebar_and_context()

facts_df = load_financial_facts(company_meta["company_id"], scope=scope)
sources_df = load_sources(company_meta["company_id"])
dq_report = audit_financial_dataset(facts_df, sources_df, company_meta["company_id"], scope=scope)

st.markdown("## 1. Company Overview & Executive Health Snapshot")
st.write(company_meta["description"])

if facts_df.empty:
    st.warning(
        f"No verified financial observations available for {company_meta['company_name']} under scope '{scope}'. "
        "Switch Reporting Scope to CONSOLIDATED in the left sidebar."
    )
    render_footer()
    st.stop()

wide_df = pivot_canonical_statements(facts_df, expected_scope=scope)
metrics_df = append_working_capital_metrics(compute_financial_metrics_table(wide_df))
cagrs = compute_summary_cagrs(metrics_df)
latest = metrics_df.iloc[-1]
multiples = compute_valuation_multiples(latest, float(company_meta["reference_price_inr"]))
alerts = evaluate_forensic_alerts(metrics_df, facts_df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    rev_g_str = f"{latest['revenue_growth']*100:+.1f}% YoY" if latest.get("revenue_growth") is not None else "Base Year"
    cagr_str = f"{cagrs['revenue_cagr']*100:.1f}% CAGR" if cagrs.get("revenue_cagr") is not None else ""
    render_kpi_card(
        f"Revenue ({latest['fiscal_year']})",
        f"₹{latest['revenue']:,.0f} Cr",
        f"{rev_g_str} | {cagr_str}",
        status="positive",
    )
with col2:
    render_kpi_card(
        f"PAT & Margin ({latest['fiscal_year']})",
        f"₹{latest['pat']:,.0f} Cr",
        f"PAT Margin: {latest['pat_margin']*100:.1f}% | EBITDA: {latest['ebitda_margin']*100:.1f}%",
        status="positive",
    )
with col3:
    render_kpi_card(
        f"Capital Efficiency ({latest['fiscal_year']})",
        f"ROE: {latest['roe']*100:.1f}%",
        f"ROCE: {latest['roce']*100:.1f}% | Net Debt: ₹{latest['net_debt']:,.0f} Cr",
        status="positive",
    )
with col4:
    render_kpi_card(
        f"Cash Conversion ({latest['fiscal_year']})",
        f"{latest['cfo_to_pat']:.2f}x CFO/PAT",
        f"FCF: ₹{latest['fcf']:,.0f} Cr | P/E: {multiples.get('pe_ratio', 0.0):.1f}x",
        status="positive" if latest["cfo_to_pat"] >= 0.80 else "warning",
    )

st.plotly_chart(build_revenue_profit_chart(metrics_df, company_meta["company_name"], scope), use_container_width=True)

c_left, c_right = st.columns(2)
with c_left:
    st.markdown("### Active Forensic Accounting Alerts")
    if not alerts:
        st.success("Zero forensic threshold breaches detected across covered periods.")
    else:
        for a in alerts:
            st.warning(
                f"**[{a.fiscal_period}] {a.rule_name}** — Actual: `{a.actual_value}` (Threshold: `{a.threshold_description}`)\n\n"
                f"{a.cautious_explanation}\n\n"
                f"*Follow-up Question:* {a.recommended_followup_question} | *Sources:* `{', '.join(a.source_references)}`"
            )

with c_right:
    st.markdown("### Data Quality & Provenance Audit")
    status_badge = "CLEAN (100% Verified)" if dq_report.is_clean else "ISSUES DETECTED"
    st.info(
        f"**Audit Status:** {status_badge} | **Observations:** {dq_report.total_observations} | "
        f"**Covered Years:** {', '.join(dq_report.covered_years)}"
    )
    if dq_report.issues:
        for iss in dq_report.issues:
            st.caption(f"[{iss.severity}] {iss.category}: {iss.message}")
    st.markdown("**Indexed Source Documents**")
    st.dataframe(
        sources_df[["source_id", "document_title", "reporting_period", "page", "verification_status"]],
        use_container_width=True,
        hide_index=True,
    )

render_footer()
