"""Central configuration, palette constants, and analytical defaults for ThesisOS."""
from pathlib import Path
from typing import Dict

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent.parent
DATA_DIR = REPO_ROOT / "data" / "demo"
COMPANIES_CSV = DATA_DIR / "companies.csv"
FINANCIAL_FACTS_CSV = DATA_DIR / "financial_facts.csv"
SAMPLE_SOURCES_CSV = DATA_DIR / "sample_sources.csv"

PALETTE: Dict[str, str] = {
    "background": "#171A1E",
    "panel": "#22272D",
    "divider": "#3A4047",
    "text_primary": "#F0ECE2",
    "text_secondary": "#A6ADB3",
    "positive": "#85AF95",
    "warning": "#C8A16C",
    "negative": "#D16D6A",
    "accent_blue": "#6C9BD2",
}

SUPPORTED_SCOPES = ("CONSOLIDATED", "STANDALONE")
SUPPORTED_UNITS = ("INR_CRORE", "INR_LAKH", "INR_MILLION", "PERCENT", "RATIO", "SHARES_CRORE", "INR_PER_SHARE")
CANONICAL_MONETARY_UNIT = "INR_CRORE"

UNIT_TO_CRORE_MULTIPLIER: Dict[str, float] = {
    "INR_CRORE": 1.0,
    "INR_LAKH": 0.01,
    "INR_MILLION": 0.1,
}

DEFAULT_FORENSIC_THRESHOLDS: Dict[str, float] = {
    "cfo_to_pat_min": 0.80,
    "receivable_vs_rev_growth_gap": 0.05,
    "receivable_days_jump": 10.0,
    "ebitda_margin_drop_bps": 200.0,
    "net_debt_to_ebitda_max": 2.5,
    "interest_coverage_min": 3.0,
    "wc_to_rev_shift": 0.04,
    "share_dilution_max": 0.02,
    "dividend_payout_vs_fcf_max": 1.00,
}

INSTITUTIONAL_DISCLAIMER = "EDUCATIONAL & RESEARCH USE ONLY — NOT SEBI-REGISTERED INVESTMENT ADVICE: ThesisOS is an open-source, deterministic equity research intelligence platform built for academic, analytical, and portfolio demonstration purposes. All financial calculations are performed deterministically from historical statutory disclosures cited by page number. Market prices shown are dated reference inputs, not live exchange feeds. Nothing herein constitutes a solicitation or recommendation to buy, sell, or hold any security."
# END OF FILE
