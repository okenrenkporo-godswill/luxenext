from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime
import models
import schemas
from models import Cart, CartItem, Product ,Coupon, Order, OrderItem
import os
import random, string
from PIL import Image

# -------------------
# Coupon CRUD
# -------------------
def create_coupon(db: Session, coupon: schemas.CouponCreate):
    try:
        db_coupon = models.Coupon(**coupon.model_dump())
        db.add(db_coupon)
        db.commit()
        db.refresh(db_coupon)
        return db_coupon
    except Exception as e:
        return {"error": str(e)}

def get_coupon(db: Session, coupon_id: int):
    return db.query(models.Coupon).filter(models.Coupon.id == coupon_id).first()

def get_coupons(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Coupon).offset(skip).limit(limit).all()

def update_coupon(db: Session, coupon_id: int, coupon: schemas.CouponUpdate):
    db_coupon = get_coupon(db, coupon_id)
    if db_coupon:
        for key, value in coupon.model_dump(exclude_unset=True).items():
            setattr(db_coupon, key, value)
        db.commit()
        db.refresh(db_coupon)
    return db_coupon

def delete_coupon(db: Session, coupon_id: int):
    db_coupon = get_coupon(db, coupon_id)
    if db_coupon:
        db.delete(db_coupon)
        db.commit()
    return db_coupon

# -------------------
# Wishlist CRUD
# -------------------
def create_wishlist(db: Session, wishlist: schemas.WishlistCreate):
    # Optional: check for duplicates
    existing = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == wishlist.user_id,
        models.Wishlist.product_id == wishlist.product_id
    ).first()
    if existing:
        return existing
    db_wishlist = models.Wishlist(**wishlist.model_dump())
    db.add(db_wishlist)
    db.commit()
    db.refresh(db_wishlist)
    return db_wishlist

def get_wishlist_by_id(db: Session, wishlist_id: int):
    return db.query(models.Wishlist).filter(models.Wishlist.id == wishlist_id).first()

def get_user_wishlist(db: Session, user_id: int):
    return db.query(models.Wishlist).options(joinedload(models.Wishlist.product)).filter(models.Wishlist.user_id == user_id).all()

def delete_wishlist(db: Session, wishlist_id: int):
    db_wishlist = get_wishlist_by_id(db, wishlist_id)
    if db_wishlist:
        db.delete(db_wishlist)
        db.commit()
    return db_wishlist

