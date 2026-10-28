"""Deterministic Free Cash Flow to Firm (FCFF) DCF Valuation Engine & Reverse DCF Solver."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DCFAssumptions(BaseModel):
    company_id: str
    base_fiscal_year: str
    base_revenue_cr: float = Field(gt=0)
    forecast_years: int = Field(default=5, ge=1, le=10)
    revenue_growth_rates: List[float]      # e.g., [0.08, 0.08, 0.075, 0.07, 0.065]
    ebit_margins: List[float]              # e.g., [0.245, 0.245, 0.25, 0.25, 0.25]
    effective_tax_rate: float = Field(default=0.25, ge=0.0, lt=0.60)
    da_pct_revenue: float = Field(default=0.02, ge=0.0, le=0.30)
    capex_pct_revenue: float = Field(default=0.018, ge=0.0, le=0.40)
    nwc_change_pct_rev_change: float = Field(default=0.08, ge=-0.50, le=0.50)

    # WACC / Capital Structure Inputs
    equity_weight: float = Field(default=0.95, ge=0.0, le=1.0)
    debt_weight: float = Field(default=0.05, ge=0.0, le=1.0)
    cost_of_equity: float = Field(default=0.115, gt=0.01, le=0.35)
    pretax_cost_of_debt: float = Field(default=0.075, ge=0.0, le=0.30)
    wacc_override: Optional[float] = None
    terminal_growth_rate: float = Field(default=0.045, ge=-0.02, lt=0.15)

    # Equity Bridge Inputs (All Monetary Values in INR Crore)
    total_debt_cr: float = Field(default=0.0, ge=0.0)
    cash_and_investments_cr: float = Field(default=0.0, ge=0.0)
    other_equity_adjustments_cr: float = Field(default=0.0)
    diluted_shares_crore: float = Field(gt=0.0)

    # Dated Reference Market Price
    reference_price_inr: float = Field(gt=0.0)
    reference_price_date: str
    reference_price_source: str = "Dated Reference Closing Price"
    assumption_sources_note: str = "Historical base from audited Annual Report; forecast parameters user-editable."

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.validate_dcf_constraints()

    def clone_with(self, **updates: Any) -> "DCFAssumptions":
        raw = self.model_dump() if hasattr(self, "model_dump") else self.dict()
        raw.update(updates)
        return DCFAssumptions(**raw)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump() if hasattr(self, "model_dump") else self.dict()

    def validate_dcf_constraints(self) -> "DCFAssumptions":
        if len(self.revenue_growth_rates) != self.forecast_years:
            raise ValueError(f"revenue_growth_rates length ({len(self.revenue_growth_rates)}) must equal forecast_years ({self.forecast_years}).")
        if len(self.ebit_margins) != self.forecast_years:
            raise ValueError(f"ebit_margins length ({len(self.ebit_margins)}) must equal forecast_years ({self.forecast_years}).")
        if abs((self.equity_weight + self.debt_weight) - 1.0) > 1e-4:
            raise ValueError("equity_weight + debt_weight must equal 1.0 (100%).")
        computed_wacc = self.compute_wacc()
        if computed_wacc <= 0:
            raise ValueError("WACC must be strictly positive.")
        if self.terminal_growth_rate >= computed_wacc:
            raise ValueError(
                f"Invalid Terminal Growth Rate ({self.terminal_growth_rate*100:.2f}%): "
                f"Terminal growth must be strictly less than WACC ({computed_wacc*100:.2f}%)."
            )
        return self

    def compute_wacc(self) -> float:
        if self.wacc_override is not None:
            return float(self.wacc_override)
        after_tax_debt = self.pretax_cost_of_debt * (1.0 - self.effective_tax_rate)
        return float(self.equity_weight * self.cost_of_equity + self.debt_weight * after_tax_debt)


class DCFYearProjection(BaseModel):
    year_index: int
    fiscal_year_label: str
    revenue_cr: float
    revenue_growth: float
    ebit_cr: float
    ebit_margin: float
    nopat_cr: float
    da_cr: float
    capex_cr: float
    nwc_change_cr: float
    fcff_cr: float
    discount_factor: float
    pv_fcff_cr: float


class DCFOutput(BaseModel):
    company_id: str
    wacc: float
    terminal_growth_rate: float
    projections: List[DCFYearProjection]
    sum_pv_fcff_cr: float
    next_period_terminal_fcff_cr: float
    undiscounted_terminal_value_cr: float
    pv_terminal_value_cr: float
    enterprise_value_cr: float
    net_debt_cr: float
    other_equity_adjustments_cr: float
    equity_value_cr: float
    diluted_shares_crore: float
    fair_value_per_share_inr: float
    reference_price_inr: float
    reference_price_date: str
    reference_price_source: str
    upside_downside_pct: float
    margin_of_safety_pct: float
    terminal_value_pct_of_ev: float
    warnings: List[str]


def calculate_cost_of_equity_capm(risk_free_rate: float, beta: float, equity_risk_premium: float) -> float:
    """Calculate Cost of Equity via CAPM: Ke = Rf + Beta * ERP."""
    return float(risk_free_rate + beta * equity_risk_premium)


def run_dcf_valuation(assumptions: DCFAssumptions) -> DCFOutput:
    """
    Execute deterministic FCFF DCF valuation.
    Formulas:
      - NOPAT = EBIT * (1 - Tax Rate)
      - FCFF  = NOPAT + D&A - Capex - Change in NWC
      - Terminal Value (at Year N) = FCFF_N * (1 + g) / (WACC - g)
      - Enterprise Value = Sum(PV of FCFF) + PV(Terminal Value)
      - Net Debt = Total Debt - Cash & Short-Term Investments
      - Equity Value = Enterprise Value - Net Debt + Other Equity Adjustments
      - Per-Share Value (INR) = Equity Value (INR Crore) / Diluted Shares (Crore)
    """
    wacc = assumptions.compute_wacc()
    g = assumptions.terminal_growth_rate

    base_yr_num = int(assumptions.base_fiscal_year.replace("FY", "")) if assumptions.base_fiscal_year.startswith("FY") else 2025
    projections: List[DCFYearProjection] = []
    prev_rev = assumptions.base_revenue_cr
    sum_pv_fcff = 0.0

    for idx in range(assumptions.forecast_years):
        t = idx + 1
        fy_label = f"FY{base_yr_num + t}E"
        rev_g = assumptions.revenue_growth_rates[idx]
        ebit_m = assumptions.ebit_margins[idx]

        rev = prev_rev * (1.0 + rev_g)
        rev_delta = rev - prev_rev
        ebit = rev * ebit_m
        nopat = ebit * (1.0 - assumptions.effective_tax_rate)
        da = rev * assumptions.da_pct_revenue
        capex = rev * assumptions.capex_pct_revenue
        nwc_chg = rev_delta * assumptions.nwc_change_pct_rev_change
        fcff = nopat + da - capex - nwc_chg

        dfactor = (1.0 + wacc) ** t
        pv_fcff = fcff / dfactor
        sum_pv_fcff += pv_fcff

        projections.append(
            DCFYearProjection(
                year_index=t,
                fiscal_year_label=fy_label,
                revenue_cr=round(rev, 2),
                revenue_growth=round(rev_g, 4),
                ebit_cr=round(ebit, 2),
                ebit_margin=round(ebit_m, 4),
                nopat_cr=round(nopat, 2),
                da_cr=round(da, 2),
                capex_cr=round(capex, 2),
                nwc_change_cr=round(nwc_chg, 2),
                fcff_cr=round(fcff, 2),
                discount_factor=round(dfactor, 6),
                pv_fcff_cr=round(pv_fcff, 2),
            )
        )
        prev_rev = rev

    final_fcff = projections[-1].fcff_cr
    next_fcff = final_fcff * (1.0 + g)
    terminal_val = next_fcff / (wacc - g)
    pv_terminal_val = terminal_val / ((1.0 + wacc) ** assumptions.forecast_years)

    enterprise_val = sum_pv_fcff + pv_terminal_val
    net_debt = assumptions.total_debt_cr - assumptions.cash_and_investments_cr
    equity_val = enterprise_val - net_debt + assumptions.other_equity_adjustments_cr
    fair_value_per_share = equity_val / assumptions.diluted_shares_crore

    upside_pct = (fair_value_per_share / assumptions.reference_price_inr) - 1.0
    mos_pct = 1.0 - (assumptions.reference_price_inr / fair_value_per_share) if fair_value_per_share > 0 else -1.0
    tv_share = (pv_terminal_val / enterprise_val) if enterprise_val > 0 else 0.0

    warnings: List[str] = []
    if tv_share > 0.75:
        warnings.append(
            f"High Terminal Value Dependency: {tv_share*100:.1f}% of Enterprise Value comes from the Terminal Value."
        )
    if final_fcff <= 0:
        warnings.append("Terminal year FCFF is non-positive; terminal value perpetuity assumptions may not be meaningful.")
    if (wacc - g) < 0.025:
        warnings.append("Narrow WACC - Terminal Growth spread (<250 bps) amplifies valuation sensitivity.")

    return DCFOutput(
        company_id=assumptions.company_id,
        wacc=round(wacc, 6),
        terminal_growth_rate=round(g, 6),
        projections=projections,
        sum_pv_fcff_cr=round(sum_pv_fcff, 2),
        next_period_terminal_fcff_cr=round(next_fcff, 2),
        undiscounted_terminal_value_cr=round(terminal_val, 2),
        pv_terminal_value_cr=round(pv_terminal_val, 2),
        enterprise_value_cr=round(enterprise_val, 2),
        net_debt_cr=round(net_debt, 2),
        other_equity_adjustments_cr=round(assumptions.other_equity_adjustments_cr, 2),
        equity_value_cr=round(equity_val, 2),
        diluted_shares_crore=assumptions.diluted_shares_crore,
        fair_value_per_share_inr=round(fair_value_per_share, 2),
        reference_price_inr=assumptions.reference_price_inr,
        reference_price_date=assumptions.reference_price_date,
        reference_price_source=assumptions.reference_price_source,
        upside_downside_pct=round(upside_pct, 4),
        margin_of_safety_pct=round(mos_pct, 4),
        terminal_value_pct_of_ev=round(tv_share, 4),
        warnings=warnings,
    )


def solve_reverse_dcf_implied_growth(
    base_assumptions: DCFAssumptions,
    target_price_inr: Optional[float] = None,
    low_bound: float = -0.15,
    high_bound: float = 0.45,
) -> Optional[float]:
    """
    Use binary search to find the uniform annual revenue growth rate over the forecast horizon
    required for the DCF Fair Value per Share to equal the Dated Reference Price.
    """
    target = target_price_inr if target_price_inr is not None else base_assumptions.reference_price_inr
    if target <= 0:
        return None

    lo, hi = low_bound, high_bound
    for _ in range(45):
        mid = (lo + hi) / 2.0
        test_assump = base_assumptions.clone_with(revenue_growth_rates=[mid] * base_assumptions.forecast_years)
        out = run_dcf_valuation(test_assump)
        if abs(out.fair_value_per_share_inr - target) < 0.05:
            return round(mid, 4)
        if out.fair_value_per_share_inr < target:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2.0, 4)
