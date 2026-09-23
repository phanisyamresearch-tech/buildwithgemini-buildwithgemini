"""Firestore client and tools for CheckGuard agent."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from google.cloud import firestore

# Hardcoded project ID as string so Agent Platform runtime does not fail with project number
PROJECT_ID = "qwiklabs-gcp-04-dacd550359a7"

_db: Optional[firestore.Client] = None

def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client instance."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def search_check_history(
    bearer_name: Optional[str] = None,
    issuer_name: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Search historical check cashing records for a given bearer and/or issuer name.

    Args:
        bearer_name: Optional name of the person cashing or presenting the check (payee).
        issuer_name: Optional name of the organization or person issuing the check (payer).
        limit: Max number of records to return (defaults to 10).

    Returns:
        List of matching check records with status, risk score, amount, and notes.
    """
    db = get_firestore_client()
    collection = db.collection("check_records")
    results = []

    # Stream matching documents
    for doc in collection.stream():
        data = doc.to_dict()
        b_match = True
        i_match = True

        if bearer_name and bearer_name.strip():
            b_match = bearer_name.lower() in str(data.get("bearer_name", "")).lower()

        if issuer_name and issuer_name.strip():
            i_match = issuer_name.lower() in str(data.get("issuer_name", "")).lower()

        if b_match and i_match:
            results.append(data)
            if len(results) >= limit:
                break

    return results


def get_entity_risk_profile(name: str) -> Dict[str, Any]:
    """Retrieve risk profile and standing for an issuer or bearer name.

    Args:
        name: Name of the issuer business or bearer person to look up.

    Returns:
        Risk profile info including trust level, total checks cashed, returned checks, and risk status.
    """
    db = get_firestore_client()
    collection = db.collection("entities")
    clean_name = name.strip().lower()

    for doc in collection.stream():
        data = doc.to_dict()
        if clean_name in str(data.get("name", "")).lower():
            return {
                "found": True,
                "entity": data,
            }

    return {
        "found": False,
        "message": f"No previous recorded profile found for '{name}'. Treated as first-time / unverified entity.",
    }


