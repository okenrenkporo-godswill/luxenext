from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
from auth import get_password_hash, generate_verification_code
from database import get_db
from models import User
from email_utilis import send_reset_email
import schemas


router = APIRouter(prefix="/password",
                    tags=["password"])


# ✅ Forgot Password - Send Reset Code
@router.post("/forgot-password")
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    email = request.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Don't reveal if user exists for security
        return {"message": "If the email exists, a reset code has been sent."}
    
    # Generate 6-digit code
    code = generate_verification_code()
    user.reset_code = code
    user.reset_code_expires_at = datetime.utcnow() + timedelta(minutes=2)
    db.commit()
    
    # Send email in background
    background_tasks.add_task(send_reset_email, user.email, code)
    
    return {"message": "If the email exists, a reset code has been sent."}


# ✅ Reset Password with Code
@router.post("/reset-password")
async def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    email = request.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify code exists
    if not user.reset_code:
        raise HTTPException(status_code=400, detail="No reset code found. Please request a new one.")
    
    # Verify code matches
    if user.reset_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    # Verify code hasn't expired
    if user.reset_code_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset code has expired. Please request a new one.")
    
    # Reset password
    user.hashed_password = get_password_hash(request.new_password)
    
    # Clear reset code
    user.reset_code = None
    user.reset_code_expires_at = None
    
    db.commit()
    db.refresh(user)
    
    return {"message": "Password reset successful"}