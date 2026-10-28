"""Comprehensive financial data-quality auditor for ThesisOS."""
from typing import List, Set
import pandas as pd
from thesisos.data.sources import DataQualityIssue, DataQualityReport

REQUIRED_CORE_METRICS = {
    "revenue": ["Growth Rates", "Margins", "Working Capital Days", "DCF Forecast"],
    "ebitda": ["EBITDA Margin", "EV/EBITDA", "Net Debt/EBITDA"],
    "ebit": ["EBIT Margin", "ROCE", "Interest Coverage", "DCF FCFF"],
    "pat": ["PAT Margin", "ROE", "CFO/PAT Conversion", "P/E"],
    "cfo": ["Free Cash Flow", "CFO/PAT Conversion", "Forensic Cash Checks"],
    "capex": ["Free Cash Flow", "Capex/Revenue"],
    "total_assets": ["Balance Sheet Identity", "Asset Turnover"],
    "total_equity": ["ROE", "Debt/Equity", "P/B"],
}


def audit_financial_dataset(
    facts_df: pd.DataFrame,
    sources_df: pd.DataFrame,
    company_id: str,
    scope: str = "CONSOLIDATED",
) -> DataQualityReport:
    """Run 10-point data quality and provenance check on a company's financial facts."""
    issues: List[DataQualityIssue] = []

    if facts_df.empty:
        issues.append(
            DataQualityIssue(
                severity="ERROR",
                category="EMPTY_DATASET",
                message=f"No financial observations found for {company_id} under scope {scope}.",
                affected_calculations=["All Financial Analysis & Valuation Modules"],
            )
        )
        return DataQualityReport(
            company_id=company_id,
            scope=scope,
            total_observations=0,
            covered_years=[],
            missing_years=[],
            is_clean=False,
            issues=issues,
        )

    # 1. Check mixed scopes
    scopes = facts_df["scope"].str.upper().unique().tolist()
    if len(scopes) > 1 or scopes[0] != scope.upper():
        issues.append(
            DataQualityIssue(
                severity="ERROR",
                category="SCOPE_MIXING",
                message=f"Dataset contains unexpected scopes: {scopes} (expected only {scope}).",
                affected_calculations=["Time-Series Growth & Ratios"],
            )
        )

    # 2. Check duplicate (fiscal_year, metric_key, scope)
    dup_mask = facts_df.duplicated(subset=["fiscal_year", "metric_key", "scope"], keep=False)
    if dup_mask.any():
        for _, row in facts_df[dup_mask].drop_duplicates(subset=["fiscal_year", "metric_key"]).iterrows():
            issues.append(
                DataQualityIssue(
                    severity="ERROR",
                    category="DUPLICATE_OBSERVATION",
                    fiscal_year=str(row["fiscal_year"]),
                    metric_key=str(row["metric_key"]),
                    message=f"Duplicate observation for {row['metric_key']} in {row['fiscal_year']}.",
                    affected_calculations=[str(row["metric_key"])],
                )
            )

    # 3. Check fiscal year sequence gaps (e.g. FY2021..FY2025)
    covered_years = sorted(facts_df["fiscal_year"].astype(str).unique().tolist())
    yr_nums = sorted([int(y.replace("FY", "")) for y in covered_years if y.startswith("FY") and y[2:].isdigit()])
    missing_years: List[str] = []
    if len(yr_nums) >= 2:
        full_range = list(range(yr_nums[0], yr_nums[-1] + 1))
        for y in full_range:
            fy_label = f"FY{y}"
            if fy_label not in covered_years:
                missing_years.append(fy_label)
                issues.append(
                    DataQualityIssue(
                        severity="WARNING",
                        category="MISSING_FISCAL_YEAR",
                        fiscal_year=fy_label,
                        message=f"Fiscal year {fy_label} is missing from the historical series.",
                        affected_calculations=["YoY Growth Rates", "Multi-Year Continuity"],
                    )
                )

    # 4. Check source provenance links
    valid_source_ids: Set[str] = set(sources_df["source_id"].astype(str).unique()) if not sources_df.empty else set()
    for _, row in facts_df.iterrows():
        sid = str(row.get("source_id", "")).strip()
        surl = str(row.get("source_url", "")).strip()
        if not sid or not surl:
            issues.append(
                DataQualityIssue(
                    severity="ERROR",
                    category="MISSING_PROVENANCE",
                    fiscal_year=str(row["fiscal_year"]),
                    metric_key=str(row["metric_key"]),
                    message=f"Missing source_id or source_url for {row['metric_key']} ({row['fiscal_year']}).",
                    affected_calculations=["Citation Verification"],
                )
            )
        elif valid_source_ids and sid not in valid_source_ids:
            issues.append(
                DataQualityIssue(
                    severity="WARNING",
                    category="UNINDEXED_SOURCE_ID",
                    fiscal_year=str(row["fiscal_year"]),
                    metric_key=str(row["metric_key"]),
                    message=f"Source ID '{sid}' is not indexed in sample_sources.csv.",
                    affected_calculations=["Passage Citation Lookup"],
                )
            )

    # 5. Check required core metrics per covered year
    for fy in covered_years:
        fy_keys = set(facts_df[facts_df["fiscal_year"] == fy]["metric_key"].unique())
        for req_key, affected in REQUIRED_CORE_METRICS.items():
            if req_key not in fy_keys:
                issues.append(
                    DataQualityIssue(
                        severity="WARNING",
                        category="MISSING_CORE_METRIC",
                        fiscal_year=fy,
                        metric_key=req_key,
                        message=f"Missing core metric '{req_key}' in {fy}. Dependent metrics will be safely disabled.",
                        affected_calculations=affected,
                    )
                )

    has_errors = any(i.severity == "ERROR" for i in issues)
    return DataQualityReport(
        company_id=company_id,
        scope=scope,
        total_observations=len(facts_df),
        covered_years=covered_years,
        missing_years=missing_years,
        is_clean=not has_errors,
        issues=issues,
    )


