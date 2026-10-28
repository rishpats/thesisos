"""Working capital efficiency and Cash Conversion Cycle (CCC) diagnostics."""
import pandas as pd
from thesisos.finance.metrics import safe_divide


def append_working_capital_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Append Receivable Days (DSO), Inventory Days (DIO), Payable Days (DPO),
    Cash Conversion Cycle (CCC), and Working Capital / Revenue ratios.
    Formulas:
      - Receivable Days = (Average Trade Receivables / Revenue) * 365
      - Inventory Days  = (Average Inventory / COGS) * 365
      - Payable Days    = (Average Trade Payables / COGS) * 365
      - CCC             = Receivable Days + Inventory Days - Payable Days
    """
    if df.empty:
        return df

    out = df.copy()
    rec_days, inv_days, pay_days, ccc_list = [], [], [], []
    rec_to_rev, inv_to_rev, nwc_to_rev = [], [], []

    for i in range(len(out)):
        rev = out.loc[i, "revenue"]
        cogs = out.loc[i, "cogs"]

        rec_curr = out.loc[i, "trade_receivables"]
        rec_prev = out.loc[i - 1, "trade_receivables"] if i > 0 and pd.notna(out.loc[i - 1, "trade_receivables"]) else rec_curr
        avg_rec = (rec_curr + rec_prev) / 2.0 if pd.notna(rec_curr) and pd.notna(rec_prev) else None

        inv_curr = out.loc[i, "inventory"]
        inv_prev = out.loc[i - 1, "inventory"] if i > 0 and pd.notna(out.loc[i - 1, "inventory"]) else inv_curr
        avg_inv = (inv_curr + inv_prev) / 2.0 if pd.notna(inv_curr) and pd.notna(inv_prev) else None

        pay_curr = out.loc[i, "trade_payables"]
        pay_prev = out.loc[i - 1, "trade_payables"] if i > 0 and pd.notna(out.loc[i - 1, "trade_payables"]) else pay_curr
        avg_pay = (pay_curr + pay_prev) / 2.0 if pd.notna(pay_curr) and pd.notna(pay_prev) else None

        r_d = safe_divide(avg_rec, rev)
        r_d = r_d * 365.0 if r_d is not None else None

        i_d = safe_divide(avg_inv, cogs)
        i_d = i_d * 365.0 if i_d is not None else None

        p_d = safe_divide(avg_pay, cogs)
        p_d = p_d * 365.0 if p_d is not None else None

        rec_days.append(r_d)
        inv_days.append(i_d)
        pay_days.append(p_d)
        if r_d is not None and i_d is not None and p_d is not None:
            ccc_list.append(r_d + i_d - p_d)
        else:
            ccc_list.append(None)

        rec_to_rev.append(safe_divide(rec_curr, rev))
        inv_to_rev.append(safe_divide(inv_curr, rev))
        nwc = (out.loc[i, "current_assets"] - out.loc[i, "cash_and_investments"]) - out.loc[i, "current_liabilities"]
        nwc_to_rev.append(safe_divide(nwc, rev, allow_negative_denom=False))

    out["receivable_days"] = rec_days
    out["inventory_days"] = inv_days
    out["payable_days"] = pay_days
    out["cash_conversion_cycle"] = ccc_list
    out["receivables_to_revenue"] = rec_to_rev
    out["inventory_to_revenue"] = inv_to_rev
    out["nwc_to_revenue"] = nwc_to_rev
    return out
