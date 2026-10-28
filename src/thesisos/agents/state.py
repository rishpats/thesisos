"""Shared workflow state for the 6-node ThesisOS research pipeline."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from thesisos.data.sources import DataQualityReport, SourceRecord
from thesisos.finance.dcf import DCFAssumptions, DCFOutput
from thesisos.finance.forensic import ForensicAlert
from thesisos.reports.memo import ResearchMemoDossier


class WorkflowState(BaseModel):
    company_meta: Dict[str, Any]
    scope: str = "CONSOLIDATED"
    dq_report: Optional[DataQualityReport] = None
    latest_metrics: Dict[str, Any] = Field(default_factory=dict)
    cagrs: Dict[str, Optional[float]] = Field(default_factory=dict)
    multiples: Dict[str, Optional[float]] = Field(default_factory=dict)
    forensic_alerts: List[ForensicAlert] = Field(default_factory=list)
    retrieved_sources: List[SourceRecord] = Field(default_factory=list)
    dcf_assumptions: Optional[DCFAssumptions] = None
    dcf_output: Optional[DCFOutput] = None
    scenarios: Dict[str, DCFOutput] = Field(default_factory=dict)
    reverse_dcf_growth: Optional[float] = None
    deterministic_dossier: Optional[ResearchMemoDossier] = None
    optional_ai_narrative: Optional[str] = None
    ai_status_message: str = "NO_API_KEY_CONFIGURED: Running 100% Deterministic Engine ($0 Mode)."
    validation_passed: bool = True
    validation_flags: List[str] = Field(default_factory=list)
