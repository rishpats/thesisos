"""Standardized Plotly chart builders for ThesisOS."""
from typing import List, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from thesisos.config import PALETTE


def _apply_base_layout(fig: go.Figure, title: str, subtitle_source: str, y_title: str) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:11px;color:{PALETTE['text_secondary']}'>{subtitle_source}</span>",
            x=0.01,
        ),
        paper_bgcolor=PALETTE["panel"],
        plot_bgcolor=PALETTE["panel"],
        font=dict(color=PALETTE["text_primary"], family="sans-serif"),
        margin=dict(l=50, r=40, t=70, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title=y_title, gridcolor=PALETTE["divider"], zerolinecolor=PALETTE["divider"]),
        xaxis=dict(title="Fiscal Year (Actuals)", gridcolor=PALETTE["divider"]),
        height=380,
    )
    return fig


def build_revenue_profit_chart(df: pd.DataFrame, company_name: str, scope: str) -> go.Figure:
    """Plot Revenue, EBITDA, and PAT bars (INR Crore) with EBITDA/PAT Margin lines (%)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    years = df["fiscal_year"].tolist()

    fig.add_trace(
        go.Bar(name="Revenue (₹ Cr)", x=years, y=df["revenue"], marker_color=PALETTE["accent_blue"]),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(name="EBITDA (₹ Cr)", x=years, y=df["ebitda"], marker_color=PALETTE["positive"]),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(name="PAT (₹ Cr)", x=years, y=df["pat"], marker_color="#9B8EC4"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            name="EBITDA Margin (%)",
            x=years,
            y=(df["ebitda_margin"] * 100.0).round(2),
            mode="lines+markers",
            line=dict(color=PALETTE["warning"], width=2.5),
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            name="PAT Margin (%)",
            x=years,
            y=(df["pat_margin"] * 100.0).round(2),
            mode="lines+markers",
            line=dict(color=PALETTE["text_primary"], width=2, dash="dot"),
        ),
        secondary_y=True,
    )

    fig.update_layout(barmode="group")
    _apply_base_layout(
        fig,
        title=f"{company_name} — Revenue, Earnings & Margin Trajectory",
        subtitle_source=f"Scope: {scope} | Units: ₹ Crore (Bars) & Percentage % (Lines) | Source: Official Annual Reports",
        y_title="₹ Crore (INR)",
    )
    fig.update_yaxes(title_text="Margin (%)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return fig


def build_cash_conversion_chart(df: pd.DataFrame, company_name: str, scope: str) -> go.Figure:
    """Plot Operating Cash Flow (CFO), Free Cash Flow (FCF), and PAT (INR Crore) with CFO/PAT ratio."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    years = df["fiscal_year"].tolist()

    fig.add_trace(
        go.Bar(name="Operating Cash Flow - CFO (₹ Cr)", x=years, y=df["cfo"], marker_color=PALETTE["positive"]),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(name="Free Cash Flow - FCF (₹ Cr)", x=years, y=df["fcf"], marker_color=PALETTE["accent_blue"]),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(name="Reported PAT (₹ Cr)", x=years, y=df["pat"], marker_color=PALETTE["text_secondary"]),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            name="CFO / PAT Ratio (x)",
            x=years,
            y=df["cfo_to_pat"].round(2),
            mode="lines+markers",
            line=dict(color=PALETTE["warning"], width=2.5),
        ),
        secondary_y=True,
    )

    fig.update_layout(barmode="group")
    _apply_base_layout(
        fig,
        title=f"{company_name} — Cash Flow Quality & Earnings Conversion",
        subtitle_source=f"Scope: {scope} | Units: ₹ Crore (Bars) & Ratio x (Line) | Threshold: CFO/PAT >= 0.80x",
        y_title="₹ Crore (INR)",
    )
    fig.update_yaxes(title_text="CFO / PAT (x)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return fig


def build_returns_and_working_capital_chart(df: pd.DataFrame, company_name: str, scope: str) -> go.Figure:
    """Plot ROE and ROCE (%) alongside Receivable Days (DSO)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    years = df["fiscal_year"].tolist()

    fig.add_trace(
        go.Scatter(
            name="ROE (%)",
            x=years,
            y=(df["roe"] * 100.0).round(2),
            mode="lines+markers",
            line=dict(color=PALETTE["positive"], width=2.5),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            name="ROCE (%)",
            x=years,
            y=(df["roce"] * 100.0).round(2),
            mode="lines+markers",
            line=dict(color=PALETTE["accent_blue"], width=2.5),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            name="Receivable Days (DSO)",
            x=years,
            y=df["receivable_days"].round(1),
            marker_color="rgba(200, 161, 108, 0.45)",
        ),
        secondary_y=True,
    )

    _apply_base_layout(
        fig,
        title=f"{company_name} — Capital Efficiency (ROE / ROCE) & Receivable Days",
        subtitle_source=f"Scope: {scope} | Units: Return % (Lines) & Days (Bars) | Source: Audited Balance Sheet & P&L",
        y_title="Return (%)",
    )
    fig.update_yaxes(title_text="Receivable Days (Days)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return fig


def build_dcf_sensitivity_heatmap(
    wacc_values: List[float],
    tg_values: List[float],
    matrix: List[List[Optional[float]]],
    company_name: str,
) -> go.Figure:
    """Render 2D heatmap of Implied Fair Value per Share (₹) across WACC and Terminal Growth."""
    x_labels = [f"{g * 100:.1f}%" for g in tg_values]
    y_labels = [f"{w * 100:.1f}%" for w in wacc_values]
    text_matrix = [
        [f"₹{val:,.0f}" if val is not None else "Invalid (g>=WACC)" for val in row]
        for row in matrix
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=x_labels,
            y=y_labels,
            text=text_matrix,
            texttemplate="%{text}",
            colorscale=[[0.0, "#D16D6A"], [0.5, "#22272D"], [1.0, "#85AF95"]],
            colorbar=dict(title="₹ / Share"),
        )
    )
    _apply_base_layout(
        fig,
        title=f"{company_name} — DCF Sensitivity Matrix: Implied Fair Value per Share (₹)",
        subtitle_source="Rows: WACC (%) | Columns: Terminal Growth Rate (%) | Deterministic FCFF Model",
        y_title="WACC (%)",
    )
    fig.update_xaxes(title_text="Terminal Growth Rate (%)")
    return fig
