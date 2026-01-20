from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from roles import require_role
import os
from urllib.parse import unquote
from jose import jwt
import crud

import models, schemas, database
from auth import authenticate_user, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, generate_verification_code, create_email_token, decode_email_token
from email_utilis import send_verification_email

load_dotenv()


FRONTEND_URL = os.getenv("FRONTEND_URL","https://luxenext-f.vercel.app")
BACKEND_URL = os.getenv("BACKEND_URL","https://luxenext.onrender.com")

router = APIRouter(prefix="/auth", tags=["Auth"])

class Token(BaseModel):
    access_token: str
    token_type: str

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}


# ---------------------- Register ----------------------
@router.post("/register")
async def register(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) |
        (models.User.email == user.email.lower())
    ).first()

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(400, "Username or email already registered")
        else:
            # User exists but not verified → resend code
            code = generate_verification_code()
            existing_user.verification_code = code
            existing_user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=2)
            db.commit()
            
            background_tasks.add_task(send_verification_email, existing_user.email, code, "Verify Your Account")
            return {"success": True, "message": "User exists but not verified. Verification code resent."}

    # ✅ Corrected password hashing
    hashed_password = get_password_hash(user.password)

    # Create user in DB with is_verified=False
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        hashed_password=hashed_password,  # ✅ field name fixed
        is_verified=False
    )
    
    # Generate code
    code = generate_verification_code()
    new_user.verification_code = code
    new_user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=2)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send email in background
    background_tasks.add_task(send_verification_email, new_user.email, code, "Verify Your Account")

    return {"success": True, "message": "Registration successful. Please check your email for the verification code."}



@router.post("/resend-verification")
async def resend_verification(email: str, db: Session = Depends(database.get_db), background_tasks: BackgroundTasks = None):
    user = db.query(models.User).filter(models.User.email == email.lower()).first()

    if not user:
        raise HTTPException(404, "User not found")

    if user.is_verified:
        raise HTTPException(400, "User already verified")

    # Generate new code
    code = generate_verification_code()
    user.verification_code = code
    user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=2)
    db.commit()

    # Send in background
    if background_tasks:
        background_tasks.add_task(send_verification_email, user.email, code, "Resend Verification Code")
    else:
        await send_verification_email(user.email, code, "Resend Verification Code")

    return {"success": True, "message": "Verification code resent"}


# ---------------------- Login ----------------------
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = authenticate_user(db, form_data.username.lower(), form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 🚫 Prevent unverified login
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    # ✅ Generate token
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "username": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # ✅ Return token + limited user data
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }



@router.post("/verify-email")
def verify_email(request: schemas.VerifyEmailRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == request.email.lower()).first()

    if not user:
        raise HTTPException(404, "User not found")

    if user.is_verified:
        return {"success": True, "message": "User already verified"}

    # Check code
    if not user.verification_code or user.verification_code != request.code:
        raise HTTPException(400, "Invalid verification code")

    # Check expiration
    if user.verification_code_expires_at < datetime.utcnow():
        raise HTTPException(400, "Verification code expired")

    # Mark verified
    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    db.commit()
    db.refresh(user)

    # 🔑 Generate access token immediately after verification
    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_verified": user.is_verified,
        }
    )

    # ✅ Return token + user info
    return {
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        },
    }




# ---------------------- Update Role ----------------------
@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,  # expected: "user" | "admin" | "superadmin" 
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role("superadmin"))  # ✅ only superadmin can assign roles
):
    if new_role not in ["user", "admin", "superadmin"]:
        raise HTTPException(400, "Invalid role")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    # 🚨 Prevent superadmin from demoting themselves
    if user.id == current_user.id and new_role != "superadmin":
        raise HTTPException(403, "You cannot change your own role from superadmin")

    user.role = new_role
    db.commit()
    db.refresh(user)
    return response_format(
        {"id": user.id, "username": user.username, "new_role": new_role},
        f"User {user.username}'s role updated to {new_role}"
    )

# ---------------------- Create Admin ----------------------
@router.post("/create-admin")
def create_admin(
    username: str,
    email: str,
    password: str,
    db: Session = Depends(database.get_db),
    current_user = Depends(require_role("superadmin"))  # ✅ only superadmin can create admins
):
    # check duplicates
    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(400, "Username already exists")
    if db.query(models.User).filter(models.User.email == email.lower()).first():
        raise HTTPException(400, "Email already exists")

    hashed_password = get_password_hash(password)
    new_admin = models.User(
        username=username,
        email=email.lower(),
        hashed_password=hashed_password,
        role="admin",
        is_verified=True  # ✅ directly verified since superadmin created them
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return response_format(
        {"id": new_admin.id, "username": new_admin.username, "role": new_admin.role},
        f"Admin {username} created successfully"
    )


# ---------------------- Delete Admin ----------------------
@router.delete("/delete-admin/{admin_id}")
def delete_admin(
    admin_id: int,
    db: Session = Depends(database.get_db),
    _= Depends(require_role("superadmin"))  # ✅ only superadmin can delete admins
):
    user = db.query(models.User).filter(models.User.id == admin_id).first()

    if not user:
        raise HTTPException(404, "Admin not found")

    if user.role != "admin":
        raise HTTPException(400, "This user is not an admin")

    db.delete(user)
    db.commit()

    return response_format(
        {"id": admin_id, "username": user.username},
        f"Admin {user.username} deleted successfully"
    )


# ---------------------- Get All Admins ----------------------
@router.get("/admins")
def get_all_admins(
    db: Session = Depends(database.get_db),
    _ = Depends(require_role("superadmin"))  # ✅ only superadmin can see all admins
):
    admins = db.query(models.User).filter(models.User.role == "admin").all()

    if not admins:
        raise HTTPException(404, "No admins found")

    return response_format(
        [{"id": admin.id, "username": admin.username, "email": admin.email, "role": admin.role} for admin in admins],
        "Admins retrieved successfully"
    )


    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user.hashed_password = hashed_pw
    db.commit()

    return {"message": "Password reset successful"}