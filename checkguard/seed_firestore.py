"""Seed Firestore with sample check verification and customer records."""
from datetime import datetime, timezone
from google.cloud import firestore

# Hardcoded project ID to prevent Agent Platform project number mismatch
PROJECT_ID = "qwiklabs-gcp-04-dacd550359a7"

def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore for project: {PROJECT_ID}")

    # Seed check_records collection
    check_records_ref = db.collection("check_records")
    checks = [
        {
            "id": "CHK-1001",
            "bearer_name": "Alice Johnson",
            "issuer_name": "Acme Construction LLC",
            "amount": 1250.00,
            "check_number": "4021",
            "status": "cleared",
            "risk_score": 10,
            "notes": "Payroll check verified with issuer HR. Cleared with no issues.",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "CHK-1002",
            "bearer_name": "Bob Vance",
            "issuer_name": "QuickFix Auto Repair",
            "amount": 3400.00,
            "check_number": "1190",
            "status": "returned_bounced",
            "risk_score": 85,
            "notes": "Insufficient funds notice from bank. Account frozen.",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "CHK-1003",
            "bearer_name": "Carol Martinez",
            "issuer_name": "Apex Logistics Inc",
            "amount": 875.50,
            "check_number": "5524",
            "status": "cleared",
            "risk_score": 15,
            "notes": "Regular weekly contractor payout. Clean record.",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "CHK-1004",
            "bearer_name": "David Smith",
            "issuer_name": "Apex Logistics Inc",
            "amount": 4200.00,
            "check_number": "9012",
            "status": "fraud_flagged",
            "risk_score": 95,
            "notes": "Signature mismatch detected and watermarking absent. Duplicate serial number.",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "CHK-1005",
            "bearer_name": "Eva Green",
            "issuer_name": "Metro Retail Services",
            "amount": 620.00,
            "check_number": "3104",
            "status": "cleared",
            "risk_score": 5,
            "notes": "Verified payroll check.",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    for check in checks:
        doc_ref = check_records_ref.document(check["id"])
        doc_ref.set(check)
        print(f"Seeded check record: {check['id']} ({check['bearer_name']} / {check['issuer_name']})")

    # Seed profile / risk entities collection (issuers & bearers)
    entities_ref = db.collection("entities")
    entities = [
        {
            "id": "issuer_acme_construction",
            "type": "issuer",
            "name": "Acme Construction LLC",
            "trust_level": "high",
            "total_checks_cashed": 42,
            "returned_checks": 0,
            "risk_status": "good_standing"
        },
        {
            "id": "issuer_quickfix_auto",
            "type": "issuer",
            "name": "QuickFix Auto Repair",
            "trust_level": "critical",
            "total_checks_cashed": 5,
            "returned_checks": 3,
            "risk_status": "stop_cashing"
        },
        {
            "id": "issuer_apex_logistics",
            "type": "issuer",
            "name": "Apex Logistics Inc",
            "trust_level": "moderate",
            "total_checks_cashed": 18,
            "returned_checks": 1,
            "risk_status": "require_manager_approval_over_2000"
        },
        {
            "id": "bearer_alice_johnson",
            "type": "bearer",
            "name": "Alice Johnson",
            "trust_level": "high",
            "total_checks_cashed": 12,
            "returned_checks": 0,
            "risk_status": "good_standing"
        },
        {
            "id": "bearer_david_smith",
            "type": "bearer",
            "name": "David Smith",
            "trust_level": "critical",
            "total_checks_cashed": 2,
            "returned_checks": 1,
            "risk_status": "banned_fraud_history"
        }
    ]

    for entity in entities:
        doc_ref = entities_ref.document(entity["id"])
        doc_ref.set(entity)
        print(f"Seeded entity: {entity['name']} ({entity['type']})")

    print("\nDatabase seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
