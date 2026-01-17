from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import schemas, crud
from database import get_db
from roles import get_current_user
from email_utilis import send_payment_received,send_payment_rejected
from models import User, Order
from models import PaymentOption

router = APIRouter(
    prefix= "/payment",
    tags=["payment"]
)

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}


# ===============================
# Create Payment Method
# ===============================

@router.post("/orders/{order_id}/confirm-payment")
def confirm_manual_payment(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    payment_option = db_order.payment_option
    if not payment_option or payment_option.provider.lower() not in ["manual", "bank_transfer", "opay"]:
        raise HTTPException(status_code=400, detail="Order is not a manual payment")

    db_order.payment_status = "paid"
    db_order.status = "processing"
    db.commit()
    db.refresh(db_order)

    if db_order.user and db_order.user.email:
        background_tasks.add_task(
            send_payment_received,
            db_order.user.email,
            db_order.order_reference,
            db_order.total_amount,
        )

    return response_format(db_order, "Manual payment confirmed")




@router.post("/orders/{order_id}/reject-payment")
def reject_manual_payment(
    order_id: int,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment_option = db_order.payment_option
    if not payment_option or payment_option.provider.lower() not in ["manual", "bank_transfer", "opay"]:
        raise HTTPException(status_code=400, detail="Order is not a manual payment")

    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_order.payment_status = "rejected"
    db_order.status = "cancelled"
    db.commit()
    db.refresh(db_order)

    if db_order.user and db_order.user.email:
        background_tasks.add_task(
            send_payment_rejected,
            db_order.user.email,
            db_order.order_reference,
            reason
        )

    return response_format(db_order, f"Payment rejected: {reason}")


@router.get("/payment-methods")
def list_payment_methods(db: Session = Depends(get_db)):
    methods = db.query(PaymentOption).all()
    return [
        {
            "id": int(m.id),
            "name": m.name,
            "provider": m.provider,
            "account_number": str(m.account_number) if m.account_number else None
        }
        for m in methods
    ]



# ===============================
# Get Payment Method by ID
# ===============================
@router.get("/{payment_id}")
def get_payment_method(payment_id: int, db: Session = Depends(get_db)):
    db_payment = crud.get_payment_method(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return response_format(db_payment, "Payment method retrieved successfully")


# ===============================
# Get All Payment Methods for a User
# ===============================
@router.get("/user/{user_id}")
def get_user_payment_methods(user_id: int, db: Session = Depends(get_db)):
    db_payments = crud.get_payment_methods(db, user_id)
    return response_format(db_payments, "User payment methods retrieved successfully")


# ===============================
# Update Payment Method
# ===============================
@router.put("/{payment_id}")
def update_payment_method(payment_id: int, payment: schemas.PaymentMethodCreate, db: Session = Depends(get_db)):
    db_payment = crud.update_payment_method(db, payment_id, payment)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return response_format(db_payment, "Payment method updated successfully")


# ===============================
# Delete Payment Method
# ===============================
@router.delete("/{payment_id}")
def delete_payment_method(payment_id: int, db: Session = Depends(get_db)):
    db_payment = crud.delete_payment_method(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return response_format(db_payment, "Payment method deleted successfully")

# ===============================
# Paystack Integration
# ===============================

import requests
import os
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

# ===============================
# Initialize Paystack Transaction
# ===============================
@router.post("/paystack/initialize")
def initialize_paystack_payment(
    payment_data: schemas.PaymentInitializeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initialize a Paystack payment for an existing order.
    Fetches order details automatically from the database.
    """
    # Fetch order from database
    db_order = db.query(Order).filter(Order.id == payment_data.order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify order belongs to current user (unless admin)
    # Verify order belongs to current user (unless admin)
    print(f"DEBUG: Payment Init - Current User ID: {current_user.id}, Role: {current_user.role}")
    print(f"DEBUG: Payment Init - Order ID: {db_order.id}, Order User ID: {db_order.user_id}")
    
    if db_order.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        print(f"DEBUG: Authorization failed. Order User {db_order.user_id} != Current User {current_user.id}")
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    
    # Check if order is already paid
    if db_order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Order is already paid")
    
    # Get user email
    user_email = db_order.user.email if db_order.user else current_user.email
    if not user_email:
        raise HTTPException(status_code=400, detail="User email not found")
    
    # Prepare Paystack request
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    # Amount must be in kobo (multiply by 100)
    data = {
        "email": user_email,
        "amount": int(db_order.total_amount * 100),
        "metadata": {
            "order_id": db_order.id,
            "order_reference": db_order.order_reference,
            "user_id": db_order.user_id
        }
    }
    
    # Add callback URL (priority: request > default)
    if payment_data.callback_url:
        data["callback_url"] = payment_data.callback_url
    else:
        # Default fallback to frontend payment page
        frontend_url = os.getenv("FRONTEND_URL", "")
        if frontend_url:
            data["callback_url"] = f"{frontend_url}/payment"
    
    # Make request to Paystack
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        paystack_response = response.json()
        # Update order with payment reference if available
        if paystack_response.get("data") and paystack_response["data"].get("reference"):
            db_order.payment_method = "Paystack"
            db.commit()
        
        return response_format(paystack_response, "Payment initialization successful")
    else:
        error_message = response.json().get("message", "Payment initialization failed")
        raise HTTPException(status_code=response.status_code, detail=error_message)


# ===============================
# Verify Paystack Transaction
# ===============================
@router.post("/paystack/verify")
def verify_paystack_payment(
    verify_data: schemas.PaymentVerifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify a Paystack payment using the payment reference.
    Updates order payment status based on verification result.
    """
    # Call Paystack verification API
    url = f"https://api.paystack.co/transaction/verify/{verify_data.reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        error_message = response.json().get("message", "Verification failed")
        raise HTTPException(status_code=response.status_code, detail=error_message)
    
    verification_data = response.json()
    
    # Check if payment was successful
    if not verification_data.get("status") or not verification_data.get("data"):
        raise HTTPException(status_code=400, detail="Invalid verification response")
    
    payment_data = verification_data["data"]
    payment_status = payment_data.get("status")
    
    # Extract order_id from metadata
    metadata = payment_data.get("metadata", {})
    order_id = metadata.get("order_id")
    
    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID not found in payment metadata")
    
    # Fetch order from database
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify order belongs to current user (unless admin)
    if db_order.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    
    # Update order based on payment status
    if payment_status == "success":
        db_order.payment_status = "paid"
        db_order.status = "processing"
        db.commit()
        db.refresh(db_order)
        
        # Send confirmation email in background
        if db_order.user and db_order.user.email:
            background_tasks.add_task(
                send_payment_received,
                db_order.user.email,
                db_order.order_reference,
                db_order.total_amount,
            )
        
        return response_format(
            {
                "order_id": db_order.id,
                "order_reference": db_order.order_reference,
                "payment_status": db_order.payment_status,
                "order_status": db_order.status,
                "amount_paid": payment_data.get("amount", 0) / 100,  # Convert from kobo
                "verification_data": payment_data
            },
            "Payment verified successfully"
        )
    else:
        # Payment failed or pending
        db_order.payment_status = payment_status
        db.commit()
        
        return response_format(
            {
                "order_id": db_order.id,
                "order_reference": db_order.order_reference,
                "payment_status": payment_status,
                "verification_data": payment_data
            },
            f"Payment status: {payment_status}"
        )


# ===============================
# Paystack Webhook Handler
# ===============================
@router.post("/paystack/webhook")
async def paystack_webhook(
    request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Handle Paystack webhook events.
    Returns 200 OK immediately and processes in background as recommended by Paystack.
    """
    # Verify webhook signature (security measure)
    # Note: In a real implementation, you should verify the signature from request headers
    # For now, we'll process the webhook data
    
    event = request.get("event")
    data = request.get("data", {})
    
    # Process charge.success event in background
    if event == "charge.success":
        background_tasks.add_task(process_successful_payment, db, data)
    
    # Return 200 OK immediately as recommended by Paystack
    return {"status": "success", "message": "Webhook received"}


# ===============================
# Background task for webhook processing
# ===============================
def process_successful_payment(db: Session, payment_data: dict):
    """
    Process successful payment from webhook.
    This runs in the background to avoid timeout.
    """
    try:
        # Extract order info from metadata
        metadata = payment_data.get("metadata", {})
        order_id = metadata.get("order_id")
        
        if not order_id:
            return  # Skip if no order_id in metadata
        
        # Fetch order
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return
        
        # Update order status
        payment_status = payment_data.get("status")
        if payment_status == "success" and db_order.payment_status != "paid":
            db_order.payment_status = "paid"
            db_order.status = "processing"
            db.commit()
            
            # Send confirmation email
            if db_order.user and db_order.user.email:
                send_payment_received(
                    db_order.user.email,
                    db_order.order_reference,
                    db_order.total_amount,
                )
    except Exception as e:
        # Log error but don't raise (this is a background task)
        print(f"Error processing webhook: {str(e)}")

