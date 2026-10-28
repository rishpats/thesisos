"""Institutional dark research-terminal CSS styling for ThesisOS."""
import streamlit as st
from thesisos.config import PALETTE


def apply_institutional_theme() -> None:
    """Inject custom CSS matching the ThesisOS institutional palette."""
    css = f"""
    <style>
        .stApp {{
            background-color: {PALETTE["background"]};
            color: {PALETTE["text_primary"]};
        }}
        .thesis-card {{
            background-color: {PALETTE["panel"]};
            border: 1px solid {PALETTE["divider"]};
            border-radius: 6px;
            padding: 16px 18px;
            margin-bottom: 14px;
        }}
        .thesis-kpi-label {{
            color: {PALETTE["text_secondary"]};
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 4px;
        }}
        .thesis-kpi-value {{
            color: {PALETTE["text_primary"]};
            font-size: 1.45rem;
            font-weight: 700;
            font-family: 'Consolas', 'Courier New', monospace;
        }}
        .thesis-kpi-sub {{
            color: {PALETTE["text_secondary"]};
            font-size: 0.76rem;
            margin-top: 4px;
        }}
        .badge-verified {{
            background-color: rgba(133, 175, 149, 0.18);
            color: {PALETTE["positive"]};
            border: 1px solid {PALETTE["positive"]};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
        }}
        .badge-warning {{
            background-color: rgba(200, 161, 108, 0.18);
            color: {PALETTE["warning"]};
            border: 1px solid {PALETTE["warning"]};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
        }}
        .badge-info {{
            background-color: rgba(108, 155, 210, 0.18);
            color: {PALETTE["accent_blue"]};
            border: 1px solid {PALETTE["accent_blue"]};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
        }}
        .context-banner {{
            background-color: {PALETTE["panel"]};
            border-left: 4px solid {PALETTE["positive"]};
            border-top: 1px solid {PALETTE["divider"]};
            border-right: 1px solid {PALETTE["divider"]};
            border-bottom: 1px solid {PALETTE["divider"]};
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 18px;
        }}
        .disclaimer-footer {{
            background-color: {PALETTE["panel"]};
            border-top: 1px solid {PALETTE["divider"]};
            color: {PALETTE["text_secondary"]};
            font-size: 0.74rem;
            padding: 12px;
            margin-top: 32px;
            border-radius: 4px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
