# CP-AM-DRILL Predictive Maintenance AI System — Complete Implementation Plan

## For: Deloitte Smart Factory Interview Demo (Data & AI Intern Position)
## Stack: Streamlit + Claude Sonnet 4.6 API + Python
## Timeline: ~1.5 days

---

## 1. PROJECT OVERVIEW & BUSINESS CONTEXT

### 1.1 What This System Does
An AI-powered predictive maintenance assistant for the Festo CP-AM-DRILL station that:
1. **Detects pneumatic degradation** by monitoring drift in actuation cycle times (Z-axis vertical movement, X-axis horizontal movement, clamping unit)
2. **Displays a Festo-style HMI error screen** when anomalies are detected
3. **Auto-generates a diagnostic report** using Claude AI, summarizing current readings, trends, severity, and recommended actions
4. **Provides an interactive chatbot** grounded in the Festo documentation (operating manual, maintenance manual, circuit diagrams) so operators can ask follow-up questions — every piece of advice is referenced to a specific document and page number

### 1.2 Who Uses It
- **Machine Operator**: Gets an immediate, plain-language alert and recommended first actions without needing to read hundreds of pages of manuals
- **Maintenance Technician**: Gets a detailed diagnostic report with severity assessment, degradation speed, and traceable references to the correct manual sections for each recommendation

### 1.3 Business Value (for the 2-minute pitch)
- Unplanned downtime on a production line costs **$10,000–$50,000+ per hour** at scale (automotive/electronics). Apple's iPhone line reportedly costs ~$1.8M/hour in lost revenue during outages.
- Predictive maintenance reduces unplanned downtime by **30–50%** and extends equipment life by **20–40%** (McKinsey, Deloitte Analytics Institute).
- This demo shows how **generative AI augments** the maintenance workflow: instead of reactive "machine broke → read 200-page manual → guess," it becomes "AI detects drift → generates diagnosis → operator confirms and acts."

### 1.4 The "Theatre" (for the 3-minute demo pitch)
**Scene**: Visitors walk up to the CP-AM-DRILL station. The drill is running normally. Then the demo operator triggers a simulated anomaly (e.g., the Z-axis descent time has been gradually increasing). The Festo-style HMI screen turns red with an interactive error message. The operator presses "Interactive Diagnostic Report." A modern dashboard loads showing the AI-generated report with charts of the timing drift. Below the report, a chatbot is ready. The operator asks: "What could cause the Z-axis to slow down?" — the AI responds with specific, referenced advice from the Festo manuals. Visitors see the full loop: detect → diagnose → advise → act.

---

## 2. SYSTEM ARCHITECTURE (High-Level)

```
┌─────────────────────────────────────────────────────────┐
│                   STREAMLIT APPLICATION                   │
│                                                           │
│  ┌─────────────────────┐   ┌──────────────────────────┐  │
│  │   PAGE 1: FESTO HMI │   │ PAGE 2: DIAGNOSTIC       │  │
│  │   Error Screen       │──▶│ Report + Chatbot         │  │
│  │   (Mimics real UI)   │   │                          │  │
│  │                      │   │ ┌──────────────────────┐ │  │
│  │  [Interactive        │   │ │ AI-Generated Report  │ │  │
│  │   Diagnostic Report] │   │ │ (timing data, trends │ │  │
│  │                      │   │ │  severity, actions)  │ │  │
│  │  [Repeat][Ignore]    │   │ └──────────────────────┘ │  │
│  │  [Abort] [Exit]      │   │ ┌──────────────────────┐ │  │
│  └─────────────────────┘   │ │ Chatbot Interface    │ │  │
│                             │ │ (Claude Sonnet 4.6)  │ │  │
│                             │ │ + Document Context   │ │  │
│                             │ └──────────────────────┘ │  │
│                             │  [Back to HMI] [Exit]    │  │
│                             └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌────────────┐ ┌───────────┐ ┌─────────────┐
   │ Simulated  │ │ Document  │ │ Claude      │
   │ Sensor     │ │ Knowledge │ │ Sonnet 4.6  │
   │ Data       │ │ Base      │ │ API         │
   │ (Python)   │ │ (indexed  │ │             │
   │            │ │  chunks)  │ │             │
   └────────────┘ └───────────┘ └─────────────┘
```

### Future Cloud Architecture (mention in interview)
- **Data ingestion**: PLC → OPC-UA/MQTT → AWS IoT Core → Kinesis
- **Storage**: S3 (raw) → Databricks (processing/feature engineering)
- **Model**: Anomaly detection on Databricks, Claude API for report gen
- **Serving**: Streamlit on EC2/ECS or a proper dashboard
- **This prototype**: Everything local, simulated data, Claude API only

---

## 3. DETAILED TECHNICAL SPECIFICATION

### 3.1 Project File Structure

```
cp-drill-maintenance/
├── app.py                          # Main Streamlit app (entry point)
├── pages/
│   (not used — we use session_state for page routing)
├── config.py                       # Constants, thresholds, styling
├── data/
│   ├── simulated_sensor_data.py    # Generates fake but realistic pneumatic timing data
│   └── documents/                  # Copied .txt files from the manuals
│       ├── operating_manual.txt
│       ├── maintenance_manual.txt
│       └── circuit_diagrams.txt
├── knowledge/
│   ├── document_index.py           # Chunk + index the documents with page refs
│   └── chunks.json                 # Pre-built chunks (generated once)
├── ai/
│   ├── report_generator.py         # Claude API call to generate diagnostic report
│   ├── chatbot.py                  # Claude API chatbot with document context
│   └── prompts.py                  # All system prompts (CRITICAL FILE)
├── ui/
│   ├── hmi_screen.py               # Festo-style HMI error page
│   ├── report_dashboard.py         # Diagnostic report display
│   └── styles.py                   # Custom CSS for Festo look
├── requirements.txt
├── .env                            # ANTHROPIC_API_KEY
└── README.md
```

### 3.2 File-by-File Specification

---

#### `config.py` — Constants and Thresholds

