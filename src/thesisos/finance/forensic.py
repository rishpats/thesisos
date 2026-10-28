"""Rule-based forensic accounting and earnings quality alert engine."""
from typing import Dict, List, Optional
import pandas as pd
from pydantic import BaseModel
from thesisos.config import DEFAULT_FORENSIC_THRESHOLDS
from thesisos.finance.metrics import calculate_yoy_growth


class ForensicAlert(BaseModel):
    rule_id: str
    rule_name: str
    severity: str  # "HIGH_INVESTIGATION", "MODERATE_WATCH", "INFO"
    threshold_description: str
    actual_value: str
    comparison_value: str
    fiscal_period: str
    cautious_explanation: str
    supporting_figures: str
    source_references: List[str]
    recommended_followup_question: str


def evaluate_forensic_alerts(
    metrics_df: pd.DataFrame,
    raw_facts_df: pd.DataFrame,
    thresholds: Optional[Dict[str, float]] = None,
) -> List[ForensicAlert]:
    """
    Evaluate 10 configurable forensic accounting rules across the historical series.
    Uses cautious institutional language: alerts indicate investigation areas, never accusations of fraud.
    """
    if metrics_df.empty:
        return []

    cfg = {**DEFAULT_FORENSIC_THRESHOLDS, **(thresholds or {})}
    alerts: List[ForensicAlert] = []
    df = metrics_df.sort_values("fiscal_year").reset_index(drop=True)

    def _sources_for_year(fy: str) -> List[str]:
        if raw_facts_df.empty:
            return ["SOURCE_PENDING"]
        sub = raw_facts_df[raw_facts_df["fiscal_year"] == fy]
        sids = sorted(sub["source_id"].dropna().astype(str).unique().tolist())
        return sids if sids else ["SOURCE_PENDING"]

    for i in range(len(df)):
        row = df.loc[i]
        fy = str(row["fiscal_year"])
        sources = _sources_for_year(fy)

        # Rule 1: Weak Cash Conversion (CFO / PAT < threshold)
        cfo_pat = row.get("cfo_to_pat")
        if pd.notna(cfo_pat) and cfo_pat < cfg["cfo_to_pat_min"]:
            alerts.append(
                ForensicAlert(
                    rule_id="FORENSIC_01_CASH_CONVERSION",
                    rule_name="Low Operating Cash Flow to PAT Conversion",
                    severity="HIGH_INVESTIGATION",
                    threshold_description=f"CFO / PAT < {cfg['cfo_to_pat_min']:.2f}x",
                    actual_value=f"{cfo_pat:.2f}x",
                    comparison_value=f">= {cfg['cfo_to_pat_min']:.2f}x benchmark",
                    fiscal_period=fy,
                    cautious_explanation=(
                        f"In {fy}, Operating Cash Flow (₹{row['cfo']:,.1f} Cr) converted only {cfo_pat:.2f}x "
                        f"of reported PAT (₹{row['pat']:,.1f} Cr). This warrants reviewing working-capital absorption "
                        "or non-cash accrual items."
                    ),
                    supporting_figures=f"CFO: ₹{row['cfo']:,.1f} Cr | PAT: ₹{row['pat']:,.1f} Cr",
                    source_references=sources,
                    recommended_followup_question=(
                        "What working capital movements or unbilled revenue accruals caused operating cash generation "
                        "to lag reported net profit in this period?"
                    ),
                )
            )

        # Rule 2: Profit Growth with Deteriorating Operating Cash Flow
        if i > 0:
            prev = df.loc[i - 1]
            pat_g = row.get("pat_growth")
            cfo_g = calculate_yoy_growth(row.get("cfo"), prev.get("cfo"))
            if pd.notna(pat_g) and pd.notna(cfo_g) and pat_g > 0.0 and cfo_g < 0.0:
                alerts.append(
                    ForensicAlert(
                        rule_id="FORENSIC_02_PAT_CFO_DIVERGENCE",
                        rule_name="Positive PAT Growth Accompanied by Contracting Operating Cash Flow",
                        severity="HIGH_INVESTIGATION",
                        threshold_description="PAT Growth > 0% while CFO Growth < 0%",
                        actual_value=f"PAT {pat_g*100:+.1f}% vs CFO {cfo_g*100:+.1f}%",
                        comparison_value=f"Prior Year ({prev['fiscal_year']}) CFO ₹{prev['cfo']:,.1f} Cr",
                        fiscal_period=fy,
                        cautious_explanation=(
                            f"Reported PAT expanded by {pat_g*100:.1f}% YoY in {fy}, whereas Operating Cash Flow "
                            f"contracted by {abs(cfo_g)*100:.1f}% YoY. Divergence between accrual earnings and cash flow "
                            "is a primary area for analyst due diligence."
                        ),
                        supporting_figures=f"{fy} PAT ₹{row['pat']:,.1f} Cr (vs ₹{prev['pat']:,.1f} Cr); CFO ₹{row['cfo']:,.1f} Cr (vs ₹{prev['cfo']:,.1f} Cr)",
                        source_references=sources,
                        recommended_followup_question=(
                            "Did extended customer credit terms or higher tax outflows drive the decline in operating cash flow despite higher accounting earnings?"
                        ),
                    )
                )

            # Rule 3: Receivables Growing Faster Than Revenue
            rec_g = calculate_yoy_growth(row.get("trade_receivables"), prev.get("trade_receivables"))
            rev_g = row.get("revenue_growth")
            if pd.notna(rec_g) and pd.notna(rev_g) and (rec_g - rev_g) > cfg["receivable_vs_rev_growth_gap"]:
                alerts.append(
                    ForensicAlert(
                        rule_id="FORENSIC_03_RECEIVABLES_OUTPACING_REVENUE",
                        rule_name="Trade Receivables Growing Faster Than Revenue",
                        severity="MODERATE_WATCH",
                        threshold_description=f"Receivables Growth - Revenue Growth > {cfg['receivable_vs_rev_growth_gap']*100:.1f}%",
                        actual_value=f"Receivables {rec_g*100:+.1f}% vs Revenue {rev_g*100:+.1f}%",
                        comparison_value=f"Spread: +{(rec_g - rev_g)*100:.1f}%",
                        fiscal_period=fy,
                        cautious_explanation=(
                            f"Trade receivables grew by {rec_g*100:.1f}% in {fy}, outpacing top-line revenue growth "
                            f"of {rev_g*100:.1f}% by {(rec_g - rev_g)*100:.1f} percentage points."
                        ),
                        supporting_figures=f"Receivables: ₹{prev['trade_receivables']:,.1f} Cr -> ₹{row['trade_receivables']:,.1f} Cr",
                        source_references=sources,
                        recommended_followup_question=(
                            "What proportion of year-end trade receivables represents unbilled revenue or milestone-delayed enterprise billings?"
                        ),
                    )
                )

            # Rule 4: Jump in Receivable Days (DSO)
            dso_curr = row.get("receivable_days")
            dso_prev = prev.get("receivable_days")
            if pd.notna(dso_curr) and pd.notna(dso_prev) and (dso_curr - dso_prev) > cfg["receivable_days_jump"]:
                alerts.append(
                    ForensicAlert(
                        rule_id="FORENSIC_04_RISING_DSO",
                        rule_name="Material Increase in Receivable Days (DSO)",
                        severity="MODERATE_WATCH",
                        threshold_description=f"YoY DSO Increase > {cfg['receivable_days_jump']:.1f} days",
                        actual_value=f"{dso_curr:.1f} days",
                        comparison_value=f"{dso_prev:.1f} days in {prev['fiscal_year']}",
                        fiscal_period=fy,
                        cautious_explanation=(
                            f"Average Receivable Days rose by {dso_curr - dso_prev:.1f} days in {fy}, indicating slower customer cash collections."
                        ),
                        supporting_figures=f"DSO: {dso_prev:.1f}d -> {dso_curr:.1f}d",
                        source_references=sources,
                        recommended_followup_question="Has the ageing schedule of receivables >180 days increased during the fiscal year?",
                    )
                )

            # Rule 5: EBITDA Margin Compression
            eb_curr = row.get("ebitda_margin")
            eb_prev = prev.get("ebitda_margin")
            if pd.notna(eb_curr) and pd.notna(eb_prev) and ((eb_prev - eb_curr) * 10000.0) > cfg["ebitda_margin_drop_bps"]:
                drop_bps = (eb_prev - eb_curr) * 10000.0
                alerts.append(
                    ForensicAlert(
                        rule_id="FORENSIC_05_MARGIN_COMPRESSION",
                        rule_name="Operating EBITDA Margin Compression",
                        severity="MODERATE_WATCH",
                        threshold_description=f"EBITDA Margin decline > {cfg['ebitda_margin_drop_bps']:.0f} bps YoY",
                        actual_value=f"{eb_curr*100:.2f}% (-{drop_bps:.0f} bps)",
                        comparison_value=f"{eb_prev*100:.2f}% in {prev['fiscal_year']}",
                        fiscal_period=fy,
                        cautious_explanation=f"EBITDA margin compressed by {drop_bps:.0f} bps in {fy}.",
                        supporting_figures=f"EBITDA ₹{row['ebitda']:,.1f} Cr on Revenue ₹{row['revenue']:,.1f} Cr",
                        source_references=sources,
                        recommended_followup_question="Was margin compression driven by wage/input inflation, pricing pressure, or one-time restructuring charges?",
                    )
                )

            # Rule 6: Capex Surge Accompanied by Declining Free Cash Flow
            cx_g = calculate_yoy_growth(row.get("capex"), prev.get("capex"))
            fcf_g = row.get("fcf_growth")
            if pd.notna(cx_g) and pd.notna(fcf_g) and cx_g > 0.15 and fcf_g < 0.0:
                alerts.append(
                    ForensicAlert(
                        rule_id="FORENSIC_06_CAPEX_FCF_SQUEEZE",
                        rule_name="Rising Capital Expenditure with Contracting Free Cash Flow",
                        severity="MODERATE_WATCH",
                        threshold_description="Capex Growth > 15% while FCF Growth < 0%",
                        actual_value=f"Capex {cx_g*100:+.1f}% | FCF {fcf_g*100:+.1f}%",
                        comparison_value=f"Prior FCF ₹{prev['fcf']:,.1f} Cr",
                        fiscal_period=fy,
                        cautious_explanation=(
                            f"Capital expenditure increased by {cx_g*100:.1f}% while Free Cash Flow declined by {abs(fcf_g)*100:.1f}% in {fy}."
                        ),
                        supporting_figures=f"Capex: ₹{row['capex']:,.1f} Cr | FCF: ₹{row['fcf']:,.1f} Cr",
                        source_references=sources,
                        recommended_followup_question="What is the expected ROIC and payback timeline on the incremental capital expenditure?",
                    )
                )

        # Rule 7: Elevated Net Debt / EBITDA
        nd_eb = row.get("net_debt_to_ebitda")
        if pd.notna(nd_eb) and nd_eb > cfg["net_debt_to_ebitda_max"]:
            alerts.append(
                ForensicAlert(
                    rule_id="FORENSIC_07_HIGH_LEVERAGE",
                    rule_name="Elevated Net Debt to EBITDA Leverage",
                    severity="HIGH_INVESTIGATION",
                    threshold_description=f"Net Debt / EBITDA > {cfg['net_debt_to_ebitda_max']:.1f}x",
                    actual_value=f"{nd_eb:.2f}x",
                    comparison_value=f"<= {cfg['net_debt_to_ebitda_max']:.1f}x",
                    fiscal_period=fy,
                    cautious_explanation=f"Net Debt / EBITDA stood at {nd_eb:.2f}x in {fy}.",
                    supporting_figures=f"Net Debt: ₹{row['net_debt']:,.1f} Cr | EBITDA: ₹{row['ebitda']:,.1f} Cr",
                    source_references=sources,
                    recommended_followup_question="What is the debt maturity schedule and refinancing plan over the next 24 months?",
                )
            )

        # Rule 8: Weak Interest Coverage
        icov = row.get("interest_coverage")
        if pd.notna(icov) and icov < cfg["interest_coverage_min"]:
            alerts.append(
                ForensicAlert(
                    rule_id="FORENSIC_08_WEAK_INTEREST_COVERAGE",
                    rule_name="Low EBIT Interest Coverage Ratio",
                    severity="HIGH_INVESTIGATION",
                    threshold_description=f"EBIT / Finance Costs < {cfg['interest_coverage_min']:.1f}x",
                    actual_value=f"{icov:.2f}x",
                    comparison_value=f">= {cfg['interest_coverage_min']:.1f}x",
                    fiscal_period=fy,
                    cautious_explanation=f"Interest coverage was {icov:.2f}x in {fy}, leaving limited buffer against earnings volatility.",
                    supporting_figures=f"EBIT: ₹{row['ebit']:,.1f} Cr | Finance Costs: ₹{row['finance_costs']:,.1f} Cr",
                    source_references=sources,
                    recommended_followup_question="Are borrowing covenants tied to minimum interest coverage thresholds?",
                )
            )

        # Rule 9: Dividends Exceeding Free Cash Flow
        divs = row.get("dividends_paid")
        fcf = row.get("fcf")
        if pd.notna(divs) and pd.notna(fcf) and fcf > 0 and (divs / fcf) > cfg["dividend_payout_vs_fcf_max"]:
            alerts.append(
                ForensicAlert(
                    rule_id="FORENSIC_09_DIVIDEND_EXCEEDS_FCF",
                    rule_name="Dividend Outflow Exceeding Annual Free Cash Flow",
                    severity="MODERATE_WATCH",
                    threshold_description="Dividends Paid / FCF > 1.00x",
                    actual_value=f"{divs / fcf:.2f}x of FCF",
                    comparison_value=f"FCF ₹{fcf:,.1f} Cr",
                    fiscal_period=fy,
                    cautious_explanation=(
                        f"In {fy}, cash dividends paid (₹{divs:,.1f} Cr) exceeded annual Free Cash Flow (₹{fcf:,.1f} Cr), "
                        "indicating distributions were partially funded from existing treasury cash reserves."
                    ),
                    supporting_figures=f"Dividends Paid: ₹{divs:,.1f} Cr | FCF: ₹{fcf:,.1f} Cr | Treasury Cash: ₹{row.get('cash_and_investments', 0.0):,.1f} Cr",
                    source_references=sources,
                    recommended_followup_question="Was the elevated payout due to a one-time special dividend from accumulated cash reserves?",
                )
            )

    return alerts
