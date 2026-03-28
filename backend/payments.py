import os
import uuid
import logging

import stripe

from db import (
    complete_purchase,
    create_purchase,
    get_user_by_id,
    update_user_plan,
)

logger = logging.getLogger(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PRICE_FIX_FILES = os.environ.get("STRIPE_PRICE_FIX_FILES", "")
PRICE_PRO = os.environ.get("STRIPE_PRICE_PRO", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


async def create_checkout_session(
    user_id: str,
    user_email: str,
    price_type: str,
    scan_id: str | None = None,
) -> str:
    """Creates a Stripe Checkout Session. Returns the checkout URL."""

    if price_type == "fix_files":
        if not scan_id:
            raise ValueError("scan_id is required for fix_files purchase.")
        if not PRICE_FIX_FILES:
            raise ValueError("STRIPE_PRICE_FIX_FILES is not configured.")

        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=user_email,
            line_items=[{"price": PRICE_FIX_FILES, "quantity": 1}],
            metadata={
                "user_id": user_id,
                "purchase_type": "fix_files",
                "scan_id": scan_id,
            },
            success_url=f"{FRONTEND_URL}/scan/{scan_id}?payment=success",
            cancel_url=f"{FRONTEND_URL}/scan/{scan_id}?payment=cancelled",
        )

        purchase_id = str(uuid.uuid4())
        await create_purchase(
            purchase_id=purchase_id,
            user_id=user_id,
            scan_id=scan_id,
            purchase_type="fix_files",
            stripe_session_id=session.id,
            amount_cents=session.amount_total,
        )

    elif price_type == "pro":
        if not PRICE_PRO:
            raise ValueError("STRIPE_PRICE_PRO is not configured.")

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=user_email,
            line_items=[{"price": PRICE_PRO, "quantity": 1}],
            metadata={
                "user_id": user_id,
                "purchase_type": "pro",
            },
            success_url=f"{FRONTEND_URL}/dashboard?payment=success",
            cancel_url=f"{FRONTEND_URL}/pricing?payment=cancelled",
        )

        purchase_id = str(uuid.uuid4())
        await create_purchase(
            purchase_id=purchase_id,
            user_id=user_id,
            scan_id=None,
            purchase_type="pro",
            stripe_session_id=session.id,
            amount_cents=None,
        )

    else:
        raise ValueError(f"Unknown price_type: {price_type}")

    return session.url


async def handle_webhook_event(payload: bytes, sig_header: str) -> None:
    """Verifies and processes Stripe webhook events."""
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid webhook signature.")
    except Exception as e:
        raise ValueError(f"Webhook error: {str(e)}")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        session_id = data["id"]
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        purchase_type = metadata.get("purchase_type")

        # Mark the purchase as completed
        await complete_purchase(session_id)

        # If this is a subscription, update the user plan
        if purchase_type == "pro" and user_id:
            stripe_customer_id = data.get("customer")
            stripe_subscription_id = data.get("subscription")
            await update_user_plan(
                user_id,
                plan="pro",
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
            )
            logger.info(f"User {user_id} upgraded to pro.")

        elif purchase_type == "fix_files" and user_id:
            logger.info(f"User {user_id} purchased fix_files for scan {metadata.get('scan_id')}.")

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        if customer_id:
            # Find the user by stripe_customer_id and downgrade
            # We need to search by customer ID - use a direct query
            import aiosqlite
            from db import get_db
            db = await get_db()
            try:
                cursor = await db.execute(
                    "SELECT id FROM users WHERE stripe_customer_id = ?",
                    (customer_id,),
                )
                row = await cursor.fetchone()
                if row:
                    await update_user_plan(row["id"], plan="free")
                    logger.info(f"User {row['id']} downgraded to free (subscription deleted).")
            finally:
                await db.close()

    else:
        logger.debug(f"Unhandled Stripe event: {event_type}")
