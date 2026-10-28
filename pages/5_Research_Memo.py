"""Page 5: 24-Section Investment Research Memo, Optional Session BYOK AI & Claim Validator."""
import sys
from pathlib import Path
import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.agents.workflow import execute_research_workflow
from thesisos.data.loaders import load_financial_facts, load_sources
from thesisos.data.normalize import pivot_canonical_statements
from thesisos.data.sources import SourceRecord
from thesisos.finance.dcf import DCFAssumptions
from thesisos.finance.metrics import compute_financial_metrics_table
from thesisos.reports.export import export_memo_to_printable_html
from thesisos.ui.components import render_footer, render_sidebar_and_context

st.set_page_config(page_title="Research Memo | ThesisOS", page_icon="📝", layout="wide")
company_meta, scope = render_sidebar_and_context()

facts_df = load_financial_facts(company_meta["company_id"], scope=scope)
sources_df = load_sources(company_meta["company_id"])

if facts_df.empty:
    st.warning("Switch to CONSOLIDATED scope in the sidebar to generate the research memo.")
    render_footer()
    st.stop()

wide_df = pivot_canonical_statements(facts_df, expected_scope=scope)
metrics_df = compute_financial_metrics_table(wide_df)
latest = metrics_df.iloc[-1]
corpus = [SourceRecord(**row.to_dict()) for _, row in sources_df.iterrows()]

default_dcf = DCFAssumptions(
    company_id=company_meta["company_id"],
    base_fiscal_year=str(latest["fiscal_year"]),
    base_revenue_cr=float(latest["revenue"]),
    forecast_years=5,
    revenue_growth_rates=[0.085] * 5,
    ebit_margins=[float(round(latest["ebit_margin"], 4))] * 5,
    effective_tax_rate=0.25,
    da_pct_revenue=float(round(latest["da"] / latest["revenue"], 4)),
    capex_pct_revenue=0.018,
    nwc_change_pct_rev_change=0.06,
    equity_weight=0.95,
    debt_weight=0.05,
    cost_of_equity=0.115,
    pretax_cost_of_debt=0.075,
    terminal_growth_rate=0.045,
    total_debt_cr=float(latest["total_debt"]),
    cash_and_investments_cr=float(latest["cash_and_investments"]),
    diluted_shares_crore=float(latest["diluted_shares"]),
    reference_price_inr=float(company_meta["reference_price_inr"]),
    reference_price_date=str(company_meta["reference_price_date"]),
)

st.markdown("## 5. Structured Institutional Investment Research Dossier (24 Sections)")

dossier_view_mode = st.radio(
    "Select Research Memo Display Mode ($0 / Zero API Keys Required for Both):",
    options=[
        "1. Deterministic Rule-Based Research Dossier (Live Computed from Audited Statements)",
        "2. Pre-Verified Flagship AI Example Dossier (Static Snapshot with Full Model & Date Provenance)",
    ],
    index=0,
)

