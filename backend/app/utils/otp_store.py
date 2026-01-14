from datetime import datetime, timedelta

OTP_STORE = {}
OTP_EXPIRY_MINUTES = 5

def store_otp(employee_id: str, email: str, otp: str):
    OTP_STORE[email] = {
        "otp": otp,
        "expires_at": datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "employee_id": employee_id
    }

def verify_otp(email: str, otp: str) -> str:
    record = OTP_STORE.get(email)
    if not record:
        return None
    if datetime.now() > record["expires_at"]:
        OTP_STORE.pop(email, None)
        return None
    if record["otp"] != otp:
        return None
    OTP_STORE.pop(email, None)
    return record["employee_id"]
