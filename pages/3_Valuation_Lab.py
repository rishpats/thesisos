"""Page 3: Deterministic DCF Valuation Lab, Sensitivity Heatmap, Scenarios, Reverse DCF & Comps."""
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.data.loaders import load_financial_facts
from thesisos.data.normalize import pivot_canonical_statements
from thesisos.finance.comparables import build_peer_comparables_table
from thesisos.finance.dcf import (
    DCFAssumptions,
    calculate_cost_of_equity_capm,
    run_dcf_valuation,
    solve_reverse_dcf_implied_growth,
)
from thesisos.finance.metrics import compute_financial_metrics_table
from thesisos.finance.scenarios import (
    generate_wacc_tg_sensitivity_grid,
    run_bull_base_bear_scenarios,
)
from thesisos.reports.export import export_dcf_assumptions_json
from thesisos.ui.charts import build_dcf_sensitivity_heatmap
from thesisos.ui.components import render_footer, render_kpi_card, render_sidebar_and_context

st.set_page_config(page_title="Valuation Lab | ThesisOS", page_icon="🧮", layout="wide")
company_meta, scope = render_sidebar_and_context()

facts_df = load_financial_facts(company_meta["company_id"], scope=scope)
if facts_df.empty:
    st.warning("Switch to CONSOLIDATED scope in sidebar to load base-year financials.")
    render_footer()
    st.stop()

wide_df = pivot_canonical_statements(facts_df, expected_scope=scope)
metrics_df = compute_financial_metrics_table(wide_df)
latest = metrics_df.iloc[-1]

st.markdown("## 3. Deterministic Valuation Laboratory (FCFF DCF, Scenarios, Reverse DCF & Comps)")

