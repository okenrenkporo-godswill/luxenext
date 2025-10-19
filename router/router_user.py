from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud, models
from database import get_db
from roles import require_role

router = APIRouter(prefix="/users", tags=["Users"])

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}


# ===============================
# ✅ Superadmin Settings Update
# ===============================
@router.put("/settings")
def update_superadmin_settings(
    settings: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superadmin"))
):
    """Allow superadmin to update their profile info (e.g., name, email, password)"""
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if settings.username:
        existing = db.query(models.User).filter(models.User.username == settings.username).first()
        if existing and existing.id != user.id:
            raise HTTPException(400, "Username already in use")

        user.username = settings.username

    if settings.email:
        existing = db.query(models.User).filter(models.User.email == settings.email).first()
        if existing and existing.id != user.id:
            raise HTTPException(400, "Email already in use")

        user.email = settings.email.lower()

    if settings.password:
        from auth import get_password_hash
        user.hashed_password = get_password_hash(settings.password)

    db.commit()
    db.refresh(user)
    return response_format({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }, "Superadmin settings updated successfully")


# ===============================
# Get User by ID
# ===============================
@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_role("superadmin"))):
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return response_format(db_user, "User retrieved successfully")


# ===============================
# Get All Users
# ===============================
@router.get("/")
def get_users(db: Session = Depends(get_db), _=Depends(require_role("superadmin"))):
    db_users = crud.get_users(db)
    return response_format(db_users, "All users retrieved successfully")


# ===============================
# Update Any User (Superadmin privilege)
# ===============================
@router.put("/{user_id}")
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role("superadmin"))
):
    db_user = crud.update_user(db, user_id, user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return response_format(db_user, "User updated successfully")


# ===============================
# Delete User
# ===============================
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_role("superadmin"))):
    db_user = crud.delete_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return response_format(db_user, "User deleted successfully")
