"""Unit tests for the deterministic DCF valuation engine, guardrails, and sensitivity rules."""
import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.finance.dcf import (
    DCFAssumptions,
    run_dcf_valuation,
    solve_reverse_dcf_implied_growth,
)
from thesisos.finance.scenarios import generate_wacc_tg_sensitivity_grid


def _make_sample_dcf_assumptions(wacc_override=0.10, tg=0.04) -> DCFAssumptions:
    return DCFAssumptions(
        company_id="TEST_CO",
        base_fiscal_year="FY2025",
        base_revenue_cr=1000.0,
        forecast_years=2,
        revenue_growth_rates=[0.10, 0.10],
        ebit_margins=[0.20, 0.20],
        effective_tax_rate=0.25,
        da_pct_revenue=0.02,
        capex_pct_revenue=0.02,
        nwc_change_pct_rev_change=0.0,
        equity_weight=1.0,
        debt_weight=0.0,
        cost_of_equity=0.10,
        pretax_cost_of_debt=0.0,
        wacc_override=wacc_override,
        terminal_growth_rate=tg,
        total_debt_cr=50.0,
        cash_and_investments_cr=150.0,
        other_equity_adjustments_cr=0.0,
        diluted_shares_crore=10.0,
        reference_price_inr=250.0,
        reference_price_date="2025-05-30",
    )


def test_manual_2_year_dcf_calculation():
    """
    Manual check:
      Year 1: Rev = 1100, EBIT = 220, NOPAT = 165, D&A = 22, Capex = 22, dNWC = 0 -> FCFF_1 = 165.0
              PV(FCFF_1) = 165 / 1.10 = 150.0
      Year 2: Rev = 1210, EBIT = 242, NOPAT = 181.5, D&A = 24.2, Capex = 24.2, dNWC = 0 -> FCFF_2 = 181.5
              PV(FCFF_2) = 181.5 / (1.10^2) = 150.0
      Sum PV FCFF = 300.0
      Terminal FCFF_3 = 181.5 * 1.04 = 188.76
      Terminal Value = 188.76 / (0.10 - 0.04) = 3146.0
      PV(Terminal Value) = 3146.0 / 1.21 = 2600.0
      Enterprise Value = 300.0 + 2600.0 = 2900.0 Cr
      Net Debt = 50.0 - 150.0 = -100.0 Cr
      Equity Value = 2900.0 - (-100.0) = 3000.0 Cr
      Per Share Value = 3000.0 / 10.0 = 300.0 INR
    """
    assump = _make_sample_dcf_assumptions(wacc_override=0.10, tg=0.04)
    out = run_dcf_valuation(assump)

    assert pytest.approx(out.projections[0].fcff_cr, rel=1e-4) == 165.0
    assert pytest.approx(out.projections[1].fcff_cr, rel=1e-4) == 181.5
    assert pytest.approx(out.sum_pv_fcff_cr, rel=1e-4) == 300.0
    assert pytest.approx(out.undiscounted_terminal_value_cr, rel=1e-4) == 3146.0
    assert pytest.approx(out.pv_terminal_value_cr, rel=1e-4) == 2600.0
    assert pytest.approx(out.enterprise_value_cr, rel=1e-4) == 2900.0
    assert pytest.approx(out.net_debt_cr, rel=1e-4) == -100.0
    assert pytest.approx(out.equity_value_cr, rel=1e-4) == 3000.0
    assert pytest.approx(out.fair_value_per_share_inr, rel=1e-4) == 300.0
    assert pytest.approx(out.upside_downside_pct, rel=1e-4) == 0.20  # (300 / 250) - 1


def test_wacc_monotonicity_and_terminal_growth_guardrail():
    low_wacc = run_dcf_valuation(_make_sample_dcf_assumptions(wacc_override=0.09, tg=0.04))
    high_wacc = run_dcf_valuation(_make_sample_dcf_assumptions(wacc_override=0.12, tg=0.04))
    assert low_wacc.fair_value_per_share_inr > high_wacc.fair_value_per_share_inr

    # Blocking g >= WACC
    with pytest.raises(ValueError, match="strictly less than WACC"):
        _make_sample_dcf_assumptions(wacc_override=0.08, tg=0.08)

    with pytest.raises(ValueError, match="strictly less than WACC"):
        _make_sample_dcf_assumptions(wacc_override=0.08, tg=0.09)


def test_reverse_dcf_and_sensitivity_grid():
    assump = _make_sample_dcf_assumptions(wacc_override=0.10, tg=0.04)
    implied_g = solve_reverse_dcf_implied_growth(assump, target_price_inr=300.0)
    assert implied_g is not None
    assert pytest.approx(implied_g, abs=1e-3) == 0.10

    w_list, g_list, grid = generate_wacc_tg_sensitivity_grid(assump)
    assert len(grid) == len(w_list)
    assert len(grid[0]) == len(g_list)