```python
# Festo CP-AM-DRILL Pneumatic Timing Thresholds
# These are derived from the operating manual flow chart timings and typical pneumatic specs

# Normal operating ranges (milliseconds)
THRESHOLDS = {
    "z_axis_descend": {
        "baseline_ms": 280,          # Normal time for Z-axis to go from BG5 (top) to BG6 (bottom)
        "warning_ms": 350,           # Yellow alert — 25% slower
        "critical_ms": 450,          # Red alert — 60% slower
        "timeout_ms": 20000,         # Festo system timeout (from message texts: 20000ms)
        "sensor_start": "VN_BG5",    # Z-axis upper end position sensor
        "sensor_end": "VN_BG6",      # Z-axis lower end position sensor
        "valve_activate": "MB6",     # Move Z-axis downwards
        "valve_deactivate": "MB5",   # Move Z-axis upwards (reset)
        "description": "Z-Axis Descent (Drill Down)",
    },
    "z_axis_ascend": {
        "baseline_ms": 260,
        "warning_ms": 330,
        "critical_ms": 420,
        "timeout_ms": 20000,
        "sensor_start": "VN_BG6",
        "sensor_end": "VN_BG5",
        "valve_activate": "MB5",
        "valve_deactivate": "MB6",
        "description": "Z-Axis Ascent (Drill Up)",
    },
    "x_axis_left": {
        "baseline_ms": 350,          # Normal time for X-axis to reach BG1 (left end)
        "warning_ms": 440,
        "critical_ms": 560,
        "timeout_ms": 20000,
        "sensor_start": "VN_BG2",
        "sensor_end": "VN_BG1",
        "valve_activate": "MB1",
        "valve_deactivate": "MB2",
        "description": "X-Axis Move Left",
    },
    "x_axis_right": {
        "baseline_ms": 350,
        "warning_ms": 440,
        "critical_ms": 560,
        "timeout_ms": 20000,
        "sensor_start": "VN_BG1",
        "sensor_end": "VN_BG2",
        "valve_activate": "MB2",
        "valve_deactivate": "MB1",
        "description": "X-Axis Move Right",
    },
    "clamp_activate": {
        "baseline_ms": 150,
        "warning_ms": 200,
        "critical_ms": 300,
        "timeout_ms": 20000,
        "valve_activate": "MB7",
        "description": "Z-Axis Clamp Open",
    },
}

# Festo colour palette (from HMI screenshots)
FESTO_COLORS = {
    "primary_blue": "#0091DC",
    "dark_blue": "#003A5D",
    "header_bg": "#2C2C2C",
    "error_red": "#E53935",
    "warning_yellow": "#FFC107",
    "ok_green": "#4CAF50",
    "bg_light": "#F5F5F5",
    "text_dark": "#333333",
    "border_grey": "#CCCCCC",
}

# System component reference (from spare parts list, Operating Manual p.85)
COMPONENTS = {
    "z_axis_cylinder": {
        "name": "Z-axis mini slide",
        "part_number": "DGSL-10-40-E3-Y3A",
        "festo_id": "543905",
    },
    "x_axis_cylinder": {
        "name": "X-axis linear drive",
        "part_number": "DGC-12-120-KF-YSR-A",
        "festo_id": "530907",
    },
    "flow_control_valve": {
        "name": "One-way flow control valve",
        "part_number": "GRLA-M5-QS-3-LF-C",
        "festo_id": "175053",
    },
    "solenoid_valve": {
        "name": "Valve CPVSC1-K-M5C",
        "part_number": "CPVSC1-K-M5C",
        "festo_id": "548899",
    },
}
```

---

#### `data/simulated_sensor_data.py` — Simulated Pneumatic Timing Data

This module generates **realistic fake data** that simulates a gradual degradation pattern. For the prototype, we pre-generate this data. In production, this would come from MES4 event timestamps or a PLC data logger.

**What to generate:**
- A time series of ~500 drill cycles over the past 2 weeks (hypothetical)
- Each cycle record contains timestamps for: Z-descend time, Z-ascend time, X-left time, X-right time, clamp time
- **The Z-axis descent should show a clear upward drift** (getting slower) starting about 4 days ago — this is the anomaly
- Other axes should show normal variance
- Include cycle number, datetime stamp, and all 5 timing values

**Data structure (list of dicts):**
```python
{
    "cycle_id": 487,
    "timestamp": "2026-03-15T09:42:31",
    "z_descend_ms": 385,       # <-- This one is drifting up (ANOMALY)
    "z_ascend_ms": 262,
    "x_left_ms": 348,
    "x_right_ms": 355,
    "clamp_ms": 152,
    "drill_program": 3,        # 1=left, 2=right, 3=both
}
```

**Degradation pattern for Z-axis descent:**
- Cycles 1-350: Normal, ~280ms ± 15ms random noise
- Cycles 350-450: Gradual increase, linear drift from 280 to 360ms + noise
- Cycles 450-500: Steeper increase, 360 to 410ms + noise
- Latest reading: ~405ms (above warning threshold of 350ms, approaching critical at 450ms)

**Defence for interview**: "MES4 already captures timestamped events across the station. Depending on logging granularity, we can derive pneumatic actuation times directly. If not, we augment with a lightweight data logger tapping the PLC's I/O register via its existing OPC-UA interface — no physical sensor installation required, just a software connection to the ET200 SP."

---

#### `knowledge/document_index.py` — Document Chunking (Simple, No Vector DB)

Since the document corpus is small (~3 files, ~15,000 words total), we do NOT need a vector database or embeddings-based RAG for this prototype. Instead:

1. **Parse each .txt file** into chunks by page (pages are already delimited by `--- Page N ---`)
2. **Each chunk** = one page of content, tagged with:
   - `doc_name`: "Operating Manual" / "Maintenance Manual" / "Circuit Diagrams"
   - `page_number`: integer
   - `content`: the text
   - `keywords`: extracted key terms for simple keyword matching (optional but nice)
3. **Store as a list of dicts** in `chunks.json`
4. **For retrieval**: Given a user query or a detected anomaly, select the most relevant chunks by keyword matching and pass them into the Claude API context window along with the query

**Chunk format:**
```python
{
    "id": "op_manual_p38",
    "doc_name": "CP-AM-DRILL Operating Manual",
    "doc_short": "Operating Manual",
    "page": 38,
    "content": "6.3.2 Pneumatic\nValve terminal CPVSC1 / part number 525675...",
    "section": "6.3.2 Pneumatic"
}
```

**Key pages to definitely include (pre-identified):**

