from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import  bcrypt, os
from auth import get_password_hash
from jose import jwt
from database import get_db
from models import User
from email_utilis import send_reset_email


router = APIRouter(prefix="/password",
                    tags=["password"])

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# ✅ Forgot Password - Send Reset Email
@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    email = email.lower().strip()  # normalize input
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(minutes=10)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"

    await send_reset_email(user.email, reset_link)
    return {"message": f"Password reset email sent to {user.email}"}

    return {"message": "Password reset email sent."}


# ✅ Reset Password
@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Correct: hash password using same function as register/login
    hashed_pw = get_password_hash(new_password)
    user.hashed_password = hashed_pw  

    db.commit()
    db.refresh(user)

    return {"message": "Password reset successful"}