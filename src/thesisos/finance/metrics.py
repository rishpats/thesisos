"""Deterministic financial statement ratios, growth rates, CAGR, and valuation multiples."""
from typing import Dict, Optional
import numpy as np
import pandas as pd


def safe_divide(numerator: Optional[float], denominator: Optional[float], allow_negative_denom: bool = False) -> Optional[float]:
    """Safely divide two numbers, returning None if inputs are missing or denominator is zero/invalid."""
    if numerator is None or denominator is None:
        return None
    if pd.isna(numerator) or pd.isna(denominator):
        return None
    if denominator == 0.0:
        return None
    if not allow_negative_denom and denominator < 0.0:
        return None
    return float(numerator) / float(denominator)


def calculate_yoy_growth(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """Calculate YoY growth: (Current / Previous) - 1. Requires positive previous base."""
    ratio = safe_divide(current, previous, allow_negative_denom=False)
    if ratio is None:
        return None
    return ratio - 1.0


def calculate_cagr(ending_value: Optional[float], beginning_value: Optional[float], num_periods: int) -> Optional[float]:
    """Calculate Compound Annual Growth Rate: (Ending / Beginning) ** (1 / num_periods) - 1."""
    if num_periods <= 0 or ending_value is None or beginning_value is None:
        return None
    if pd.isna(ending_value) or pd.isna(beginning_value) or beginning_value <= 0 or ending_value <= 0:
        return None
    return float((ending_value / beginning_value) ** (1.0 / num_periods) - 1.0)


def compute_financial_metrics_table(wide_df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a wide fiscal_year-indexed DataFrame of canonical financial facts (in INR_CRORE),
    compute all growth, profitability, return, leverage, liquidity, and cash-flow quality metrics.
    """
    if wide_df.empty:
        return pd.DataFrame()

    df = wide_df.sort_values("fiscal_year").reset_index(drop=True).copy()

    # Ensure expected columns exist (fill missing columns with NaN so formulas degrade gracefully)
    expected_cols = [
        "revenue", "cogs", "ebitda", "da", "ebit", "finance_costs", "pbt", "tax", "pat", "eps",
        "cash_and_investments", "trade_receivables", "inventory", "current_assets", "total_assets",
        "trade_payables", "current_liabilities", "total_debt", "total_equity", "diluted_shares",
        "cfo", "capex", "dividends_paid",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = np.nan

    # 1. Free Cash Flow (FCF = CFO - Capex)
    df["fcf"] = df["cfo"] - df["capex"]

    # 2. YoY Growth Rates
    for metric in ["revenue", "ebitda", "ebit", "pat", "eps", "fcf"]:
        growth_vals = [None]
        for i in range(1, len(df)):
            growth_vals.append(calculate_yoy_growth(df.loc[i, metric], df.loc[i - 1, metric]))
        df[f"{metric}_growth"] = growth_vals

    # 3. Profitability Margins
    df["gross_profit"] = df["revenue"] - df["cogs"]
    df["gross_margin"] = [safe_divide(gp, rev) for gp, rev in zip(df["gross_profit"], df["revenue"])]
    df["ebitda_margin"] = [safe_divide(eb, rev) for eb, rev in zip(df["ebitda"], df["revenue"])]
    df["ebit_margin"] = [safe_divide(ebit, rev) for ebit, rev in zip(df["ebit"], df["revenue"])]
    df["pat_margin"] = [safe_divide(pat, rev) for pat, rev in zip(df["pat"], df["revenue"])]

    # Distinguish Company-Reported EBITDA vs Internally Computed (EBIT + D&A)
    df["computed_ebitda"] = df["ebit"] + df["da"]
    df["ebitda_discrepancy"] = df["ebitda"] - df["computed_ebitda"]

    # 4. Returns (ROE and ROCE using Average Equity and Average Capital Employed where prior year exists)
    roe_list, roce_list = [], []
    for i in range(len(df)):
        eq_curr = df.loc[i, "total_equity"]
        eq_prev = df.loc[i - 1, "total_equity"] if i > 0 and pd.notna(df.loc[i - 1, "total_equity"]) else eq_curr
        avg_eq = (eq_curr + eq_prev) / 2.0 if pd.notna(eq_curr) and pd.notna(eq_prev) else None
        roe_list.append(safe_divide(df.loc[i, "pat"], avg_eq))

        ce_curr = df.loc[i, "total_assets"] - df.loc[i, "current_liabilities"]
        if i > 0 and pd.notna(df.loc[i - 1, "total_assets"]) and pd.notna(df.loc[i - 1, "current_liabilities"]):
            ce_prev = df.loc[i - 1, "total_assets"] - df.loc[i - 1, "current_liabilities"]
        else:
            ce_prev = ce_curr
        avg_ce = (ce_curr + ce_prev) / 2.0 if pd.notna(ce_curr) and pd.notna(ce_prev) else None
        roce_list.append(safe_divide(df.loc[i, "ebit"], avg_ce))

    df["roe"] = roe_list
    df["roce"] = roce_list

    # 5. Leverage & Liquidity
    df["net_debt"] = df["total_debt"] - df["cash_and_investments"]
    df["debt_to_equity"] = [safe_divide(d, eq) for d, eq in zip(df["total_debt"], df["total_equity"])]
    df["net_debt_to_ebitda"] = [safe_divide(nd, eb) for nd, eb in zip(df["net_debt"], df["ebitda"])]
    df["interest_coverage"] = [safe_divide(ebit, fc) for ebit, fc in zip(df["ebit"], df["finance_costs"])]
    df["current_ratio"] = [safe_divide(ca, cl) for ca, cl in zip(df["current_assets"], df["current_liabilities"])]
    df["quick_ratio"] = [
        safe_divide(ca - (inv if pd.notna(inv) else 0.0), cl)
        for ca, inv, cl in zip(df["current_assets"], df["inventory"], df["current_liabilities"])
    ]

    # 6. Cash Flow Quality
    df["cfo_to_pat"] = [safe_divide(cfo, pat) for cfo, pat in zip(df["cfo"], df["pat"])]
    df["capex_to_revenue"] = [safe_divide(cx, rev) for cx, rev in zip(df["capex"], df["revenue"])]

    return df


def compute_summary_cagrs(metrics_df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Compute multi-year CAGRs across the available span of fiscal years."""
    if len(metrics_df) < 2:
        return {"revenue_cagr": None, "ebitda_cagr": None, "pat_cagr": None, "fcf_cagr": None, "years_span": 0}
    n_years = len(metrics_df) - 1
    first = metrics_df.iloc[0]
    last = metrics_df.iloc[-1]
    return {
        "years_span": n_years,
        "revenue_cagr": calculate_cagr(last.get("revenue"), first.get("revenue"), n_years),
        "ebitda_cagr": calculate_cagr(last.get("ebitda"), first.get("ebitda"), n_years),
        "pat_cagr": calculate_cagr(last.get("pat"), first.get("pat"), n_years),
        "fcf_cagr": calculate_cagr(last.get("fcf"), first.get("fcf"), n_years),
    }


def compute_valuation_multiples(latest_row: pd.Series, reference_price_inr: float) -> Dict[str, Optional[float]]:
    """Compute Market Cap, Enterprise Value, P/E, P/B, EV/EBITDA, EV/Sales, and FCF Yield."""
    shares_cr = latest_row.get("diluted_shares")
    if shares_cr is None or pd.isna(shares_cr) or shares_cr <= 0 or reference_price_inr <= 0:
        return {}
    market_cap_cr = float(shares_cr) * float(reference_price_inr)
    net_debt_cr = float(latest_row.get("net_debt", 0.0)) if pd.notna(latest_row.get("net_debt")) else 0.0
    ev_cr = market_cap_cr + net_debt_cr

    return {
        "market_cap_cr": round(market_cap_cr, 2),
        "enterprise_value_cr": round(ev_cr, 2),
        "pe_ratio": safe_divide(market_cap_cr, latest_row.get("pat")),
        "pb_ratio": safe_divide(market_cap_cr, latest_row.get("total_equity")),
        "ev_to_ebitda": safe_divide(ev_cr, latest_row.get("ebitda")),
        "ev_to_sales": safe_divide(ev_cr, latest_row.get("revenue")),
        "fcf_yield": safe_divide(latest_row.get("fcf"), market_cap_cr),
    }


