# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Payment, Credit Card & Subscription Billing Routes (Stripe + Database)
# ==============================================================================

import os
import uuid
import stripe
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.database import get_db, init_db
from db.models import User, PaymentMethod, Subscription, Transaction, AuditLogEntry, PaymentRequest
from api.auth_routes import get_current_user, get_optional_current_user, require_admin
from typing import Optional

router = APIRouter(prefix="/api/v2/billing", tags=["Billing & Payments"])

# Configure Stripe credentials from environment if available
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class AddCardRequest(BaseModel):
    card_number: str = Field(..., description="16-digit card number or test card 4242...")
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int = Field(..., ge=2024, le=2040)
    cvc: str = Field(..., min_length=3, max_length=4)
    cardholder_name: str = "Authorized Cardholder"
    make_default: bool = True


class SetDefaultCardRequest(BaseModel):
    card_id: str


class ChangePlanRequest(BaseModel):
    plan_name: str = Field(..., description="Core, Pro, Enterprise, or Free")


class PurchaseCreditsRequest(BaseModel):
    credit_amount: int = Field(..., gt=0, description="1000, 5000, 10000, or 25000")
    card_id: Optional[str] = None


def detect_card_brand(number: str) -> str:
    cleaned = number.replace(" ", "").replace("-", "")
    if cleaned.startswith("4"):
        return "visa"
    elif cleaned.startswith(("51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27")):
        return "mastercard"
    elif cleaned.startswith(("34", "37")):
        return "amex"
    elif cleaned.startswith(("6011", "65")):
        return "discover"
    return "visa"


@router.get("/summary")
def get_billing_summary(user: Optional[User] = Depends(get_optional_current_user)):
    """Returns active subscription, credit balance, default card, and payment capabilities."""
    if not user:
        return {
            "success": True,
            "subscription": {"plan_name": "Core", "status": "Active", "monthly_price": 129.00},
            "credits_balance": 5000,
            "credits_value_usd": 50.00,
            "default_card": None,
            "total_cards": 0,
            "stripe_configured": bool(STRIPE_SECRET_KEY),
            "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
            "is_guest": True,
        }

    sub = user.subscriptions[0] if user.subscriptions else None
    default_card = next((c for c in user.payment_methods if c.is_default), None)
    if not default_card and user.payment_methods:
        default_card = user.payment_methods[0]

    return {
        "success": True,
        "subscription": sub.to_dict() if sub else {"plan_name": "Core", "status": "Active", "monthly_price": 129.00},
        "credits_balance": user.credits_balance,
        "credits_value_usd": round(user.credits_balance * 0.01, 2),
        "default_card": default_card.to_dict() if default_card else None,
        "total_cards": len(user.payment_methods),
        "stripe_configured": bool(STRIPE_SECRET_KEY),
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
        "is_guest": False,
    }


@router.get("/cards")
def list_cards(user: Optional[User] = Depends(get_optional_current_user)):
    """List all saved credit cards for the authenticated user."""
    if not user:
        return {
            "success": True,
            "cards": [],
        }
    return {
        "success": True,
        "cards": [card.to_dict() for card in user.payment_methods],
    }


def validate_luhn(card_number: str) -> bool:
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


