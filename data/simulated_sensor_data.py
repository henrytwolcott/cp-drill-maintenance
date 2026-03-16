"""
Simulated pneumatic timing data for the CP-AM-DRILL station.

Generates 500 drill cycles over the past ~2 weeks with a realistic Z-axis
ascent degradation pattern to demonstrate predictive maintenance detection.

In production, this data would come from MES4 timestamped events or a PLC
data logger connected via OPC-UA to the ET200 SP I/O module.
"""

import numpy as np
import json
from datetime import datetime, timedelta


def generate_sensor_data(seed: int = 42) -> list[dict]:
    """
    Generate 500 cycles of simulated pneumatic timing data.

    Z-axis ascent shows a clear degradation pattern:
    - Cycles 1-350:   Normal ~260ms ± 12ms noise
    - Cycles 350-450: Linear drift 260 → 340ms + noise
    - Cycles 450-500: Steeper drift 340 → 390ms + noise
    All other axes remain within normal operating range.
    """
    rng = np.random.default_rng(seed)
    n_cycles = 500

    # Build timestamps: ~35 cycles/day, going back from now
    end_time = datetime(2026, 3, 15, 10, 0, 0)
    interval_minutes = int(24 * 60 / 35)  # ~41 min per cycle
    timestamps = [
        end_time - timedelta(minutes=interval_minutes * (n_cycles - i))
        for i in range(n_cycles)
    ]

    # --- Z-axis ascent degradation pattern ---
    z_ascend = np.empty(n_cycles)
    z_ascend[:350] = 260 + rng.normal(0, 12, 350)
    drift_1 = np.linspace(260, 340, 100)
    z_ascend[350:450] = drift_1 + rng.normal(0, 12, 100)
    drift_2 = np.linspace(340, 390, 50)
    z_ascend[450:] = drift_2 + rng.normal(0, 10, 50)
    z_ascend = np.round(z_ascend).astype(int)

    # --- Other axes: normal variance ---
    z_descend = np.round(280 + rng.normal(0, 15, n_cycles)).astype(int)
    x_left    = np.round(350 + rng.normal(0, 18, n_cycles)).astype(int)
    x_right   = np.round(350 + rng.normal(0, 18, n_cycles)).astype(int)
    clamp     = np.round(150 + rng.normal(0, 8,  n_cycles)).astype(int)

    cycles = []
    for i in range(n_cycles):
        cycles.append({
            "cycle_id":     i + 1,
            "timestamp":    timestamps[i].strftime("%Y-%m-%dT%H:%M:%S"),
            "z_descend_ms": int(z_descend[i]),
            "z_ascend_ms":  int(z_ascend[i]),
            "x_left_ms":    int(x_left[i]),
            "x_right_ms":   int(x_right[i]),
            "clamp_ms":     int(clamp[i]),
            "drill_program": 3,
        })

    return cycles


