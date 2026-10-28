"""WACC vs. Terminal Growth sensitivity grids and Bull/Base/Bear scenario builder."""
from typing import Dict, List, Optional, Tuple
from thesisos.finance.dcf import DCFAssumptions, DCFOutput, run_dcf_valuation


def generate_wacc_tg_sensitivity_grid(
    base_assumptions: DCFAssumptions,
    wacc_steps: Optional[List[float]] = None,
    tg_steps: Optional[List[float]] = None,
) -> Tuple[List[float], List[float], List[List[Optional[float]]]]:
    """Compute a 2D matrix of Fair Value per Share (₹) across WACC and Terminal Growth values."""
    base_wacc = base_assumptions.compute_wacc()
    base_tg = base_assumptions.terminal_growth_rate

    wacc_list = wacc_steps or [round(base_wacc + d, 4) for d in (-0.015, -0.0075, 0.0, 0.0075, 0.015)]
    tg_list = tg_steps or [round(base_tg + d, 4) for d in (-0.010, -0.005, 0.0, 0.005, 0.010)]

    matrix: List[List[Optional[float]]] = []
    for w in wacc_list:
        row_vals: List[Optional[float]] = []
        for g in tg_list:
            if w <= 0 or g >= w:
                row_vals.append(None)
            else:
                clone = base_assumptions.clone_with(**{"wacc_override": w, "terminal_growth_rate": g})
                res = run_dcf_valuation(clone)
                row_vals.append(res.fair_value_per_share_inr)
        matrix.append(row_vals)
    return wacc_list, tg_list, matrix


def run_bull_base_bear_scenarios(base_assumptions: DCFAssumptions) -> Dict[str, DCFOutput]:
    """Run deterministic Bull, Base, and Bear valuation scenarios."""
    base_out = run_dcf_valuation(base_assumptions)
    base_wacc = base_assumptions.compute_wacc()

    bull_assump = base_assumptions.clone_with(**{
            "revenue_growth_rates": [min(g + 0.025, 0.35) for g in base_assumptions.revenue_growth_rates],
            "ebit_margins": [min(m + 0.015, 0.45) for m in base_assumptions.ebit_margins],
            "wacc_override": max(base_wacc - 0.005, 0.05),
            "terminal_growth_rate": min(base_assumptions.terminal_growth_rate + 0.005, max(base_wacc - 0.015, 0.02)),
        }
    )
    bear_assump = base_assumptions.clone_with(**{
            "revenue_growth_rates": [max(g - 0.025, -0.05) for g in base_assumptions.revenue_growth_rates],
            "ebit_margins": [max(m - 0.015, 0.05) for m in base_assumptions.ebit_margins],
            "wacc_override": base_wacc + 0.0075,
            "terminal_growth_rate": max(base_assumptions.terminal_growth_rate - 0.005, 0.01),
        }
    )
    return {
        "BEAR": run_dcf_valuation(bear_assump),
        "BASE": base_out,
        "BULL": run_dcf_valuation(bull_assump),
    }