def record_check_verification(
    bearer_name: str,
    issuer_name: str,
    amount: float,
    check_number: str,
    decision: str,
    risk_score: int,
    notes: str,
) -> Dict[str, Any]:
    """Record a new check verification decision into the database.

    Args:
        bearer_name: Name of the payee/bearer presenting the check.
        issuer_name: Name of the maker/company issuing the check.
        amount: Dollar amount of the check.
        check_number: Check sequence number.
        decision: Decision reached: 'approved', 'rejected', or 'hold_for_review'.
        risk_score: Assessed risk score (0 to 100, where 100 is maximum risk/fraud).
        notes: Reasoning, verification steps completed, or red flags identified.

    Returns:
        Confirmation dict with newly created record ID and timestamp.
    """
    db = get_firestore_client()
    record_id = f"CHK-{uuid.uuid4().hex[:6].upper()}"
    new_record = {
        "id": record_id,
        "bearer_name": bearer_name.strip(),
        "issuer_name": issuer_name.strip(),
        "amount": float(amount),
        "check_number": str(check_number).strip(),
        "status": decision.strip().lower(),
        "risk_score": int(risk_score),
        "notes": notes.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection("check_records").document(record_id).set(new_record)
    return {
        "success": True,
        "id": record_id,
        "record": new_record,
    }


def query_business_statistics(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """Query operational and financial statistics on checks presented, cashed, rejected, and bounced.

    Store managers use this tool to review monthly and yearly performance, fee revenue, loss rates,
    and risk indicators.

    Args:
        year: Optional 4-digit calendar year (e.g. 2026). If omitted, aggregates across all recorded data.
        month: Optional month number from 1 to 12 (e.g. 9 for September). If omitted, aggregates for the whole year.

    Returns:
        Dict containing comprehensive summary statistics:
        - filter_applied: The year and month filtered.
        - counts: Checks presented, cashed/cleared, rejected, bounced/returned, and held.
        - volume: Dollar face value for total presented, cashed, rejected, and bounced checks.
        - financial_metrics: Total cashing fees earned, average check amount, bounce loss amount.
        - performance_rates: Clearance rate (%), bounce rate (%), rejection rate (%).
        - monthly_breakdown: Monthly counts and amounts when querying an entire year.
        - high_risk_issuers: Issuers associated with bounced or rejected checks.
    """
    db = get_firestore_client()
    collection = db.collection("check_records")

    total_presented_count = 0
    cashed_count = 0
    rejected_count = 0
    bounced_count = 0
    held_count = 0

    total_presented_volume = 0.0
    cashed_volume = 0.0
    rejected_volume = 0.0
    bounced_volume = 0.0
    held_volume = 0.0
    total_fees_earned = 0.0

    monthly_stats: Dict[str, Dict[str, Any]] = {}
    problem_issuers: Dict[str, Dict[str, Any]] = {}

    for doc in collection.stream():
        data = doc.to_dict()
        created_at_raw = data.get("created_at")
        if not created_at_raw:
            continue

        try:
            # Parse ISO timestamp
            dt = datetime.fromisoformat(str(created_at_raw))
        except Exception:
            continue

        # Filter by year if specified
        if year is not None and dt.year != year:
            continue

        # Filter by month if specified
        if month is not None and dt.month != month:
            continue

        amount = float(data.get("amount", 0.0))
        status = str(data.get("status", "")).lower().strip()
        issuer = str(data.get("issuer_name", "Unknown")).strip()
        month_key = f"{dt.year:04d}-{dt.month:02d}"

        # Initialize monthly bucket
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                "month": month_key,
                "total_presented": 0,
                "cashed_count": 0,
                "rejected_count": 0,
                "bounced_count": 0,
                "cashed_volume": 0.0,
                "bounced_volume": 0.0,
                "rejected_volume": 0.0,
                "fees_collected": 0.0,
            }

        total_presented_count += 1
        total_presented_volume += amount
        monthly_stats[month_key]["total_presented"] += 1

        # Classify by status
        # 'cleared' or 'approved' counts as cashed
        if status in ("cleared", "approved", "cashed"):
            cashed_count += 1
            cashed_volume += amount
            # Estimated fee: 2.0% average or $3.00 minimum
            fee = max(round(amount * 0.02, 2), 3.00)
            total_fees_earned += fee
            monthly_stats[month_key]["cashed_count"] += 1
            monthly_stats[month_key]["cashed_volume"] += amount
            monthly_stats[month_key]["fees_collected"] += fee

        elif status in ("returned_bounced", "bounced", "returned"):
            bounced_count += 1
            bounced_volume += amount
            # When a check bounces, store loses the cashed amount
            monthly_stats[month_key]["bounced_count"] += 1
            monthly_stats[month_key]["bounced_volume"] += amount
            if issuer not in problem_issuers:
                problem_issuers[issuer] = {"bounced_count": 0, "bounced_amount": 0.0, "rejected_count": 0}
            problem_issuers[issuer]["bounced_count"] += 1
            problem_issuers[issuer]["bounced_amount"] += amount

        elif status in ("fraud_flagged", "rejected"):
            rejected_count += 1
            rejected_volume += amount
            monthly_stats[month_key]["rejected_count"] += 1
            monthly_stats[month_key]["rejected_volume"] += amount
            if issuer not in problem_issuers:
                problem_issuers[issuer] = {"bounced_count": 0, "bounced_amount": 0.0, "rejected_count": 0}
            problem_issuers[issuer]["rejected_count"] += 1

        elif status in ("held", "hold_for_review"):
            held_count += 1
            held_volume += amount

    # Calculated rates
    clearance_rate = round((cashed_count / total_presented_count * 100), 2) if total_presented_count > 0 else 0.0
    bounce_rate = round((bounced_count / (cashed_count + bounced_count) * 100), 2) if (cashed_count + bounced_count) > 0 else 0.0
    rejection_rate = round((rejected_count / total_presented_count * 100), 2) if total_presented_count > 0 else 0.0
    avg_check_size = round(total_presented_volume / total_presented_count, 2) if total_presented_count > 0 else 0.0

    # Sort monthly breakdown chronologically
    sorted_monthly = [monthly_stats[k] for k in sorted(monthly_stats.keys())]

    filter_desc = "All Time"
    if year and month:
        filter_desc = f"{datetime(year, month, 1).strftime('%B %Y')}"
    elif year:
        filter_desc = f"Year {year}"
    elif month:
        filter_desc = f"Month {month} (all years)"

    return {
        "period": filter_desc,
        "counts": {
            "total_presented": total_presented_count,
            "cashed_cleared": cashed_count,
            "rejected_fraud": rejected_count,
            "returned_bounced": bounced_count,
            "held_in_review": held_count,
        },
        "dollar_volumes": {
            "total_presented": round(total_presented_volume, 2),
            "cashed_cleared": round(cashed_volume, 2),
            "rejected_fraud": round(rejected_volume, 2),
            "returned_bounced": round(bounced_volume, 2),
            "held_in_review": round(held_volume, 2),
        },
        "financial_kpis": {
            "total_cashing_fees_earned": round(total_fees_earned, 2),
            "average_check_amount": avg_check_size,
            "net_bounced_loss": round(bounced_volume, 2),
            "clearance_rate_percent": clearance_rate,
            "bounce_rate_percent": bounce_rate,
            "rejection_rate_percent": rejection_rate,
        },
        "monthly_breakdown": sorted_monthly,
        "high_risk_issuers": problem_issuers,
    }

