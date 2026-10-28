"""Cached data loaders for demo CSV files."""
import pandas as pd
import streamlit as st
from thesisos.config import COMPANIES_CSV, FINANCIAL_FACTS_CSV, SAMPLE_SOURCES_CSV
from thesisos.data.normalize import normalize_monetary_value


@st.cache_data(show_spinner=False)
def load_companies() -> pd.DataFrame:
    """Load verified demo company metadata registry."""
    return pd.read_csv(COMPANIES_CSV)


@st.cache_data(show_spinner=False)
def load_financial_facts(company_id: str, scope: str = "CONSOLIDATED") -> pd.DataFrame:
    """Load and normalize financial facts for a specific company and statement scope."""
    df = pd.read_csv(FINANCIAL_FACTS_CSV)
    filtered = df[
        (df["company_id"].str.upper() == company_id.strip().upper())
        & (df["scope"].str.upper() == scope.strip().upper())
    ].copy()
    if not filtered.empty:
        filtered["normalized_value"] = filtered.apply(
            lambda r: normalize_monetary_value(r["original_value"], r["original_unit"]), axis=1
        )
    return filtered


@st.cache_data(show_spinner=False)
def load_sources(company_id: str = "") -> pd.DataFrame:
    """Load indexed Annual Report source passages and page provenance."""
    df = pd.read_csv(SAMPLE_SOURCES_CSV)
    if company_id:
        df = df[df["company_id"].str.upper() == company_id.strip().upper()].copy()
    return df
