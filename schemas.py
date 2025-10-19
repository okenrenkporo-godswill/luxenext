from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# ===============================
# Coupon Schemas
# ===============================
class CouponBase(BaseModel):
    code: str
    discount_percent: float
    valid_from: datetime
    valid_to: datetime
    active: bool = True

class CouponCreate(CouponBase):
    pass

class CouponUpdate(BaseModel):
    code: Optional[str] = None
    discount_percent: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    active: Optional[bool] = None

class Coupon(CouponBase):
    id: int

    class Config:
        from_attributes = True

# ===============================
# Wishlist Schemas
# ===============================
class WishlistBase(BaseModel):
    user_id: int
    product_id: int

class WishlistCreate(WishlistBase):
    pass

class Wishlist(WishlistBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ===============================
# PaymentMethod Schemas
# ===============================
class PaymentMethodCreateSimple(BaseModel):
    method_type: str
    provider: Optional[str] = None
    account_number: Optional[str] = None
    expiry_date: Optional[str] = None

class PaymentMethodBase(BaseModel):
    user_id: int
    method_type: str
    provider: Optional[str] = None
    account_number: Optional[str] = None
    expiry_date: Optional[str] = None
    is_default: bool = False

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodUpdate(BaseModel):
    method_type: Optional[str] = None
    provider: Optional[str] = None
    account_number: Optional[str] = None
    expiry_date: Optional[str] = None
    is_default: Optional[bool] = None

class PaymentMethod(PaymentMethodBase):
    id: int

    class Config:
        from_attributes = True

# ===============================
# Address Schemas
# ===============================
class AddressBase(BaseModel):
    address_line: str
    city: str
    state: str
    country: str
    postal_code: str
    phone_number: str

class AddressCreate(AddressBase):
    pass  # ✅ user_id will be injected automatically from current_user

class AddressUpdate(BaseModel):
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone_number: Optional[str] = None

class Address(AddressBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
# ===============================
# Category Schemas
# ===============================

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    class Config:
        orm_mode = True


# ===============================
# Product Schemas
# ===============================
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    image_url: Optional[str] = None   # Full-size image
    thumbnail_url: Optional[str] = None  # 👈 Thumbnail
    category_id: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None 
    category_id: Optional[int] = None

class Product(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ===============================
# User Schemas
# ===============================
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "user"   # "user", "admin", "superadmin"
    is_verified: bool = False

class UserCreate(UserBase):
    password: str



class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
   

class User(UserBase):
    id: int
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ===============================
# CartItem Schemas

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ===============================
# CartItem Schemas
# ===============================
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None

class CartItem(CartItemBase):
    id: int
    cart_id: int
    price_at_addition: float  # ✅ snapshot price
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    product_thumbnail: Optional[str] = None
    subtotal: Optional[float] = None  # quantity * price_at_addition

    class Config:
        from_attributes = True


# ===============================
# Cart Schemas
# ===============================
class CartBase(BaseModel):
    user_id: int

class CartCreate(CartBase):
    items: List[CartItemCreate] = Field(default_factory=list)

class Cart(CartBase):
    id: int
    created_at: datetime
    items: List[CartItem] = Field(default_factory=list)

    # Cart totals
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0

    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float
    product_snapshot: Optional[dict] = None  # Snapshot of product info at checkout

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int

    class Config:
        orm_mode = True
# ===============================
class OrderBase(BaseModel):
    user_id: int
    address_id: int
    status: str = "pending"
    total_amount: float
    discount_amount: float = 0.0
    payment_method: Optional[str] = None
    payment_status: str = "pending"

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]
    coupon_ids: Optional[List[int]] = None  # Optional, not required

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    total_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    payment_status: Optional[str] = None
    address_id: Optional[int] = None

class Order(OrderBase):
    id: int
    order_reference: str
    created_at: datetime
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[OrderItem] = []
    coupons: List[dict] = []  # coupon code and discount info

    class Config:
        orm_mode = True


class CheckoutRequest(BaseModel):
    address_id: int
    payment_method_id: int
    coupon_ids: Optional[List[int]] = None

class ConfirmPaymentRequest(BaseModel):
    payment_reference: str

# ===============================
# Review Schemas
# ===============================
class ReviewBase(BaseModel):
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None

class Review(ReviewBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
