from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud
from database import get_db

router = APIRouter(
    prefix="/reviews", tags=["Reviews"]
)

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}


# ===============================
# Create Review
# ===============================
@router.post("/")
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    db_review = crud.create_review(db, review)
    return response_format(db_review, "Review created successfully")


# ===============================
# Get Review by ID
# ===============================
@router.get("/{review_id}")
def get_review(review_id: int, db: Session = Depends(get_db)):
    db_review = crud.get_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return response_format(db_review, "Review retrieved successfully")


# ===============================
# Get Reviews by Product
# ===============================
@router.get("/product/{product_id}")
def get_reviews_by_product(product_id: int, db: Session = Depends(get_db)):
    db_reviews = crud.get_reviews_by_product(db, product_id)
    return response_format(db_reviews, "Product reviews retrieved successfully")


# ===============================
# Get Reviews by User
# ===============================
@router.get("/user/{user_id}")
def get_reviews_by_user(user_id: int, db: Session = Depends(get_db)):
    db_reviews = crud.get_reviews_by_user(db, user_id)
    return response_format(db_reviews, "User reviews retrieved successfully")


# ===============================
# Delete Review
# ===============================
@router.delete("/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    db_review = crud.delete_review(db, review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return response_format(db_review, "Review deleted successfully")
