from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, UniqueConstraint,JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Table
from database import Base
import uuid

# models.py
# SQLAlchemy models for a basic e-commerce website (like Jumia or Temu)
# These models cover Users, Products, Categories, Orders, OrderItems, Reviews, and Addresses.


# You can add more features by defining additional models and relationships.
# Example extensions:
order_coupons = Table(
    'order_coupons', Base.metadata,
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('coupon_id', Integer, ForeignKey('coupons.id'))
)

# Coupon model for discounts
class Coupon(Base):
    __tablename__ = 'coupons'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_percent = Column(Float, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True)


    # Coupons can be applied to orders

# Wishlist model for users
class Wishlist(Base):
    __tablename__ = 'wishlists'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')
    product = relationship('Product')

    # Users can add products to their wishlist

# PaymentMethod model for storing user payment optionsclass PaymentOption(Base):
class PaymentOption(Base):
    __tablename__ = "payment_options"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)        # e.g. "Bank Transfer"
    provider = Column(String(100), nullable=False)    # e.g. "GTBank"
    account_name = Column(String(150), nullable=True) # e.g. "BuyPoint Ecommerce"
    account_number = Column(String(50), nullable=True) # e.g. "0123456789"
    is_active = Column(Boolean, default=True)



# The relationship to Coupon will be added inside the Order class below.
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
  
    role = Column(String(20), default="user")
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


    addresses = relationship('Address', back_populates='user')
    orders = relationship('Order', back_populates='user')
    reviews = relationship('Review', back_populates='user')

    # Users can have multiple addresses, orders, and reviews

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    address_line = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    phone_number = Column(String(20), nullable=False)

    user = relationship('User', back_populates='addresses')

    # Stores user shipping/billing addresses

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)

    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")
    # Categories help organize products


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image_url = Column(String(255))
    thumbnail_url = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # <-- soft delete flag

    category = relationship('Category', back_populates='products')
    order_items = relationship('OrderItem', back_populates='product')
    reviews = relationship('Review', back_populates='product')

    # Products belong to a category and can have reviews
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_reference = Column(String(20), unique=True, index=True, default=lambda: f"ORD-{uuid.uuid4().hex[:8].upper()}")
    user_id = Column(Integer, ForeignKey('users.id'))
    address_id = Column(Integer, ForeignKey('addresses.id'))

    status = Column(String(50), default='pending')  
    payment_method = Column(String(50), nullable=True)  
    payment_status = Column(String(50), default='pending')  

    payment_option_id = Column(Integer, ForeignKey("payment_options.id"), nullable=True)  # ✅ new column

    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)  
    created_at = Column(DateTime, default=datetime.utcnow)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    user = relationship('User', back_populates='orders')
    address = relationship('Address')
    items = relationship('OrderItem', back_populates='order', cascade="all, delete-orphan")
    coupons = relationship('Coupon', secondary=order_coupons, backref='orders')
    payment_option = relationship('PaymentOption')  # 🔹 link to PaymentOption


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Snapshot price at checkout
    product_snapshot = Column(JSON, nullable=True)  # Snapshot of product info (name, image, etc.)

    # Relationships
    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')

    def __repr__(self):
        return f"<OrderItem Product {self.product_id} | Qty {self.quantity} | Price {self.price}>"

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='reviews')
    product = relationship('Product', back_populates='reviews')

    # Users can leave reviews for products


class Cart(Base):
    __tablename__ = 'carts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ Ensure one cart per user
    __table_args__ = (UniqueConstraint('user_id', name='unique_user_cart'),)

    user = relationship('User')
    items = relationship('CartItem', back_populates='cart', cascade="all, delete-orphan")  
    # ✅ Cascade delete ensures if a cart is removed, its items are removed too

class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False, default=1)

    # ✅ Price snapshot (locks price when added to cart)
    price_at_addition = Column(Float, nullable=False)

    cart = relationship('Cart', back_populates='items')
    product = relationship('Product')



