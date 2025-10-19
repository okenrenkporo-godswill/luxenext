from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud
from database import get_db

router = APIRouter(
   prefix="/wishlist",
   tags=["wishlist"]
)



def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}

@router.post("/")
def create_wishlist(wishlist: schemas.WishlistCreate, db: Session = Depends(get_db)):
    return response_format(crud.create_wishlist(db, wishlist), "Wishlist item created successfully")

@router.get("/{wishlist_id}")
def get_wishlist(wishlist_id: int, db: Session = Depends(get_db)):
    db_wishlist = crud.get_wishlists(db, wishlist_id)
    if not db_wishlist:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return response_format(db_wishlist, "Wishlist retrieved successfully")

@router.get("/user/{user_id}")
def get_user_wishlist(user_id: int, db: Session = Depends(get_db)):
    db_wishlist = crud.get_wishlist(db, user_id)
    return response_format(db_wishlist, "User wishlist retrieved successfully")

@router.delete("/{wishlist_id}")
def delete_wishlist(wishlist_id: int, db: Session = Depends(get_db)):
    db_wishlist = crud.delete_wishlist(db, wishlist_id)
    if not db_wishlist:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return response_format(db_wishlist, "Wishlist item deleted successfully")
