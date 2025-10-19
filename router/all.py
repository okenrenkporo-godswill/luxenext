from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from crud import (
    create_coupon, get_coupon, get_coupons, update_coupon, delete_coupon,
    create_wishlist, get_wishlist, get_wishlists, delete_wishlist,
    create_payment_method, get_payment_method, get_payment_methods, update_payment_method, delete_payment_method,
    create_address, get_address, get_addresses, update_address, delete_address,
    create_category, get_category, get_categories, update_category, delete_category,
    create_product, get_product, get_products, update_product, delete_product,
    get_user, get_users, delete_user,
    create_order_item, get_order_item, get_order_items, delete_order_item,
    create_order, get_order, get_orders, update_order, delete_order,
    create_review, get_review, get_reviews, update_review, delete_review
)

router = APIRouter()

# Coupon Endpoints
@router.post("/coupons/", response_model=schemas.Coupon)
def create_coupon_endpoint(coupon: schemas.CouponCreate, db: Session = Depends(get_db)):
    return create_coupon(db, coupon)

@router.get("/coupons/{coupon_id}", response_model=schemas.Coupon)
def get_coupon_endpoint(coupon_id: int, db: Session = Depends(get_db)):
    db_coupon = get_coupon(db, coupon_id)
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return db_coupon

@router.get("/coupons/", response_model=List[schemas.Coupon])
def get_coupons_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_coupons(db, skip, limit)

@router.put("/coupons/{coupon_id}", response_model=schemas.Coupon)
def update_coupon_endpoint(coupon_id: int, coupon: schemas.CouponCreate, db: Session = Depends(get_db)):
    db_coupon = update_coupon(db, coupon_id, coupon)
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return db_coupon

@router.delete("/coupons/{coupon_id}", response_model=schemas.Coupon)
def delete_coupon_endpoint(coupon_id: int, db: Session = Depends(get_db)):
    db_coupon = delete_coupon(db, coupon_id)
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return db_coupon

# Wishlist Endpoints
@router.post("/wishlists/", response_model=schemas.Wishlist)
def create_wishlist_endpoint(wishlist: schemas.WishlistCreate, db: Session = Depends(get_db)):
    return create_wishlist(db, wishlist)

@router.get("/wishlists/{wishlist_id}", response_model=schemas.Wishlist)
def get_wishlist_endpoint(wishlist_id: int, db: Session = Depends(get_db)):
    db_wishlist = get_wishlist(db, wishlist_id)
    if not db_wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    return db_wishlist

@router.get("/wishlists/", response_model=List[schemas.Wishlist])
def get_wishlists_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_wishlists(db, skip, limit)

@router.delete("/wishlists/{wishlist_id}", response_model=schemas.Wishlist)
def delete_wishlist_endpoint(wishlist_id: int, db: Session = Depends(get_db)):
    db_wishlist = delete_wishlist(db, wishlist_id)
    if not db_wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    return db_wishlist

# PaymentMethod Endpoints
@router.post("/payment-methods/", response_model=schemas.PaymentMethod)
def create_payment_method_endpoint(payment: schemas.PaymentMethodCreate, db: Session = Depends(get_db)):
    return create_payment_method(db, payment)