| Page | Document | Content | Why Relevant |
|------|----------|---------|--------------|
| 38-39 | Operating Manual | Pneumatic valve terminal, axes, flow control valves | Core component reference |
| 40 | Operating Manual | Function description of drilling process | Process understanding |
| 41-42 | Operating Manual | Process description with step-by-step procedure | Sequence understanding |
| 44 | Operating Manual | I/O module XD1 — all sensor/actuator mappings | Sensor identification |
| 61-64 | Operating Manual | Proximity sensor adjustment (X-axis and Z-axis) | Sensor calibration procedures |
| 65-66 | Operating Manual | One-way flow control valve adjustment | Flow control troubleshooting |
| 73-79 | Operating Manual | Flow chart with all states and transitions | PLC logic reference |
| 82 | Operating Manual | Message texts — all alarm codes | Error code reference |
| 83-84 | Operating Manual | Interactive error messages — Repeat/Ignore/Abort | Error handling procedures |
| 85 | Operating Manual | Spare parts list (electric + pneumatic) | Part numbers for ordering |
| 86 | Operating Manual | Service and cleaning instructions | Maintenance procedures |
| 5 | Maintenance Manual | Visual inspection checklist | Daily inspection tasks |
| 6 | Maintenance Manual | Safety checklist — emergency stop, safety sensors | Monthly safety checks |
| 7-8 | Maintenance Manual | Components checklist — conveyor belts, stoppers, linear axes, fans | Scheduled maintenance intervals |
| 16-17 | Circuit Diagrams | Pneumatic circuit — valve connections, flow control | Pneumatic troubleshooting |

**For the chatbot**: When the user asks a question, we do simple keyword matching to find the top 5-8 most relevant chunks and inject them into the Claude prompt as context. This is a lightweight alternative to full RAG — mention in the interview that "in production, we would use an embeddings-based retrieval system (e.g., Amazon Bedrock Knowledge Bases or Databricks Vector Search) for better semantic matching across larger document sets."

---

#### `ai/prompts.py` — System Prompts (CRITICAL)

This file contains all the prompts that give the AI system its "understanding" of the Festo CP-AM-DRILL context.

**PROMPT 1: `SYSTEM_CONTEXT` — Shared context for all AI calls**

```
You are an AI maintenance assistant for the Festo CP-AM-DRILL drilling station, 
part of a CP Factory / CP Lab system used in manufacturing environments.

SYSTEM OVERVIEW:
The CP-AM-DRILL is an application module that drills 4 holes into the lower part 
of a housing component. It has two pneumatic axes:
- X-axis: Moves the drill unit left/right using a linear drive (DGC-12-120-KF-YSR-A, 
  Part #530907). Controlled by valves MB1 (left) and MB2 (right). End position 
  sensors: BG1 (left) and BG2 (right). Uses proximity sensors SMT-10M (Part #551373).
- Z-axis: Moves the drill unit up/down using a mini slide (DGSL-10-40-E3-Y3A, 
  Part #543905). Controlled by valves MB5 (up) and MB6 (down). End position 
  sensors: BG5 (top) and BG6 (bottom). Uses proximity sensors SMT-10M (Part #551373).
- Clamping unit: Integrated with Z-axis mini slide, controlled by valve MB7.
- All valves are CPVSC1-K-M5C (Part #548899) on a CPVSC1 valve terminal.
- Flow control: One-way flow control valves GRLA-M5-QS-3-LF-C (Part #175053) 
  regulate exhaust air speed on both axes.

DRILL PROCESS (Program 3 — Both Sides):
1. Carrier with workpiece arrives and is stopped
2. Workpiece check (front cover present, correct orientation, no back cover)
3. Drills switch on (MA3, MA4), clamp opens (MB7)
4. X-axis moves left (MB1) → wait for BG1
5. Z-axis descends (MB6) → wait for BG6 → drill 1s → Z-axis ascends (MB5) → wait for BG5
6. X-axis moves right (MB2) → wait for BG2
7. Z-axis descends (MB6) → wait for BG6 → drill 1s → Z-axis ascends (MB5) → wait for BG5
8. X-axis returns left (MB1) → drills off → clamp closes → carrier released

ERROR HANDLING:
The system has a 20,000ms timeout on all actuator movements. If an end position 
sensor is not reached within this timeout, a Class 0 alarm is raised which 
immediately stops the program and terminates automatic mode.

PREDICTIVE MAINTENANCE APPROACH:
We monitor the time between valve activation and end-position sensor trigger for
each pneumatic movement. Gradual increases in these times indicate:
- Worn seals or O-rings in pneumatic cylinders
- Contamination or debris on linear guide rails
- Air leaks in pneumatic connections
- Degraded flow control valve performance
- Insufficient or fluctuating supply air pressure
- Sensor misalignment (proximity sensor drift)

COMPONENT SERVICE HISTORY:
You will be provided with a service log for each key component (seals, flow control valves,
linear guide lubrication, etc.), including the date last replaced/serviced, the number of
cycles accumulated since that service, and the manufacturer-recommended service interval.
Use this information when ranking root causes and forming recommendations:
- If a component's service interval has been exceeded AND the current sensor anomaly is
  consistent with that component's failure mode, rank it as the most likely cause.
- If a component's interval is approaching (within 10%), flag it as a preventive action
  even if it is not the primary suspect.
- Always note in the report whether service history supports or contradicts each hypothesis.

You must ONLY provide advice based on the documentation provided. Every recommendation
must include a reference in the format [Doc Name, p.XX]. Never invent procedures
not found in the documentation.
```

**PROMPT 2: `REPORT_GENERATION_PROMPT` — For generating the diagnostic report**

