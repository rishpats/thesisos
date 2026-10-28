# ThesisOS: Zero-Cost Institutional Equity Research Intelligence Platform (India NSE/BSE)

**An analyst-grade equity research workstation where financial calculations are 100% deterministic, every observation is traceable to an official Annual Report page number, optional AI synthesis is independently validated, and mandatory operating cost is $0.**

---

## 1. Key Capabilities
- **Canonical Sourced Financial Database (`data/demo/`)**: Audited 5-year Ind-AS Consolidated financial statements for flagship Indian listed non-financial companies (`TCS`, `INFY`) with row-level Annual Report page numbers.
- **Deterministic Financial & Forensic Engine (`src/thesisos/finance/`)**: Pure Python calculations for Revenue/EBITDA/PAT/FCF growth, multi-year CAGRs, ROE, ROCE, Working Capital Days (`DSO`, `DIO`, `DPO`, `CCC`), `CFO/PAT` earnings quality, and 9 cautious rule-based forensic accounting alerts.
- **Valuation Laboratory (`pages/3_Valuation_Lab.py`)**: Interactive 5-year FCFF DCF engine, CAPM/WACC builder, `g < WACC` mathematical guardrails, Enterprise-to-Equity bridge (`INR_CRORE` to `INR_PER_SHARE`), 2D WACC vs. Terminal Growth sensitivity heatmap, Bull/Base/Bear scenarios, Reverse DCF implied-growth solver, and Peer Comparable multiples.
- **Filings Intelligence (`pages/4_Filings_Intelligence.py`)**: Page-aware PDF parser (`pypdf` + `pdfplumber`), scanned-page detector, untrusted prompt-injection sanitizer, and deterministic `scikit-learn` TF-IDF passage retrieval.
- **24-Section Research Dossier & Independent Validator (`pages/5_Research_Memo.py`)**: Generates a complete 24-section institutional research memo in **100% No-API Mode ($0)** alongside a **Pre-Verified Flagship AI Dossier**, plus optional session-scoped Bring-Your-Own-Key (BYOK) Groq/Gemini synthesis guarded by an independent numeric and citation validator.

---

## 2. Quickstart (Local Windows PowerShell)

    git clone https://github.com/<your-username>/thesisos.git
    cd thesisos
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements-dev.txt
    python -m pytest -q
    streamlit run app.py

---

## 3. Known Limitations & Regulatory Disclosure
- **Non-Financial Corporate Scope**: Designed for industrial, technology, and consumer non-financial companies; bank/NBFC balance sheets require specialized DDM/ROE excess-return models (`docs/known_limitations.md`).
- **Dated Reference Market Prices**: To respect the NSE Data Sharing & Usage Policy at $0 cost, reference stock prices are explicitly dated static/user-editable inputs, never live exchange feeds.
- **Free Cloud Hibernation**: Hosted on Streamlit Community Cloud's free tier (2.7 GB RAM limit; container sleeps after ~12 hours of inactivity and wakes in ~15 seconds on click).
- **Not Investment Advice**: Built strictly for educational, academic, and portfolio demonstration purposes.