# -------------------
# # PaymentMethod CRUD
# -------------------
def create_payment_method(db: Session, payment: schemas.PaymentMethodCreate):
    db_payment = models.PaymentMethod(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment_method(db: Session, payment_id: int):
    return db.query(models.PaymentMethod).filter(models.PaymentMethod.id == payment_id).first()

def get_payment_methods(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PaymentMethod).offset(skip).limit(limit).all()

def update_payment_method(db: Session, payment_id: int, payment: schemas.PaymentMethodUpdate):
    db_payment = get_payment_method(db, payment_id)
    if db_payment:
        for key, value in payment.model_dump(exclude_unset=True).items():
            setattr(db_payment, key, value)
        db.commit()
        db.refresh(db_payment)
    return db_payment

def delete_payment_method(db: Session, payment_id: int):
    db_payment = get_payment_method(db, payment_id)
    if db_payment:
        db.delete(db_payment)
        db.commit()
    return db_payment

# -------------------
# Address CRUD
# -------------------

def create_address(db: Session, address: schemas.AddressCreate, user_id: int):
    db_address = models.Address(**address.model_dump(), user_id=user_id)
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

def get_address(db: Session, address_id: int):
    return db.query(models.Address).filter(models.Address.id == address_id).first()

def get_addresses(db: Session, user_id: int):
    return db.query(models.Address).filter(models.Address.user_id == user_id).all()

def update_address(db: Session, address_id: int, address: schemas.AddressUpdate):
    db_address = get_address(db, address_id)
    if db_address:
        for key, value in address.model_dump(exclude_unset=True).items():
            setattr(db_address, key, value)
        db.commit()
        db.refresh(db_address)
    return db_address

def delete_address(db: Session, address_id: int):
    db_address = get_address(db, address_id)
    if db_address:
        db.delete(db_address)
        db.commit()
    return db_address


# -------------------
# Category CRUD
# -------------------


def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def update_category(db: Session, category_id: int, category: schemas.CategoryUpdate):
    db_category = get_category(db, category_id)
    if db_category:
        for key, value in category.model_dump(exclude_unset=True).items():
            setattr(db_category, key, value)
        db.commit()
        db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if db_category:
        # Optional: prevent delete if products exist
        if db_category.products:
            return None
        db.delete(db_category)
        db.commit()
    return db_category

# -------------------
# Product CRUD
# -------------------
def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products(db: Session):
    return db.query(models.Product).all()


def update_product(db: Session, product_id: int, product: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if db_product:
        for key, value in product.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
    return db_product


def delete_product(db: Session, product: models.Product):
    db.delete(product)
    db.commit()




def search_products(
    db: Session,
    q: str,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort: Optional[str] = "relevance",
    skip: int = 0,
    limit: int = 20
) -> List[models.Product]:
    query = db.query(models.Product)

    # 🔍 Search by name or description
    query = query.filter(
        (models.Product.name.ilike(f"%{q}%")) |
        (models.Product.description.ilike(f"%{q}%"))
    )

    # 🏷️ Category filter
    if category_id:
        query = query.filter(models.Product.category_id == category_id)

    # 💰 Price filtering
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)

    # 📊 Sorting
    if sort == "price_asc":
        query = query.order_by(models.Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Product.price.desc())
    elif sort == "name_asc":
        query = query.order_by(models.Product.name.asc())
    elif sort == "name_desc":
        query = query.order_by(models.Product.name.desc())
    else:
        # Default "relevance" → order by ID newest first
        query = query.order_by(models.Product.id.desc())

    # 📑 Pagination
    return query.offset(skip).limit(limit).all()


# -------------------
# User CRUD
# -------------------
def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user: schemas.UserUpdate, hashed_password: Optional[str] = None):
    db_user = get_user(db, user_id)
    if db_user:
        for key, value in user.model_dump(exclude_unset=True).items():
            setattr(db_user, key, value)
        if hashed_password:
            db_user.hashed_password = hashed_password
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# -------------------
# Order CRUD
# -------------------
def generate_order_reference(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# checkout_cart was duplicated here - removed first instance.


# ===============================
# Get Orders by User
# ===============================
def get_orders_by_user(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).all()


# ===============================
# Get Single Order
# ===============================
def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


# ===============================
# Update Order Status
# ===============================
def update_order_status(db: Session, order_id: int, status: str):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None
    order.status = status
    if status == "shipped":
        order.shipped_at = datetime.utcnow()
    elif status == "delivered":
        order.delivered_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order_id: int):
    """
    Cancel an order:
    - Sets status to 'cancelled'
    - Restores product stock
    - Keeps order in DB for history
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None

    # Only allow cancellation if not delivered
    if order.status in ["delivered", "cancelled"]:
        raise Exception(f"Cannot cancel order with status '{order.status}'")

    # Update order status
    order.status = "cancelled"

    # Restore stock
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
            db.add(product)

    db.commit()
    db.refresh(order)
    return order

# -------------------
# Review CRUD
# -------------------
def create_review(db: Session, review: schemas.ReviewCreate):
    db_review = models.Review(**review.model_dump())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def get_review(db: Session, review_id: int):
    return db.query(models.Review).filter(models.Review.id == review_id).first()

def get_reviews(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Review).offset(skip).limit(limit).all()

def update_review(db: Session, review_id: int, review: schemas.ReviewUpdate):
    db_review = get_review(db, review_id)
    if db_review:
        for key, value in review.model_dump(exclude_unset=True).items():
            setattr(db_review, key, value)
        db.commit()
        db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int):
    db_review = get_review(db, review_id)
    if db_review:
        db.delete(db_review)
        db.commit()
    return db_review

# -------------------
# Cart CRUD (NEW)

# ===============================
# Create Cart
# ===============================


# ===============================
# Create Cart
# ===============================
def create_cart(db: Session, cart: schemas.CartCreate):
    # Check if user already has a cart
    db_cart = db.query(Cart).filter(Cart.user_id == cart.user_id).first()
    if not db_cart:
        db_cart = Cart(user_id=cart.user_id)
        db.add(db_cart)
        db.commit()
        db.refresh(db_cart)

    # Add items if provided
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            continue

        # Check if item already exists
        db_item = db.query(CartItem).filter(
            CartItem.cart_id == db_cart.id,
            CartItem.product_id == item.product_id
        ).first()

        if db_item:
            db_item.quantity += item.quantity
        else:
            db_item = CartItem(
                cart_id=db_cart.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_addition=product.price  # snapshot
            )
            db.add(db_item)

    db.commit()
    db.refresh(db_cart)
    return db_cart  # ✅ return ORM object


# ===============================
# Add Item to Cart
# ===============================

def add_cart_item(db: Session, cart_id: int, item: schemas.CartItemCreate):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id,
        CartItem.product_id == item.product_id
    ).first()

    if db_item:
        # ✅ update quantity
        db_item.quantity += item.quantity
    else:
        # ✅ create new cart item
        db_item = CartItem(
            cart_id=cart_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_addition=product.price,  # snapshot at add time
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_item)
    return db_item


def get_cart(db: Session, user_id: int):
    return db.query(Cart).filter(Cart.user_id == user_id).first()
  # ✅ still return ORM object

 
def format_cart(cart: Cart):
    if not cart:
        return {"items": [], "subtotal": 0.0, "tax": 0.0, "total": 0.0}

    subtotal = 0.0
    cart_items = []

    for item in cart.items:
        if item.product:
            subtotal += item.price_at_addition * item.quantity
            cart_items.append({
                "id": item.id,
                "cart_id": item.cart_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "product_name": item.product.name,
                "product_price": item.price_at_addition,
                "product_image": item.product.image_url,
                "product_thumbnail": item.product.thumbnail_url,
                "subtotal": item.price_at_addition * item.quantity
            })

    tax_rate = 0.05
    tax = subtotal * tax_rate
    total = subtotal + tax

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "created_at": cart.created_at,
        "items": cart_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }

# ===============================
# Update Cart Item
# ===============================
def update_cart_item(db: Session, item_id: int, item: schemas.CartItemUpdate):
    db_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not db_item:
        return None

    if item.quantity is not None:
        if item.quantity <= 0:
            db.delete(db_item)
            db.commit()
            return None
        else:
            db_item.quantity = item.quantity

    db.commit()
    db.refresh(db_item)
    return db_item

# ===============================
# Remove Item from Cart
# ===============================
def remove_cart_item(db: Session, item_id: int):
    db_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not db_item:
        return None
    db.delete(db_item)
    db.commit()
    return db_item

def clear_cart(db: Session, cart_id: int):
    items = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).all()
    for item in items:
        db.delete(item)
    db.commit()
    return items


# ===============================
# Clear Cart
# ================

def format_cart(cart: Cart):
    if not cart:
        return {"items": [], "subtotal": 0.0, "tax": 0.0, "total": 0.0}

    subtotal = 0.0
    cart_items = []

    for item in cart.items:
        if item.product:
            subtotal += item.price_at_addition * item.quantity
            cart_items.append({
                "id": item.id,
                "cart_id": item.cart_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "product_name": item.product.name,
                "product_price": item.price_at_addition,  # snapshot at add time
                "product_image": item.product.image_url,  # full-size
                "product_thumbnail": item.product.thumbnail_url,  # ✅ thumbnail
                "subtotal": item.price_at_addition * item.quantity
            })

    tax_rate = 0.05
    tax = subtotal * tax_rate
    total = subtotal + tax

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "created_at": cart.created_at,
        "items": cart_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }


def checkout_cart(db: Session, user_id: int, address_id: int, coupon_ids: list[int] = None):
    # 1️⃣ Get the user's cart
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = 0.0
    order_items_data = []

    # 2️⃣ Validate stock and prepare order items
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        if product.stock < item.quantity:
             # Raise 400 Bad Request instead of generic Exception to avoid 500 error
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name} (Available: {product.stock}, Requested: {item.quantity})")

        subtotal += item.price_at_addition * item.quantity
        order_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price_at_addition
        })

    # 3️⃣ Apply tax (5%)
    tax_rate = 0.05
    tax = subtotal * tax_rate
    total = subtotal + tax

    # 4️⃣ Apply coupons if provided
    coupons = []
    discount_total = 0.0
    if coupon_ids:
        for cid in coupon_ids:
            coupon = db.query(Coupon).filter(Coupon.id == cid, Coupon.active == True).first()
            if coupon:
                discount_amount = total * (coupon.discount_percent / 100)
                total -= discount_amount
                discount_total += discount_amount
                coupons.append(coupon)

    # 5️⃣ Create Order
    db_order = Order(
        user_id=user_id,
        address_id=address_id,
        total_amount=total,
        discount_amount=discount_total,
        status="pending",
        payment_status="pending",
        order_reference=generate_order_reference() # ensure unique reference is generated
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # 6️⃣ Create OrderItems and update stock
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price=item_data["price"]
        )
        db.add(order_item)

        # 📉 Deduct stock
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock -= item_data["quantity"]
        db.add(product)

    # 7️⃣ Link coupons
    for coupon in coupons:
        db_order.coupons.append(coupon)

    db.commit()

    # 8️⃣ Clear cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()

    db.refresh(db_order)
    return db_order