```
Based on the following sensor data summary, generate a structured diagnostic report.

FORMAT (follow exactly):
## Anomaly Detected: {axis/component name}

### Current Status
- Current average cycle time: {X} ms (last 10 cycles)
- Baseline cycle time: {X} ms  
- Deviation: +{X} ms ({X}% above baseline)
- Status: WARNING / CRITICAL

### Trend Analysis  
- The {component} cycle time has been increasing over the past {N} days
- Rate of degradation: approximately {X} ms/day
- At current rate, the system timeout ({timeout} ms) would be reached in approximately {N} days
- Immediate attention: {YES/NO}

### Component Service History
- {Component name}: last replaced {date} — {N} cycles ago (service interval: {N} cycles) — **OVERDUE / OK**
- {Component name}: last serviced {date} — {N} cycles ago (service interval: {N} cycles) — **OVERDUE / OK**
- Note any components where the service interval has been exceeded or is within 10% of the threshold.

### Possible Root Causes (ranked by likelihood)
When ranking causes, CROSS-REFERENCE the sensor trend data with the component service history above.
If a component's service interval is exceeded AND the anomaly pattern is consistent with that component's
known failure mode (e.g. worn seals → increasing actuation time on that axis), elevate that cause in the ranking.
1. {Cause} — {brief explanation, including whether service history supports this} [Doc Name, p.XX]
2. {Cause} — {brief explanation} [Doc Name, p.XX]
3. {Cause} — {brief explanation} [Doc Name, p.XX]

### Recommended Actions
1. **Immediate**: {action} [Doc Name, p.XX]
2. **Short-term (within 1 week)**: {action} [Doc Name, p.XX]
3. **Scheduled maintenance**: {action — if any components are overdue for service, flag them explicitly here} [Doc Name, p.XX]

### Component Reference
- Affected component: {name} (Part #{number}, Festo ID: {id})
- Related valves: {list with part numbers}
- Related sensors: {list with part numbers}

### Severity Assessment
- Severity: {LOW / MEDIUM / HIGH / CRITICAL}
- Estimated time to failure: {estimate}
- Production impact if unaddressed: {description}
```

**PROMPT 3: `CHATBOT_SYSTEM_PROMPT` — For the interactive chatbot**

```
You are a maintenance assistant chatbot for the Festo CP-AM-DRILL drilling station.

RULES:
1. ONLY answer based on the provided documentation and diagnostic report. 
   If the documentation does not contain the answer, say so explicitly.
2. Every factual claim or recommendation MUST end with a reference number in 
   parentheses, e.g., "Clean the linear guide rails with a dry cloth (1)". 
3. At the END of your response, list all references like:
   ---
   References:
   (1) Operating Manual, p.86
   (2) Maintenance Manual, p.7
4. Keep responses concise and actionable — operators are busy.
5. If the user asks about something outside the scope of the CP-AM-DRILL 
   documentation, politely redirect them to the relevant Festo support channel.
6. You have access to the current diagnostic report which shows the latest 
   sensor readings and anomaly analysis. Reference it when relevant.
7. Be precise with part numbers and component identifiers.
8. If a question requires physical intervention, always remind the operator 
   to follow safety procedures: switch off the station, disconnect power supply 
   [Maintenance Manual, p.4].

CONTEXT DOCUMENTS PROVIDED:
{inserted dynamically — relevant document chunks}

CURRENT DIAGNOSTIC REPORT:
{inserted dynamically — the generated report}
```

---

#### `ai/report_generator.py` — Diagnostic Report Generation

```python
import anthropic
from ai.prompts import SYSTEM_CONTEXT, REPORT_GENERATION_PROMPT

def generate_diagnostic_report(sensor_summary: dict, relevant_chunks: list[dict]) -> str:
    """
    Calls Claude Sonnet 4.6 to generate a diagnostic report.
    
    Args:
        sensor_summary: Dict with current readings, baselines, trends
        relevant_chunks: List of document chunks relevant to the anomaly
    
    Returns:
        Markdown-formatted diagnostic report string
    """
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    
    # Build the document context string
    doc_context = "\n\n".join([
        f"--- {c['doc_name']}, Page {c['page']} ---\n{c['content']}"
        for c in relevant_chunks
    ])
    
    user_message = f"""
    SENSOR DATA SUMMARY:
    {format_sensor_summary(sensor_summary)}
    
    RELEVANT DOCUMENTATION:
    {doc_context}
    
    Please generate the diagnostic report following the exact format specified.
    """
    
    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=2000,
        system=SYSTEM_CONTEXT + "\n\n" + REPORT_GENERATION_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    
    return response.content[0].text
```

**The `sensor_summary` dict structure** (pre-calculated from simulated data):

```python
{
    "anomaly_axis": "z_axis_descend",
    "anomaly_description": "Z-Axis Descent (Drill Down)",
    "current_avg_ms": 405,
    "baseline_ms": 280,
    "deviation_ms": 125,
    "deviation_pct": 44.6,
    "warning_threshold_ms": 350,
    "critical_threshold_ms": 450,
    "timeout_ms": 20000,
    "status": "WARNING",  # WARNING because 405 > 350 but < 450
    "trend_start_date": "2026-03-11",
    "trend_duration_days": 4,
    "degradation_rate_ms_per_day": 31.25,
    "estimated_days_to_critical": 1.4,
    "estimated_days_to_timeout": 628,  # very far for timeout but critical is imminent
    "last_10_readings": [398, 401, 405, 392, 410, 408, 403, 415, 399, 407],
    "last_maintenance_date": "2026-02-15",
    "total_cycles_since_maintenance": 487,
    "component_service_log": {
        # Per-component service history for wear-based diagnostics
        # Fields: last_replaced (date), cycles_since_replacement (int),
        #         service_interval_cycles (int from Festo spec), interval_exceeded (bool)
        #
        # ⚠️  PROTOTYPE NOTE — SIMULATED DATA:
        # The service interval values (service_interval_cycles) below are illustrative.
        # The CP-AM-DRILL Operating Manual states components are "maintenance-free" and
        # the Festo CP Maintenance Manual (2023) only specifies calendar-based tasks
        # (e.g. 3-week visual inspection of linear axes) — it does not publish cycle-count
        # thresholds for individual pneumatic components.
        #
        # In a real production deployment, these values would be sourced from:
        #   1. Festo component datasheets — individual product pages on festo.com for each
        #      part number (e.g. DGSL-10-40-E3-Y3A #543905, GRLA-M5-QS-3-LF-C #175053)
        #      publish endurance ratings and recommended service intervals.
        #   2. CMMS (Computerised Maintenance Management System) — e.g. SAP PM, IBM Maximo,
        #      or UpKeep. The CMMS holds the actual service log: who did what, when, and
        #      what parts were replaced. This is the authoritative source for last_replaced
        #      dates and cycles_since_replacement.
        #   3. MES4 / PLC cycle counters — the MES4 system or PLC can expose a running
        #      cycle count per station, allowing cycles_since_replacement to be computed
        #      automatically from the replacement event timestamp.
        #   4. OEM/manufacturer service bulletins — Festo and third-party seal suppliers
        #      sometimes publish application-specific service life guidance based on
        #      operating pressure, duty cycle, and ambient conditions.
        #
        # For interview: "In production we would pull service interval thresholds from
        # Festo's component datasheets and populate last-replaced dates from the CMMS.
        # The prototype uses representative values to demonstrate the diagnostic logic."
        "z_axis_seals": {
            "last_replaced": "2025-09-10",
            "cycles_since_replacement": 8420,
            "service_interval_cycles": 8000,   # Festo recommended interval
            "interval_exceeded": True,
        },
        "z_axis_flow_control_valve": {
            "last_replaced": "2025-09-10",
            "cycles_since_replacement": 8420,
            "service_interval_cycles": 12000,
            "interval_exceeded": False,
        },
        "linear_guide_lubrication": {
            "last_serviced": "2026-02-15",
            "cycles_since_service": 487,
            "service_interval_cycles": 2000,
            "interval_exceeded": False,
        },
        "x_axis_seals": {
            "last_replaced": "2025-09-10",
            "cycles_since_replacement": 8420,
            "service_interval_cycles": 8000,
            "interval_exceeded": True,
        },
    },
    "other_axes_status": {
        "z_axis_ascend": {"current_avg_ms": 262, "status": "NORMAL"},
        "x_axis_left": {"current_avg_ms": 348, "status": "NORMAL"},
        "x_axis_right": {"current_avg_ms": 355, "status": "NORMAL"},
        "clamp_activate": {"current_avg_ms": 152, "status": "NORMAL"},
    }
}
```

