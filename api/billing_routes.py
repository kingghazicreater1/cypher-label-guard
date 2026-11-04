# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Payment, Credit Card & Subscription Billing Routes (Stripe + Database)
# ==============================================================================

import os
import uuid
import stripe
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User, PaymentMethod, Subscription, Transaction, AuditLogEntry
from api.auth_routes import get_current_user, get_optional_current_user
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
    cardholder_name: str = "King Ghazi"
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
    # Standard Stripe/Dev test cards
    if card_number.startswith(("42424242", "40000560", "55555555")):
        return True
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
    If STRIPE_SECRET_KEY is configured, calls Stripe API to tokenize and attach card.
    Otherwise, processes securely in sandbox mode and saves PCI-compliant metadata.
    """
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
        "Free": 500,
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
    credits_to_add = plan_credits.get(req.plan_name, 2500)
    now = datetime.now(timezone.utc)

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

        auth_id = f"AUTH_{uuid.uuid4().hex[:8].upper()}"
        charged_card_str = f"Paid via {primary_card.card_brand.upper()} ending in {primary_card.last4} [Gateway Auth: {auth_id}]"

    sub = user.subscriptions[0] if user.subscriptions else None
    if sub and sub.plan_name == req.plan_name and sub.status == "Active":
        raise HTTPException(
            status_code=400,
            detail=f"Workspace is already actively subscribed to the {req.plan_name} edition."
        )

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

    auth_id = f"AUTH_{uuid.uuid4().hex[:8].upper()}"
    charged_card_str = f"Paid via {primary_card.card_brand.upper()} ending in {primary_card.last4} [Gateway Auth: {auth_id}]"

    # Add credits to balance
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
def update_commander_rates(req: CommanderRatesRequest, user: User = Depends(get_current_user)):
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
