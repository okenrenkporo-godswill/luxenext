from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from roles import require_role
import os
from urllib.parse import unquote
from jose import jwt
import crud

import models, schemas, database
from auth import authenticate_user, create_access_token, create_email_token, get_password_hash, decode_email_token, ACCESS_TOKEN_EXPIRE_MINUTES
from email_utilis import send_verification_email

load_dotenv()


FRONTEND_URL =  os.environ.get("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL =  os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

router = APIRouter(prefix="/auth", tags=["Auth"])

class Token(BaseModel):
    access_token: str
    token_type: str

def response_format(data=None, message="Success", success=True):
    return {"success": success, "message": message, "data": data}


# ---------------------- Register -------------------# ---------------------- Register ----------------------
@router.post("/register")
async def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) |
        (models.User.email == user.email.lower())
    ).first()

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(400, "Username or email already registered")
        else:
            # User exists but not verified → resend link
            email_token = create_email_token({
                "username": existing_user.username,
                "email": existing_user.email,
            })
            verification_link = f"{ os.environ.get('FRONTEND_URL').rstrip('/')}/auth/verify?token={email_token}"
            await send_verification_email(existing_user.email, verification_link, "Verify Your Account")
            return {"success": True, "message": "User exists but not verified. Verification email resent."}

    # ✅ Corrected password hashing
    hashed_password = get_password_hash(user.password)

    # Create user in DB with is_verified=False
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        hashed_password=hashed_password,  # ✅ field name fixed
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate token & link (no password in token anymore 👍)
    email_token = create_email_token({
        "username": new_user.username,
        "email": new_user.email,
    })
    verification_link = f"{ os.environ.get('FRONTEND_URL').rstrip('/')}/auth/verify?token={email_token}"

    # Send email
    await send_verification_email(new_user.email, verification_link, "Verify Your Account")

    return {"success": True, "message": "Registration successful. Please check your email to verify your account."}


from fastapi import BackgroundTasks

@router.post("/resend-verification")
async def resend_verification(email: str, db: Session = Depends(database.get_db), background_tasks: BackgroundTasks = None):
    user = db.query(models.User).filter(models.User.email == email.lower()).first()

    if not user:
        raise HTTPException(404, "User not found")

    if user.is_verified:
        raise HTTPException(400, "User already verified")

    # Generate new token
    email_token = create_email_token({
        "username": user.username,
        "email": user.email,
    })
    verification_link = f"{ os.environ.get('FRONTEND_URL').rstrip('/')}/auth/verify?token={email_token}"

    # Send in background
    background_tasks.add_task(send_verification_email, user.email, verification_link, "Resend Verification Link")

    return {"success": True, "message": "Verification email resent"}


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



@router.get("/verify")
def verify_email(token: str, db: Session = Depends(database.get_db)):
    payload = decode_email_token(token)

    user = db.query(models.User).filter(
        models.User.email == payload["email"].lower()
    ).first()

    if user:
        user.is_verified = True
        db.commit()
        db.refresh(user)
    else:
        hashed_password = get_password_hash(payload["password"])
        user = models.User(
            username=payload["username"],
            email=payload["email"].lower(),
            hashed_password=hashed_password,
            role="user",
            is_verified=True,  # ✅ ensure it's True after verification
        )
        db.add(user)
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