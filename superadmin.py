
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import dotenv_values

import models, database
from auth import oauth2_scheme

env = dotenv_values(".env")
SECRET_KEY = env.get("SECRET_KEY", "change-me")
ALGORITHM = env.get("ALGORITHM", "HS256")

def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("id"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def require_role(*roles: str):
    def role_checker(user: models.User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {roles}"
            )
        return user
    return role_checker
from database import SessionLocal
from models import User
from auth import get_password_hash

# 🚨 Change these values to your preferred credentials
SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_EMAIL = "kiyed10181@chaublog.com"
SUPERADMIN_PASSWORD = "StrongPassword123"  # use a strong password!

def create_superadmin():
    db = SessionLocal()
    existing = db.query(User).filter(User.email == SUPERADMIN_EMAIL).first()
    if existing:
        print("❌ Superadmin already exists")
        return

    superadmin = User(
        username=SUPERADMIN_USERNAME,
        email=SUPERADMIN_EMAIL,
        hashed_password=get_password_hash(SUPERADMIN_PASSWORD),
        role="superadmin",
        is_verified=True  # mark as verifieds
    )
    db.add(superadmin)
    db.commit()
    db.refresh(superadmin)
    db.close()
    print(f"✅ Superadmin created: {superadmin.username} ({superadmin.email})")

if __name__ == "__main__":
    create_superadmin()