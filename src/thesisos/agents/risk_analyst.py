"""Node 3: Disclosure & Filing Evidence Analyst."""
from typing import List
from thesisos.agents.state import WorkflowState
from thesisos.data.sources import SourceRecord
from thesisos.filings.retrieval import retrieve_relevant_passages


def run_disclosure_analyst_node(state: WorkflowState, corpus: List[SourceRecord]) -> WorkflowState:
    """Retrieve relevant passages covering growth drivers, risks, cash flow, and contingent liabilities."""
    queries = [
        "revenue growth drivers operating margin",
        "key risks macroeconomic headwinds client spending",
        "operating cash flow capex trade receivables working capital",
        "contingent liabilities disputed tax claims auditor report",
    ]
    seen_ids = set()
    selected: List[SourceRecord] = []
    for q in queries:
        hits = retrieve_relevant_passages(q, corpus, top_k=3)
        for h in hits:
            if h.source.source_id not in seen_ids:
                seen_ids.add(h.source.source_id)
                selected.append(h.source)
    state.retrieved_sources = selected if selected else corpus
    return state