@router.get("/payment-methods/{payment_id}", response_model=schemas.PaymentMethod)
def get_payment_method_endpoint(payment_id: int, db: Session = Depends(get_db)):
    db_payment = get_payment_method(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return db_payment

@router.get("/payment-methods/", response_model=List[schemas.PaymentMethod])
def get_payment_methods_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_payment_methods(db, skip, limit)

@router.put("/payment-methods/{payment_id}", response_model=schemas.PaymentMethod)
def update_payment_method_endpoint(payment_id: int, payment: schemas.PaymentMethodCreate, db: Session = Depends(get_db)):
    db_payment = update_payment_method(db, payment_id, payment)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return db_payment

@router.delete("/payment-methods/{payment_id}", response_model=schemas.PaymentMethod)
def delete_payment_method_endpoint(payment_id: int, db: Session = Depends(get_db)):
    db_payment = delete_payment_method(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return db_payment

# Address Endpoints
@router.post("/addresses/", response_model=schemas.Address)
def create_address_endpoint(address: schemas.AddressCreate, db: Session = Depends(get_db)):
    return create_address(db, address)

@router.get("/addresses/{address_id}", response_model=schemas.Address)
def get_address_endpoint(address_id: int, db: Session = Depends(get_db)):
    db_address = get_address(db, address_id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    return db_address

@router.get("/addresses/", response_model=List[schemas.Address])
def get_addresses_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_addresses(db, skip, limit)

@router.put("/addresses/{address_id}", response_model=schemas.Address)
def update_address_endpoint(address_id: int, address: schemas.AddressCreate, db: Session = Depends(get_db)):
    db_address = update_address(db, address_id, address)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    return db_address

@router.delete("/addresses/{address_id}", response_model=schemas.Address)
def delete_address_endpoint(address_id: int, db: Session = Depends(get_db)):
    db_address = delete_address(db, address_id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    return db_address

# Category Endpoints
@router.post("/categories/", response_model=schemas.Category)
def create_category_endpoint(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return create_category(db, category)

@router.get("/categories/{category_id}", response_model=schemas.Category)
def get_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.get("/categories/", response_model=List[schemas.Category])
def get_categories_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_categories(db, skip, limit)

@router.put("/categories/{category_id}", response_model=schemas.Category)
def update_category_endpoint(category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = update_category(db, category_id, category)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.delete("/categories/{category_id}", response_model=schemas.Category)
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    db_category = delete_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

# Product Endpoints
@router.post("/products/", response_model=schemas.Product)
def create_product_endpoint(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, product)

@router.get("/products/{product_id}", response_model=schemas.Product)
def get_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.get("/products/", response_model=List[schemas.Product])
def get_products_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_products(db, skip, limit)

@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product_endpoint(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = update_product(db, product_id, product)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.delete("/products/{product_id}", response_model=schemas.Product)
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    db_product = delete_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# User Endpoints
@router.post("/users/", response_model=schemas.User)
def create_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # You need to hash the password before calling create_user
    # hashed_password = hash_password(user.password)
    # return create_user(db, user, hashed_password)
    raise HTTPException(status_code=501, detail="Password hashing not implemented in this endpoint")

@router.get("/users/{user_id}", response_model=schemas.User)
def get_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/users/", response_model=List[schemas.User])
def get_users_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_users(db, skip, limit)

@router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    db_user = delete_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# OrderItem Endpoints
@router.post("/order-items/", response_model=schemas.OrderItem)
def create_order_item_endpoint(order_item: schemas.OrderItemCreate, order_id: int, db: Session = Depends(get_db)):
    return create_order_item(db, order_item, order_id)

@router.get("/order-items/{order_item_id}", response_model=schemas.OrderItem)
def get_order_item_endpoint(order_item_id: int, db: Session = Depends(get_db)):
    db_order_item = get_order_item(db, order_item_id)
    if not db_order_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return db_order_item

@router.get("/order-items/", response_model=List[schemas.OrderItem])
def get_order_items_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_order_items(db, skip, limit)

@router.delete("/order-items/{order_item_id}", response_model=schemas.OrderItem)
def delete_order_item_endpoint(order_item_id: int, db: Session = Depends(get_db)):
    db_order_item = delete_order_item(db, order_item_id)
    if not db_order_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return db_order_item

# Order Endpoints
@router.post("/orders/", response_model=schemas.Order)
def create_order_endpoint(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    return create_order(db, order)

@router.get("/orders/{order_id}", response_model=schemas.Order)
def get_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    db_order = get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.get("/orders/", response_model=List[schemas.Order])
def get_orders_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_orders(db, skip, limit)

@router.put("/orders/{order_id}", response_model=schemas.Order)
def update_order_endpoint(order_id: int, order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = update_order(db, order_id, order)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.delete("/orders/{order_id}", response_model=schemas.Order)
def delete_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    db_order = delete_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

# Review Endpoints
@router.post("/reviews/", response_model=schemas.Review)
def create_review_endpoint(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    return create_review(db, review)

@router.get("/reviews/{review_id}", response_model=schemas.Review)
def get_review_endpoint(review_id: int, db: Session = Depends(get_db)):
    db_review = get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review

@router.get("/reviews/", response_model=List[schemas.Review])
def get_reviews_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_reviews(db, skip, limit)

@router.put("/reviews/{review_id}", response_model=schemas.Review)
def update_review_endpoint(review_id: int, review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    db_review = update_review(db, review_id, review)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review

@router.delete("/reviews/{review_id}", response_model=schemas.Review)
def delete_review_endpoint(review_id: int, db: Session = Depends(get_db)):
    db_review = delete_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review