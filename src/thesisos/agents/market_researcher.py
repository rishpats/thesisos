"""Node 4: Deterministic Valuation & Scenario Node."""
from thesisos.agents.state import WorkflowState
from thesisos.finance.dcf import DCFAssumptions, run_dcf_valuation, solve_reverse_dcf_implied_growth
from thesisos.finance.scenarios import run_bull_base_bear_scenarios


def run_valuation_node(state: WorkflowState, assumptions: DCFAssumptions) -> WorkflowState:
    """Execute deterministic FCFF DCF, Bull/Base/Bear scenarios, and Reverse DCF."""
    state.dcf_assumptions = assumptions
    state.dcf_output = run_dcf_valuation(assumptions)
    state.scenarios = run_bull_base_bear_scenarios(assumptions)
    state.reverse_dcf_growth = solve_reverse_dcf_implied_growth(assumptions)
    return state
