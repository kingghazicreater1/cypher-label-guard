# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Database Seeder: Seeds Default User, Credit Cards, Invoices & Job History
# ==============================================================================

import sys
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import bcrypt
from datetime import datetime, timezone, timedelta
from db.database import SessionLocal, init_db
from db.models import User, PaymentMethod, Subscription, Transaction, JobRecord, AuditLogEntry


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def seed_database():
    init_db()
    db = SessionLocal()
    try:
        # Check if default user exists
        user = db.query(User).filter(User.email == "ghazi@cypherlabelguard.ai").first()
        if not user:
            print("[*] Creating default admin user: ghazi@cypherlabelguard.ai...")
            user = User(
                email="ghazi@cypherlabelguard.ai",
                hashed_password=hash_password("GuardianPass2026!"),
                full_name="King Ghazi",
                role="Workspace Administrator",
                workspace_name="Ghazi Workspace",
                credits_balance=8500,  # 8,500 token credits (~$85.00)
                stripe_customer_id="cus_test_ghazi_2026",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Initial Subscription (Free Tier - Requires adding a payment method to upgrade)
            now = datetime.now(timezone.utc)
            sub = Subscription(
                user_id=user.id,
                plan_name="Free",
                monthly_price=0.00,
                status="Active",
                current_period_start=now - timedelta(days=1),
                current_period_end=now + timedelta(days=30),
            )
            db.add(sub)

            # Add Historical Invoices
            tx1 = Transaction(
                user_id=user.id,
                invoice_number="INV-2026-0891",
                description="CypherLabelGuard Core Edition (Monthly)",
                amount=129.00,
                status="Paid",
                created_at=now - timedelta(days=44),
            )
            tx2 = Transaction(
                user_id=user.id,
                invoice_number="INV-2026-0944",
                description="Token Credit Pack (10,000 Credits)",
                amount=50.00,
                status="Paid",
                created_at=now - timedelta(days=22),
            )
            tx3 = Transaction(
                user_id=user.id,
                invoice_number="INV-2026-1002",
                description="CypherLabelGuard Core Edition (Monthly Renewal)",
                amount=129.00,
                status="Paid",
                created_at=now - timedelta(days=14),
            )
            db.add_all([tx1, tx2, tx3])

            # Add Historical Jobs
            jobs = [
                JobRecord(
                    user_id=user.id,
                    job_number="4521",
                    name="Legal Contract Review",
                    modality="Text",
                    status="Completed",
                    progress=100,
                    labels_count=1000,
                    cost="$4.28",
                    consensus_label="HIGH RISK",
                    affirmative_votes=30,
                    created_at=now - timedelta(hours=2),
                ),
                JobRecord(
                    user_id=user.id,
                    job_number="4520",
                    name="Product Quality Control",
                    modality="Image",
                    status="Completed",
                    progress=100,
                    labels_count=2480,
                    cost="$6.12",
                    consensus_label="DEFECT_CLEARED",
                    affirmative_votes=32,
                    created_at=now - timedelta(hours=5),
                ),
                JobRecord(
                    user_id=user.id,
                    job_number="4519",
                    name="Video Content Moderation",
                    modality="Video",
                    status="Completed",
                    progress=100,
                    labels_count=320,
                    cost="$3.84",
                    consensus_label="SAFE",
                    affirmative_votes=28,
                    created_at=now - timedelta(days=1),
                ),
                JobRecord(
                    user_id=user.id,
                    job_number="4518",
                    name="Customer Call Transcripts",
                    modality="Audio",
                    status="Completed",
                    progress=100,
                    labels_count=180,
                    cost="$1.20",
                    consensus_label="POSITIVE",
                    affirmative_votes=31,
                    created_at=now - timedelta(days=2),
                ),
            ]
            db.add_all(jobs)

            # Add Audit Log Entries
            logs = [
                AuditLogEntry(
                    user_id=user.id,
                    action="WORKSPACE_INITIALIZED",
                    details="Workspace 'Ghazi Workspace' configured with 38 core features",
                    created_at=now - timedelta(days=44),
                ),
                AuditLogEntry(
                    user_id=user.id,
                    action="PAYMENT_METHOD_ADDED",
                    details="Visa credit card ending in 4242 added as default",
                    created_at=now - timedelta(days=44),
                ),
                AuditLogEntry(
                    user_id=user.id,
                    action="SUBSCRIPTION_ACTIVATED",
                    details="Subscribed to Core Edition ($129/mo)",
                    created_at=now - timedelta(days=44),
                ),
                AuditLogEntry(
                    user_id=user.id,
                    action="CREDIT_PACK_PURCHASED",
                    details="Purchased 10,000 token credits for $50.00",
                    created_at=now - timedelta(days=22),
                ),
            ]
            db.add_all(logs)

            db.commit()
            print("[OK] Database initialized and seeded successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
