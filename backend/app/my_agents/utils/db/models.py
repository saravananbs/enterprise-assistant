from sqlalchemy import (
    Column, String, Date, DateTime, Boolean, Text, LargeBinary,
    Integer, Numeric, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from pgvector.sqlalchemy import Vector
from ..db.connection import Base

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_code = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    department = Column(String(50), nullable=False)
    designation = Column(String(50), nullable=False)
    date_of_joining = Column(Date, nullable=False)
    employment_status = Column(String(20), nullable=False)

class SalaryStructure(Base):
    __tablename__ = "salary_structure"

    salary_structure_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)

    basic_salary = Column(Numeric(12,2), nullable=False)
    hra = Column(Numeric(12,2), nullable=False)
    special_allowance = Column(Numeric(12,2), nullable=False)
    bonus = Column(Numeric(12,2), default=0)

    provident_fund = Column(Numeric(12,2), nullable=False)
    professional_tax = Column(Numeric(12,2), nullable=False)
    income_tax = Column(Numeric(12,2), nullable=False)

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    created_at = Column(DateTime, server_default=func.now())

class Payroll(Base):
    __tablename__ = "payroll"
    __table_args__ = (
        UniqueConstraint("employee_id", "payroll_month"),
    )

    payroll_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)

    payroll_month = Column(Date, nullable=False)
    gross_salary = Column(Numeric(12,2), nullable=False)
    total_deductions = Column(Numeric(12,2), nullable=False)
    net_salary = Column(Numeric(12,2), nullable=False)

    payment_status = Column(String(20), nullable=False)
    payment_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())

class PayrollComponent(Base):
    __tablename__ = "payroll_components"

    component_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_id = Column(UUID(as_uuid=True), ForeignKey("payroll.payroll_id"), nullable=False)

    component_name = Column(String(50), nullable=False)
    component_type = Column(String(20), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)

class LeaveType(Base):
    __tablename__ = "leave_types"

    leave_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    leave_name = Column(String(50), unique=True, nullable=False)
    max_days_per_year = Column(Integer, nullable=False)
    is_paid = Column(Boolean, nullable=False)

class LeaveBalance(Base):
    __tablename__ = "leave_balance"
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id"),
    )

    leave_balance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("leave_types.leave_type_id"), nullable=False)

    total_allocated = Column(Integer, nullable=False)
    used = Column(Integer, nullable=False)
    remaining = Column(Integer, nullable=False)
    last_updated = Column(DateTime, server_default=func.now())

class LeaveHistory(Base):
    __tablename__ = "leave_history"

    leave_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("leave_types.leave_type_id"), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    number_of_days = Column(Integer, nullable=False)

    leave_status = Column(String(20), nullable=False)
    applied_on = Column(DateTime, server_default=func.now())
    approved_by = Column(UUID(as_uuid=True))
    remarks = Column(String)

class UserOAuthCredentials(Base):
    __tablename__ = "user_oauth_credentials"

    user_id = Column(String, primary_key=True, nullable=False)
    provider = Column(Text, nullable=False, index=True)
    encrypted_credentials = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return (
            f"<UserOAuthCredentials("
            f"user_id={self.user_id}, "
            f"provider={self.provider}"
            f")>"
        )

class LangchainPgCollection(Base):
    __tablename__ = "langchain_pg_collection"

    uuid = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, unique=True)


class LangchainPgEmbedding(Base):
    __tablename__ = "langchain_pg_embedding"

    id = Column(UUID(as_uuid=True), primary_key=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("langchain_pg_collection.uuid"))
    embedding = Column(Vector) 
    document = Column(String)
    cmetadata = Column(JSONB)
