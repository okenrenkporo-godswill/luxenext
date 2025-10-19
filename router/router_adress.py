from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud
from database import get_db
from roles import get_current_user
from models import User

router = APIRouter(prefix="/addresses", tags=["Addresses"])

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}

# ===============================
# Create Address (Authenticated User Only)
# ===============================
@router.post("/")
def create_address(
    address: schemas.AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_address = crud.create_address(db, address, current_user.id)
    return response_format(db_address, "Address created successfully")

# ===============================
# Get All Addresses (Authenticated User Only)
# ===============================
@router.get("/")
def get_my_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_addresses = crud.get_addresses(db, current_user.id)
    return response_format(db_addresses, "User addresses retrieved successfully")

# ===============================
# Get Single Address (Only if owner)
# ===============================
@router.get("/{address_id}")
def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_address = crud.get_address(db, address_id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    if db_address.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this address")
    return response_format(db_address, "Address retrieved successfully")

# ===============================
# Update Address (Only if owner)
# ===============================
@router.put("/{address_id}")
def update_address(
    address_id: int,
    address: schemas.AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_address = crud.get_address(db, address_id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    if db_address.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this address")

    updated_address = crud.update_address(db, address_id, address)
    return response_format(updated_address, "Address updated successfully")

# ===============================
# Delete Address (Only if owner)
# ===============================
@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_address = crud.get_address(db, address_id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    if db_address.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this address")

    deleted_address = crud.delete_address(db, address_id)
    return response_format(deleted_address, "Address deleted successfully")