with st.expander("⚙️ Configure Operating Forecast, WACC / CAPM & Equity Bridge Assumptions", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Operating Forecast (5-Year)**")
        rev_g_pct = st.slider("Annual Revenue Growth (%)", min_value=-5.0, max_value=25.0, value=8.5, step=0.5)
        ebit_m_pct = st.slider("Target EBIT Margin (%)", min_value=5.0, max_value=40.0, value=float(round(latest["ebit_margin"] * 100, 1)), step=0.5)
        tax_pct = st.slider("Effective Tax Rate (%)", min_value=15.0, max_value=35.0, value=25.0, step=0.5)
        capex_pct = st.slider("Capex (% of Revenue)", min_value=0.5, max_value=15.0, value=1.8, step=0.2)
    with c2:
        st.markdown("**WACC & CAPM Cost of Capital**")
        rf_pct = st.number_input("India 10Y G-Sec Risk-Free Rate (%)", value=6.85, step=0.1)
        beta_val = st.number_input("Equity Beta (β)", value=0.85, step=0.05)
        erp_pct = st.number_input("Equity Risk Premium (%)", value=5.50, step=0.25)
        ke_capm = calculate_cost_of_equity_capm(rf_pct / 100.0, beta_val, erp_pct / 100.0)
        st.caption(f"CAPM Implied Cost of Equity (Ke): **{ke_capm*100:.2f}%**")
        tg_pct = st.slider("Terminal Growth Rate (%)", min_value=1.0, max_value=8.0, value=4.5, step=0.25)
    with c3:
        st.markdown("**Dated Reference Price & Equity Bridge**")
        ref_price = st.number_input("Dated Reference Market Price (₹/Share)", value=float(company_meta["reference_price_inr"]), step=10.0)
        ref_date = st.text_input("Price Reference Date", value=str(company_meta["reference_price_date"]))
        ref_source = st.text_input("Price Source Label", value="Dated Reference Closing Price (Manual/Static Input)")

try:
    assumptions = DCFAssumptions(
        company_id=company_meta["company_id"],
        base_fiscal_year=str(latest["fiscal_year"]),
        base_revenue_cr=float(latest["revenue"]),
        forecast_years=5,
        revenue_growth_rates=[rev_g_pct / 100.0] * 5,
        ebit_margins=[ebit_m_pct / 100.0] * 5,
        effective_tax_rate=tax_pct / 100.0,
        da_pct_revenue=float(round(latest["da"] / latest["revenue"], 4)),
        capex_pct_revenue=capex_pct / 100.0,
        nwc_change_pct_rev_change=0.06,
        equity_weight=0.95,
        debt_weight=0.05,
        cost_of_equity=ke_capm,
        pretax_cost_of_debt=0.075,
        terminal_growth_rate=tg_pct / 100.0,
        total_debt_cr=float(latest["total_debt"]),
        cash_and_investments_cr=float(latest["cash_and_investments"]),
        diluted_shares_crore=float(latest["diluted_shares"]),
        reference_price_inr=ref_price,
        reference_price_date=ref_date,
        reference_price_source=ref_source,
    )
except ValueError as err:
    st.error(f"Valuation Guardrail Triggered: {err}")
    render_footer()
    st.stop()

dcf_out = run_dcf_valuation(assumptions)
scenarios = run_bull_base_bear_scenarios(assumptions)
rev_dcf_g = solve_reverse_dcf_implied_growth(assumptions)

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi_card(
        "Implied Fair Value / Share",
        f"₹{dcf_out.fair_value_per_share_inr:,.2f}",
        f"WACC: {dcf_out.wacc*100:.2f}% | Term Growth: {dcf_out.terminal_growth_rate*100:.2f}%",
        status="positive" if dcf_out.upside_downside_pct >= 0 else "warning",
    )
with k2:
    render_kpi_card(
        f"Dated Ref Price ({dcf_out.reference_price_date})",
        f"₹{dcf_out.reference_price_inr:,.2f}",
        dcf_out.reference_price_source,
        status="neutral",
    )
with k3:
    render_kpi_card(
        "Implied Upside / (Downside)",
        f"{dcf_out.upside_downside_pct*100:+.1f}%",
        f"Margin of Safety: {dcf_out.margin_of_safety_pct*100:+.1f}%",
        status="positive" if dcf_out.upside_downside_pct >= 0 else "warning",
    )
with k4:
    imp_str = f"{rev_dcf_g*100:.2f}% / yr" if rev_dcf_g is not None else "N/A"
    render_kpi_card(
        "Reverse DCF Implied 5Y Growth",
        imp_str,
        f"Growth needed to justify ₹{dcf_out.reference_price_inr:,.0f}",
        status="neutral",
    )

for w_msg in dcf_out.warnings:
    st.warning(w_msg)

st.markdown("#### 5-Year Explicit FCFF Forecast Schedule (₹ Crore)")
proj_df = pd.DataFrame([(p.model_dump() if hasattr(p, 'model_dump') else p.dict()) for p in dcf_out.projections])
st.dataframe(proj_df, use_container_width=True, hide_index=True)

c_bridge, c_scen = st.columns(2)
with c_bridge:
    st.markdown("#### Enterprise-to-Equity Valuation Bridge")
    bridge_df = pd.DataFrame(
        [
            {"Component": "PV of 5Y Forecast FCFF (₹ Cr)", "Value": f"₹{dcf_out.sum_pv_fcff_cr:,.2f}"},
            {"Component": "PV of Terminal Value (₹ Cr)", "Value": f"₹{dcf_out.pv_terminal_value_cr:,.2f}"},
            {"Component": "Enterprise Value (₹ Cr)", "Value": f"₹{dcf_out.enterprise_value_cr:,.2f}"},
            {"Component": "Less: Net Debt (Debt - Cash) (₹ Cr)", "Value": f"₹{dcf_out.net_debt_cr:,.2f}"},
            {"Component": "Implied Equity Value (₹ Cr)", "Value": f"₹{dcf_out.equity_value_cr:,.2f}"},
            {"Component": "Diluted Shares (Crore)", "Value": f"{dcf_out.diluted_shares_crore:.2f} Cr"},
            {"Component": "Implied Fair Value per Share (₹)", "Value": f"₹{dcf_out.fair_value_per_share_inr:,.2f}"},
        ]
    )
    st.dataframe(bridge_df, use_container_width=True, hide_index=True)

with c_scen:
    st.markdown("#### Bull / Base / Bear Scenario Comparison")
    scen_rows = []
    for label, s_out in scenarios.items():
        scen_rows.append(
            {
                "Scenario": label,
                "WACC (%)": f"{s_out.wacc*100:.2f}%",
                "Term Growth (%)": f"{s_out.terminal_growth_rate*100:.2f}%",
                "Enterprise Value (₹ Cr)": f"₹{s_out.enterprise_value_cr:,.0f}",
                "Fair Value / Share (₹)": f"₹{s_out.fair_value_per_share_inr:,.2f}",
                "Upside / Downside (%)": f"{s_out.upside_downside_pct*100:+.1f}%",
            }
        )
    st.dataframe(pd.DataFrame(scen_rows), use_container_width=True, hide_index=True)

w_list, g_list, grid = generate_wacc_tg_sensitivity_grid(assumptions)
st.plotly_chart(build_dcf_sensitivity_heatmap(w_list, g_list, grid, company_meta["company_name"]), use_container_width=True)

st.markdown("#### Peer Comparable Companies Valuation Benchmark")
comps_df = build_peer_comparables_table(sector_filter=company_meta["sector"])
st.dataframe(comps_df, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Download DCF Assumptions & Valuation Bridge (JSON)",
    data=export_dcf_assumptions_json(assumptions, dcf_out),
    file_name=f"{company_meta['symbol']}_dcf_valuation.json",
    mime="application/json",
)

render_footer()
