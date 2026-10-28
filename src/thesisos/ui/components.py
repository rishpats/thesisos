"""Shared institutional UI components, context bars, and sidebar selectors."""
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import streamlit as st

# Ensure src/ is importable when running pages directly
SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.config import INSTITUTIONAL_DISCLAIMER, PALETTE
from thesisos.data.loaders import load_companies, load_financial_facts, load_sources
from thesisos.ui.theme import apply_institutional_theme


def render_sidebar_and_context() -> Tuple[Dict[str, Any], str]:
    """Render sidebar company/scope controls and persistent top context bar."""
    apply_institutional_theme()
    companies_df = load_companies()

    with st.sidebar:
        st.markdown("### THESISOS TERMINAL")
        st.caption("Zero-Cost Institutional Equity Research Platform (India NSE/BSE)")
        st.markdown("---")

        company_options = {
            f"{row['symbol']} — {row['company_name']}": row.to_dict()
            for _, row in companies_df.iterrows()
        }
        selected_label = st.selectbox(
            "Select Covered Company",
            options=list(company_options.keys()),
            index=0,
            help="Verified Indian non-financial listed companies with row-level Annual Report provenance.",
        )
        company_meta = company_options[selected_label]

        selected_scope = st.selectbox(
            "Reporting Scope",
            options=["CONSOLIDATED", "STANDALONE"],
            index=0,
            help="ThesisOS blocks mixing Consolidated and Standalone statements.",
        )

        st.markdown("---")
        st.markdown("**Operating Mode**")
        st.markdown(
            '<span class="badge-verified">DETERMINISTIC ENGINE ACTIVE ($0 / NO KEY)</span>',
            unsafe_allow_html=True,
        )
        st.caption(
            "All financial ratios, DCF valuations, forensic alerts, and TF-IDF passage searches "
            "run 100% deterministically offline."
        )

    # Top persistent institutional banner
    facts_df = load_financial_facts(company_meta["company_id"], scope=selected_scope)
    years = sorted(facts_df["fiscal_year"].unique().tolist()) if not facts_df.empty else []
    period_str = f"{years[0]} – {years[-1]} ({len(years)}Y)" if years else "No Data for Selected Scope"

    st.markdown(
        f"""
        <div class="context-banner">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                <div>
                    <span style="font-size:1.15rem; font-weight:700; color:{PALETTE['text_primary']};">
                        {company_meta['company_name']} ({company_meta['exchange']}: {company_meta['symbol']})
                    </span>
                    &nbsp;|&nbsp;
                    <span style="color:{PALETTE['text_secondary']}; font-size:0.9rem;">
                        Sector: <b>{company_meta['sector']}</b> &bull; Scope: <b>{selected_scope}</b> &bull; Coverage: <b>{period_str}</b>
                    </span>
                </div>
                <div>
                    <span class="badge-info">Ref Price: ₹{company_meta['reference_price_inr']:,.1f} ({company_meta['reference_price_date']})</span>
                    &nbsp;
                    <span class="badge-verified">Verified: {company_meta['last_verified_date']}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return company_meta, selected_scope


def render_kpi_card(label: str, value: str, subtitle: str = "", status: str = "neutral") -> None:
    """Render a stylized institutional metric card."""
    border_color = PALETTE["divider"]
    if status == "positive":
        border_color = PALETTE["positive"]
    elif status == "warning":
        border_color = PALETTE["warning"]
    elif status == "negative":
        border_color = PALETTE["negative"]

    st.markdown(
        f"""
        <div class="thesis-card" style="border-top: 3px solid {border_color};">
            <div class="thesis-kpi-label">{label}</div>
            <div class="thesis-kpi-value">{value}</div>
            <div class="thesis-kpi-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render mandatory institutional and regulatory disclaimer footer."""
    st.markdown(
        f'<div class="disclaimer-footer">{INSTITUTIONAL_DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )
