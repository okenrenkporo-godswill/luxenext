from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud
from auth import get_current_user
from database import get_db
import models

router = APIRouter(prefix="/cart", tags=["Cart"])

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}

# ---------------------------
# Get Current User Cart
# ---------------------------
@router.get("/user", summary="Get current user's cart")
def get_cart_by_current_user(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_cart = crud.get_cart(db, current_user.id)
    if not db_cart:
        db_cart = crud.create_cart(db, schemas.CartCreate(user_id=current_user.id))
    return crud.format_cart(db_cart)

# ---------------------------
# Add Item to Cart
# ---------------------------
@router.post("/items")
def add_item_to_cart(
    item: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_cart = crud.get_cart(db, current_user.id) or crud.create_cart(db, schemas.CartCreate(user_id=current_user.id))
    db_item = crud.add_cart_item(db, db_cart.id, item)  # merges quantity if exists
    return response_format(db_item, "Item added to cart successfully")

# ---------------------------
# Merge Guest Cart
# ---------------------------
@router.post("/merge")
def merge_guest_cart(
    items: list[schemas.CartItemCreate],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_cart = crud.get_cart(db, current_user.id) or crud.create_cart(db, schemas.CartCreate(user_id=current_user.id))
    merged_items = [crud.add_cart_item(db, db_cart.id, item) for item in items]
    return response_format(crud.format_cart(db_cart), "Guest cart merged successfully")

# ---------------------------
# Update Cart Item Quantity
# ---------------------------
@router.put("/items/{item_id}")
def update_cart_item(item_id: int, item: schemas.CartItemUpdate, db: Session = Depends(get_db)):
    db_item = crud.update_cart_item(db, item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found or removed")
    return response_format(db_item, "Cart item updated successfully")

# ---------------------------
# Remove Cart Item
# ---------------------------
@router.delete("/items/{item_id}")
def remove_cart_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.remove_cart_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return response_format(db_item, "Cart item removed successfully")

# ---------------------------
# Clear Entire Cart
# ---------------------------
@router.delete("/clear")
def clear_cart_route(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_cart = crud.get_cart(db, current_user.id)
    if not db_cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    crud.clear_cart(db, db_cart.id)
    return response_format(None, "Cart cleared successfully")
