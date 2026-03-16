"""
Diagnostic report generation via Claude Sonnet 4.6.

Generates a structured maintenance report once, which is then cached in
Streamlit session_state for the remainder of the session.

The report is returned as a dict of sections keyed by tab name, so the
dashboard can render each section in its own tab without parsing markdown.
"""

import re
import anthropic
from ai.prompts import SYSTEM_CONTEXT, REPORT_GENERATION_PROMPT
from data.simulated_sensor_data import format_sensor_summary

SECTION_KEYS = ["SITUATION", "ROOT_CAUSE", "ACTIONS", "MACHINE_CONTEXT"]
TAB_LABELS   = ["Situation", "Root Cause Analysis", "Recommended Actions", "Machine Context"]


def generate_diagnostic_report(sensor_summary: dict, relevant_chunks: list[dict]) -> dict:
    """
    Call Claude Sonnet 4.6 to generate the diagnostic report.

    Args:
        sensor_summary:   Dict produced by compute_sensor_summary()
        relevant_chunks:  List of document chunks from retrieve_chunks()

    Returns:
        Dict mapping TAB_LABELS to markdown strings for each section.
    """
    client = anthropic.Anthropic()

    doc_context = _build_doc_context(relevant_chunks)
    sensor_text = format_sensor_summary(sensor_summary)

    user_message = (
        f"SENSOR DATA SUMMARY:\n{sensor_text}\n\n"
        f"RELEVANT DOCUMENTATION:\n{doc_context}\n\n"
        "Please generate the diagnostic report following the exact format specified. "
        "Fill in all placeholder values from the sensor data above. "
        "Use the documentation to justify every recommendation with a page reference."
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            temperature=0,
            system=SYSTEM_CONTEXT + "\n\n" + REPORT_GENERATION_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return _parse_sections(response.content[0].text)
    except anthropic.APIConnectionError:
        return _fallback_report(sensor_summary)
    except anthropic.APIStatusError as e:
        return _fallback_report(sensor_summary, error=str(e))


def _build_doc_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"--- {c['doc_name']}, Page {c['page']} ---\n{c['content']}"
        for c in chunks
    )


def _parse_sections(raw: str) -> dict:
    """Extract the four delimited sections from the model output."""
    sections = {}
    for key, label in zip(SECTION_KEYS, TAB_LABELS):
        pattern = rf"==={key}===(.*?)===END==="
        match = re.search(pattern, raw, re.DOTALL)
        sections[label] = match.group(1).strip() if match else raw
    return sections


def _fallback_report(summary: dict, error: str = "") -> dict:
    """Simple fallback report dict when the API is unavailable."""
    err_note = f"\n\n> **Note**: AI report generation unavailable ({error}). Showing summary only." if error else ""

    situation = f"""## What's Happening{err_note}

The Z-axis ascent time has been degrading over the past {summary['trend_duration_days']} days.

| Metric | Value |
|---|---|
| Current average (last 10 cycles) | **{summary['current_avg_ms']} ms** |
| Baseline | {summary['baseline_ms']} ms |
| Deviation | +{summary['deviation_ms']} ms ({summary['deviation_pct']}% above baseline) |
| Status | **{summary['status']}** |
| Degradation rate | ~{summary['degradation_rate_ms_per_day']} ms/day |
| Estimated days to critical | {summary['estimated_days_to_critical']} days |"""

    root_cause = """## Possible Root Causes

| # | Cause | Likelihood | Reference |
|---|---|---|---|
| 1 | Worn Z-axis seals / O-rings | High | Operating Manual, p.39 |
| 2 | Flow control valve degradation | High | Operating Manual, p.65–66 |
| 3 | Linear guide contamination | Medium | Maintenance Manual, p.7 |
| 4 | Supply air pressure drop | Medium | Operating Manual, p.65 |
| 5 | BG5 sensor positional drift | Low | Operating Manual, p.63–64 |"""

    actions = f"""## Recommended Actions

### Immediate (do today)
1. Check and adjust the one-way flow control valves on the Z-axis [Operating Manual, p.65–66]
2. Verify supply air pressure is within operating range [Operating Manual, p.65]

### Short-term (within 1 week)
1. Inspect linear guide rails for contamination and clean with a dry cloth [Maintenance Manual, p.7]
2. Check Z-axis proximity sensor BG5 alignment [Operating Manual, p.63–64]

### Scheduled Maintenance
1. Replace Z-axis seals — **OVERDUE** ({summary['component_service_log']['z_axis_seals']['cycles_since_replacement']:,} cycles, interval {summary['component_service_log']['z_axis_seals']['service_interval_cycles']:,}) [Operating Manual, p.39]

### Component Reference
- Z-axis mini slide: DGSL-10-40-E3-Y3A (Part #543905)
- Flow control valves: GRLA-M5-QS-3-LF-C (Part #175053)
- Valves MB5/MB6: CPVSC1-K-M5C (Part #548899)"""

    context = """## Machine Context

### Affected Axis
The Z-axis ascent is the upward return stroke of the drill head after each hole is drilled.
It is triggered by valve MB5 and completed when sensor BG5 (top position) fires.
This movement occurs twice per drill cycle (Program 3, steps 5 and 7).

### Normal Operating Parameters
| Parameter | Value |
|---|---|
| Baseline ascent time | 260 ms |
| Warning threshold | 330 ms |
| Critical threshold | 420 ms |
| Timeout (alarm) | 20,000 ms |

### How Degradation Develops
As seals wear or guides become contaminated, exhaust air escapes more slowly, increasing
the time the piston takes to reach its end position. This manifests as a gradual upward
trend in ascent time across many cycles [Operating Manual, p.39, p.65–66]."""

    return {
        "Situation":              situation,
        "Root Cause Analysis":    root_cause,
        "Recommended Actions":    actions,
        "Machine Context":        context,
    }
