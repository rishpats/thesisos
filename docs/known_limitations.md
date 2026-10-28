# ThesisOS Known Limitations (`docs/known_limitations.md`)

1. **Sector Coverage (Non-Financials Only)**: Standard FCFF DCF, EBITDA, Net Debt, and Working Capital ratios apply to industrial, IT, and consumer companies. Banks, NBFCs, and insurers are intentionally excluded from standard DCF/leverage modules.
2. **Static Dated Reference Market Prices**: Market prices are dated reference inputs, not real-time tickers.
3. **Scanned PDFs & OCR**: `pypdf` and `pdfplumber` extract digital PDF text layers. Pages with <30 characters (such as scanned image PDFs) are flagged with `SCANNED_PDF_OCR_UNAVAILABLE` rather than guessed.
4. **Free Cloud Hosting Constraints**: Streamlit Community Cloud enforces a 2.7 GB RAM limit and hibernates containers after ~12 hours of inactivity (waking in ~15–30 seconds).
5. **Optional BYOK LLM Quotas**: Visitors using optional live AI synthesis must supply their own free-tier Groq or Gemini key, which is subject to provider rate limits (HTTP 429). The core platform and 24-section deterministic research memo require zero API keys.
