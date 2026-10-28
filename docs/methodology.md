# ThesisOS Financial & Valuation Methodology (`docs/methodology.md`)

## 1. Unit Normalization & Scope Isolation
- **Canonical Monetary Unit**: `INR_CRORE` ($1\text{ Crore} = 10,000,000\text{ INR} = 100\text{ Lakh} = 10\text{ Million}$).
- **Scope Isolation**: `pivot_canonical_statements()` raises a hard `ValueError` if `CONSOLIDATED` and `STANDALONE` observations are mixed in the same series.

## 2. Financial Ratio Conventions
- **YoY Growth**: $(\text{Metric}_t / \text{Metric}_{t-1}) - 1$ (disabled if $\text{Metric}_{t-1} \le 0$).
- **CAGR**: $(\text{Ending Value} / \text{Beginning Value})^{(1/n)} - 1$ (disabled if Beginning or Ending Value $\le 0$).
- **EBITDA Margin**: $\text{EBITDA} / \text{Revenue}$ (distinguishes reported EBITDA from $\text{EBIT} + \text{D\&A}$).
- **ROE**: $\text{PAT}_t / \text{Average Total Equity}_{t-1, t}$.
- **ROCE**: $\text{EBIT}_t / \text{Average Capital Employed}_{t-1, t}$, where $\text{Capital Employed} = \text{Total Assets} - \text{Current Liabilities}$.
- **Working Capital Cycle**:
  - $\text{Receivable Days (DSO)} = (\text{Average Trade Receivables} / \text{Revenue}) \times 365$
  - $\text{Inventory Days (DIO)} = (\text{Average Inventory} / \text{COGS}) \times 365$
  - $\text{Payable Days (DPO)} = (\text{Average Trade Payables} / \text{COGS}) \times 365$
  - $\text{Cash Conversion Cycle (CCC)} = \text{DSO} + \text{DIO} - \text{DPO}$
- **Free Cash Flow (FCF)**: $\text{Operating Cash Flow (CFO)} - \text{Capital Expenditure (Capex)}$.

## 3. Deterministic FCFF DCF Valuation
- $\text{NOPAT}_t = \text{EBIT}_t \times (1 - \text{Effective Tax Rate})$
- $\text{FCFF}_t = \text{NOPAT}_t + \text{D\&A}_t - \text{Capex}_t - \Delta\text{NWC}_t$
- $\text{WACC} = \left(\frac{E}{V} \times K_e\right) + \left(\frac{D}{V} \times K_d \times (1 - T)\right)$
- $\text{Terminal Value}_N = \frac{\text{FCFF}_N \times (1 + g)}{\text{WACC} - g}$ (strictly enforces $g < \text{WACC}$ and $\text{WACC} > 0$).
- $\text{Enterprise Value} = \sum_{t=1}^{N} \frac{\text{FCFF}_t}{(1+\text{WACC})^t} + \frac{\text{Terminal Value}_N}{(1+\text{WACC})^N}$
- $\text{Equity Value (₹ Cr)} = \text{Enterprise Value} - (\text{Total Debt} - \text{Cash \& Investments}) + \text{Other Equity Adjustments}$
- $\text{Implied Fair Value per Share (₹)} = \frac{\text{Equity Value (₹ Cr)}}{\text{Diluted Shares (Cr)}}$
