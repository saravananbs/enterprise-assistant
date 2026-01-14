from sqlalchemy.orm import Session
from ..my_agents.utils.db.models import Employee
from ..utils.generate_otp import generate_otp
from ..utils.otp_store import store_otp, verify_otp
from ..utils.send_email_otp import send_otp_email

def login_with_email(db: Session, email: str):
    employee = db.query(Employee).filter(Employee.email == email).first()
    if not employee:
        return None
    otp = generate_otp()
    store_otp(employee.employee_code, email, otp)
    send_otp_email(receiver_email=email, otp=otp)
    return employee

def verify_login_otp(email: str, otp: str) -> str:
    return verify_otp(email, otp)
