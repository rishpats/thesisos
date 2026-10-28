"""Explicit, testable unit normalization and series alignment functions."""
from typing import Dict
import pandas as pd
from thesisos.config import CANONICAL_MONETARY_UNIT, UNIT_TO_CRORE_MULTIPLIER


def normalize_monetary_value(value: float, unit: str) -> float:
    """Convert a monetary observation (INR_CRORE, INR_LAKH, INR_MILLION) into INR_CRORE."""
    clean_unit = unit.strip().upper()
    if clean_unit in UNIT_TO_CRORE_MULTIPLIER:
        return round(float(value) * UNIT_TO_CRORE_MULTIPLIER[clean_unit], 4)
    if clean_unit in ("INR_PER_SHARE", "SHARES_CRORE", "PERCENT", "RATIO"):
        return float(value)
    raise ValueError(f"Cannot normalize unsupported unit: {unit}")


def pivot_canonical_statements(facts_df: pd.DataFrame, expected_scope: str = "CONSOLIDATED") -> pd.DataFrame:
    """
    Pivot normalized financial facts into a wide fiscal_year-indexed DataFrame.
    Strictly blocks mixing CONSOLIDATED and STANDALONE observations or incompatible units.
    """
    if facts_df.empty:
        return pd.DataFrame()

    scopes_present = facts_df["scope"].str.upper().unique().tolist()
    if len(scopes_present) > 1:
        raise ValueError(
            f"Scope Mixing Violation: Facts contain multiple scopes {scopes_present}. "
            "Filter to a single scope before pivoting."
        )
    if scopes_present[0] != expected_scope.upper():
        raise ValueError(f"Requested scope '{expected_scope}' but dataset has scope '{scopes_present[0]}'.")

    # Ensure monetary metrics are normalized to INR_CRORE
    monetary_mask = facts_df["original_unit"].isin(["INR_CRORE", "INR_LAKH", "INR_MILLION"])
    bad_norm = facts_df[monetary_mask & (facts_df["normalized_unit"] != CANONICAL_MONETARY_UNIT)]
    if not bad_norm.empty:
        raise ValueError("Normalized unit mismatch: All monetary metrics must be normalized to INR_CRORE.")

    # Check for duplicate (fiscal_year, metric_key) pairs
    dups = facts_df[facts_df.duplicated(subset=["fiscal_year", "metric_key"], keep=False)]
    if not dups.empty:
        dup_keys = dups[["fiscal_year", "metric_key"]].drop_duplicates().to_dict(orient="records")
        raise ValueError(f"Duplicate financial observations detected for: {dup_keys}")

    pivoted = facts_df.pivot(index="fiscal_year", columns="metric_key", values="normalized_value")
    pivoted = pivoted.sort_index().reset_index()
    return pivoted
