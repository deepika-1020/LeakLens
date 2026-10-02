import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# ==============================================================================
# LEAKLENS - AUDIT TRAIL & DECISION GOVERNANCE LOGGER
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Human-in-the-Loop & Audit Persistence)
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIT_FILE = BASE_DIR / "audit_trail.json"

def get_audit_trail() -> List[Dict[str, Any]]:
    """Retrieve full audit history from persistent storage."""
    if not AUDIT_FILE.exists():
        return []
    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def log_decision(
    query_id: str,
    question: str,
    investigation_type: str,
    finding: str,
    calculated_metrics: Dict[str, Any],
    recommendation: str,
    decision: str,  # 'APPROVED' or 'REJECTED'
    reviewer: str = "Data Analytics & AI Reviewer",
    notes: Optional[str] = "",
    evidence_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Append an immutable decision audit record.
    The system NEVER executes an automated operational action without human signoff.
    """
    trail = get_audit_trail()

    audit_entry = {
        "audit_id": f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(trail) + 1:04d}",
        "timestamp_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "query_id": query_id,
        "question": question,
        "investigation_type": investigation_type,
        "finding": finding,
        "calculated_metrics": calculated_metrics,
        "recommendation": recommendation,
        "decision": decision.upper(),
        "reviewer": reviewer,
        "reviewer_notes": notes.strip() if notes and notes.strip() else "Reviewed and acknowledged without additional comments.",
        "evidence_summary": evidence_summary or {},
        "execution_status": "MANUAL_ACTION_REQUIRED" if decision.upper() == "APPROVED" else "ACTION_ABORTED"
    }

    trail.insert(0, audit_entry)  # Most recent first

    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(trail, f, indent=2, default=str)

    return audit_entry
