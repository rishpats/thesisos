"""Unit tests for the deterministic financial engine using the exact synthetic benchmark from Section 16."""
import sys
from pathlib import Path
import pandas as pd
import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.finance.forensic import evaluate_forensic_alerts
from thesisos.finance.metrics import (
    calculate_cagr,
    calculate_yoy_growth,
    compute_financial_metrics_table,
    safe_divide,
)
from thesisos.finance.working_capital import append_working_capital_metrics


def test_section_16_synthetic_company_known_answers():
    """
    Verify exact expected answers from Section 16:
      FY2024: Revenue 500, EBITDA 75, PAT 40, CFO 45, Capex 20
      FY2025: Revenue 600, EBITDA 90, PAT 48, CFO 36, Capex 25
      Expected:
        - Revenue growth: 20% (0.20)
        - EBITDA margin: 15% (0.15) in both years
        - PAT margin: 8% (0.08) in both years
        - CFO/PAT: 1.125x in FY2024, 0.75x in FY2025
        - FCF: 25 Cr in FY2024, 11 Cr in FY2025
    """
    wide_df = pd.DataFrame(
        [
            {
                "fiscal_year": "FY2024",
                "revenue": 500.0,
                "cogs": 300.0,
                "ebitda": 75.0,
                "da": 15.0,
                "ebit": 60.0,
                "finance_costs": 5.0,
                "pbt": 55.0,
                "tax": 15.0,
                "pat": 40.0,
                "eps": 40.0,
                "cfo": 45.0,
                "capex": 20.0,
                "trade_receivables": 50.0,
                "inventory": 30.0,
                "trade_payables": 25.0,
                "current_assets": 150.0,
                "cash_and_investments": 40.0,
                "total_assets": 400.0,
                "current_liabilities": 60.0,
                "total_debt": 20.0,
                "total_equity": 250.0,
                "diluted_shares": 1.0,
                "dividends_paid": 10.0,
            },
            {
                "fiscal_year": "FY2025",
                "revenue": 600.0,
                "cogs": 360.0,
                "ebitda": 90.0,
                "da": 18.0,
                "ebit": 72.0,
                "finance_costs": 6.0,
                "pbt": 66.0,
                "tax": 18.0,
                "pat": 48.0,
                "eps": 48.0,
                "cfo": 36.0,
                "capex": 25.0,
                "trade_receivables": 75.0,
                "inventory": 36.0,
                "trade_payables": 30.0,
                "current_assets": 180.0,
                "cash_and_investments": 35.0,
                "total_assets": 450.0,
                "current_liabilities": 70.0,
                "total_debt": 20.0,
                "total_equity": 288.0,
                "diluted_shares": 1.0,
                "dividends_paid": 10.0,
            },
        ]
    )

    res = append_working_capital_metrics(compute_financial_metrics_table(wide_df))
    fy24 = res.iloc[0]
    fy25 = res.iloc[1]

    assert fy24["revenue_growth"] is None or pd.isna(fy24["revenue_growth"])
    assert pytest.approx(fy25["revenue_growth"], rel=1e-6) == 0.20

    assert pytest.approx(fy24["ebitda_margin"], rel=1e-6) == 0.15
    assert pytest.approx(fy25["ebitda_margin"], rel=1e-6) == 0.15

    assert pytest.approx(fy24["pat_margin"], rel=1e-6) == 0.08
    assert pytest.approx(fy25["pat_margin"], rel=1e-6) == 0.08

    assert pytest.approx(fy24["cfo_to_pat"], rel=1e-6) == 1.125
    assert pytest.approx(fy25["cfo_to_pat"], rel=1e-6) == 0.75

    assert pytest.approx(fy24["fcf"], rel=1e-6) == 25.0
    assert pytest.approx(fy25["fcf"], rel=1e-6) == 11.0

    # Forensic alerts should flag FY2025 CFO/PAT < 0.80x and PAT growth (+20%) with CFO contraction (-20%)
    alerts = evaluate_forensic_alerts(res, pd.DataFrame())
    rule_ids = {a.rule_id for a in alerts}
    assert "FORENSIC_01_CASH_CONVERSION" in rule_ids
    assert "FORENSIC_02_PAT_CFO_DIVERGENCE" in rule_ids
    assert "FORENSIC_03_RECEIVABLES_OUTPACING_REVENUE" in rule_ids


def test_zero_and_negative_denominator_safety():
    assert safe_divide(100.0, 0.0) is None
    assert safe_divide(100.0, -50.0, allow_negative_denom=False) is None
    assert calculate_yoy_growth(120.0, 0.0) is None
    assert calculate_yoy_growth(120.0, -40.0) is None
    assert calculate_cagr(200.0, -50.0, 3) is None
