"""24-Section Institutional Investment Research Memo Schema & Deterministic Generator."""
from datetime import date
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel
from thesisos.config import INSTITUTIONAL_DISCLAIMER
from thesisos.data.sources import DataQualityReport, SourceRecord
from thesisos.finance.dcf import DCFOutput
from thesisos.finance.forensic import ForensicAlert


class MemoSection(BaseModel):
    section_number: int
    title: str
    epistemic_badge: str  # "VERIFIED FACT", "CALCULATED METRIC", "ANALYST ASSUMPTION", "RULE-BASED SYNTHESIS", "AI INTERPRETATION"
    content: str
    citations: List[str] = []


class ResearchMemoDossier(BaseModel):
    company_id: str
    company_name: str
    exchange_symbol: str
    reporting_scope: str
    generation_mode: str  # "DETERMINISTIC_RULE_BASED", "PREVERIFIED_EXAMPLE_DOSSIER", "LIVE_BYOK_AI_VALIDATED"
    generation_date: str
    underlying_data_date: str
    model_provenance: str
    sections: List[MemoSection]
    validation_warnings: List[str] = []
    disclaimer: str = INSTITUTIONAL_DISCLAIMER


def build_deterministic_research_memo(
    company_meta: Dict[str, Any],
    scope: str,
    metrics_df: pd.DataFrame,
    cagrs: Dict[str, Optional[float]],
    multiples: Dict[str, Optional[float]],
    forensic_alerts: List[ForensicAlert],
    dcf_output: DCFOutput,
    scenarios: Dict[str, DCFOutput],
    reverse_dcf_growth: Optional[float],
    dq_report: DataQualityReport,
    sources: List[SourceRecord],
) -> ResearchMemoDossier:
    """Generate the complete 24-section institutional research memo deterministically ($0, no API key)."""
    latest = metrics_df.iloc[-1]
    first = metrics_df.iloc[0]
    fy_span = f"{first['fiscal_year']} to {latest['fiscal_year']}"
    sids = [f"{s.source_id} (p.{s.page})" for s in sources[:5]]

    rev_cagr_str = f"{cagrs['revenue_cagr']*100:.2f}%" if cagrs.get("revenue_cagr") is not None else "N/A"
    pat_cagr_str = f"{cagrs['pat_cagr']*100:.2f}%" if cagrs.get("pat_cagr") is not None else "N/A"
    alert_summary = (
        f"{len(forensic_alerts)} forensic investigation alert(s) triggered across {fy_span}."
        if forensic_alerts
        else f"Zero high-severity forensic accounting alerts triggered across {fy_span}."
    )

    sections: List[MemoSection] = [
        MemoSection(
            section_number=1,
            title="Company Identity & Research Date",
            epistemic_badge="VERIFIED FACT",
            content=(
                f"**{company_meta['company_name']}** ({company_meta['exchange']}: `{company_meta['symbol']}`) | "
                f"Sector: {company_meta['sector']} | Research Date: {date.today().isoformat()} | "
                f"Last Data Verification: {company_meta['last_verified_date']}."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=2,
            title="Reporting Scope & Data Coverage",
            epistemic_badge="VERIFIED FACT",
            content=(
                f"Scope: **{scope}** Ind-AS Audited Financial Statements covering **{fy_span}** "
                f"({len(metrics_df)} annual periods, {dq_report.total_observations} verified observations). "
                f"Missing years: {dq_report.missing_years or 'None'}."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=3,
            title="Executive Summary",
            epistemic_badge="RULE-BASED SYNTHESIS",
            content=(
                f"In {latest['fiscal_year']}, {company_meta['company_name']} reported {scope} Revenue of "
                f"**₹{latest['revenue']:,.1f} Cr** ({latest['revenue_growth']*100:+.1f}% YoY) and PAT of "
                f"**₹{latest['pat']:,.1f} Cr** (PAT Margin: {latest['pat_margin']*100:.1f}%). "
                f"Our deterministic FCFF DCF yields an implied fair value of **₹{dcf_output.fair_value_per_share_inr:,.2f}/share** "
                f"against the dated reference price of **₹{dcf_output.reference_price_inr:,.1f}** ({dcf_output.reference_price_date}), "
                f"representing **{dcf_output.upside_downside_pct*100:+.1f}%** implied upside/downside."
            ),
            citations=sids[:3],
        ),
        MemoSection(
            section_number=4,
            title="Business Overview",
            epistemic_badge="VERIFIED FACT",
            content=str(company_meta.get("description", "")),
            citations=sids[:1],
        ),
        MemoSection(
            section_number=5,
            title="Historical Financial Performance",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"Across {fy_span}, Revenue scaled from ₹{first['revenue']:,.1f} Cr to ₹{latest['revenue']:,.1f} Cr "
                f"(CAGR: **{rev_cagr_str}**), while PAT expanded from ₹{first['pat']:,.1f} Cr to ₹{latest['pat']:,.1f} Cr "
                f"(CAGR: **{pat_cagr_str}**)."
            ),
            citations=sids[:3],
        ),
        MemoSection(
            section_number=6,
            title="Profitability & Return Analysis",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"In {latest['fiscal_year']}, EBITDA Margin stood at **{latest['ebitda_margin']*100:.2f}%**, "
                f"EBIT Margin at **{latest['ebit_margin']*100:.2f}%**, ROE at **{latest['roe']*100:.2f}%**, "
                f"and ROCE at **{latest['roce']*100:.2f}%**."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=7,
            title="Balance-Sheet & Liquidity Analysis",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"Total Equity stood at ₹{latest['total_equity']:,.1f} Cr against Total Debt (lease liabilities) of "
                f"₹{latest['total_debt']:,.1f} Cr and Cash & Investments of ₹{latest['cash_and_investments']:,.1f} Cr, "
                f"resulting in Net Debt of **₹{latest['net_debt']:,.1f} Cr** and Current Ratio of **{latest['current_ratio']:.2f}x**."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=8,
            title="Cash-Flow Quality",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"{latest['fiscal_year']} Operating Cash Flow (CFO) was **₹{latest['cfo']:,.1f} Cr**, representing a "
                f"**{latest['cfo_to_pat']:.2f}x** CFO/PAT conversion ratio. After Capex of ₹{latest['capex']:,.1f} Cr, "
                f"Free Cash Flow (FCF) reached **₹{latest['fcf']:,.1f} Cr**."
            ),
            citations=sids[:3],
        ),
        MemoSection(
            section_number=9,
            title="Working-Capital Analysis",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"Receivable Days (DSO): **{latest['receivable_days']:.1f} days** | "
                f"Inventory Days (DIO): **{latest['inventory_days']:.1f} days** | "
                f"Payable Days (DPO): **{latest['payable_days']:.1f} days** | "
                f"Cash Conversion Cycle (CCC): **{latest['cash_conversion_cycle']:.1f} days**."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=10,
            title="Financial-Quality & Forensic Alerts",
            epistemic_badge="CALCULATED METRIC",
            content=alert_summary
            + (
                " Triggered rules: " + "; ".join([f"{a.rule_name} ({a.fiscal_period}: {a.actual_value})" for a in forensic_alerts])
                if forensic_alerts
                else ""
            ),
            citations=sids[:3],
        ),
        MemoSection(
            section_number=11,
            title="Industry Context (Verified Disclosures Only)",
            epistemic_badge="VERIFIED FACT",
            content=(
                next((s.extracted_passage for s in sources if "growth" in s.extracted_passage.lower()), "Refer to Annual Report MD&A.")
            ),
            citations=sids[:1],
        ),
        MemoSection(
            section_number=12,
            title="Key Disclosed Risks",
            epistemic_badge="VERIFIED FACT",
            content=(
                next((s.extracted_passage for s in sources if "risk" in s.extracted_passage.lower()), "Refer to Statutory Risk Disclosures.")
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=13,
            title="Bull Thesis (Evidence-Backed)",
            epistemic_badge="RULE-BASED SYNTHESIS",
            content=(
                f"Sustained capital efficiency (ROE {latest['roe']*100:.1f}%, ROCE {latest['roce']*100:.1f}%), net-cash balance sheet "
                f"(Net Debt ₹{latest['net_debt']:,.1f} Cr), and strong cash conversion ({latest['cfo_to_pat']:.2f}x CFO/PAT). "
                f"Bull Case DCF implies **₹{scenarios['BULL'].fair_value_per_share_inr:,.2f}/share**."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=14,
            title="Bear Thesis (Evidence-Backed)",
            epistemic_badge="RULE-BASED SYNTHESIS",
            content=(
                "Prolonged macroeconomic tightening in North America/Europe could compress client discretionary spending and operating margins. "
                f"Bear Case DCF implies **₹{scenarios['BEAR'].fair_value_per_share_inr:,.2f}/share**."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=15,
            title="Key Catalysts to Monitor",
            epistemic_badge="RULE-BASED SYNTHESIS",
            content=(
                "1. Quarterly order-book TCV conversion into billed revenue.\n"
                "2. Operating EBIT margin expansion vs. wage hike cycle.\n"
                "3. Resolution of disputed tax claims disclosed under contingent liabilities."
            ),
            citations=sids[:2],
        ),
        MemoSection(
            section_number=16,
            title="DCF Valuation Assumptions",
            epistemic_badge="ANALYST ASSUMPTION",
            content=(
                f"WACC: **{dcf_output.wacc*100:.2f}%** | Terminal Growth: **{dcf_output.terminal_growth_rate*100:.2f}%** | "
                f"Forecast Horizon: {len(dcf_output.projections)} years | Diluted Shares: {dcf_output.diluted_shares_crore:.2f} Cr."
            ),
            citations=[],
        ),
        MemoSection(
            section_number=17,
            title="DCF Outputs & Sensitivity Summary",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"PV of Forecast FCFF: ₹{dcf_output.sum_pv_fcff_cr:,.1f} Cr | "
                f"PV of Terminal Value: ₹{dcf_output.pv_terminal_value_cr:,.1f} Cr ({dcf_output.terminal_value_pct_of_ev*100:.1f}% of EV) | "
                f"Enterprise Value: ₹{dcf_output.enterprise_value_cr:,.1f} Cr | "
                f"Equity Value: ₹{dcf_output.equity_value_cr:,.1f} Cr | "
                f"Implied Fair Value: **₹{dcf_output.fair_value_per_share_inr:,.2f}/share**."
            ),
            citations=[],
        ),
        MemoSection(
            section_number=18,
            title="Comparable Valuation Multiples",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"At reference price ₹{dcf_output.reference_price_inr:,.1f} ({dcf_output.reference_price_date}): "
                f"P/E: **{multiples.get('pe_ratio', 0.0):.2f}x** | P/B: **{multiples.get('pb_ratio', 0.0):.2f}x** | "
                f"EV/EBITDA: **{multiples.get('ev_to_ebitda', 0.0):.2f}x** | FCF Yield: **{(multiples.get('fcf_yield') or 0.0)*100:.2f}%**."
            ),
            citations=[],
        ),
        MemoSection(
            section_number=19,
            title="Reverse DCF Implied Expectations",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"To justify the reference market price of ₹{dcf_output.reference_price_inr:,.1f}/share at a WACC of {dcf_output.wacc*100:.2f}% "
                f"and terminal growth of {dcf_output.terminal_growth_rate*100:.2f}%, the market implies a 5-year annual revenue growth rate of "
                f"**{reverse_dcf_growth*100:.2f}%**."
                if reverse_dcf_growth is not None
                else "Reverse DCF solver constrained."
            ),
            citations=[],
        ),
        MemoSection(
            section_number=20,
            title="Margin of Safety Analysis",
            epistemic_badge="CALCULATED METRIC",
            content=(
                f"Base Case Implied Margin of Safety: **{dcf_output.margin_of_safety_pct*100:+.2f}%** "
                f"(Upside/Downside: **{dcf_output.upside_downside_pct*100:+.2f}%** vs. dated reference price)."
            ),
            citations=[],
        ),
        MemoSection(
            section_number=21,
            title="Thesis-Breaking Conditions",
            epistemic_badge="ANALYST ASSUMPTION",
            content=(
                "1. CFO/PAT conversion dropping below 0.80x for two consecutive fiscal years.\n"
                "2. Operating EBIT margin falling below 21.0% structurally.\n"
                "3. Adverse crystallization of disputed contingent liabilities exceeding 15% of annual FCF."
            ),
            citations=[],
        ),
        MemoSection(
            section_number=22,
            title="Missing Evidence & Data Quality Gaps",
            epistemic_badge="VERIFIED FACT",
            content=(
                f"Data Quality Status: {'CLEAN' if dq_report.is_clean else 'ISSUES FLAGGED'}. "
                f"Total issues logged: {len(dq_report.issues)}. "
                "Segment-level geographic contract profitability and live intraday order-book figures require quarterly earnings call transcripts."
            ),
            citations=[],
        ),
        MemoSection(
            section_number=23,
            title="Traceable Source References",
            epistemic_badge="VERIFIED FACT",
            content="\n".join(
                [f"- **`{s.source_id}`**: {s.document_title} ({s.reporting_period}), Page {s.page} — [Official Filing Link]({s.source_url})" for s in sources]
            ),
            citations=sids,
        ),
        MemoSection(
            section_number=24,
            title="Limitations & Regulatory Disclosure",
            epistemic_badge="VERIFIED FACT",
            content=INSTITUTIONAL_DISCLAIMER,
            citations=[],
        ),
    ]

    return ResearchMemoDossier(
        company_id=company_meta["company_id"],
        company_name=company_meta["company_name"],
        exchange_symbol=f"{company_meta['exchange']}:{company_meta['symbol']}",
        reporting_scope=scope,
        generation_mode="DETERMINISTIC_RULE_BASED",
        generation_date=date.today().isoformat(),
        underlying_data_date=str(company_meta["last_verified_date"]),
        model_provenance="ThesisOS Deterministic Python Engine v1.0 (Zero External LLM / 100% Offline)",
        sections=sections,
        validation_warnings=dcf_output.warnings,
    )
