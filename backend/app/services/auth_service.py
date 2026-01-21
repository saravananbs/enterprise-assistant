from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from ..my_agents.utils.db.models import Employee
from ..utils.generate_otp import generate_otp
from ..utils.otp_store import store_otp, verify_otp
from ..utils.send_email_otp import send_otp_email

async def login_with_email(db: AsyncSession, email: str):
    stmt = select(Employee).where(Employee.email == email)
    res = await db.execute(stmt)
    try:
        employee = res.scalar_one()
    except NoResultFound:
        return None
    if not employee:
        return None
    otp = await generate_otp()
    await store_otp(employee.employee_code, email, otp)
    await send_otp_email(receiver_email=email, otp=otp)
    return employee

async def verify_login_otp(email: str, otp: str) -> str:
    return await verify_otp(email, otp)
