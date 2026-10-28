"""Safe, page-aware PDF text and table extractor with scanned-page detection."""
import hashlib
import io
import re
from typing import Dict, List, Optional
import pdfplumber
from pydantic import BaseModel
from pypdf import PdfReader

MAX_PDF_BYTES = 25 * 1024 * 1024  # 25 MB hard ceiling for free cloud safety

PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)system\s+prompt\s*:",
    r"(?i)you\s+are\s+now\s+an?\s+",
    r"(?i)disregard\s+system\s+rules",
]


class ExtractedPage(BaseModel):
    page_number: int
    raw_text: str
    sanitized_text: str
    char_count: int
    is_low_text_or_scanned: bool
    extracted_tables_count: int
    injection_pattern_detected: bool


class ParsedDocumentResult(BaseModel):
    document_id: str
    document_title: str
    company_id: str
    reporting_period: str
    source_url_or_provenance: str
    total_pages: int
    pages_parsed: int
    scanned_or_empty_pages: List[int]
    injection_warnings: List[str]
    extraction_status: str
    pages: List[ExtractedPage]


def sanitize_untrusted_document_text(text: str) -> tuple[str, bool]:
    """Neutralize prompt-injection instructions inside untrusted PDF text while keeping evidence."""
    detected = False
    cleaned = text
    for pat in PROMPT_INJECTION_PATTERNS:
        if re.search(pat, cleaned):
            detected = True
            cleaned = re.sub(pat, "[UNTRUSTED_INSTRUCTION_REDACTED]", cleaned)
    return cleaned.strip(), detected


def parse_uploaded_pdf_bytes(
    pdf_bytes: bytes,
    filename: str,
    company_id: str,
    reporting_period: str = "FY2025",
    max_pages_to_parse: int = 120,
    extract_tables_max_pages: int = 10,
) -> ParsedDocumentResult:
    """Parse PDF bytes in-memory without writing permanent files to disk."""
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Uploaded file must have a .pdf extension.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError(f"PDF exceeds maximum safe cloud upload size of {MAX_PDF_BYTES // (1024*1024)} MB.")

    doc_hash = hashlib.sha256(pdf_bytes).hexdigest()[:10].upper()
    doc_id = f"DOC_{company_id}_{doc_hash}"

    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    limit = min(total_pages, max_pages_to_parse)

    pages_out: List[ExtractedPage] = []
    scanned_pages: List[int] = []
    injection_warnings: List[str] = []

    # Optional targeted table count on first N pages via pdfplumber
    table_counts: Dict[int, int] = {}
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pl_pdf:
            for p_idx in range(min(total_pages, extract_tables_max_pages)):
                tbls = pl_pdf.pages[p_idx].extract_tables()
                table_counts[p_idx + 1] = len(tbls) if tbls else 0
    except Exception:
        pass

    for idx in range(limit):
        page_num = idx + 1
        raw_txt = reader.pages[idx].extract_text() or ""
        sanitized, inj_found = sanitize_untrusted_document_text(raw_txt)
        char_len = len(sanitized)
        is_low = char_len < 30
        if is_low:
            scanned_pages.append(page_num)
        if inj_found:
            injection_warnings.append(f"Page {page_num} contained instruction-like text that was neutralized.")

        pages_out.append(
            ExtractedPage(
                page_number=page_num,
                raw_text=raw_txt,
                sanitized_text=sanitized,
                char_count=char_len,
                is_low_text_or_scanned=is_low,
                extracted_tables_count=table_counts.get(page_num, 0),
                injection_pattern_detected=inj_found,
            )
        )

    status = "COMPLETE"
    if len(scanned_pages) == limit and limit > 0:
        status = "SCANNED_PDF_OCR_UNAVAILABLE"
    elif scanned_pages:
        status = "PARTIAL_TEXT_EXTRACTED"

    return ParsedDocumentResult(
        document_id=doc_id,
        document_title=filename,
        company_id=company_id,
        reporting_period=reporting_period,
        source_url_or_provenance=f"USER_UPLOAD:{filename}",
        total_pages=total_pages,
        pages_parsed=limit,
        scanned_or_empty_pages=scanned_pages,
        injection_warnings=injection_warnings,
        extraction_status=status,
        pages=pages_out,
    )