---

#### `ai/chatbot.py` — Interactive Chatbot

```python
def get_chatbot_response(
    user_message: str,
    conversation_history: list[dict],
    diagnostic_report: str,
    relevant_chunks: list[dict]
) -> str:
    """
    Calls Claude Sonnet 4.6 for chatbot responses with full context.
    
    Conversation history is maintained in Streamlit session_state.
    """
    client = anthropic.Anthropic()
    
    doc_context = "\n\n".join([
        f"--- {c['doc_name']}, Page {c['page']} ---\n{c['content']}"
        for c in relevant_chunks
    ])
    
    system_prompt = CHATBOT_SYSTEM_PROMPT.replace(
        "{inserted dynamically — relevant document chunks}", doc_context
    ).replace(
        "{inserted dynamically — the generated report}", diagnostic_report
    )
    
    messages = conversation_history + [{"role": "user", "content": user_message}]
    
    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=1500,
        system=SYSTEM_CONTEXT + "\n\n" + system_prompt,
        messages=messages
    )
    
    return response.content[0].text
```

**Memory**: Conversation history is stored in `st.session_state.chat_history` as a list of `{"role": "user"/"assistant", "content": "..."}` dicts. This is passed to each API call so Claude has full conversational context.

---

#### `ui/hmi_screen.py` — Festo-Style HMI Error Screen (Page 1)

