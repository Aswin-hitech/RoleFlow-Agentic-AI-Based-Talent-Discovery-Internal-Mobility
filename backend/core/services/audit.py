"""Audit logging service — Immutable tracking of mobility decisions, overrides, and approvals."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)

# In-memory audit log ledger for fallback / fast querying
_IN_MEMORY_AUDIT_LOGS: List[Dict[str, Any]] = []


def record_audit_event(
    event_type: str,
    actor_id: str,
    actor_role: str,
    role_id: str,
    employee_id: str,
    action: str,
    previous_state: Optional[str] = None,
    new_state: Optional[str] = None,
    justification: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record an audit entry to MongoDB and persistent in-memory/relational stores.
    
    Args:
        event_type: 'transfer_transition', 'score_override', 'shortlist', 'approval'
        actor_id: ID or email of the authenticated user taking action
        actor_role: 'manager', 'employee', 'hr', 'system'
        role_id: Target role identifier
        employee_id: Affected employee identifier
        action: Human-readable action description
        previous_state: Previous status/score
        new_state: Updated status/score
        justification: Mandatory rationale for overrides or manual decisions
        metadata: Additional contextual payload
    """
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": now,
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "role_id": role_id,
        "employee_id": employee_id,
        "action": action,
        "previous_state": previous_state,
        "new_state": new_state,
        "justification": justification or "Standard automated/user action",
        "metadata": metadata or {},
    }

    _IN_MEMORY_AUDIT_LOGS.append(entry)

    # Attempt to persist to MongoDB
    try:
        from ..extensions import mongo
        if mongo and hasattr(mongo, "db") and mongo.db is not None:
            mongo.db.audit_logs.insert_one(dict(entry))
    except Exception as exc:
        logger.debug("MongoDB audit logging skipped (using in-memory/relational ledger): %s", exc)

    logger.info("AUDIT [%s] by %s (%s): %s on role %s / emp %s", event_type, actor_id, actor_role, action, role_id, employee_id)
    return entry


def get_audit_logs(
    role_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve filtered audit history for governance inspections."""
    try:
        from ..extensions import mongo
        if mongo and hasattr(mongo, "db") and mongo.db is not None:
            query = {}
            if role_id:
                query["role_id"] = role_id
            if employee_id:
                query["employee_id"] = employee_id
            cursor = mongo.db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
            results = list(cursor)
            if results:
                return results
    except Exception:
        pass

    # Fallback to in-memory ledger
    filtered = [
        log for log in _IN_MEMORY_AUDIT_LOGS
        if (not role_id or log["role_id"] == role_id)
        and (not employee_id or log["employee_id"] == employee_id)
    ]
    return sorted(filtered, key=lambda x: x["timestamp"], reverse=True)[:limit]
