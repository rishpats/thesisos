"""ThesisOS Main Entrypoint — Zero-Cost Institutional Equity Research Platform."""
import sys
from pathlib import Path
import streamlit as st

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.ui.components import render_footer, render_kpi_card, render_sidebar_and_context

st.set_page_config(
    page_title="ThesisOS | Institutional Equity Research Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

company_meta, selected_scope = render_sidebar_and_context()

st.markdown("## THESISOS: INSTITUTIONAL EQUITY RESEARCH WORKSTATION")
st.markdown(
    "**An analyst-grade research system where calculations are deterministic, sources are traceable by page number, "
    "AI interprets evidence optionally, and unsupported claims are explicitly identified.**"
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Core Engine Cost", "$0 / ₹0", "100% Free & Offline Capable", status="positive")
with c2:
    render_kpi_card("API Key Requirement", "NONE REQUIRED", "Full Demo Works Out-of-the-Box", status="positive")
with c3:
    render_kpi_card("Calculation Mode", "DETERMINISTIC", "Zero LLM Arithmetic Hallucinations", status="positive")
with c4:
    render_kpi_card("Data Provenance", "PAGE-LEVEL", "Audited Ind-AS Annual Reports", status="positive")

st.markdown("### Workstation Modules (Select from Left Navigation Sidebar)")
st.markdown(
    """
1. **1_Company_Overview**: Executive KPI snapshot, multi-year growth CAGRs, active forensic accounting alerts, data-quality audit, and source registry.
2. **2_Financial_Analysis**: Complete 5-year Income Statement, Balance Sheet, Cash Flow Statement, interactive Plotly charts, working-capital cycle diagnostics, and CSV exports.
3. **3_Valuation_Lab**: Interactive FCFF DCF valuation model, WACC & CAPM calculator, 2D WACC/Terminal Growth sensitivity heatmap, Bull/Base/Bear scenarios, Reverse DCF solver, and peer comparables.
4. **4_Filings_Intelligence**: Annual Report PDF uploader (page-aware `pypdf` + `pdfplumber`), prompt-injection sanitizer, and deterministic `scikit-learn` TF-IDF passage retrieval with page citations.
5. **5_Research_Memo**: 24-section Institutional Research Dossier generator (Rule-Based Deterministic Mode + Pre-Verified Flagship Dossier + Optional Session-Only BYOK AI Synthesis with Independent Claim Validator) and Print-Ready HTML/PDF export.
"""
)

render_footer()
