"""Unit tests for canonical data normalization, scope isolation, and data quality checks."""
import sys
from pathlib import Path
import pandas as pd
import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from thesisos.data.normalize import normalize_monetary_value, pivot_canonical_statements
from thesisos.data.validation import audit_financial_dataset


def test_unit_conversion_to_crore():
    assert normalize_monetary_value(100.0, "INR_CRORE") == 100.0
    assert normalize_monetary_value(500.0, "INR_LAKH") == 5.0
    assert normalize_monetary_value(250.0, "INR_MILLION") == 25.0


def test_scope_mixing_and_duplicate_rejection():
    mixed_df = pd.DataFrame(
        [
            {"fiscal_year": "FY2024", "scope": "CONSOLIDATED", "metric_key": "revenue", "original_unit": "INR_CRORE", "normalized_unit": "INR_CRORE", "normalized_value": 100.0},
            {"fiscal_year": "FY2025", "scope": "STANDALONE", "metric_key": "revenue", "original_unit": "INR_CRORE", "normalized_unit": "INR_CRORE", "normalized_value": 110.0},
        ]
    )
    with pytest.raises(ValueError, match="Scope Mixing Violation"):
        pivot_canonical_statements(mixed_df, expected_scope="CONSOLIDATED")

    dup_df = pd.DataFrame(
        [
            {"fiscal_year": "FY2024", "scope": "CONSOLIDATED", "metric_key": "revenue", "original_unit": "INR_CRORE", "normalized_unit": "INR_CRORE", "normalized_value": 100.0},
            {"fiscal_year": "FY2024", "scope": "CONSOLIDATED", "metric_key": "revenue", "original_unit": "INR_CRORE", "normalized_unit": "INR_CRORE", "normalized_value": 105.0},
        ]
    )
    with pytest.raises(ValueError, match="Duplicate financial observations"):
        pivot_canonical_statements(dup_df, expected_scope="CONSOLIDATED")


def test_missing_years_and_provenance_audit():
    facts = pd.DataFrame(
        [
            {"fiscal_year": "FY2022", "scope": "CONSOLIDATED", "metric_key": "revenue", "source_id": "SRC_1", "source_url": "https://nseindia.com"},
            {"fiscal_year": "FY2024", "scope": "CONSOLIDATED", "metric_key": "revenue", "source_id": "", "source_url": ""},
        ]
    )
    sources = pd.DataFrame([{"source_id": "SRC_1"}])
    report = audit_financial_dataset(facts, sources, company_id="TEST", scope="CONSOLIDATED")
    assert "FY2023" in report.missing_years
    assert not report.is_clean
    categories = {i.category for i in report.issues}
    assert "MISSING_FISCAL_YEAR" in categories
    assert "MISSING_PROVENANCE" in categories
