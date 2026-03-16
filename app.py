"""
CP-AM-DRILL Predictive Maintenance System
==========================================
Streamlit entry point. Handles session state initialisation and page routing.

Run with:
    streamlit run app.py
"""

import os
from dotenv import load_dotenv
import streamlit as st

# Load .env for local dev; Streamlit Cloud injects via st.secrets
load_dotenv()

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="CP-AM-DRILL Maintenance System",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Imports (after set_page_config) ───────────────────────────────────────────
from data.simulated_sensor_data import generate_sensor_data, compute_sensor_summary
from knowledge.document_index import load_chunks
from ui.hmi_screen import render_hmi_screen
from ui.report_dashboard import render_report_dashboard


# ── Session state initialisation ──────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "hmi"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "diagnostic_report" not in st.session_state:
    st.session_state.diagnostic_report = None

if "report_chunks" not in st.session_state:
    st.session_state.report_chunks = []

# Generate sensor data once per session
if "sensor_cycles" not in st.session_state:
    st.session_state.sensor_cycles = generate_sensor_data()

if "sensor_summary" not in st.session_state:
    st.session_state.sensor_summary = compute_sensor_summary(st.session_state.sensor_cycles)

# Load document chunks once per session
if "all_chunks" not in st.session_state:
    with st.spinner("Loading knowledge base..."):
        st.session_state.all_chunks = load_chunks()

# ── API key guard ──────────────────────────────────────────────────────────────
# Support both local .env and Streamlit Cloud secrets
if not os.getenv("ANTHROPIC_API_KEY"):
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your_api_key_here":
    st.error(
        "**API key not configured.** "
        "Please add your Anthropic API key to the `.env` file:\n\n"
        "```\nANTHROPIC_API_KEY=sk-ant-...\n```\n\n"
        "Then restart the app with `streamlit run app.py`."
    )
    st.stop()

# ── Page routing ───────────────────────────────────────────────────────────────
if st.session_state.page == "hmi":
    render_hmi_screen(st.session_state.sensor_summary)

elif st.session_state.page == "report":
    render_report_dashboard(
        sensor_summary=st.session_state.sensor_summary,
        cycles=st.session_state.sensor_cycles,
        all_chunks=st.session_state.all_chunks,
    )