@router.post("/cards")
def add_card(req: AddCardRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Adds a new credit card with strict validation (Luhn checksum, expiry check, CVV).
    Requires live Stripe configuration so unverified test cards cannot mint credits.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Card registration is not available yet: commercial payment processing (Stripe) is not configured on this server."
        )
    cleaned = req.card_number.replace(" ", "").replace("-", "")
    if len(cleaned) < 13 or len(cleaned) > 19:
        raise HTTPException(status_code=400, detail="Invalid card number length. Must be 13 to 19 digits.")

    # 1. Luhn Checksum Verification
    if not validate_luhn(cleaned):
        raise HTTPException(status_code=400, detail="Card validation failed: Invalid card number checksum (Luhn check failed).")

    # 2. Expiry Verification
    now = datetime.now(timezone.utc)
    if req.exp_year < now.year or (req.exp_year == now.year and req.exp_month < now.month):
        raise HTTPException(status_code=400, detail="Card validation failed: Expiration date is in the past. Card is expired.")

    # 3. CVC Verification
    if not req.cvc.isdigit() or len(req.cvc) not in (3, 4):
        raise HTTPException(status_code=400, detail="Card validation failed: CVC/CVV security code must be 3 or 4 digits.")

    last4 = cleaned[-4:]
    brand = detect_card_brand(cleaned)
    pm_id = f"pm_token_{uuid.uuid4().hex[:12]}"

    if STRIPE_SECRET_KEY:
        try:
            # Create Stripe Customer if not existing
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(email=user.email, name=user.full_name)
                user.stripe_customer_id = customer.id
                db.commit()

            # Attach card to Stripe Customer
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": cleaned,
                    "exp_month": req.exp_month,
                    "exp_year": req.exp_year,
                    "cvc": req.cvc,
                },
                billing_details={"name": req.cardholder_name, "email": user.email},
            )
            stripe.PaymentMethod.attach(payment_method.id, customer=user.stripe_customer_id)
            pm_id = payment_method.id
            brand = payment_method.card.brand
            last4 = payment_method.card.last4
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Stripe card processing error: {str(e)}")

    # If make_default, reset others
    if req.make_default:
        for c in user.payment_methods:
            c.is_default = False

    new_card = PaymentMethod(
        user_id=user.id,
        card_brand=brand,
        last4=last4,
        exp_month=req.exp_month,
        exp_year=req.exp_year,
        cardholder_name=req.cardholder_name,
        is_default=req.make_default or len(user.payment_methods) == 0,
        stripe_payment_method_id=pm_id,
    )
    db.add(new_card)

    # Log action
    log = AuditLogEntry(
        user_id=user.id,
        action="CREDIT_CARD_ADDED",
        details=f"Added {brand.upper()} ending in {last4}",
    )
    db.add(log)
    db.commit()
    db.refresh(new_card)

    return {"success": True, "message": "Credit card added successfully", "card": new_card.to_dict()}


