"""Page 2: Historical Financial Statements, Ratios, Working Capital, Cash Flow & CSV Exports."""
import sys
from pathlib import Path
import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.data.loaders import load_financial_facts
from thesisos.data.normalize import pivot_canonical_statements
from thesisos.finance.forensic import evaluate_forensic_alerts
from thesisos.finance.metrics import compute_financial_metrics_table
from thesisos.finance.working_capital import append_working_capital_metrics
from thesisos.reports.export import export_dataframe_to_csv_bytes
from thesisos.ui.charts import (
    build_cash_conversion_chart,
    build_returns_and_working_capital_chart,
    build_revenue_profit_chart,
)
from thesisos.ui.components import render_footer, render_sidebar_and_context

st.set_page_config(page_title="Financial Analysis | ThesisOS", page_icon="📈", layout="wide")
company_meta, scope = render_sidebar_and_context()

facts_df = load_financial_facts(company_meta["company_id"], scope=scope)
if facts_df.empty:
    st.warning(f"No data for {company_meta['company_name']} ({scope}). Switch to CONSOLIDATED.")
    render_footer()
    st.stop()

wide_df = pivot_canonical_statements(facts_df, expected_scope=scope)
metrics_df = append_working_capital_metrics(compute_financial_metrics_table(wide_df))
alerts = evaluate_forensic_alerts(metrics_df, facts_df)

st.markdown("## 2. Historical Financial Statements & Quality Diagnostics")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Interactive Charts", "📑 Financial Statements (₹ Crore)", "🔬 Ratios & Working Capital", "🚨 Forensic & Provenance Ledger"]
)

with tab1:
    st.plotly_chart(build_revenue_profit_chart(metrics_df, company_meta["company_name"], scope), use_container_width=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(build_cash_conversion_chart(metrics_df, company_meta["company_name"], scope), use_container_width=True)
    with col_b:
        st.plotly_chart(build_returns_and_working_capital_chart(metrics_df, company_meta["company_name"], scope), use_container_width=True)

with tab2:
    st.markdown("#### Income Statement (Normalized to ₹ Crore)")
    inc_cols = ["fiscal_year", "revenue", "cogs", "ebitda", "da", "ebit", "finance_costs", "pbt", "tax", "pat", "eps"]
    st.dataframe(metrics_df[inc_cols], use_container_width=True, hide_index=True)

    st.markdown("#### Balance Sheet (Normalized to ₹ Crore)")
    bs_cols = [
        "fiscal_year", "cash_and_investments", "trade_receivables", "inventory",
        "current_assets", "total_assets", "trade_payables", "current_liabilities",
        "total_debt", "total_equity", "net_debt", "diluted_shares",
    ]
    st.dataframe(metrics_df[bs_cols], use_container_width=True, hide_index=True)

    st.markdown("#### Cash Flow Statement (Normalized to ₹ Crore)")
    cf_cols = ["fiscal_year", "cfo", "capex", "fcf", "dividends_paid", "cfo_to_pat"]
    st.dataframe(metrics_df[cf_cols], use_container_width=True, hide_index=True)

with tab3:
    st.markdown("#### Profitability, Return, Leverage & Working Capital Matrix")
    ratio_disp = metrics_df[["fiscal_year"]].copy()
    ratio_disp["Revenue Growth (%)"] = (metrics_df["revenue_growth"] * 100.0).round(2)
    ratio_disp["EBITDA Margin (%)"] = (metrics_df["ebitda_margin"] * 100.0).round(2)
    ratio_disp["EBIT Margin (%)"] = (metrics_df["ebit_margin"] * 100.0).round(2)
    ratio_disp["PAT Margin (%)"] = (metrics_df["pat_margin"] * 100.0).round(2)
    ratio_disp["ROE (%)"] = (metrics_df["roe"] * 100.0).round(2)
    ratio_disp["ROCE (%)"] = (metrics_df["roce"] * 100.0).round(2)
    ratio_disp["Current Ratio (x)"] = metrics_df["current_ratio"].round(2)
    ratio_disp["Interest Coverage (x)"] = metrics_df["interest_coverage"].round(1)
    ratio_disp["Receivable Days (DSO)"] = metrics_df["receivable_days"].round(1)
    ratio_disp["Payable Days (DPO)"] = metrics_df["payable_days"].round(1)
    ratio_disp["Cash Conversion Cycle (Days)"] = metrics_df["cash_conversion_cycle"].round(1)
    ratio_disp["CFO / PAT (x)"] = metrics_df["cfo_to_pat"].round(2)
    st.dataframe(ratio_disp, use_container_width=True, hide_index=True)

with tab4:
    st.markdown("#### Rule-Based Forensic Investigation Alerts")
    if not alerts:
        st.success("No forensic thresholds triggered.")
    else:
        for a in alerts:
            st.warning(
                f"**{a.fiscal_period} — {a.rule_name}** | Actual: `{a.actual_value}` vs `{a.threshold_description}`\n\n"
                f"{a.cautious_explanation}\n\n"
                f"**Supporting Figures:** {a.supporting_figures} | **Source IDs:** `{', '.join(a.source_references)}`\n\n"
                f"**Recommended Analyst Question:** *{a.recommended_followup_question}*"
            )
    st.markdown("#### Raw Canonical Observations with Row-Level Source Provenance")
    st.dataframe(
        facts_df[["fiscal_year", "statement_type", "metric_key", "original_value", "original_unit", "source_id", "source_page", "verification_status"]],
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")
dl1, dl2 = st.columns(2)
with dl1:
    st.download_button(
        "⬇️ Download Raw Financial Facts (CSV)",
        data=export_dataframe_to_csv_bytes(facts_df),
        file_name=f"{company_meta['symbol']}_{scope}_financial_facts.csv",
        mime="text/csv",
    )
with dl2:
    st.download_button(
        "⬇️ Download Computed Ratios & Metrics (CSV)",
        data=export_dataframe_to_csv_bytes(metrics_df),
        file_name=f"{company_meta['symbol']}_{scope}_calculated_metrics.csv",
        mime="text/csv",
    )

render_footer()
