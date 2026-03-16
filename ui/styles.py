"""
Custom CSS for the Festo CP-AM-DRILL HMI interface.
Matches the Festo colour palette and layout from the HMI screenshots.
"""

FESTO_CSS = """
<style>
/* ── Global reset / font ───────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* ── Festo header bar ──────────────────────────────────────── */
.festo-header {
    background-color: #2C2C2C;
    color: white;
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 3px solid #0091DC;
    margin-bottom: 0;
}
.festo-header .brand {
    font-size: 22px;
    font-weight: 700;
    color: #0091DC;
    letter-spacing: 2px;
}
.festo-header .station-info {
    font-size: 13px;
    color: #CCCCCC;
    text-align: right;
    line-height: 1.4;
}

/* ── Navigation bar ────────────────────────────────────────── */
.festo-nav {
    background-color: #E8E8E8;
    border-bottom: 2px solid #CCCCCC;
    padding: 6px 20px;
    display: flex;
    gap: 2px;
    margin-bottom: 0;
}
.festo-nav .nav-item {
    padding: 5px 16px;
    font-size: 13px;
    border: 1px solid #BBBBBB;
    background-color: #F5F5F5;
    cursor: default;
    color: #333333;
}
.festo-nav .nav-item.active {
    background-color: #0091DC;
    color: white;
    border-color: #0091DC;
}

/* ── Error / Warning banner ────────────────────────────────── */
.error-banner {
    background-color: #E53935;
    color: white;
    padding: 18px 24px;
    margin: 20px 0;
    font-weight: 700;
    font-size: 16px;
    border-left: 6px solid #B71C1C;
}
.warning-banner {
    background-color: #FFC107;
    color: #333333;
    padding: 18px 24px;
    margin: 20px 0;
    font-weight: 700;
    font-size: 16px;
    border-left: 6px solid #F57F17;
}
.ok-banner {
    background-color: #4CAF50;
    color: white;
    padding: 18px 24px;
    margin: 20px 0;
    font-weight: 700;
    font-size: 16px;
    border-left: 6px solid #1B5E20;
}

/* ── HMI action row ────────────────────────────────────────── */
.hmi-action-row {
    display: flex;
    align-items: center;
    padding: 8px 24px;
    border-bottom: 1px solid #DDDDDD;
    background-color: #F9F9F9;
    font-size: 13px;
    color: #555555;
}
.hmi-action-row .state-code {
    width: 120px;
}
.hmi-action-row .state-value {
    width: 50px;
    text-align: center;
    background-color: #EEEEEE;
    border: 1px solid #BBBBBB;
    padding: 2px 8px;
    margin-right: 20px;
    font-family: monospace;
}

/* ── Status indicator tags ─────────────────────────────────── */
.status-warning {
    background-color: #FFF3CD;
    color: #856404;
    padding: 2px 10px;
    border-radius: 3px;
    font-weight: 600;
    font-size: 12px;
}
.status-critical {
    background-color: #F8D7DA;
    color: #721C24;
    padding: 2px 10px;
    border-radius: 3px;
    font-weight: 600;
    font-size: 12px;
}
.status-normal {
    background-color: #D4EDDA;
    color: #155724;
    padding: 2px 10px;
    border-radius: 3px;
    font-weight: 600;
    font-size: 12px;
}

/* ── Progress bar labels ───────────────────────────────────── */
.axis-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    font-size: 13px;
}
.axis-label {
    width: 220px;
    color: #333333;
}
.axis-value {
    width: 70px;
    text-align: right;
    font-family: monospace;
    font-weight: 600;
}

/* ── Report card ───────────────────────────────────────────── */
.report-card {
    background-color: #FFFFFF;
    border: 1px solid #DDDDDD;
    border-top: 4px solid #0091DC;
    padding: 24px;
    margin: 16px 0;
    border-radius: 2px;
}

/* ── Dashboard page header ─────────────────────────────────── */
.dashboard-header {
    background-color: #003A5D;
    color: white;
    padding: 14px 24px;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 20px;
}

/* ── Hide Streamlit default menu / footer ──────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""


def inject_css() -> str:
    return FESTO_CSS
