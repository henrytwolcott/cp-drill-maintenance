"""
Diagnostic report + interactive chatbot dashboard (Page 2).

Shows:
  1. Plotly trend chart of Z-axis ascent times with threshold lines
  2. All-axes status bars
  3. AI-generated diagnostic report (markdown)
  4. Interactive maintenance chatbot (Claude Sonnet 4.6)
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from ui.styles import inject_css
from ai.report_generator import generate_diagnostic_report
from ai.chatbot import get_chatbot_response
from knowledge.document_index import retrieve_chunks


# ── Trend chart ────────────────────────────────────────────────────────────────

def _build_trend_chart(cycles: list[dict]) -> go.Figure:
    xs = [c["cycle_id"] for c in cycles]
    ys = [c["z_ascend_ms"] for c in cycles]

    fig = go.Figure()

    # Raw data scatter
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers",
        marker=dict(size=3, color="#0091DC", opacity=0.5),
        name="Z-Axis Ascent (ms)",
        hovertemplate="Cycle %{x}<br>%{y} ms<extra></extra>",
    ))

    # Rolling average (20-cycle window)
    window = 20
    rolling = []
    for i in range(len(ys)):
        start = max(0, i - window + 1)
        rolling.append(sum(ys[start:i + 1]) / (i - start + 1))

    fig.add_trace(go.Scatter(
        x=xs, y=rolling,
        mode="lines",
        line=dict(color="#003A5D", width=2),
        name="20-cycle rolling average",
    ))

    # Threshold lines
    fig.add_hline(y=330, line_dash="dash", line_color="#FFC107", line_width=1.5,
                  annotation_text="Warning 330 ms", annotation_position="top right")
    fig.add_hline(y=420, line_dash="dash", line_color="#E53935", line_width=1.5,
                  annotation_text="Critical 420 ms", annotation_position="top right")
    fig.add_hline(y=260, line_dash="dot", line_color="#4CAF50", line_width=1,
                  annotation_text="Baseline 260 ms", annotation_position="bottom right")

    fig.update_layout(
        title="Z-Axis Ascent Time — 500 Production Cycles",
        xaxis_title="Cycle Number",
        yaxis_title="Actuation Time (ms)",
        height=360,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F9F9F9",
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ── Axes overview ──────────────────────────────────────────────────────────────

def _render_axes_overview(sensor_summary: dict) -> None:
    st.markdown("#### All-Axes Status")

    axes = [
        {
            "label":    "Z-Axis Ascent (anomaly)",
            "val":      sensor_summary["current_avg_ms"],
            "baseline": sensor_summary["baseline_ms"],
            "crit":     sensor_summary["critical_threshold_ms"],
            "status":   sensor_summary["status"],
        },
        {
            "label":    "Z-Axis Descent",
            "val":      sensor_summary["other_axes_status"]["z_axis_descend"]["current_avg_ms"],
            "baseline": 280,
            "crit":     450,
            "status":   "NORMAL",
        },
        {
            "label":    "X-Axis Left",
            "val":      sensor_summary["other_axes_status"]["x_axis_left"]["current_avg_ms"],
            "baseline": 350,
            "crit":     560,
            "status":   "NORMAL",
        },
        {
            "label":    "X-Axis Right",
            "val":      sensor_summary["other_axes_status"]["x_axis_right"]["current_avg_ms"],
            "baseline": 350,
            "crit":     560,
            "status":   "NORMAL",
        },
    ]

    with st.container():
        for ax in axes:
            frac = min(ax["val"] / ax["crit"], 1.0)
            if ax["status"] == "CRITICAL":
                colour = "#E53935"
                badge = "🔴 CRITICAL"
            elif ax["status"] == "WARNING":
                colour = "#FFC107"
                badge = "🟡 WARNING"
            else:
                colour = "#4CAF50"
                badge = "🟢 NORMAL"

            c1, c2, c3, c4 = st.columns([3, 4, 1.5, 1.5])
            c1.markdown(f"<small><b>{ax['label']}</b></small>", unsafe_allow_html=True)
            c2.progress(frac)
            c3.markdown(
                f"<span style='font-family:monospace;font-weight:600;'>{ax['val']} ms</span>",
                unsafe_allow_html=True,
            )
            c4.markdown(badge)


# ── Main render ────────────────────────────────────────────────────────────────

def render_report_dashboard(sensor_summary: dict, cycles: list[dict], all_chunks: list[dict]) -> None:
    st.markdown(inject_css(), unsafe_allow_html=True)

    # ── Dashboard header ───────────────────────────────────────────────────────
    st.markdown("""
