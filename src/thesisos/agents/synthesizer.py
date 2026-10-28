"""Node 5: Thesis Synthesizer (Category A Deterministic Default + Optional Session-Only BYOK LLM)."""
from typing import Callable, Optional
import requests
from thesisos.agents.state import WorkflowState


def call_optional_byok_llm(
    provider: str,
    api_key: str,
    prompt: str,
    http_post_fn: Optional[Callable] = None,
) -> tuple[Optional[str], str]:
    """
    Call optional free-tier Groq or Google Gemini API using visitor-supplied session key.
    Never logs the API key, never persists it, and handles all failure modes honestly.
    """
    clean_key = (api_key or "").strip()
    if not clean_key:
        return None, "NO_API_KEY: Using 100% Deterministic Rule-Based Report ($0 Mode)."

    post = http_post_fn or requests.post
    try:
        if provider.upper() == "GROQ":
            resp = post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {clean_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a strict institutional equity research analyst. Use ONLY the exact numbers "
                                "and [SRC_..., p.X] citations provided in the prompt. Never invent numbers or citations."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 700,
                },
                timeout=15,
            )
        elif provider.upper() == "GEMINI":
            resp = post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={clean_key}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=15,
            )
        else:
            return None, f"UNSUPPORTED_PROVIDER: '{provider}'. Falling back to deterministic report."

        if resp.status_code == 401 or resp.status_code == 403:
            return None, "INVALID_API_KEY (HTTP 401/403): Key rejected by provider. Deterministic report remains active."
        if resp.status_code == 429:
            return None, "RATE_LIMIT_REACHED (HTTP 429): Free-tier quota exhausted. Deterministic report remains active."
        if resp.status_code != 200:
            return None, f"PROVIDER_ERROR (HTTP {resp.status_code}): External service unavailable. Deterministic report active."

        data = resp.json()
        if provider.upper() == "GROQ":
            text = data["choices"][0]["message"]["content"]
        else:
            text = data["candidates"][0]["content"]["parts"][0]["text"]

        if not isinstance(text, str) or len(text.strip()) < 20:
            return None, "MALFORMED_MODEL_OUTPUT: Empty or invalid response structure. Deterministic report active."

        return text.strip(), f"LIVE_AI_SYNTHESIS_SUCCESS ({provider.upper()})"

    except requests.exceptions.Timeout:
        return None, "NETWORK_TIMEOUT: External LLM timed out. Deterministic report active."
    except Exception as exc:
        return None, f"EXTERNAL_SERVICE_FAILURE ({type(exc).__name__}): Deterministic report active."


def build_strict_evidence_prompt(state: WorkflowState) -> str:
    """Construct a grounded prompt containing only verified metrics and indexed citations."""
    m = state.latest_metrics
    d = state.dcf_output
    src_lines = "\n".join(
        [f"[{s.source_id}, p.{s.page}]: {s.extracted_passage}" for s in state.retrieved_sources]
    )
    return (
        f"Company: {state.company_meta['company_name']} ({state.scope})\n"
        f"Latest Fiscal Year: {m.get('fiscal_year')}\n"
        f"Verified Revenue: Rs {m.get('revenue'):,.1f} Cr | EBIT: Rs {m.get('ebit'):,.1f} Cr | PAT: Rs {m.get('pat'):,.1f} Cr | CFO: Rs {m.get('cfo'):,.1f} Cr\n"
        f"DCF Implied Fair Value: Rs {d.fair_value_per_share_inr:,.2f}/share (WACC {d.wacc*100:.2f}%, Terminal Growth {d.terminal_growth_rate*100:.2f}%)\n"
        f"Indexed Sources:\n{src_lines}\n\n"
        "Write a 3-paragraph institutional synthesis citing the exact [SRC_..., p.X] tags above and using ONLY the exact numbers provided."
    )
