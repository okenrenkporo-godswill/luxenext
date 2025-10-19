from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import dotenv_values
from fastapi.security import OAuth2PasswordBearer

import models, database

# ✅ Load environment variables
env = dotenv_values(".env")
SECRET_KEY = env.get("SECRET_KEY", "change-me")
ALGORITHM = env.get("ALGORITHM", "HS256")

# ✅ OAuth2PasswordBearer (for header-based tokens)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    request: Request,
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Hybrid token extractor:
    - Tries Authorization header (Bearer token)
    - Falls back to HTTP-only cookie ('Token')
    """

    # ✅ Try header token first
    if not token:
        token = request.cookies.get("Token")  # Fallback to cookie token

    # ✅ Some FastAPI versions set token='' (empty string) instead of None
    if not token:
        token = request.cookies.get("Token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    # ✅ Decode token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # ✅ Fetch user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_role(*roles: str):
    """
    Role-based access dependency.
    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    """
    def role_checker(user: models.User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {roles}",
            )
        return user

    return role_checker
