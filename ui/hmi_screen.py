"""
Festo-style HMI error screen (Page 1).

Mimics the real Festo CP-AM-DRILL HMI interface as seen in the operating manual
screenshots (Operating Manual, p.83-84) — dark header, blue branding, grey nav bar,
red error banner, and Repeat/Ignore/Abort action buttons.
"""

import streamlit as st
from datetime import datetime
from ui.styles import inject_css
from config import FESTO_COLORS


def render_hmi_screen(sensor_summary: dict) -> None:
    st.markdown(inject_css(), unsafe_allow_html=True)

    status = sensor_summary.get("status", "WARNING")
    current_ms = sensor_summary.get("current_avg_ms", 0)
    baseline_ms = sensor_summary.get("baseline_ms", 280)
    dev_pct = sensor_summary.get("deviation_pct", 0)

    # ── Header ──────────────────────────────────────────────────────────────
    now = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
<div class="festo-header">
  <div>
    <span class="brand">FESTO</span>
    <span style="color:#888; font-size:12px; margin-left:16px;">CP Lab &nbsp;|&nbsp; Drilling Station</span>
  </div>
  <div class="station-info">
    System – Diagnostics &nbsp;|&nbsp; Automatic mode<br>
    Default Mode &nbsp;|&nbsp; {now}
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Navigation bar ───────────────────────────────────────────────────────
    st.markdown("""
<div class="festo-nav">
  <span class="nav-item active">Home</span>
  <span class="nav-item">Setup mode</span>
  <span class="nav-item">Parameters</span>
  <span class="nav-item">System</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Error / Warning banner ───────────────────────────────────────────────
    if status == "CRITICAL":
        banner_class = "error-banner"
        status_label = "CRITICAL — Immediate shutdown recommended"
        icon = "CRITICAL ALERT"
    elif status == "WARNING":
        banner_class = "warning-banner"
        status_label = "WARNING — Performance degrading, action required"
        icon = "PREDICTIVE MAINTENANCE ALERT"
    else:
        banner_class = "ok-banner"
        status_label = "Normal operation"
        icon = "SYSTEM OK"

    st.markdown(f"""
<div class="{banner_class}">
  &#9608;&#9608; {icon} &#9608;&#9608;<br><br>
  Warning: Z-Axis ascent time degradation detected<br>
  Current: <strong>{current_ms} ms</strong> &nbsp;|&nbsp;
  Baseline: <strong>{baseline_ms} ms</strong> &nbsp;|&nbsp;
  Deviation: <strong>+{dev_pct}%</strong><br><br>
  Status: {status_label}
</div>
""", unsafe_allow_html=True)

    # ── HMI action rows (Repeat / Ignore / Abort) ────────────────────────────
    st.markdown("""
<div class="hmi-action-row">
  <span class="state-code">act. State code</span>
  <span class="state-value">1</span>
  <span style="color:#555;">Class 0 alarm — predictive threshold exceeded</span>
</div>
<div class="hmi-action-row">
  <span class="state-code">State after Ignore</span>
  <span class="state-value">2</span>
  <span style="color:#555;">Continue automatic mode — monitoring active</span>
</div>
<div class="hmi-action-row">
  <span class="state-code">State after Abort</span>
  <span class="state-value">0</span>
  <span style="color:#555;">Terminate automatic mode</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Action buttons ────────────────────────────────────────────────────────
    col1, col2, col3, col_space, col4 = st.columns([1, 1, 1, 0.5, 2])

    with col1:
        if st.button("Repeat", key="btn_repeat", use_container_width=True):
            st.info("Retrying last operation...")

    with col2:
        if st.button("Ignore", key="btn_ignore", use_container_width=True):
            st.info("Alert acknowledged. Monitoring continues.")

    with col3:
        if st.button("Abort", key="btn_abort", use_container_width=True):
            st.warning("Automatic mode terminated.")

    with col4:
        # Primary action — navigate to the diagnostic report page
        if st.button(
            "Interactive Diagnostic Report",
            key="btn_diagnostic",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.page = "report"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Real-time axis status mini-panel ──────────────────────────────────────
    with st.expander("Live Axis Status", expanded=True):
        axes = [
            ("Z-Axis Ascent (anomaly)", current_ms, 330, 420, status),
            ("Z-Axis Descent", sensor_summary["other_axes_status"]["z_axis_descend"]["current_avg_ms"], 360, 450, "NORMAL"),
            ("X-Axis Left",  sensor_summary["other_axes_status"]["x_axis_left"]["current_avg_ms"],  455, 560, "NORMAL"),
            ("X-Axis Right", sensor_summary["other_axes_status"]["x_axis_right"]["current_avg_ms"], 455, 560, "NORMAL"),
        ]
        for label, val, warn, crit, ax_status in axes:
            tag_class = (
                "status-critical" if ax_status == "CRITICAL"
                else "status-warning" if ax_status == "WARNING"
                else "status-normal"
            )
            total = crit * 1.10
            green_pct  = warn / total * 100
            yellow_pct = (crit - warn) / total * 100
            red_pct    = 100 - green_pct - yellow_pct
            marker_pct = min(val / total * 100, 99.5)

            bar_html = f"""
<div style="position:relative; height:18px; border-radius:4px; overflow:visible; background:#e0e0e0; margin:6px 0;">
  <div style="position:absolute; left:0; top:0; height:100%;
              width:{green_pct:.2f}%; background:#4CAF50; border-radius:4px 0 0 4px;"></div>
  <div style="position:absolute; left:{green_pct:.2f}%; top:0; height:100%;
              width:{yellow_pct:.2f}%; background:#FFC107;"></div>
  <div style="position:absolute; left:{green_pct + yellow_pct:.2f}%; top:0; height:100%;
              width:{red_pct:.2f}%; background:#E53935; border-radius:0 4px 4px 0;"></div>
  <div style="position:absolute; left:{marker_pct:.2f}%; top:-3px; height:calc(100% + 6px);
              width:3px; background:white; border:1px solid #333; border-radius:2px; z-index:10;"></div>
</div>
"""
            col_a, col_b, col_c = st.columns([3, 5, 1])
            col_a.markdown(f"<small>{label}</small>", unsafe_allow_html=True)
            col_b.markdown(bar_html, unsafe_allow_html=True)
            col_c.markdown(
                f'<span class="{tag_class}">{val} ms</span>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Exit button ───────────────────────────────────────────────────────────
    if st.button("Exit System", key="btn_exit_hmi"):
        st.markdown(
            '<div class="ok-banner">System exited. You may close this window.</div>',
            unsafe_allow_html=True,
        )
        st.stop()
