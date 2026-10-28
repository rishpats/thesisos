# ThesisOS System Architecture (`docs/architecture.md`)

ThesisOS is organized into five decoupled layers:
1. **Data & Provenance Layer (`src/thesisos/data/`)**: Pydantic schemas (`FinancialObservation`, `SourceRecord`, `DataQualityReport`), unit normalizer (`INR_CRORE`), and 10-point data quality auditor.
2. **Deterministic Finance & Valuation Core (`src/thesisos/finance/`)**: Pure Python functions for financial ratios, working capital days, 9 forensic accounting rules, FCFF DCF, WACC/CAPM, 2D sensitivity grids, Bull/Base/Bear scenarios, Reverse DCF binary solver, and peer comparables.
3. **Filings & Retrieval Layer (`src/thesisos/filings/`)**: In-memory PDF parser (`pypdf` + `pdfplumber`), scanned-page detector, prompt-injection redactor, page-preserving chunker, `scikit-learn` TF-IDF retriever, and regex citation auditor.
4. **6-Node Research Workflow & Validator (`src/thesisos/agents/` & `src/thesisos/reports/`)**: Generates the 24-section `ResearchMemoDossier` deterministically ($0 mode) and validates any optional BYOK LLM output against the calculation engine.
5. **Institutional Dark UI (`app.py`, `pages/`, `src/thesisos/ui/`)**: 5-page Streamlit workstation styled in `#171A1E` / `#22272D` with interactive Plotly charts and HTML/CSV exports.
