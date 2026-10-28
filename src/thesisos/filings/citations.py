"""Citation provenance registry and claim-to-source verification rules."""
import re
from typing import Dict, List, Set
from pydantic import BaseModel
from thesisos.data.sources import SourceRecord

CITATION_TAG_REGEX = re.compile(r"\[(SRC_[A-Za-z0-9_]+|DOC_[A-Za-z0-9_]+)(?:,\s*p\.?\s*(\d+))?\]")


class CitationAuditResult(BaseModel):
    total_citations_found: int
    valid_citations: List[str]
    invalid_or_missing_sources: List[str]
    page_mismatch_citations: List[str]
    is_valid: bool


def verify_text_citations(text: str, indexed_sources: List[SourceRecord]) -> CitationAuditResult:
    """
    Verify every [SOURCE_ID, p.X] citation in a text block against real indexed SourceRecords.
    Rejects fabricated source IDs or mismatched page numbers.
    """
    source_map: Dict[str, SourceRecord] = {s.source_id: s for s in indexed_sources}
    matches = CITATION_TAG_REGEX.findall(text)

    valid_list: List[str] = []
    invalid_list: List[str] = []
    mismatch_list: List[str] = []

    for sid, page_str in matches:
        if sid not in source_map:
            invalid_list.append(sid)
            continue
        rec = source_map[sid]
        if page_str and int(page_str) != rec.page:
            mismatch_list.append(f"{sid} (claimed p.{page_str}, actual p.{rec.page})")
            continue
        valid_list.append(f"{sid} (p.{rec.page})")

    is_ok = len(invalid_list) == 0 and len(mismatch_list) == 0
    return CitationAuditResult(
        total_citations_found=len(matches),
        valid_citations=valid_list,
        invalid_or_missing_sources=invalid_list,
        page_mismatch_citations=mismatch_list,
        is_valid=is_ok,
    )