@router.delete("/cards/{card_id}")
def delete_card(card_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a saved credit card."""
    card = db.query(PaymentMethod).filter(PaymentMethod.id == card_id, PaymentMethod.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")

    if card.is_default and len(user.payment_methods) > 1:
        # Transfer default to next card
        next_card = next((c for c in user.payment_methods if c.id != card_id), None)
        if next_card:
            next_card.is_default = True

    last4 = card.last4
    db.delete(card)

    log = AuditLogEntry(user_id=user.id, action="CREDIT_CARD_REMOVED", details=f"Removed card ending in {last4}")
    db.add(log)
    db.commit()

    return {"success": True, "message": f"Card ending in {last4} removed successfully"}


@router.post("/cards/{card_id}/default")
def set_default_card(card_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Set a credit card as the primary payment method."""
    card = db.query(PaymentMethod).filter(PaymentMethod.id == card_id, PaymentMethod.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")

    for c in user.payment_methods:
        c.is_default = (c.id == card_id)

    db.commit()
    return {"success": True, "message": f"Card ending in {card.last4} set as default"}


@router.post("/subscription")
def update_subscription(req: ChangePlanRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upgrade or downgrade subscription plan (Basic $19, Master $49, Max $99, Team $499)."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Plan upgrades are not available yet: commercial payment processing (Stripe) is not configured on this server."
        )
    prices = {
        "Free": 0.0,
        "Basic": 19.00,
        "Master": 49.00,
        "Max": 99.00,
        "Team": 499.00,
        "Core": 49.00,
        "Pro": 99.00,
        "Enterprise": 499.00,
    }
    plan_credits = {
        "Free": 0,
        "Basic": 2500,
        "Master": 7500,
        "Max": 20000,
        "Team": 120000,
        "Core": 7500,
        "Pro": 20000,
        "Enterprise": 120000,
    }
    if req.plan_name not in prices:
        raise HTTPException(status_code=400, detail="Invalid plan name. Choose Basic, Master, Max, or Team.")

    price = prices[req.plan_name]
    credits_to_add = plan_credits.get(req.plan_name, 0)
    now = datetime.now(timezone.utc)

    sub = user.subscriptions[0] if user.subscriptions else None
    if sub and sub.plan_name == req.plan_name and sub.status == "Active":
        raise HTTPException(
            status_code=400,
            detail=f"Workspace is already actively subscribed to the {req.plan_name} edition."
        )

    # STRICT PAYMENT METHOD ENFORCEMENT: No free plan activations for paid packages!
    charged_card_str = "No payment required (Free Tier)"
    if price > 0:
        if not user.payment_methods or len(user.payment_methods) == 0:
            raise HTTPException(
                status_code=402,
                detail=f"Payment Required: You must add and authorize a valid credit card under the Credit Cards tab before activating the {req.plan_name} (${price:.2f}/mo) package."
            )

        primary_card = next((c for c in user.payment_methods if c.is_default), user.payment_methods[0])
        # Verify card is not expired
        if primary_card.exp_year < now.year or (primary_card.exp_year == now.year and primary_card.exp_month < now.month):
            raise HTTPException(
                status_code=402,
                detail=f"Payment Declined: Card ending in {primary_card.last4} has expired ({primary_card.exp_month}/{primary_card.exp_year}). Please update your payment card."
            )

        try:
            charge = stripe.Charge.create(
                amount=int(price * 100),
                currency="usd",
                description=f"CypherLabelGuard {req.plan_name} Plan Subscription for {user.email}",
                customer=user.stripe_customer_id or None,
                source=primary_card.stripe_payment_method_id or None,
            )
            auth_id = charge.id
            charged_card_str = f"Paid via {primary_card.card_brand.upper()} ending in {primary_card.last4} [Stripe Charge: {auth_id}]"
        except Exception as e:
            raise HTTPException(status_code=402, detail=f"Subscription payment declined by gateway: {str(e)}")

    if not sub:
        sub = Subscription(
            user_id=user.id,
            plan_name=req.plan_name,
            monthly_price=price,
            status="Active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        db.add(sub)
    else:
        sub.plan_name = req.plan_name
        sub.monthly_price = price
        sub.status = "Active"

    # Add monthly package credits to user account
    user.credits_balance += credits_to_add

    # Create Invoice record for upgrade
    if price > 0:
        inv_num = f"INV-2026-{uuid.uuid4().hex[:6].upper()}"
        tx = Transaction(
            user_id=user.id,
            invoice_number=inv_num,
            description=f"CypherLabelGuard {req.plan_name} Edition (Monthly Plan + {credits_to_add:,} Credits) · {charged_card_str}",
            amount=price,
            status="Paid",
        )
        db.add(tx)

    log = AuditLogEntry(
        user_id=user.id,
        action="SUBSCRIPTION_PLAN_CHANGED",
        details=f"Plan updated to {req.plan_name} (${price}/mo) with +{credits_to_add:,} credits added. {charged_card_str}",
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully activated {req.plan_name} plan! {credits_to_add:,} credits loaded. ({charged_card_str})",
        "subscription": sub.to_dict(),
        "credits_balance": user.credits_balance,
        "payment_authorized": charged_card_str,
    }


@router.post("/credits/purchase")
def purchase_credits(req: PurchaseCreditsRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Purchase token credits:
    - 1,000 Credits = $10.00
    - 5,000 Credits = $45.00 (10% discount)
    - 10,000 Credits = $80.00 (20% discount)
    - 25,000 Credits = $175.00 (30% discount)
    """
    credit_packs = {
        1000: 10.00,
        5000: 45.00,
        10000: 80.00,
        25000: 175.00,
    }
    if req.credit_amount not in credit_packs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid credit package: {req.credit_amount}. Allowed packages: 1,000 ($10), 5,000 ($45), 10,000 ($80), 25,000 ($175)."
        )
    cost = credit_packs[req.credit_amount]
    now = datetime.now(timezone.utc)

    # STRICT PAYMENT METHOD ENFORCEMENT: Cannot buy credits without an authorized card
    if not user.payment_methods or len(user.payment_methods) == 0:
        raise HTTPException(
            status_code=402,
            detail=f"Payment Required: You must add an authorized credit card under the Credit Cards tab before purchasing {req.credit_amount:,} credits (${cost:.2f})."
        )

    primary_card = next((c for c in user.payment_methods if c.is_default), user.payment_methods[0])
    if primary_card.exp_year < now.year or (primary_card.exp_year == now.year and primary_card.exp_month < now.month):
        raise HTTPException(
            status_code=402,
            detail=f"Payment Declined: Primary card ending in {primary_card.last4} is expired. Please update your card."
        )

    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Commercial payment processing (Stripe) is not configured on this server. Contact workspace administrator to allocate credits."
        )

    try:
        # Process live payment via Stripe PaymentIntent / Charge
        charge = stripe.Charge.create(
            amount=int(cost * 100),
            currency="usd",
            description=f"CypherLabelGuard: {req.credit_amount:,} credits for {user.email}",
            customer=user.stripe_customer_id or None,
            source=primary_card.stripe_payment_method_id or None,
        )
        auth_id = charge.id
        charged_card_str = f"Paid via {primary_card.card_brand.upper()} ending in {primary_card.last4} [Stripe Charge: {auth_id}]"
    except Exception as e:
        raise HTTPException(status_code=402, detail=f"Card processing declined by payment gateway: {str(e)}")

    # Add credits to balance only after successful gateway capture
    user.credits_balance += req.credit_amount

    # Record invoice transaction
    inv_num = f"INV-2026-{uuid.uuid4().hex[:6].upper()}"
    tx = Transaction(
        user_id=user.id,
        invoice_number=inv_num,
        description=f"Token Credit Pack ({req.credit_amount:,} Credits) · {charged_card_str}",
        amount=cost,
        status="Paid",
    )
    db.add(tx)

    log = AuditLogEntry(
        user_id=user.id,
        action="CREDIT_PACK_PURCHASED",
        details=f"Purchased {req.credit_amount:,} credits for ${cost:.2f} via {primary_card.card_brand} {primary_card.last4}",
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully purchased {req.credit_amount:,} token credits for ${cost:.2f}! ({charged_card_str})",
        "new_balance": user.credits_balance,
        "transaction": tx.to_dict(),
        "payment_authorized": charged_card_str,
    }


@router.get("/invoices")
def list_invoices(user: Optional[User] = Depends(get_optional_current_user)):
    """Returns invoice billing history."""
    if not user:
        return {"success": True, "invoices": []}
    invoices = sorted(user.transactions, key=lambda t: t.created_at, reverse=True)
    return {
        "success": True,
        "invoices": [inv.to_dict() for inv in invoices],
    }


# ------------------------------------------------------------------------------
# Commander's Custom Labeling Rate Controller
# ------------------------------------------------------------------------------
class CommanderRatesRequest(BaseModel):
    base_text_credits: float = Field(default=1.0, ge=0.1, le=100.0)
    vision_inspection_credits: float = Field(default=2.0, ge=0.1, le=100.0)
    parliament_consensus_credits: float = Field(default=1.0, ge=0.0, le=100.0)
    cryptographic_proof_credits: float = Field(default=1.0, ge=0.0, le=100.0)
    turbo_speed_credits: float = Field(default=0.5, ge=0.0, le=100.0)


COMMANDER_RATES = {
    "base_text_credits": 1.0,
    "vision_inspection_credits": 2.0,
    "parliament_consensus_credits": 1.0,
    "cryptographic_proof_credits": 1.0,
    "turbo_speed_credits": 0.5,
}


@router.get("/rates")
def get_commander_rates():
    """Returns the Commander's custom credit burn rates for labeling options."""
    return {
        "success": True,
        "rates": COMMANDER_RATES,
    }


@router.post("/rates")
def update_commander_rates(req: CommanderRatesRequest, user: User = Depends(require_admin)):
    """Admin endpoint to customize how fast credits decrease per label option."""
    COMMANDER_RATES["base_text_credits"] = req.base_text_credits
    COMMANDER_RATES["vision_inspection_credits"] = req.vision_inspection_credits
    COMMANDER_RATES["parliament_consensus_credits"] = req.parliament_consensus_credits
    COMMANDER_RATES["cryptographic_proof_credits"] = req.cryptographic_proof_credits
    COMMANDER_RATES["turbo_speed_credits"] = req.turbo_speed_credits
    return {
        "success": True,
        "message": "Commander credit rates updated successfully!",
        "rates": COMMANDER_RATES,
    }


class GrantCreditsRequest(BaseModel):
    user_id: str
    credit_amount: int = Field(..., gt=0)
    reason: Optional[str] = "Admin Grant"


@router.post("/credits/grant")
def grant_credits_admin(
    req: GrantCreditsRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Allows administrators to allocate token credits to workspace accounts."""
    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found.")
    target_user.credits_balance += req.credit_amount
    log = AuditLogEntry(
        user_id=target_user.id,
        action="CREDITS_GRANTED_BY_ADMIN",
        details=f"Admin {admin.email} granted {req.credit_amount:,} credits. Reason: {req.reason}",
    )
    db.add(log)
    db.commit()
    return {
        "success": True,
        "message": f"Successfully granted {req.credit_amount:,} credits to {target_user.email}.",
        "new_balance": target_user.credits_balance,
    }


# ------------------------------------------------------------------------------
# Pakistan-First Dual-Track Billing (SadaPay / Raast / Bank IBAN & Lemon Squeezy)
# ------------------------------------------------------------------------------

class ManualPaymentRequest(BaseModel):
    credit_amount: int = Field(..., gt=0, description="1000, 5000, 10000, or 25000")
    payment_channel: str = Field(..., description="SadaPay, Raast, Bank Transfer, or Nayapay")
    transaction_reference: str = Field(..., min_length=4, max_length=100, description="Transaction ID (TID) / Ref Number")
    sender_name: Optional[str] = Field(default=None, max_length=100)
    amount_paid_pkr: Optional[float] = Field(default=None, ge=0)


class ApproveManualPaymentRequest(BaseModel):
    transaction_id: str


@router.get("/bank-details")
def get_bank_transfer_details():
    """Returns official Pakistani bank / SadaPay deposit details for wire transfer payments."""
    return {
        "success": True,
        "channels": {
            "sadapay": {
                "account_title": os.getenv("SADAPAY_ACCOUNT_TITLE", "CypherLabelGuard Treasury"),
                "number": os.getenv("SADAPAY_NUMBER", "03XX-XXXXXXX"),
                "currency": "PKR",
            },
            "raast": {
                "account_title": os.getenv("RAAST_ACCOUNT_TITLE", "CypherLabelGuard Treasury"),
                "raast_id": os.getenv("RAAST_ID", "03XX-XXXXXXX"),
                "currency": "PKR",
            },
            "bank_transfer": {
                "bank_name": os.getenv("BANK_NAME", "Meezan Bank / HBL"),
                "account_title": os.getenv("BANK_ACCOUNT_TITLE", "CypherLabelGuard"),
                "account_number": os.getenv("BANK_ACCOUNT_NUMBER", "XXXXXXXXXXXXXX"),
                "iban": os.getenv("BANK_IBAN", "PKXXXXXXXXXXXXXXXXXXXXXX"),
                "currency": "PKR",
            },
        },
        "credit_rates_pkr": {
            1000: 2800,   # $10 @ 280 PKR/USD
            5000: 12600,  # $45
            10000: 22400, # $80
            25000: 49000, # $175
        },
    }


@router.post("/manual-payment-request")
def submit_manual_payment(
    req: ManualPaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submits a SadaPay / Raast / Bank wire transfer for administrator confirmation."""
    credit_packs = {1000: 10.0, 5000: 45.0, 10000: 80.0, 25000: 175.0}
    usd_val = credit_packs.get(req.credit_amount, req.credit_amount * 0.01)

    inv_num = f"TID-{uuid.uuid4().hex[:6].upper()}"
    desc = (
        f"Manual Transfer via {req.payment_channel} (Ref: {req.transaction_reference.strip()}) "
        f"for {req.credit_amount:,} Credits"
    )
    if req.sender_name:
        desc += f" by {req.sender_name.strip()}"

    tx = Transaction(
        user_id=user.id,
        invoice_number=inv_num,
        description=desc,
        amount=usd_val,
        currency="USD",
        status="PendingApproval",
    )
    db.add(tx)

    log = AuditLogEntry(
        user_id=user.id,
        action="MANUAL_PAYMENT_SUBMITTED",
        details=f"Submitted {req.payment_channel} transfer (Ref: {req.transaction_reference}) for {req.credit_amount:,} credits.",
    )
    db.add(log)
    db.commit()
    db.refresh(tx)

    return {
        "success": True,
        "message": f"Payment reference submitted successfully! Once verified, {req.credit_amount:,} credits will be allocated.",
        "transaction": tx.to_dict(),
    }


@router.post("/manual-payment/approve")
def approve_manual_payment(
    req: ApproveManualPaymentRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint to verify and allocate credits from a submitted manual payment."""
    tx = db.query(Transaction).filter(Transaction.id == req.transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if tx.status == "Paid":
        raise HTTPException(status_code=400, detail="Transaction is already approved and paid.")

    # Parse credit amount from description
    import re
    match = re.search(r"for\s+([0-9,]+)\s+Credits", tx.description)
    credits_to_grant = int(match.group(1).replace(",", "")) if match else int(tx.amount * 100)

    target_user = db.query(User).filter(User.id == tx.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found.")

    target_user.credits_balance += credits_to_grant
    tx.status = "Paid"

    log = AuditLogEntry(
        user_id=target_user.id,
        action="MANUAL_PAYMENT_APPROVED",
        details=f"Admin {admin.email} approved manual transaction {tx.invoice_number}. Allocated {credits_to_grant:,} credits.",
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "message": f"Approved transaction {tx.invoice_number}. {credits_to_grant:,} credits granted to {target_user.email}.",
        "new_balance": target_user.credits_balance,
        "transaction": tx.to_dict(),
    }


@router.post("/webhook/lemonsqueezy")
async def lemonsqueezy_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Lemon Squeezy Merchant of Record (MoR) automated webhook.
    Receives order_created events, validates HMAC-SHA256 signature, and grants credits.
    """
    secret = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
    body_bytes = await request.body()

    if secret:
        import hmac
        import hashlib
        signature = request.headers.get("X-Signature", "")
        digest = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    try:
        import json
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    event_name = payload.get("meta", {}).get("event_name", "")
    if event_name in ("order_created", "subscription_payment_success"):
        custom_data = payload.get("meta", {}).get("custom_data", {})
        user_id = custom_data.get("user_id")
        user_email = payload.get("data", {}).get("attributes", {}).get("user_email")

        # Resolve user
        user = None
        if user_id:
            user = db.query(User).filter(User.id == str(user_id)).first()
        if not user and user_email:
            user = db.query(User).filter(User.email == str(user_email).strip().lower()).first()

        if user:
            total_cents = payload.get("data", {}).get("attributes", {}).get("total", 0)
            credits_to_add = int(custom_data.get("credits", total_cents))  # 1 cent = 1 credit default
            user.credits_balance += credits_to_add

            order_id = str(payload.get("data", {}).get("id", uuid.uuid4().hex[:6]))
            tx = Transaction(
                user_id=user.id,
                invoice_number=f"LS-{order_id}",
                description=f"Lemon Squeezy Order #{order_id} ({credits_to_add:,} Credits)",
                amount=round(total_cents / 100.0, 2),
                currency="USD",
                status="Paid",
            )
            db.add(tx)
            db.add(AuditLogEntry(
                user_id=user.id,
                action="LEMONSQUEEZY_ORDER_CREDITED",
                details=f"Credited {credits_to_add:,} tokens via Lemon Squeezy Order #{order_id}.",
            ))
            db.commit()

    return {"success": True}


# ==============================================================================
# PAKISTANI BANKING & SADAPAY / RAAST PROOF VERIFICATION ENGINE
# ==============================================================================

class SubmitProofRequest(BaseModel):
    plan_name: str = Field(..., description="Basic, Master, Max, Team or Custom Credits")
    amount_pkr: float = Field(..., gt=0, description="Amount transferred in PKR")
    credits: int = Field(..., gt=0, description="Requested credits amount")
    payment_method: str = Field("SADAPAY", description="SADAPAY, RAAST, BANK_TRANSFER, or NAYAPAY")
    transaction_ref: str = Field(..., min_length=4, description="Transaction ID or Reference number")
    sender_name: Optional[str] = None
    sender_account: Optional[str] = None
    notes: Optional[str] = None


class ReviewProofRequest(BaseModel):
    admin_notes: Optional[str] = None


@router.get("/pakistan-accounts")
def get_pakistan_accounts():
    """Returns official Pakistani banking & Raast channels and current pricing packages."""
    return {
        "success": True,
        "accounts": [
            {
                "method": "SADAPAY",
                "title": "SadaPay Direct Transfer",
                "account_title": os.getenv("SADAPAY_TITLE", "AV GUARDIAN ENTERPRISE"),
                "iban": os.getenv("SADAPAY_IBAN", "PK36SADA0000001234567890"),
                "account_number": os.getenv("SADAPAY_NUMBER", "0300-1234567"),
                "badge": "0% Fee · Instant 24/7",
                "instructions": "Send to SadaPay via mobile number or IBAN. Submit transaction ID below.",
            },
            {
                "method": "RAAST",
                "title": "State Bank of Pakistan (Raast Instant P2P)",
                "account_title": os.getenv("RAAST_TITLE", "AV GUARDIAN ENTERPRISE"),
                "raast_id": os.getenv("RAAST_ID", "03001234567"),
                "badge": "Instant SBP Settlement",
                "instructions": "Transfer via Raast ID from any Pakistani mobile banking app with zero transaction charges.",
            },
            {
                "method": "BANK_TRANSFER",
                "title": "Commercial Bank IBFT (Meezan / HBL / Alfalah)",
                "account_title": os.getenv("BANK_TITLE", "AV GUARDIAN ENTERPRISE"),
                "bank_name": os.getenv("BANK_NAME", "Meezan Bank Ltd"),
                "iban": os.getenv("BANK_IBAN", "PK00MEZN0000000000000000"),
                "badge": "Inter-Bank Funds Transfer",
                "instructions": "Standard IBFT transfer. Enter the 6 to 12 digit banking reference number.",
            },
        ],
        "packages": [
            {"plan_name": "Basic", "pkr": 5200, "usd": 19, "credits": 2500, "desc": "Standard 4-Model Parliament SLA"},
            {"plan_name": "Master", "pkr": 13500, "usd": 49, "credits": 7500, "desc": "Priority Pool & Deep Vision Inspection"},
            {"plan_name": "Max", "pkr": 27000, "usd": 99, "credits": 20000, "desc": "500 Managed Connections & SHA-256 Proofs"},
            {"plan_name": "Team", "pkr": 135000, "usd": 499, "credits": 120000, "desc": "Dedicated VIP Chamber & Unlimited Seats"},
            {"plan_name": "Starter Pack (5,000 Credits)", "pkr": 2800, "usd": 10, "credits": 5000, "desc": "5,000 On-Demand Token Credits"},
            {"plan_name": "Growth Pack (20,000 Credits)", "pkr": 11000, "usd": 40, "credits": 20000, "desc": "20,000 High-Volume Token Credits"},
        ],
    }


@router.post("/submit-proof")
def submit_payment_proof(
    req: SubmitProofRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit proof of manual payment via SadaPay, Raast, or Pakistani bank transfer."""
    init_db()
    existing = db.query(PaymentRequest).filter(
        PaymentRequest.transaction_ref == req.transaction_ref.strip()
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A payment proof with reference '{req.transaction_ref}' has already been submitted (Status: {existing.status})."
        )

    amount_usd = round(req.amount_pkr / 280.0, 2)

    payment_req = PaymentRequest(
        user_id=user.id,
        plan_name=req.plan_name.strip(),
        amount_pkr=req.amount_pkr,
        amount_usd=amount_usd,
        credits=req.credits,
        payment_method=req.payment_method.strip().upper(),
        transaction_ref=req.transaction_ref.strip(),
        sender_name=req.sender_name.strip() if req.sender_name else None,
        sender_account=req.sender_account.strip() if req.sender_account else None,
        notes=req.notes.strip() if req.notes else None,
        status="PENDING",
    )
    db.add(payment_req)
    db.add(AuditLogEntry(
        user_id=user.id,
        action="PAYMENT_PROOF_SUBMITTED",
        details=f"Submitted {req.payment_method} proof for PKR {req.amount_pkr:,.0f} ({req.plan_name}) [Ref: {req.transaction_ref}]",
    ))
    db.commit()
    db.refresh(payment_req)

    return {
        "success": True,
        "message": "Payment proof submitted successfully. Credits will be allocated immediately upon verification.",
        "request": payment_req.to_dict(),
    }


@router.get("/my-requests")
def get_my_payment_requests(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve list of payment proofs submitted by the current authenticated user."""
    init_db()
    reqs = db.query(PaymentRequest).filter(
        PaymentRequest.user_id == user.id
    ).order_by(PaymentRequest.created_at.desc()).all()
    return {
        "success": True,
        "requests": [r.to_dict() for r in reqs],
    }


@router.get("/admin/requests")
def get_all_payment_requests_admin(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: Retrieve all pending, approved, and rejected manual payment requests."""
    init_db()
    reqs = db.query(PaymentRequest).order_by(PaymentRequest.created_at.desc()).all()
    return {
        "success": True,
        "requests": [r.to_dict() for r in reqs],
    }


@router.post("/admin/approve/{request_id}")
def approve_payment_request(
    request_id: str,
    req_body: ReviewProofRequest = ReviewProofRequest(),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: Verify proof and allocate credits and activate plan subscription."""
    init_db()
    payment_req = db.query(PaymentRequest).filter(PaymentRequest.id == request_id).first()
    if not payment_req:
        raise HTTPException(status_code=404, detail="Payment request not found.")

    if payment_req.status == "APPROVED":
        raise HTTPException(status_code=400, detail="This payment request has already been approved.")

    target_user = db.query(User).filter(User.id == payment_req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Associated user not found.")

    # 1. Credit the balance
    target_user.credits_balance += payment_req.credits

    # 2. Upgrade subscription if it corresponds to a plan
    if payment_req.plan_name in ["Basic", "Master", "Max", "Team", "Core", "Pro", "Enterprise"]:
        sub = target_user.subscriptions[0] if target_user.subscriptions else None
        now = datetime.now(timezone.utc)
        if sub:
            sub.plan_name = payment_req.plan_name
            sub.status = "Active"
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=30)
        else:
            new_sub = Subscription(
                user_id=target_user.id,
                plan_name=payment_req.plan_name,
                monthly_price=payment_req.amount_usd,
                status="Active",
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
            )
            db.add(new_sub)

    # 3. Create persistent transaction invoice
    tx = Transaction(
        user_id=target_user.id,
        invoice_number=f"PKR-{payment_req.transaction_ref[-8:]}",
        description=f"{payment_req.payment_method} Payment: {payment_req.plan_name} ({payment_req.credits:,} Credits)",
        amount=payment_req.amount_usd,
        currency="USD",
        status="Paid",
    )
    db.add(tx)

    # 4. Mark request approved
    payment_req.status = "APPROVED"
    payment_req.reviewed_at = datetime.now(timezone.utc)
    if req_body.admin_notes:
        payment_req.admin_notes = req_body.admin_notes

    # 5. Audit log
    db.add(AuditLogEntry(
        user_id=admin.id,
        action="MANUAL_PAYMENT_APPROVED",
        details=f"Admin {admin.email} approved {payment_req.payment_method} ref '{payment_req.transaction_ref}' for {target_user.email} (+{payment_req.credits:,} credits).",
    ))
    db.commit()

    return {
        "success": True,
        "message": f"Payment approved. {payment_req.credits:,} credits successfully allocated to {target_user.email}.",
        "new_balance": target_user.credits_balance,
    }


@router.post("/admin/reject/{request_id}")
def reject_payment_request(
    request_id: str,
    req_body: ReviewProofRequest = ReviewProofRequest(),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: Reject invalid or fraudulent payment proof."""
    init_db()
    payment_req = db.query(PaymentRequest).filter(PaymentRequest.id == request_id).first()
    if not payment_req:
        raise HTTPException(status_code=404, detail="Payment request not found.")

    payment_req.status = "REJECTED"
    payment_req.reviewed_at = datetime.now(timezone.utc)
    if req_body.admin_notes:
        payment_req.admin_notes = req_body.admin_notes

    db.add(AuditLogEntry(
        user_id=admin.id,
        action="MANUAL_PAYMENT_REJECTED",
        details=f"Admin {admin.email} rejected {payment_req.payment_method} ref '{payment_req.transaction_ref}'. Reason: {req_body.admin_notes or 'Unverified'}",
    ))
    db.commit()

    return {
        "success": True,
        "message": "Payment request has been marked as REJECTED.",
    }


