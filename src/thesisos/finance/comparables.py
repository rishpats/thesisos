"""Comparable company valuation multiples and peer median/quartile benchmarking."""
import pandas as pd
from thesisos.data.loaders import load_companies, load_financial_facts
from thesisos.data.normalize import pivot_canonical_statements
from thesisos.finance.metrics import compute_financial_metrics_table, compute_valuation_multiples


def build_peer_comparables_table(sector_filter: str = "") -> pd.DataFrame:
    """Build a comparable valuation table across all verified companies in companies.csv."""
    companies_df = load_companies()
    if sector_filter:
        companies_df = companies_df[companies_df["sector"].str.lower() == sector_filter.lower()]

    rows = []
    for _, comp in companies_df.iterrows():
        cid = comp["company_id"]
        facts = load_financial_facts(cid, scope=comp["default_scope"])
        if facts.empty:
            continue
        wide = pivot_canonical_statements(facts, expected_scope=comp["default_scope"])
        metrics = compute_financial_metrics_table(wide)
        latest = metrics.iloc[-1]
        mults = compute_valuation_multiples(latest, float(comp["reference_price_inr"]))
        rows.append(
            {
                "Symbol": comp["symbol"],
                "Company": comp["company_name"],
                "Sector": comp["sector"],
                "Latest Period": latest["fiscal_year"],
                "Ref Price (₹)": comp["reference_price_inr"],
                "Price Date": comp["reference_price_date"],
                "Market Cap (₹ Cr)": mults.get("market_cap_cr"),
                "Enterprise Value (₹ Cr)": mults.get("enterprise_value_cr"),
                "P/E (x)": round(mults["pe_ratio"], 2) if mults.get("pe_ratio") else None,
                "P/B (x)": round(mults["pb_ratio"], 2) if mults.get("pb_ratio") else None,
                "EV/EBITDA (x)": round(mults["ev_to_ebitda"], 2) if mults.get("ev_to_ebitda") else None,
                "EV/Sales (x)": round(mults["ev_to_sales"], 2) if mults.get("ev_to_sales") else None,
                "FCF Yield (%)": round(mults["fcf_yield"] * 100.0, 2) if mults.get("fcf_yield") else None,
                "ROE (%)": round(latest["roe"] * 100.0, 2) if pd.notna(latest.get("roe")) else None,
                "EBITDA Margin (%)": round(latest["ebitda_margin"] * 100.0, 2) if pd.notna(latest.get("ebitda_margin")) else None,
            }
        )
    return pd.DataFrame(rows)
