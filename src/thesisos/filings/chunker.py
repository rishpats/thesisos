"""Page-preserving text chunker that converts ParsedDocumentResult into SourceRecords."""
from datetime import date
from typing import List
from thesisos.data.sources import SourceRecord
from thesisos.filings.pdf_parser import ParsedDocumentResult


def chunk_parsed_document(
    parsed_doc: ParsedDocumentResult,
    chunk_size_chars: int = 750,
    overlap_chars: int = 100,
) -> List[SourceRecord]:
    """Split each extracted page into overlapping passages while preserving exact page numbers."""
    records: List[SourceRecord] = []
    today_str = date.today().isoformat()

    for page in parsed_doc.pages:
        if page.is_low_text_or_scanned or not page.sanitized_text:
            continue
        text = " ".join(page.sanitized_text.split())
        start = 0
        chunk_idx = 1
        while start < len(text):
            end = min(start + chunk_size_chars, len(text))
            passage = text[start:end].strip()
            if len(passage) >= 25:
                sid = f"{parsed_doc.document_id}_P{page.page_number}_C{chunk_idx}"
                records.append(
                    SourceRecord(
                        source_id=sid,
                        company_id=parsed_doc.company_id,
                        document_title=parsed_doc.document_title,
                        source_url=parsed_doc.source_url_or_provenance,
                        page=page.page_number,
                        reporting_period=parsed_doc.reporting_period,
                        extracted_passage=passage,
                        retrieval_date=today_str,
                        extraction_method="PYPDF_PAGE_CHUNKER",
                        verification_status="UPLOADED_UNVERIFIED",
                    )
                )
                chunk_idx += 1
            if end == len(text):
                break
            start = max(end - overlap_chars, start + 1)
    return records
