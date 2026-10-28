"""Canonical Pydantic schemas for financial observations, sources, and provenance."""
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from thesisos.config import SUPPORTED_SCOPES, SUPPORTED_UNITS


class CompanyMetadata(BaseModel):
    company_id: str
    company_name: str
    exchange: str
    symbol: str
    sector: str
    default_scope: str = "CONSOLIDATED"
    currency: str = "INR"
    reference_price_inr: float
    reference_price_date: str
    reference_price_source: str
    diluted_shares_crore: float
    last_verified_date: str
    description: str


class SourceRecord(BaseModel):
    source_id: str
    company_id: str
    document_title: str
    source_url: str
    page: int = Field(ge=1)
    reporting_period: str
    extracted_passage: str
    retrieval_date: str
    extraction_method: str
    verification_status: str


class FinancialObservation(BaseModel):
    company_id: str
    company_name: str
    exchange: str
    symbol: str
    sector: str
    fiscal_year: str
    period_start: str
    period_end: str
    period_type: str = "ANNUAL"
    statement_type: str
    scope: str
    metric_key: str
    original_value: float
    original_unit: str
    normalized_value: float
    normalized_unit: str
    currency: str = "INR"
    source_id: str
    source_url: str
    source_page: str
    extraction_method: str
    verification_date: str
    verification_status: str
    notes: Optional[str] = ""

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.scope = self.scope.strip().upper()
        if self.scope not in SUPPORTED_SCOPES:
            raise ValueError(f"Unsupported statement scope '{self.scope}'. Must be one of {SUPPORTED_SCOPES}")
        self.original_unit = self.original_unit.strip().upper()
        self.normalized_unit = self.normalized_unit.strip().upper()
        if self.original_unit not in SUPPORTED_UNITS or self.normalized_unit not in SUPPORTED_UNITS:
            raise ValueError(f"Unsupported unit. Must be one of {SUPPORTED_UNITS}")


class DataQualityIssue(BaseModel):
    severity: str  # "ERROR" or "WARNING"
    category: str
    fiscal_year: Optional[str] = None
    metric_key: Optional[str] = None
    message: str
    affected_calculations: List[str] = Field(default_factory=list)


class DataQualityReport(BaseModel):
    company_id: str
    scope: str
    total_observations: int
    covered_years: List[str]
    missing_years: List[str]
    is_clean: bool
    issues: List[DataQualityIssue] = Field(default_factory=list)