This page mimics the real Festo HMI interface shown in the uploaded screenshots.

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  FESTO    System - Diagnostics       Automatic mode  │
│  CP Lab                              Default Mode    │
│  Drilling                            HH:MM:SS       │
│  Station                                             │
├──────────────────────────────────────────────────────┤
│  Home | Setup mode | Parameters | System             │
├──────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐  │
│  │  ██ PREDICTIVE MAINTENANCE ALERT ██            │  │  ← Red banner
│  │                                                │  │
│  │  Warning: Z-Axis descent time degradation      │  │
│  │  detected. Current: 405ms (Baseline: 280ms)    │  │
│  │                                                │  │
│  │  Status: WARNING — Performance degrading       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  act. State code    [  1  ]     [ Repeat         ] 1 │
│  State after Ignore [  2  ]     [ Ignore         ] 2 │
│  State after Abort  [  0  ]     [ Abort          ] 3 │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  🔍 Interactive Diagnostic Report              │  │  ← NEW BUTTON
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  [ Exit System ]                                     │
└──────────────────────────────────────────────────────┘
```

**Implementation notes:**
- Use `st.markdown()` with extensive custom CSS to match Festo colors (dark header bar, blue accents, grey background)
- The red error banner mimics the real "Interactive Error Message" popup from the manual (Operating Manual, p.83)
- The Repeat/Ignore/Abort buttons mirror the real HMI interface (see uploaded screenshot `1773605206806_image.png`)
- The **"Interactive Diagnostic Report"** button is the NEW addition — it navigates to Page 2
- Use `st.session_state.page = "report"` for navigation

**CSS approach:**
```css
/* Match Festo HMI styling */
.festo-header {
    background-color: #2C2C2C;
    color: white;
    padding: 10px 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.festo-nav {
    background-color: #E8E8E8;
    border-bottom: 2px solid #CCCCCC;
}
.error-banner {
    background-color: #E53935;
    color: white;
    padding: 20px;
    margin: 20px;
    font-weight: bold;
}
.action-button {
    background-color: #E8E8E8;
    border: 1px solid #999;
    padding: 8px 24px;
    min-width: 150px;
}
.diagnostic-button {
    background-color: #0091DC;
    color: white;
    padding: 12px 32px;
    font-size: 16px;
    border: none;
    cursor: pointer;
}
```

---

#### `ui/report_dashboard.py` — Diagnostic Report + Chatbot (Page 2)

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  CP-AM-DRILL Predictive Maintenance Dashboard        │
│  ─────────────────────────────────────────────────── │
│                                                      │
│  ┌─ Timing Trend Chart ──────────────────────────┐  │
│  │  [Line chart: Z-axis descent time over 500     │  │
│  │   cycles, with horizontal lines at warning     │  │
│  │   (350ms) and critical (450ms) thresholds]     │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─ All Axes Overview ───────────────────────────┐  │
│  │  Z-Descend: 405ms ████████████░░ WARNING      │  │
│  │  Z-Ascend:  262ms ████████░░░░░░ NORMAL       │  │
│  │  X-Left:    348ms ████████░░░░░░ NORMAL       │  │
│  │  X-Right:   355ms ████████░░░░░░ NORMAL       │  │
│  │  Clamp:     152ms █████░░░░░░░░░ NORMAL       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─ AI Diagnostic Report ────────────────────────┐  │
│  │  ## Anomaly Detected: Z-Axis Descent           │  │
│  │  ### Current Status                            │  │
│  │  - Current: 405ms, Baseline: 280ms (+44.6%)   │  │
│  │  ### Trend Analysis                            │  │
│  │  - Degrading at ~31 ms/day for 4 days         │  │
│  │  ### Possible Root Causes                      │  │
│  │  1. Worn seals on Z-axis mini slide [Op, p.39]│  │
│  │  2. Flow control valve needs adjustment...     │  │
│  │  ### Recommended Actions                       │  │
│  │  1. Check/adjust flow control valves [Op, p65] │  │
│  │  ...                                           │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─ Maintenance Assistant ───────────────────────┐  │
│  │  💬 Ask a question about the diagnosis...      │  │
│  │                                                │  │
│  │  User: What could cause the Z-axis to slow?   │  │
│  │  AI: Based on the diagnostic report, the       │  │
│  │  Z-axis descent time has increased by 44.6%.  │  │
│  │  The most likely causes are:                   │  │
│  │  1. The one-way flow control valves may need   │  │
│  │     readjustment (1). The procedure involves   │  │
│  │     turning off both valves completely, then    │  │
│  │     slowly opening to desired speed (2).       │  │
│  │  2. Check linear axes for pollution and clean  │  │
│  │     with a dry cloth (3).                      │  │
│  │  ---                                           │  │
│  │  References:                                   │  │
│  │  (1) Operating Manual, p.65                    │  │
│  │  (2) Operating Manual, p.66                    │  │
│  │  (3) Maintenance Manual, p.7                   │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  [ ← Back to HMI ]    [ Exit System ]               │
└──────────────────────────────────────────────────────┘
```

**Charts**: Use `st.line_chart()` or `plotly` for the timing trend. Use `st.progress()` or custom HTML bars for the axes overview.

**Report**: Rendered as `st.markdown()` from the Claude-generated report text.

**Chatbot**: Use `st.chat_input()` and `st.chat_message()` for the conversational UI. History stored in `st.session_state.chat_history`.

---

#### `app.py` — Main Entry Point

```python
import streamlit as st

st.set_page_config(
    page_title="CP-AM-DRILL Maintenance System",
    page_icon="🔧",
    layout="wide"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "hmi"           # "hmi" or "report"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "diagnostic_report" not in st.session_state:
    st.session_state.diagnostic_report = None
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = generate_sensor_data()  # Generate once

# Route to correct page
if st.session_state.page == "hmi":
    render_hmi_screen()
elif st.session_state.page == "report":
    render_report_dashboard()
```

---

## 4. IMPLEMENTATION STEPS (Ordered)

### Step 1: Project Setup (~15 min)
- Create project directory structure
- Create `requirements.txt`: `streamlit`, `anthropic`, `plotly`, `python-dotenv`
- Copy the 3 .txt document files into `data/documents/`
- Create `.env` with `ANTHROPIC_API_KEY`

### Step 2: Config & Simulated Data (~30 min)
- Implement `config.py` with all thresholds and component data
- Implement `data/simulated_sensor_data.py` — generate the 500-cycle dataset with Z-axis degradation pattern
- Write the `sensor_summary` dict calculation function

### Step 3: Document Indexing (~30 min)
- Implement `knowledge/document_index.py` — parse the 3 .txt files by `--- Page N ---` delimiters
- Build the chunks list with doc_name, page, content, section headers
- Implement simple keyword-based retrieval function
- Save/load from `chunks.json`

### Step 4: AI Prompts & Report Generator (~45 min)
- Write all 3 prompts in `ai/prompts.py` (SYSTEM_CONTEXT, REPORT_GENERATION_PROMPT, CHATBOT_SYSTEM_PROMPT)
- Implement `ai/report_generator.py`
- Test report generation with a single API call — verify output format and references
- Store the generated report in session state (generate once, reuse)

### Step 5: Chatbot (~30 min)
- Implement `ai/chatbot.py` with conversation history management
- Implement chunk retrieval for user queries (select top 8 relevant chunks)
- Test with sample questions

### Step 6: HMI Screen UI (~1 hour)
- Implement `ui/styles.py` with Festo CSS
- Implement `ui/hmi_screen.py` — the Festo-style error page
- Match colors, layout, button placement from the uploaded HMI screenshots
- Wire up navigation buttons

### Step 7: Report Dashboard UI (~1 hour)
- Implement `ui/report_dashboard.py`
- Create the trend chart (plotly line chart with threshold lines)
- Create the axes overview bars
- Render the diagnostic report as markdown
- Implement the chatbot UI with st.chat_input / st.chat_message
- Wire up Back/Exit buttons

### Step 8: Integration & Polish (~1 hour)
- Connect all components in `app.py`
- Test full flow: HMI → Report → Chat → Back → Exit
- Polish CSS, fix spacing, ensure mobile-friendly
- Handle edge cases (API errors, empty responses)
- Create README.md

---

## 5. KEY DESIGN DECISIONS & TRADE-OFFS

| Decision | Choice | Rationale |
|----------|--------|-----------|
| RAG approach | Simple keyword matching, not vector DB | Small corpus (~15K words); full chunks fit in context window; mention "production would use embeddings" in interview |
| Data source | Simulated Python data | No live PLC connection for prototype; realistic patterns demonstrate the concept |
| LLM | Claude Sonnet 4.6 | As specified; good balance of quality and speed for real-time chat |
| UI framework | Streamlit | Fast to build, supports chat UI natively, good for prototyping |
| Report generation | On-demand via API | Generate once when user clicks "Diagnostic Report", cache in session state |
| Conversation memory | Streamlit session_state | Simple, works for single-session demo; mention "production would use persistent storage" |

---

## 6. CONSIDERATIONS FOR THE INTERVIEW

### Transparency & Traceability
- Every AI recommendation includes a document reference (page number)
- The diagnostic report shows exactly what numbers triggered the alert
- The chatbot cannot fabricate advice — it is constrained to the provided documents
- The system clearly separates "measured data" from "AI interpretation"

### Documentation of the System
- README.md explains how to run the prototype
- All prompts are in a single file (`prompts.py`) for easy audit and modification
- The config file makes thresholds transparent and adjustable

### Future Multi-Modal Chatbot
- "In production, operators could photograph a component and ask the chatbot to identify it or diagnose visible wear. Claude's vision capabilities support this — the operator sends an image, and the system matches it against the component database."
- "We could also integrate the circuit diagrams as images rather than text, allowing the AI to reference specific wiring visually."

### Production Scaling Path
1. **Data Pipeline**: PLC → OPC-UA → AWS IoT Core → Kinesis → S3 → Databricks Delta table
2. **Feature Engineering**: Databricks job computes rolling averages, drift rates, CUSUM statistics
3. **Anomaly Detection**: Statistical process control (SPC) or lightweight ML model on Databricks
4. **Alert Trigger**: Lambda function triggers when anomaly detected → generates report → pushes to HMI
5. **RAG at Scale**: Amazon Bedrock Knowledge Bases or Databricks Vector Search for large document corpora
6. **Dashboard**: AWS QuickSight or custom React app replacing Streamlit

### Defensible Data Acquisition Argument
"MES4 already captures timestamped events across the station. Depending on logging granularity, we can derive pneumatic actuation times directly, or we augment with a lightweight data logger tapping the PLC's I/O register — which requires no physical sensor installation, just a software connection to the ET200 SP via its existing web server or OPC-UA interface."

---

## 7. SAMPLE CHATBOT INTERACTIONS

**Q: "How do I adjust the flow control valves on the Z-axis?"**
A: To adjust the one-way flow control valves on the Z-axis, follow this procedure:
1. Ensure the pneumatic port is connected and compressed air supply is switched on (1)
2. Turn off both one-way flow control valves completely, then turn them on again by about one rotation (2)
3. Start a test run (2)
4. Slowly turn the valves until the required piston speed is reached (2)
The flow control valves for the Z-axis are the GRLA-M5-QS-3-LF-C, Part #175053 (3).
---
References:
(1) Operating Manual, p.66
(2) Operating Manual, p.66
(3) Operating Manual, p.85

**Q: "What safety precautions should I take before working on this?"**
A: Before carrying out any maintenance work on the CP-AM-DRILL station:
1. The entire station must be switched off and the power supply disconnected (1)
2. The system must be secured against being switched on again during maintenance (1)
3. If work must be done with control system on, additional protective measures must be defined for safe personal protection, such as marking with a sign on the system (1)
4. All maintenance should be carried out by qualified personnel only (1)
---
References:
(1) Maintenance Manual, p.4

**Q: "Could a worn drill bit be causing the Z-axis to slow down?"** ⭐ *Good stakeholder demo question — see Section 8*
A: This is a great question, and the answer requires looking carefully at the PLC sequence.
Based on the flow chart for the drilling process (1), the sequence is:

1. Drills switch on and spin up (500ms warm-up) — Z-axis still at top position
2. Z-axis descends (MB6 activated) → system waits for BG6 (bottom end position sensor)
3. **BG6 triggers** — descent measurement ends here
4. 1-second drill dwell begins — this is when the drill contacts and machines the workpiece
5. Z-axis ascends

This means BG6 fires at the mechanical end of the pneumatic stroke, *before* the drill dwell begins (2).
The Z-axis descent time we monitor is defined as MB6 activation → BG6 trigger.
BG6 is a proximity sensor that reacts to a permanent magnet on the piston of the DGSL-10-40 mini slide —
it registers the physical end of the pneumatic stroke, not workpiece contact (2).

Therefore, drill bit wear cannot influence the descent time measurement. The Z-axis reaches its
bottom end position before any drilling load is applied. The degradation is a pneumatic issue:
worn seals, flow control valve drift, guide rail contamination, or supply air pressure drop (3)(4).
---
References:
(1) Operating Manual, p.75
(2) Operating Manual, p.63
(3) Operating Manual, p.39
(4) Operating Manual, p.65-66

**Q: "What spare parts would I need?"**
A: Based on the Z-axis descent anomaly, the potentially relevant spare parts are:
1. Z-axis mini slide: DGSL-10-40-E3-Y3A, Part #543905 (1)
2. One-way flow control valves: GRLA-M5-QS-3-LF-C, Part #175053 — there are 2 for the Z-axis (1)
3. Solenoid valves: CPVSC1-K-M5C, Part #548899 — MB5 (up) and MB6 (down) (1)
4. Proximity sensors: SMT-10M-PS-24V-E-2,5-L-OE, Part #551373 — BG5 (top) and BG6 (bottom) (1)
However, start with cleaning and flow control adjustment before ordering parts (2).
---
References:
(1) Operating Manual, p.85
(2) Operating Manual, p.65-66

---

## 8. WHAT TO TELL THE INTERVIEWER

### 2-Minute Value Pitch
"I chose generative AI for maintenance because it solves a real pain point: when something goes wrong on a production line, operators face hundreds of pages of manuals and need to diagnose quickly. Unplanned downtime costs manufacturers $10K-50K+ per hour. This system detects pneumatic degradation before it causes a failure, auto-generates a diagnosis with specific manual references, and gives operators an AI assistant that can answer their questions in real time — all grounded in the actual Festo documentation so there are no hallucinations. It turns a reactive 'machine broke, now what?' workflow into a proactive 'we see the trend, here's exactly what to do' workflow."

### 3-Minute Demo Script
"Imagine you're a client walking through the Smart Factory. You see the CP-AM-DRILL station running normally — drilling holes in components. Then [trigger the demo] — the HMI screen goes red. The system has detected that the Z-axis is taking 45% longer than usual to descend. But instead of just an error code, there's a new button: 'Interactive Diagnostic Report.' You press it, and immediately see a dashboard showing the timing trend over the last 500 cycles, an AI-generated report explaining the likely causes — worn seals, flow control valve drift — with exact page references to the Festo manual. Below that, a chatbot where you can ask 'How do I adjust the flow control valves?' and get step-by-step instructions with part numbers. This is what AI-augmented maintenance looks like."

### Suggested Stakeholder Demo Question (Advanced)
For a technically curious audience, ask the chatbot: **"Could a worn drill bit be causing the Z-axis to slow down?"**

This works well as a demo moment because:
- It sounds like a plausible hypothesis to a non-expert (more resistance = slower movement)
- The AI correctly reasons through the PLC sequence from the documentation and rejects it
- It demonstrates that the system doesn't just retrieve facts — it follows logical chains grounded in the actual Festo flow chart (Operating Manual, p.75)
- It shows the value of having documentation in the context: the AI can prove *why* something is NOT a cause, not just list what is

Full worked answer is in Section 7 and Appendix B.

### 5-Minute Architecture Discussion
Use the architecture diagram from Section 2. Emphasize:
- Prototype: Local Streamlit + Claude API + simulated data
- Production: PLC → OPC-UA → AWS IoT Core → Kinesis → S3/Databricks → anomaly detection → Claude API → dashboard
- The key insight: we're not adding physical sensors — we're extracting value from timing data the PLC already captures
- Future: embeddings-based RAG for larger doc sets, multi-modal (image) support, integration with CMMS

---

## 9. COMPLETE REQUIREMENTS.TXT

```
streamlit>=1.30.0
anthropic>=0.40.0
plotly>=5.18.0
python-dotenv>=1.0.0
pandas>=2.0.0
```

---

## 10. IMPORTANT IMPLEMENTATION NOTES FOR OPUS

1. **Do NOT use a vector database** — simple keyword/page-based chunk retrieval is sufficient for this prototype
2. **Generate the diagnostic report ONCE** when the user clicks "Interactive Diagnostic Report" and cache it in `st.session_state` — don't regenerate on every page render
3. **The simulated data must look realistic** — use numpy with random normal noise plus a clear linear/exponential drift pattern for the Z-axis descent
4. **All document references must be real** — cross-reference against the actual page numbers in the uploaded .txt files
5. **The Festo HMI styling must closely match the uploaded screenshots** — dark header, blue Festo branding, grey navigation bar, red error banner, Repeat/Ignore/Abort buttons
6. **The chatbot must have conversation memory** — pass full `conversation_history` to each Claude API call
7. **The system prompt in `prompts.py` is the most important file** — it must contain all the technical context about the CP-AM-DRILL system so Claude can give accurate, referenced responses
8. **Include an "Exit System" button** on both pages that cleanly stops the Streamlit app (or shows a confirmation message)
9. **Error handling**: Wrap all API calls in try/except, show user-friendly error messages in the Streamlit UI
10. **The model string for Claude Sonnet 4.6 is `claude-sonnet-4-6-20250514`** — use this exact string in all API calls

---

## APPENDIX A: KEY DOCUMENT PAGE REFERENCES (for cross-checking)

| Reference | Document | Page | Content Summary |
|-----------|----------|------|-----------------|
| Pneumatic components | Operating Manual | 38 | Valve terminal CPVSC1, all 5 valves (MB1, MB2, MB5, MB6, MB7) |
| Axes and flow control | Operating Manual | 39 | Mini slide, linear drive, 4 flow control valves |
| Function description | Operating Manual | 40 | Drilling process overview |
| Process steps | Operating Manual | 41-42 | 12-step procedure |
| I/O mappings | Operating Manual | 44 | All inputs (BG1-BG8) and outputs (MB1-MB7, MA3-MA4) |
| X-axis sensor adjust | Operating Manual | 61-62 | Proximity sensor alignment procedure |
| Z-axis sensor adjust | Operating Manual | 63-64 | Proximity sensor alignment procedure |
| Flow control adjust | Operating Manual | 65-66 | One-way flow control valve adjustment procedure |
| Flow chart | Operating Manual | 73-79 | Complete PLC state machine |
| Error messages | Operating Manual | 82 | All alarm codes and timeout values |
| Interactive errors | Operating Manual | 83-84 | Repeat/Ignore/Abort/Reject functionality |
| Spare parts | Operating Manual | 85 | All electric and pneumatic part numbers |
| Service/cleaning | Operating Manual | 86 | Maintenance-free note, lens/sensor cleaning |
| Visual inspection | Maintenance Manual | 5 | Daily inspection checklist |
| Safety checklist | Maintenance Manual | 6 | Monthly safety function tests |
| Component intervals | Maintenance Manual | 7-8 | Scheduled maintenance (linear axes: 3 weeks, fans: 6 months) |
| Pneumatic circuit | Circuit Diagrams | 16-17 | Valve wiring, flow control, cylinder connections |

---

## APPENDIX B: TECHNICAL NOTES

### B.1 Why drill head wear does NOT affect Z-axis descent time

**Question:** Could a worn/dull drill bit create resistance during descent, slow the Z-axis stroke, and cause BG6 to trigger later — thereby inflating the Z-axis descent time measurement?

**Verdict: No. Drill head condition is irrelevant to the descent time measurement.**

**Evidence — Operating Manual, p.75 (Flow Chart, CP-AM-DRILL 3):**

The PLC sequence is:
```
S8:  Activate drills, open clamp — set MA3+MA4, set MB7
T8:  Wait for drill on — wait 500ms          ← drills spin up, Z still at top
S9:  Move Z-Axis to lower position — set MB6, reset MB5
T9:  Wait for Z-Axis in lower end position — wait for BG6   ← descent measurement ends here
S10: Wait step drill time
T10: Wait for drill time 1s                  ← actual drilling happens AFTER BG6 triggers
S11: Move Z-Axis to upper position — set MB5, reset MB6
```

The descent time we measure is **MB6 activation → BG6 trigger**. BG6 triggers at the end of the pneumatic stroke. The 1-second drill dwell (`T10`) only begins *after* BG6 has already fired — meaning the workpiece is contacted and drilled entirely within that dwell period, not during the descent stroke.

**Supporting evidence — Operating Manual, p.63:**
> "The proximity sensors react to a permanent magnet on the piston of the cylinder."

BG6 is a fixed mechanical end-of-stroke sensor on the DGSL-10-40 mini slide (40mm stroke, Part #543905). It fires when the piston reaches its physical stop — a fixed position regardless of what the drill bit encounters.

**Conclusion:** Any increase in Z-axis descent time is purely a pneumatic or mechanical issue. Drill bit condition has no bearing on this measurement and should not appear as a root cause in the diagnostic report. Valid root causes are worn Z-axis seals (p.39), flow control valve adjustment (p.65–66), linear guide contamination (Maintenance Manual p.7), supply air pressure drop, or BG6 sensor positional drift (p.63–64).
