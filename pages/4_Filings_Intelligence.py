"""Page 4: Annual Report PDF Uploader, Page-Aware Extraction & TF-IDF Passage Search."""
import sys
from pathlib import Path
import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.data.loaders import load_sources
from thesisos.data.sources import SourceRecord
from thesisos.filings.chunker import chunk_parsed_document
from thesisos.filings.pdf_parser import parse_uploaded_pdf_bytes
from thesisos.filings.retrieval import retrieve_relevant_passages
from thesisos.ui.components import render_footer, render_sidebar_and_context

st.set_page_config(page_title="Filings Intelligence | ThesisOS", page_icon="📄", layout="wide")
company_meta, scope = render_sidebar_and_context()

st.markdown("## 4. Filings Intelligence & Traceable Evidence Retrieval")
st.caption(
    "Search verified Annual Report disclosures using deterministic TF-IDF retrieval, or upload a PDF filing "
    "(processed temporarily in memory; untrusted instructions are sanitized automatically)."
)

sources_df = load_sources(company_meta["company_id"])
corpus = [SourceRecord(**row.to_dict()) for _, row in sources_df.iterrows()]

uploaded_pdf = st.file_uploader(
    "Optional: Upload Additional Annual Report or Exchange Filing PDF (Max 25 MB, Temporary Session Memory)",
    type=["pdf"],
)
if uploaded_pdf is not None:
    try:
        parsed = parse_uploaded_pdf_bytes(
            uploaded_pdf.read(),
            filename=uploaded_pdf.name,
            company_id=company_meta["company_id"],
        )
        st.success(
            f"Parsed `{parsed.document_title}` (ID: `{parsed.document_id}`): {parsed.pages_parsed}/{parsed.total_pages} pages extracted "
            f"| Status: `{parsed.extraction_status}`"
        )
        if parsed.scanned_or_empty_pages:
            st.warning(
                f"Pages {parsed.scanned_or_empty_pages[:15]} contained <30 characters (likely scanned images). "
                "OCR is not enabled in the zero-cost cloud runtime; those pages are skipped rather than fabricated."
            )
        if parsed.injection_warnings:
            for iw in parsed.injection_warnings:
                st.warning(f"Security Sanitizer: {iw}")
        extra_chunks = chunk_parsed_document(parsed)
        corpus.extend(extra_chunks)
    except Exception as exc:
        st.error(f"PDF Upload Validation Error: {exc}")

preset_queries = [
    "What risks and macroeconomic headwinds does management disclose?",
    "What did the company say about revenue growth drivers and operating margins?",
    "What changed in trade receivables and working capital?",
    "What contingent liabilities and disputed tax claims were disclosed?",
    "What auditor qualifications or key audit matters are mentioned?",
    "What does the report say about operating cash flow and capital expenditure?",
]
selected_preset = st.selectbox("Select an Analyst Due-Diligence Question (or type a custom query below):", options=preset_queries)
custom_query = st.text_input("Custom Filing Search Query:", value=selected_preset)

hits = retrieve_relevant_passages(custom_query, corpus, top_k=5)
st.markdown(f"### Retrieved Evidence Passages ({len(hits)} Matches)")

if not hits:
    st.info("No matching passages found for this query. Try broader financial terms.")
else:
    for hit in hits:
        s = hit.source
        st.markdown(
            f"""
            <div class="thesis-card">
                <div style="display:flex; justify-content:space-between;">
                    <span><b>Rank #{hit.rank}</b> &bull; <code>{s.source_id}</code> &bull; <b>{s.document_title}</b> ({s.reporting_period})</span>
                    <span class="badge-verified">Page {s.page} | Score: {hit.score:.3f} | {s.verification_status}</span>
                </div>
                <p style="margin-top:10px; color:#F0ECE2;">"{s.extracted_passage}"</p>
                <div style="font-size:0.78rem; color:#A6ADB3;">
                    Provenance: <a href="{s.source_url}" target="_blank" style="color:#85AF95;">{s.source_url}</a>
                    | Extraction Method: <code>{s.extraction_method}</code> | Verified: {s.retrieval_date}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

render_footer()
