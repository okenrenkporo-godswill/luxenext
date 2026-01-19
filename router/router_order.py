from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import schemas, crud, models
from database import get_db
from roles import get_current_user, require_role  # 🔒 add admin role check
from models import User, Address, PaymentOption
from email_utilis import send_order_email

router = APIRouter(prefix="/orders", tags=["Orders"])

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}

# ===============================
# Create Order / Checkout Cart
# ===============================


@router.post("/checkout")
def checkout_cart_route(
    request: schemas.CheckoutRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user or not current_user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get payment method
    payment_method = db.query(PaymentOption).filter(
        PaymentOption.id == request.payment_method_id,
        PaymentOption.is_active == True
    ).first()
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    # Create order (stock ignored)
    db_order = crud.checkout_cart(
        db,
        user_id=current_user.id,
        address_id=request.address_id,
        coupon_ids=request.coupon_ids,
    )

    # Attach payment info
    db_order.payment_method = payment_method.provider
    db_order.payment_option_id = payment_method.id
    manual_providers = ["opay", "uba bank", "gtbank"]
    db_order.payment_status = "awaiting_confirmation" if payment_method.provider.lower() in manual_providers else "pending"

    db.commit()
    db.refresh(db_order)

    # Prepare response
    items_data = [
        {
            "name": item.product_snapshot.get("name") if item.product_snapshot else item.product.name,
            "quantity": item.quantity,
            "price": item.price
        }
        for item in db_order.items
    ]

    db_address = db.query(Address).filter(Address.id == request.address_id).first()
    address_data = {
        "city": db_address.city,
        "state": db_address.state,
        "country": db_address.country,
        "postal_code": db_address.postal_code,
    } if db_address else None

    order_data = {
        "id": db_order.id,
        "order_reference": db_order.order_reference,
        "status": db_order.status,
        "total_amount": db_order.total_amount,
        "payment_status": db_order.payment_status,
        "payment_method": db_order.payment_method,
        "items": items_data,
        "address": address_data
    }

    # Send email
    if current_user.email:
        background_tasks.add_task(
            send_order_email,
            current_user.email,
            f"Order Confirmation - {db_order.order_reference}",
            order_data
        )

    return response_format(order_data, "Checkout successful, order created")




# ===============================
# Get All Orders (Admin & Superadmin Only)
# ===============================
@router.get("/")
def get_all_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view all orders")

    db_orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()
    if not db_orders:
        return response_format([], "No orders found")

    formatted_orders = []
    for order in db_orders:
        # 🛒 Get order items
        items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).all()
        order_items = []
        for item in items:
            product_name = item.product or (
                item.product_snapshot.get("name") if item.product_snapshot else "Unknown Product"
            )
            order_items.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product_name,
                "price": item.price,
                "quantity": item.quantity,
                "subtotal": item.price * item.quantity,
            })

        # 👤 User details
        user = db.query(models.User).filter(models.User.id == order.user_id).first()
        user_info = {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": user.role,
        } if user else {
            "id": None,
            "name": "Deleted User",
            "email": "N/A",
            "role": "unknown"
        }

        formatted_orders.append({
            "id": order.id,
            "order_reference": order.order_reference,
            "user": user_info,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_amount": order.total_amount,
            "payment_method": order.payment_method,
            "created_at": order.created_at,
            "items": order_items,
        })

    return response_format(formatted_orders, "All orders retrieved successfully")

# ===============================
# Get Order by ID (only owner or admin)
# ===============================   

@router.get("/user")
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_orders = crud.get_orders_by_user(db, current_user.id)
    return response_format(db_orders, "User orders retrieved successfully")


@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_order = crud.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Allow owner, admin, or superadmin
    if db_order.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    # 🛒 Get order items
    items = db.query(models.OrderItem).filter(models.OrderItem.order_id == db_order.id).all()
    order_items = []
    for item in items:
        product_name = (
            item.product_snapshot.get("name") if item.product_snapshot
            else (item.product.name if item.product else "Unknown Product")
        )

        # Get product image
        product_image = (
            item.product_snapshot.get("image") if item.product_snapshot and item.product_snapshot.get("image")
            else (item.product.image if item.product and getattr(item.product, "image", None) else None)
        )

        order_items.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product_name,
            "price": item.price,
            "quantity": item.quantity,
            "subtotal": item.price * item.quantity,
            "image": product_image,
        })

    # 👤 User details
    user = db.query(models.User).filter(models.User.id == db_order.user_id).first()
    user_info = {
        "id": user.id,
        "name": user.username,
        "email": user.email,
        "role": user.role,
    } if user else {
        "id": None,
        "name": "Deleted User",
        "email": "N/A",
        "role": "unknown"
    }

    # 🏠 Address details
    address = db.query(models.Address).filter(models.Address.id == db_order.address_id).first()
    address_info = {
        "id": address.id,
        "city": address.city,
        "state": address.state,
        "country": address.country,
        "postal_code": address.postal_code,
    } if address else None

    order_data = {
        "id": db_order.id,
        "order_reference": db_order.order_reference,
        "status": db_order.status,
        "payment_status": db_order.payment_status,
        "total_amount": db_order.total_amount,
        "payment_method": db_order.payment_method,
        "created_at": db_order.created_at,
        "items": order_items,
        "user": user_info,
        "address": address_info
    }

    return response_format(order_data, "Order retrieved successfully")



# ===============================
# Get Orders by Logged-in User



# ===============================
# Update Order Status (Admin only)
# ===============================
@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    update: schemas.OrderUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "superadmin")),
):
    db_order = crud.update_order_status(db, order_id, update.status)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if db_order.user and db_order.user.email:
        background_tasks.add_task(
            send_order_email,
            db_order.user.email,
            f"Your Order {db_order.order_reference} is now {db_order.status.capitalize()}",
            db_order
        )

    return response_format(db_order, "Order status updated successfully")

# ===============================
# Cancel Order (Owner or Admin)
# ===============================
@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_order = crud.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if db_order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to cancel this order")

    try:
        db_order = crud.cancel_order(db, order_id)

        items_data = []
        for item in db_order.items:
            product_name = (
                item.product_snapshot.get("name")
                if item.product_snapshot
                else (item.product.name if item.product else "Unknown Product")
            )
            items_data.append({
                "name": product_name,
                "quantity": item.quantity,
                "price": item.price
            })

        order_data = {
            "order_reference": db_order.order_reference,
            "status": db_order.status,
            "total_amount": db_order.total_amount,
            "payment_status": db_order.payment_status,
            "items": items_data
        }

        if db_order.user and db_order.user.email:
            background_tasks.add_task(
                send_order_email,
                db_order.user.email,
                f"Your Order {db_order.order_reference} has been Cancelled",
                order_data
            )

        return response_format(db_order, "Order cancelled successfully")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===============================
# Delete Order (Admin Only)
# ===============================
@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "superadmin")),  # only admin/superadmin can delete
):
    db_order = crud.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        # Delete the order and its items
        db.delete(db_order)
        db.commit()
        return response_format(None, f"Order {db_order.order_reference} deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===============================
# Delete My Order (User Only - Pending or Canceled only)
# ===============================
@router.delete("/user/{order_id}")
def delete_my_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_order = crud.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Security check: must be owner
    if db_order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this order")

    # Logic check: only pending or canceled
    allowed_statuses = ["pending", "canceled", "failed", "awaiting_confirmation"]
    if db_order.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Cannot delete order with status: {db_order.status}")

    try:
        db.delete(db_order)
        db.commit()
        return response_format(None, "Order deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
