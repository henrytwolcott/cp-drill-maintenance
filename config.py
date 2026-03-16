# CP-AM-DRILL Predictive Maintenance System — Configuration
# Thresholds derived from Operating Manual flow chart timings and Festo pneumatic specs

THRESHOLDS = {
    "z_axis_descend": {
        "baseline_ms": 280,
        "warning_ms": 350,
        "critical_ms": 450,
        "timeout_ms": 20000,
        "sensor_start": "VN_BG5",
        "sensor_end": "VN_BG6",
        "valve_activate": "MB6",
        "valve_deactivate": "MB5",
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
        "baseline_ms": 350,
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

# System component reference (Operating Manual p.85)
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
    "proximity_sensor": {
        "name": "Proximity sensor",
        "part_number": "SMT-10M-PS-24V-E-2,5-L-OE",
        "festo_id": "551373",
    },
}

# Sensor data file path
SENSOR_DATA_CACHE = "data/sensor_cache.json"
