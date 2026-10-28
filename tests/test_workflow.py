"""Unit tests for the 6-node workflow and all mocked AI failure/hallucination states."""
import sys
from pathlib import Path
import requests

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.agents.workflow import execute_research_workflow
from thesisos.data.loaders import load_companies, load_financial_facts, load_sources
from thesisos.data.sources import SourceRecord
from thesisos.finance.dcf import DCFAssumptions


class _MockResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


def _get_tcs_inputs():
    comp = load_companies().iloc[0].to_dict()
    facts = load_financial_facts("TCS", "CONSOLIDATED")
    sources_df = load_sources("TCS")
    corpus = [SourceRecord(**r.to_dict()) for _, r in sources_df.iterrows()]
    dcf_assump = DCFAssumptions(
        company_id="TCS",
        base_fiscal_year="FY2025",
        base_revenue_cr=255324.0,
        forecast_years=5,
        revenue_growth_rates=[0.08] * 5,
        ebit_margins=[0.243] * 5,
        effective_tax_rate=0.25,
        da_pct_revenue=0.02,
        capex_pct_revenue=0.015,
        nwc_change_pct_rev_change=0.05,
        equity_weight=0.95,
        debt_weight=0.05,
        cost_of_equity=0.11,
        pretax_cost_of_debt=0.075,
        terminal_growth_rate=0.045,
        total_debt_cr=8240.0,
        cash_and_investments_cr=51420.0,
        diluted_shares_crore=361.81,
        reference_price_inr=4085.0,
        reference_price_date="2025-05-30",
    )
    return comp, facts, sources_df, corpus, dcf_assump


def test_workflow_no_api_key_deterministic_mode():
    comp, facts, sources_df, corpus, dcf_assump = _get_tcs_inputs()
    state = execute_research_workflow(comp, "CONSOLIDATED", facts, sources_df, corpus, dcf_assump)
    assert state.deterministic_dossier is not None
    assert len(state.deterministic_dossier.sections) == 24
    assert state.optional_ai_narrative is None


def test_workflow_invalid_key_and_rate_limit_fallbacks():
    comp, facts, sources_df, corpus, dcf_assump = _get_tcs_inputs()

    # 1. Invalid Key (401)
    state_401 = execute_research_workflow(
        comp, "CONSOLIDATED", facts, sources_df, corpus, dcf_assump,
        optional_provider="GROQ", optional_api_key="bad_key",
        http_post_fn=lambda *a, **kw: _MockResponse(401, {}),
    )
    assert "INVALID_API_KEY" in state_401.ai_status_message
    assert state_401.deterministic_dossier is not None

    # 2. Rate Limit (429)
    state_429 = execute_research_workflow(
        comp, "CONSOLIDATED", facts, sources_df, corpus, dcf_assump,
        optional_provider="GROQ", optional_api_key="valid_key",
        http_post_fn=lambda *a, **kw: _MockResponse(429, {}),
    )
    assert "RATE_LIMIT_REACHED" in state_429.ai_status_message
    assert state_429.deterministic_dossier is not None

    # 3. Network Timeout
    def _raise_timeout(*a, **kw):
        raise requests.exceptions.Timeout("Timed out")

    state_timeout = execute_research_workflow(
        comp, "CONSOLIDATED", facts, sources_df, corpus, dcf_assump,
        optional_provider="GROQ", optional_api_key="valid_key",
        http_post_fn=_raise_timeout,
    )
    assert "NETWORK_TIMEOUT" in state_timeout.ai_status_message


def test_validator_flags_hallucinated_numbers_missing_citations_and_contradictions():
    comp, facts, sources_df, corpus, dcf_assump = _get_tcs_inputs()

    # Hallucinated figure Rs 999999 Cr + fake citation [SRC_FAKE_1, p.1] + contradictory claim "revenue declined"
    bad_llm_text = (
        "In FY2025, TCS revenue declined sharply to Rs 999999 Cr [SRC_FAKE_1, p.1] despite market tailwinds."
    )
    state_bad = execute_research_workflow(
        comp, "CONSOLIDATED", facts, sources_df, corpus, dcf_assump,
        optional_provider="GROQ", optional_api_key="valid_key",
        http_post_fn=lambda *a, **kw: _MockResponse(
            200, {"choices": [{"message": {"content": bad_llm_text}}]}
        ),
    )
    assert state_bad.validation_passed is False
    joined_flags = " | ".join(state_bad.validation_flags)
    assert "UNVERIFIED_SOURCE_ID" in joined_flags
    assert "UNSUPPORTED_FINANCIAL_VALUE" in joined_flags
    assert "CONTRADICTORY_CLAIM" in joined_flags