def compute_sensor_summary(cycles: list[dict]) -> dict:
    """
    Derive the anomaly summary dict used by the report generator.
    The anomaly axis is z_ascend — this is hardcoded for the demo scenario.
    """
    last_10 = [c["z_ascend_ms"] for c in cycles[-10:]]
    current_avg = int(round(sum(last_10) / len(last_10)))
    baseline_ms = 260
    warning_ms  = 330
    critical_ms = 420
    timeout_ms  = 20000

    deviation_ms  = current_avg - baseline_ms
    deviation_pct = round((deviation_ms / baseline_ms) * 100, 1)

    if current_avg >= critical_ms:
        status = "CRITICAL"
    elif current_avg >= warning_ms:
        status = "WARNING"
    else:
        status = "NORMAL"

    # Find the cycle where drift starts (first crossing of 280ms rolling avg)
    drift_start_idx = 350  # Known from generation
    drift_start_date = cycles[drift_start_idx]["timestamp"][:10]
    trend_duration_days = 4

    # Degradation rate: ms gained per day over drift period
    drift_values = [c["z_ascend_ms"] for c in cycles[drift_start_idx:]]
    degradation_rate = round((current_avg - 260) / trend_duration_days, 1)

    # Days until critical threshold at current rate
    if degradation_rate > 0:
        days_to_critical = round((critical_ms - current_avg) / degradation_rate, 1)
        days_to_timeout  = round((timeout_ms - current_avg) / degradation_rate, 1)
    else:
        days_to_critical = 999
        days_to_timeout  = 999

    # Other axes — averages of last 10 cycles
    def avg_last10(key):
        return int(round(sum(c[key] for c in cycles[-10:]) / 10))

    return {
        "anomaly_axis":             "z_axis_ascend",
        "anomaly_description":      "Z-Axis Ascent (Drill Up)",
        "current_avg_ms":           current_avg,
        "baseline_ms":              baseline_ms,
        "deviation_ms":             deviation_ms,
        "deviation_pct":            deviation_pct,
        "warning_threshold_ms":     warning_ms,
        "critical_threshold_ms":    critical_ms,
        "timeout_ms":               timeout_ms,
        "status":                   status,
        "trend_start_date":         drift_start_date,
        "trend_duration_days":      trend_duration_days,
        "degradation_rate_ms_per_day": degradation_rate,
        "estimated_days_to_critical": max(0, days_to_critical),
        "estimated_days_to_timeout":  max(0, days_to_timeout),
        "last_10_readings":         last_10,
        "last_maintenance_date":    "2026-02-15",
        "total_cycles_since_maintenance": len(cycles),
        "component_service_log": {
            "z_axis_seals": {
                "last_replaced":             "2025-09-10",
                "cycles_since_replacement":  8420,
                "service_interval_cycles":   8000,
                "interval_exceeded":         True,
            },
            "z_axis_flow_control_valve": {
                "last_replaced":             "2025-09-10",
                "cycles_since_replacement":  8420,
                "service_interval_cycles":   12000,
                "interval_exceeded":         False,
            },
            "linear_guide_lubrication": {
                "last_serviced":             "2026-02-15",
                "cycles_since_service":      500,
                "service_interval_cycles":   2000,
                "interval_exceeded":         False,
            },
            "x_axis_seals": {
                "last_replaced":             "2025-09-10",
                "cycles_since_replacement":  8420,
                "service_interval_cycles":   8000,
                "interval_exceeded":         True,
            },
        },
        "other_axes_status": {
            "z_axis_descend": {
                "current_avg_ms": avg_last10("z_descend_ms"),
                "baseline_ms":    280,
                "status":         "NORMAL",
            },
            "x_axis_left": {
                "current_avg_ms": avg_last10("x_left_ms"),
                "baseline_ms":    350,
                "status":         "NORMAL",
            },
            "x_axis_right": {
                "current_avg_ms": avg_last10("x_right_ms"),
                "baseline_ms":    350,
                "status":         "NORMAL",
            },
        },
    }


def format_sensor_summary(summary: dict) -> str:
    """Format sensor summary as a readable string for the Claude API prompt."""
    sl = summary["component_service_log"]
    other = summary["other_axes_status"]

    lines = [
        f"ANOMALY AXIS: {summary['anomaly_description']}",
        f"Current average (last 10 cycles): {summary['current_avg_ms']} ms",
        f"Baseline: {summary['baseline_ms']} ms",
        f"Deviation: +{summary['deviation_ms']} ms ({summary['deviation_pct']}% above baseline)",
        f"Warning threshold: {summary['warning_threshold_ms']} ms",
        f"Critical threshold: {summary['critical_threshold_ms']} ms",
        f"Status: {summary['status']}",
        "",
        f"TREND:",
        f"Drift started: {summary['trend_start_date']} ({summary['trend_duration_days']} days ago)",
        f"Degradation rate: ~{summary['degradation_rate_ms_per_day']} ms/day",
        f"Estimated days to critical threshold: {summary['estimated_days_to_critical']}",
        f"Last 10 readings (ms): {summary['last_10_readings']}",
        "",
        "COMPONENT SERVICE LOG:",
        f"  Z-axis seals: last replaced {sl['z_axis_seals']['last_replaced']}, "
        f"{sl['z_axis_seals']['cycles_since_replacement']} cycles ago "
        f"(interval: {sl['z_axis_seals']['service_interval_cycles']}) — "
        f"{'OVERDUE' if sl['z_axis_seals']['interval_exceeded'] else 'OK'}",
        f"  Z-axis flow control valve: last replaced {sl['z_axis_flow_control_valve']['last_replaced']}, "
        f"{sl['z_axis_flow_control_valve']['cycles_since_replacement']} cycles ago "
        f"(interval: {sl['z_axis_flow_control_valve']['service_interval_cycles']}) — "
        f"{'OVERDUE' if sl['z_axis_flow_control_valve']['interval_exceeded'] else 'OK'}",
        f"  Linear guide lubrication: last serviced {sl['linear_guide_lubrication']['last_serviced']}, "
        f"{sl['linear_guide_lubrication']['cycles_since_service']} cycles ago "
        f"(interval: {sl['linear_guide_lubrication']['service_interval_cycles']}) — "
        f"{'OVERDUE' if sl['linear_guide_lubrication']['interval_exceeded'] else 'OK'}",
        "",
        "OTHER AXES (all normal):",
    ]
    for axis, data in other.items():
        lines.append(
            f"  {axis}: {data['current_avg_ms']} ms (baseline {data['baseline_ms']} ms) — {data['status']}"
        )
    return "\n".join(lines)
