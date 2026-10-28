"""Central configuration, palette constants, and analytical defaults for ThesisOS."""
from pathlib import Path
from typing import Dict

# Repository Root and Data Paths
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent.parent
DATA_DIR = REPO_ROOT / "data" / "demo"
COMPANIES_CSV = DATA_DIR / "companies.csv"
FINANCIAL_FACTS_CSV = DATA_DIR / "financial_facts.csv"
SAMPLE_SOURCES_CSV = DATA_DIR / "sample_sources.csv"

# Institutional Dark Terminal Palette
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

# Standard Units and Scopes
SUPPORTED_SCOPES = ("CONSOLIDATED", "STANDALONE")
SUPPORTED_UNITS = ("INR_CRORE", "INR_LAKH", "INR_MILLION", "PERCENT", "RATIO", "SHARES_CRORE", "INR_PER_SHARE")
CANONICAL_MONETARY_UNIT = "INR_CRORE"

# Unit Normalization Multipliers to INR_CRORE (1 Crore = 100 Lakh = 10 Million)
UNIT_TO_CRORE_MULTIPLIER: Dict[str, float] = {
    "INR_CRORE": 1.0,
    "INR_LAKH": 0.01,
    "INR_MILLION": 0.1,
}

# Default Forensic Alert Thresholds
DEFAULT_FORENSIC_THRESHOLDS: Dict[str, float] = {
    "cfo_to_pat_min": 0.80,              # Flag if CFO / PAT < 0.80x
    "receivable_vs_rev_growth_gap": 0.05, # Flag if Receivables growth exceeds Revenue growth by >5% (500 bps)
    "receivable_days_jump": 10.0,        # Flag if Receivable Days increase by >10 days YoY
    "ebitda_margin_drop_bps": 200.0,     # Flag if EBITDA margin drops by >200 bps (2.0 percentage points) YoY
    "net_debt_to_ebitda_max": 2.5,       # Flag if Net Debt / EBITDA > 2.5x
    "interest_coverage_min": 3.0,        # Flag if EBIT / Finance Costs < 3.0x
    "wc_to_rev_shift": 0.04,             # Flag if Working Capital / Revenue shifts >400 bps YoY
    "share_dilution_max": 0.02,          # Flag if Diluted Shares grow >2.0% YoY
    "dividend_payout_vs_fcf_max": 1.00,  # Flag if Dividends Paid > Free Cash Flow
}

# Mandatory Institutional & Regulatory Disclosure
INSTITUTIONAL_DISCLAIMER = (
    "EDUCATIONAL & RESEARCH USE ONLY — NOT SEBI-REGISTERED INVESTMENT ADVICE: "
    "ThesisOS is an open-source, deterministic equity research intelligence platform built for academic, "
    "analytical, and portfolio demonstration purposes. All financial calculations are performed deterministically "
    "from historical statutory disclosures cited by page number. Market prices shown are dated reference inputs, "
    "not live exchange feeds. Nothing herein constitutes a solicitation or recommendation to buy, sell, or hold any security."
