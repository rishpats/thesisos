"""Safe, privacy-preserving CSV and Print-Ready HTML Dossier exporters."""
import json
from typing import Any, Dict
import pandas as pd
from thesisos.finance.dcf import DCFAssumptions, DCFOutput
from thesisos.reports.memo import ResearchMemoDossier


def export_dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Export a DataFrame to UTF-8 CSV bytes without index."""
    return df.to_csv(index=False).encode("utf-8")


def export_dcf_assumptions_json(assumptions: DCFAssumptions, output: DCFOutput) -> bytes:
    """Export DCF assumptions and summary outputs to a clean, auditable JSON file."""
    payload: Dict[str, Any] = {
        "assumptions": assumptions.to_dict(),
        "valuation_summary": {
            "wacc": output.wacc,
            "terminal_growth_rate": output.terminal_growth_rate,
            "enterprise_value_cr": output.enterprise_value_cr,
            "equity_value_cr": output.equity_value_cr,
            "fair_value_per_share_inr": output.fair_value_per_share_inr,
            "reference_price_inr": output.reference_price_inr,
            "reference_price_date": output.reference_price_date,
            "upside_downside_pct": output.upside_downside_pct,
            "margin_of_safety_pct": output.margin_of_safety_pct,
            "warnings": output.warnings,
        },
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def export_memo_to_printable_html(dossier: ResearchMemoDossier) -> bytes:
    """Render a print-ready HTML Research Report (users can Ctrl+P -> Save as PDF in any browser)."""
    sections_html = ""
    for sec in dossier.sections:
        cites = f"<div class='cites'>Citations: {', '.join(sec.citations)}</div>" if sec.citations else ""
        sections_html += f"""
        <div class="sec">
            <div class="sec-hdr">
                <span class="sec-title">{sec.section_number}. {sec.title}</span>
                <span class="badge">{sec.epistemic_badge}</span>
            </div>
            <p>{sec.content.replace(chr(10), '<br>')}</p>
            {cites}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ThesisOS Equity Research Dossier — {dossier.company_name}</title>
<style>
    body {{ font-family: Georgia, 'Times New Roman', serif; color: #111; max-width: 860px; margin: 24px auto; line-height: 1.5; }}
    .hdr {{ border-bottom: 3px solid #171A1E; padding-bottom: 12px; margin-bottom: 20px; }}
    .title {{ font-size: 24px; font-weight: bold; margin: 0; }}
    .meta {{ font-size: 12px; color: #444; margin-top: 6px; font-family: sans-serif; }}
    .sec {{ margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #ddd; page-break-inside: avoid; }}
    .sec-hdr {{ display: flex; justify-content: space-between; align-items: center; }}
    .sec-title {{ font-weight: bold; font-size: 15px; font-family: sans-serif; color: #171A1E; }}
    .badge {{ font-size: 10px; font-family: monospace; background: #eee; padding: 2px 6px; border: 1px solid #bbb; border-radius: 3px; }}
    .cites {{ font-size: 11px; color: #555; font-family: monospace; margin-top: 4px; }}
    .footer {{ font-size: 11px; color: #555; border-top: 2px solid #171A1E; padding-top: 10px; margin-top: 28px; }}
</style>
</head>
<body>
    <div class="hdr">
        <div class="title">THESISOS INSTITUTIONAL EQUITY RESEARCH DOSSIER</div>
        <div class="meta">
            <b>Company:</b> {dossier.company_name} ({dossier.exchange_symbol}) |
            <b>Scope:</b> {dossier.reporting_scope} |
            <b>Generation Mode:</b> {dossier.generation_mode} |
            <b>Generated:</b> {dossier.generation_date} |
            <b>Data Verified:</b> {dossier.underlying_data_date}<br>
            <b>Provenance:</b> {dossier.model_provenance}
        </div>
    </div>
    {sections_html}
    <div class="footer">{dossier.disclaimer}</div>
</body>
</html>"""
    return html.encode("utf-8")
