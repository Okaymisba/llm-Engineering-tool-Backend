import datetime
import logging
import os
from typing import Annotated

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.__init__ import get_db
from models.user import User
from routers.auth import get_current_user
from utilities.email_service import send_email
from utilities.email_templates import successful_transaction, transaction_failure

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load keys and URLs
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
SUCCESS_URL = os.getenv("SUCCESS_URL")
CANCEL_URL = os.getenv("CANCEL_URL")

router = APIRouter(
    prefix='/payment',
    tags=['payment']
)


class CheckoutRequest(BaseModel):
    """Request model for creating checkout session"""
    amount: float


class CheckoutResponse(BaseModel):
    """Response model for checkout session"""
    checkout_url: str


class PaymentResponse(BaseModel):
    """Response model for payment status"""
    message: str


async def send_transaction_email(user: User, amount: float, success: bool = True, session_id: str = None):
    """
    Send transaction notification email to user.
    
    Args:
        user (User): User object
        amount (float): Transaction amount
        success (bool): Whether transaction was successful
        session_id (str): Stripe session ID for failed transactions
    """
    try:
        if success:
            subject = "Payment Successful - Credits Added to Your Account"
            body = successful_transaction.format(
                user_name=user.username,
                email=user.email,
                amount=amount,
                new_credit_balance=user.credits_remaining
            )
        else:
            subject = "Payment Failed - Please Try Again"
            body = transaction_failure.format(
                user_name=user.username,
                email=user.email,
                amount=amount,
                session_id=session_id
            )

        await send_email(user.email, subject, body)
        logger.info(f"Transaction email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send transaction email: {str(e)}")


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
        data: CheckoutRequest,
        current_user: Annotated[User, Depends(get_current_user)],
        db: Session = Depends(get_db)
):
    """
    Creates a Stripe checkout session for payment.
    
    Args:
        data (CheckoutRequest): Payment amount
        current_user (User): Authenticated user
        db (Session): Database session
        
    Returns:
        CheckoutResponse: Checkout session URL
        
    Raises:
        HTTPException: If session creation fails or user has pending transaction
    """
    try:
        # Check if user has any pending transaction
        if current_user.pending_transaction:
            logger.warning(f"User {current_user.email} has a pending transaction")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have a pending transaction. Please wait for it to complete."
            )

        # Set pending transaction flag
        current_user.pending_transaction = True
        db.commit()

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(data.amount * 100),
                    "product_data": {
                        "name": "API Credit Top-Up",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
            metadata={
                "user_id": str(current_user.id),
                "email": current_user.email
            }
        )
        logger.info(f"Checkout session created for user {current_user.email}")
        return CheckoutResponse(checkout_url=session.url)
    except HTTPException:
        # Reset pending transaction flag if it was set
        current_user.pending_transaction = False
        db.commit()
        raise
    except Exception as e:
        # Reset pending transaction flag if it was set
        current_user.pending_transaction = False
        db.commit()
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating checkout session"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handles Stripe webhook events for payment processing.
    
    Args:
        request (Request): FastAPI request object
        db (Session): Database session
        
    Returns:
        dict: Success status
        
    Raises:
        HTTPException: If webhook signature is invalid
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        email = session['metadata']['email']
        amount = session['amount_total'] / 100  # Convert to dollars

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found for webhook: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Update user credits and transaction info
            user.total_credits += amount
            user.credits_remaining += amount
            user.no_of_transactions += 1
            user.pending_transaction = False  # Reset pending transaction flag
            user.last_transaction = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            logger.info(f"Credits added for user {email}: {amount}")

            # Send success email
            await send_transaction_email(user, amount, success=True)

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing payment"
            )

    elif event['type'] == 'checkout.session.expired':
        # Handle expired checkout sessions
        session = event['data']['object']
        user_id = session['metadata']['user_id']

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.pending_transaction = False  # Reset pending transaction flag
                db.commit()
                logger.info(f"Reset pending transaction for user {user.email} due to expired session")

                # Send failure email
                amount = session['amount_total'] / 100 if session['amount_total'] else 0
                await send_transaction_email(user, amount, success=False, session_id=session.id)

        except Exception as e:
            db.rollback()
            logger.error(f"Error handling expired session: {str(e)}")

    return {"status": "success"}


@router.get("/success", response_model=PaymentResponse)
async def success():
    """Returns success message after payment completion"""
    return PaymentResponse(message="Payment successful, credits added!")


@router.get("/cancel", response_model=PaymentResponse)
async def cancel():
    """Returns cancel message after payment cancellation"""
    return PaymentResponse(message="Payment canceled.")
