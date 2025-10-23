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