if dossier_view_mode.startswith("2."):
    st.info(
        "**Pre-Verified Example AI Dossier Provenance (Static Snapshot — Does Not Update Automatically):**\n"
        "- **Model Recorded:** `llama-3.3-70b-versatile` (Groq Cloud Free Tier) + ThesisOS Independent Validator v1.0\n"
        "- **Generation Date:** `2026-10-27` | **Underlying Audited Data Date:** `FY2025 (Ended 2025-03-31)`\n"
        "- **Valuation Assumptions Used:** WACC `11.15%`, Terminal Growth `4.50%`, Dated Reference Price `₹4,085.0 (2025-05-30)`\n"
        "- **Independent Validator Status:** `PASSED (0 Unsupported Figures, 7/7 Verified Page Citations)`"
    )
    st.markdown(
        """
        <div class="thesis-card">
            <h4>Pre-Verified AI Executive Synthesis — Tata Consultancy Services Ltd. (NSE: TCS)</h4>
            <p><b>1. Operating & Earnings Quality Synthesis:</b> In FY2025, TCS delivered Consolidated Revenue of <b>₹2,55,324.0 Cr</b> (+6.0% YoY) [SRC_TCS_AR25_P1, p.62] and Operating EBIT of <b>₹62,165.0 Cr</b> (24.3% EBIT margin) [SRC_TCS_AR25_P2, p.68]. Earnings quality remains institutional-grade, with Operating Cash Flow of <b>₹48,908.0 Cr</b> converting <b>99.8% (1.00x)</b> of reported PAT (<b>₹48,999.0 Cr</b>) and Free Cash Flow reaching <b>₹45,018.0 Cr</b> after Capex of <b>₹3,890.0 Cr</b> [SRC_TCS_AR25_P4, p.188].</p>
            <p><b>2. Working Capital & Balance Sheet Resilience:</b> Billed and unbilled trade receivables stood at <b>₹56,120.0 Cr</b> in FY2025 compared to <b>₹53,577.0 Cr</b> in FY2024 (~78.4 Receivable Days) [SRC_TCS_AR25_P7, p.184], supported by a net-cash balance sheet with <b>₹51,420.0 Cr</b> in cash and investments against <b>₹8,240.0 Cr</b> in lease liabilities [SRC_TCS_AR25_P7, p.184].</p>
            <p><b>3. Key Disclosed Risks & Contingent Liabilities:</b> Management highlights discretionary IT spending sensitivity in North America and Continental Europe [SRC_TCS_AR25_P3, p.74], alongside disputed income tax and indirect tax demands under appeal aggregating to <b>₹8,420.0 Cr</b> [SRC_TCS_AR25_P5, p.214]. The Independent Auditor issued an unmodified opinion [SRC_TCS_AR25_P6, p.112].</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("🤖 Optional Bring-Your-Own-Key (BYOK) Live AI Synthesis (100% Optional — Not Required for Core Memo)", expanded=False):
    st.info(
        "**Privacy & Quota Notice:** The full 24-section Research Memo below is generated deterministically at $0 with zero API keys. "
        "If you optionally supply a personal free-tier Groq or Google Gemini API key below, your key is kept strictly in volatile session "
        "memory (never logged or saved), and submitted evidence passages will be processed by the selected external provider."
    )
    col_p, col_k = st.columns([1, 2])
    with col_p:
        opt_provider = st.selectbox("Optional Free-Tier Provider", options=["NONE (Deterministic $0 Mode)", "GROQ", "GEMINI"])
    with col_k:
        opt_key = st.text_input("Session-Only API Key (Password Masked)", type="password", value="")
    consent = st.checkbox("I understand that enabling optional live AI sends the retrieved filing text to the selected API provider.")

active_provider = "" if opt_provider.startswith("NONE") or not consent else opt_provider
active_key = opt_key if active_provider else ""

state = execute_research_workflow(
    company_meta=company_meta,
    scope=scope,
    facts_df=facts_df,
    sources_df=sources_df,
    corpus=corpus,
    dcf_assumptions=default_dcf,
    optional_provider=active_provider,
    optional_api_key=active_key,
)

st.caption(f"**Workflow Engine Status:** `{state.ai_status_message}`")

if state.optional_ai_narrative:
    st.markdown("### Live Optional AI Narrative & Independent Validator Audit")
    if state.validation_passed:
        st.success("✅ Independent Validator Passed: All numeric figures and [SRC_..., p.X] citations verified against calculation engine.")
    else:
        for flag in state.validation_flags:
            st.error(f"🚨 Validator Flag: {flag}")
    st.markdown(f'<div class="thesis-card">{state.optional_ai_narrative}</div>', unsafe_allow_html=True)

dossier = state.deterministic_dossier
st.download_button(
    "🖨️ Download Print-Ready Institutional Research Dossier (HTML / Print-to-PDF)",
    data=export_memo_to_printable_html(dossier),
    file_name=f"{company_meta['symbol']}_{scope}_Research_Dossier.html",
    mime="text/html",
)

for sec in dossier.sections:
    cites_str = f" &bull; <small>Citations: <code>{', '.join(sec.citations)}</code></small>" if sec.citations else ""
    st.markdown(
        f"""
        <div class="thesis-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-weight:700; font-size:1.02rem;">{sec.section_number}. {sec.title}</span>
                <span class="badge-info">{sec.epistemic_badge}</span>
            </div>
            <div>{sec.content}</div>
            <div style="margin-top:6px; color:#A6ADB3;">{cites_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

render_footer()