<div class="dashboard-header">
  CP-AM-DRILL &nbsp;|&nbsp; Predictive Maintenance Dashboard
</div>
""", unsafe_allow_html=True)

    # ── Navigation ─────────────────────────────────────────────────────────────
    col_back, col_exit = st.columns([1, 8])
    with col_back:
        if st.button("Back to HMI", key="btn_back"):
            st.session_state.page = "hmi"
            st.rerun()
    with col_exit:
        if st.button("Exit System", key="btn_exit_dash"):
            st.markdown(
                '<div class="ok-banner">System exited. You may close this window.</div>',
                unsafe_allow_html=True,
            )
            st.stop()

    st.markdown("---")

    # ── Trend chart ────────────────────────────────────────────────────────────
    st.plotly_chart(_build_trend_chart(cycles), use_container_width=True)

    # ── Axes overview ──────────────────────────────────────────────────────────
    _render_axes_overview(sensor_summary)

    st.markdown("---")

    # ── AI Diagnostic Report ───────────────────────────────────────────────────
    st.markdown("### AI Diagnostic Report")

    if st.session_state.get("diagnostic_report") is None:
        with st.spinner("Generating AI diagnostic report..."):
            relevant_chunks = retrieve_chunks(
                "Z-axis ascent degradation flow control valve seal pneumatic", all_chunks, top_k=10
            )
            report = generate_diagnostic_report(sensor_summary, relevant_chunks)
            st.session_state.diagnostic_report = report
            st.session_state.report_chunks = relevant_chunks

    # Status badge above tabs
    report = st.session_state.diagnostic_report or {}
    _status = sensor_summary.get("status", "NORMAL")
    if _status == "CRITICAL":
        st.error(f"**{_status}** — Z-Axis Ascent | {sensor_summary['current_avg_ms']} ms | "
                 f"+{sensor_summary['deviation_ms']} ms above baseline", icon="🔴")
    elif _status == "WARNING":
        st.warning(f"**{_status}** — Z-Axis Ascent | {sensor_summary['current_avg_ms']} ms | "
                   f"+{sensor_summary['deviation_ms']} ms above baseline", icon="🟡")
    else:
        st.success(f"**{_status}** — Z-Axis Ascent | {sensor_summary['current_avg_ms']} ms", icon="🟢")

    # Tabbed report sections
    tab_labels = ["Situation", "Root Cause Analysis", "Recommended Actions", "Machine Context"]
    tabs = st.tabs(tab_labels)
    for tab, label in zip(tabs, tab_labels):
        with tab:
            section_content = report.get(label, "") if isinstance(report, dict) else report
            with st.container(border=True):
                st.markdown(section_content)

    # ── AI Disclaimer ──────────────────────────────────────────────────────────
    st.warning(
        "**AI-generated content — please verify before acting.** "
        "This report is produced by a large language model and may contain inaccuracies or hallucinations. "
        "Always consult the original Festo documentation and qualified engineering staff before performing "
        "any maintenance, adjustments, or component replacements.",
        icon="⚠️",
    )

    # ── Transparency expanders ─────────────────────────────────────────────────
    with st.expander("Sources Used (documentation chunks fed to AI)"):
        chunks = st.session_state.get("report_chunks", [])
        if chunks:
            seen = set()
            for c in chunks:
                key = (c["doc_name"], c["page"])
                if key not in seen:
                    seen.add(key)
                    st.markdown(f"- **{c['doc_name']}** — Page {c['page']}")
        else:
            st.caption("No source information available.")

    with st.expander("Raw Sensor Summary (computed — not AI-generated)"):
        s = sensor_summary
        sl = s["component_service_log"]
        other = s["other_axes_status"]

        st.markdown("**Anomaly Axis**")
        col_a, col_b = st.columns(2)
        col_a.metric("Current Avg (last 10 cycles)", f"{s['current_avg_ms']} ms")
        col_b.metric("Baseline", f"{s['baseline_ms']} ms")
        col_a.metric("Deviation", f"+{s['deviation_ms']} ms ({s['deviation_pct']}%)")
        col_b.metric("Status", s["status"])
        col_a.metric("Warning Threshold", f"{s['warning_threshold_ms']} ms")
        col_b.metric("Critical Threshold", f"{s['critical_threshold_ms']} ms")

        st.markdown("**Trend**")
        col_c, col_d = st.columns(2)
        col_c.metric("Drift Started", s["trend_start_date"])
        col_d.metric("Trend Duration", f"{s['trend_duration_days']} days")
        col_c.metric("Degradation Rate", f"{s['degradation_rate_ms_per_day']} ms/day")
        col_d.metric("Est. Days to Critical", str(s["estimated_days_to_critical"]))

        st.markdown("**Last 10 Readings (ms)**")
        st.code(", ".join(str(v) for v in s["last_10_readings"]))

        st.markdown("**Component Service Log**")
        for comp, data in sl.items():
            replaced_key = "last_replaced" if "last_replaced" in data else "last_serviced"
            interval_key = "service_interval_cycles"
            cycles_key   = "cycles_since_replacement" if "cycles_since_replacement" in data else "cycles_since_service"
            overdue = "🔴 OVERDUE" if data.get("interval_exceeded") else "🟢 OK"
            st.markdown(
                f"- **{comp.replace('_', ' ').title()}**: "
                f"last serviced {data[replaced_key]}, "
                f"{data[cycles_key]:,} cycles ago "
                f"(interval: {data[interval_key]:,}) — {overdue}"
            )

        st.markdown("**Other Axes (last 10-cycle avg)**")
        for axis, data in other.items():
            st.markdown(
                f"- **{axis.replace('_', ' ').title()}**: "
                f"{data['current_avg_ms']} ms (baseline {data['baseline_ms']} ms) — {data['status']}"
            )

    st.markdown("---")

    # ── Interactive Chatbot ────────────────────────────────────────────────────
    st.markdown("### Maintenance Assistant")
    st.caption("Ask any question about the diagnosis or maintenance procedures. "
               "All answers are referenced to the Festo documentation.")

    # Render existing conversation history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask about the diagnosis, components, or maintenance steps...")

    if user_input:
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add to history before API call
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Flatten the report dict to a single string for the chatbot context
                _report = st.session_state.diagnostic_report or {}
                _report_str = (
                    "\n\n".join(f"### {k}\n{v}" for k, v in _report.items())
                    if isinstance(_report, dict) else _report
                )
                response = get_chatbot_response(
                    user_message=user_input,
                    conversation_history=st.session_state.chat_history[:-1],  # exclude current user msg
                    diagnostic_report=_report_str,
                    all_chunks=all_chunks,
                )
            st.markdown(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("Clear conversation", key="btn_clear_chat"):
            st.session_state.chat_history = []
            st.rerun()


def _md_to_safe(text: str) -> str:
    """
    Pass markdown through for st.markdown rendering inside a div.
    Streamlit's markdown renderer handles this correctly when unsafe_allow_html=True.
    We just need to escape any literal HTML angle brackets in the text itself.
    Actually — Streamlit renders markdown in its own container, so we render the
    report separately with st.markdown rather than embedding in a div.
    This helper is kept for future use; the actual render uses st.markdown directly.
    """
    return text
