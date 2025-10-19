from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud
from roles import require_role
from database import get_db

router = APIRouter(
   prefix="/coupons",
   tags=["Coupons"]
)

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}

@router.post("/")

def create_coupon(coupon: schemas.CouponCreate, db: Session = Depends(get_db) ,  _= Depends(require_role("admin", "superadmin"))):
    return response_format(crud.create_coupon(db, coupon), "Coupon created successfully")

@router.get("/{coupon_id}")
def get_coupon(coupon_id: int, db: Session = Depends(get_db)):
    db_coupon = crud.get_coupon(db, coupon_id)
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return response_format(db_coupon, "Coupon retrieved successfully")

@router.get("/")
def get_coupons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return response_format(crud.get_coupons(db, skip, limit), "Coupons retrieved successfully")

@router.put("/{coupon_id}")
def update_coupon(coupon_id: int, coupon: schemas.CouponCreate, db: Session = Depends(get_db),  _= Depends(require_role("admin", "superadmin"))):
    db_coupon = crud.update_coupon(db, coupon_id, coupon)
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return response_format(db_coupon, "Coupon updated successfully")

@router.delete("/{coupon_id}")
def delete_coupon(coupon_id: int, db: Session = Depends(get_db),_= Depends(require_role("admin", "superadmin"))):
    db_coupon = crud.delete_coupon(db, coupon_id)
    if not db_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return response_format(db_coupon, "Coupon deleted successfully")
