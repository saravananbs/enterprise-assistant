from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import LoginRequest, VerifyOTPRequest
from app.services.auth_service import login_with_email, verify_login_otp
from app.my_agents.utils.db.connection import get_async_session

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    employee = await login_with_email(db, request.email)
    if not employee:
        raise HTTPException(status_code=404, detail="Invalid email")
    return {"message": "OTP sent to registered email"}

@router.post("/verify-otp-login")
async def verify_otp(request: VerifyOTPRequest):
    is_valid = await verify_login_otp(request.email, request.otp)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    return {
        "message": "Login successful",
        "email": request.email,
        "employee_id": is_valid
    }
