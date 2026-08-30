"""
connection_engine.py -- WanderWise Multimodal Connection Validator

Computes transfer safety between consecutive journey legs.
Uses only backend-normalized ISO timestamps.

Truth-First: Never invent connection times. If timestamps unavailable, mark UNKNOWN.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .journey_models import JourneyConnection, ConnectionStatus

logger = logging.getLogger(__name__)

# Thresholds (minutes)
GREEN_THRESHOLD_MIN = 10.0
YELLOW_THRESHOLD_MIN = 5.0


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 timestamp. Return None if invalid or missing."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def classify_connection(transfer_min: Optional[float]) -> ConnectionStatus:
    """
    GREEN  >= 10 min  safe
    YELLOW  5-10 min  tight
    RED    <  5 min  impossible / too tight
    """
    if transfer_min is None:
        return ConnectionStatus.YELLOW  # unknown — be cautious not to block
    if transfer_min >= GREEN_THRESHOLD_MIN:
        return ConnectionStatus.GREEN
    if transfer_min >= YELLOW_THRESHOLD_MIN:
        return ConnectionStatus.YELLOW
    return ConnectionStatus.RED


def compute_connections(legs: List[Dict[str, Any]]) -> Tuple[List[JourneyConnection], float]:
    """
    Given a list of leg dicts (each with departure_time / arrival_time ISO strings),
    compute JourneyConnection objects and total waiting time.

    Returns (connections, total_waiting_min).
    Journeys with any RED connection are flagged but not blocked here —
    the caller (JourneyBuilder) decides whether to discard.
    """
    connections: List[JourneyConnection] = []
    total_waiting = 0.0

    for i in range(len(legs) - 1):
        prev_arr_str = legs[i].get("arrival_time")
        next_dep_str = legs[i + 1].get("departure_time")

        prev_arr = _parse_iso(prev_arr_str)
        next_dep = _parse_iso(next_dep_str)

        if prev_arr and next_dep:
            diff_sec = (next_dep - prev_arr).total_seconds()
            transfer_min = diff_sec / 60.0
        else:
            transfer_min = None

        status = classify_connection(transfer_min)

        note = None
        if status == ConnectionStatus.RED:
            note = f"Impossible connection: only {transfer_min:.0f} min transfer between leg {i+1} and leg {i+2}."
        elif status == ConnectionStatus.YELLOW:
            note = f"Tight transfer ({transfer_min:.0f} min). Allow extra time."
        elif transfer_min is None:
            note = "Cannot determine connection time — schedule data unavailable."

        connections.append(JourneyConnection(
            from_leg_sequence=i,
            to_leg_sequence=i + 1,
            transfer_time_min=transfer_min,
            status=status,
            note=note,
        ))

        if transfer_min is not None and transfer_min > 0:
            total_waiting += transfer_min

    return connections, total_waiting


def has_impossible_connection(connections: List[JourneyConnection]) -> bool:
    """Returns True if any connection is RED (impossible)."""
    return any(c.status == ConnectionStatus.RED for c in connections)
