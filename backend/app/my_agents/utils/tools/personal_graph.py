from typing import List, Dict, Optional
from datetime import date
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import aliased
from sqlalchemy import or_
from sqlalchemy.exc import NoResultFound
from ..db.models import (
    Employee, SalaryStructure, Payroll, PayrollComponent,
    LeaveType, LeaveBalance, LeaveHistory
)
from langchain_core.tools import tool
from ..db.connection import SessionLocal

@tool
def get_employee_by_code(employee_code: str) -> Optional[Dict]:
    """
    Retrieve basic employee details like name, department, designation, 
    date of joining,employment status by employee code.

    Args:
        employee_code: Unique employee code (string)

    Returns:
        Dict with employee information or None if not found
        Example:
        {
            "employee_id": str,
            "employee_code": str,
            "full_name": str,
            "department": str,
            "designation": str,
            "date_of_joining": date,
            "employment_status": str
        }
    """
    with SessionLocal() as db:
        stmt = select(Employee).where(Employee.employee_code == employee_code)
        
        try:
            employee = db.scalars(stmt).one()
            return {
                "employee_id": str(employee.employee_id),
                "employee_code": employee.employee_code,
                "full_name": employee.full_name,
                "department": employee.department,
                "designation": employee.designation,
                "date_of_joining": employee.date_of_joining,
                "employment_status": employee.employment_status
            }
        except NoResultFound:
            return None

@tool
def get_current_salary_structure(employee_code: str) -> Optional[Dict]:
    """
    Get the currently active (most recent valid) salary structure for an employee.

    Current = latest record where effective_from <= today AND (effective_to IS NULL OR effective_to >= today)

    Args:
        employee_code: Unique employee code

    Returns:
        Dict with salary structure details or None
        Example:
        {
            "effective_from": date,
            "effective_to": date or None,
            "basic_salary": float,
            "hra": float,
            "special_allowance": float,
            "bonus": float,
            "provident_fund": float,
            "professional_tax": float,
            "income_tax": float,
            "gross_earnings": float,        # basic + hra + special + bonus
            "total_deductions": float       # pf + pt + it
        }
    """
    with SessionLocal() as db:
        today = date.today()

        stmt = (
            select(SalaryStructure)
            .join(Employee)
            .where(Employee.employee_code == employee_code)
            .where(
                and_(
                    SalaryStructure.effective_from <= today,
                    or_(
                        SalaryStructure.effective_to.is_(None),
                        SalaryStructure.effective_to >= today
                    )
                )
            )
            .order_by(desc(SalaryStructure.effective_from))
            .limit(1)
        )

        try:
            structure = db.scalars(stmt).one()

            gross = (
                structure.basic_salary +
                structure.hra +
                structure.special_allowance +
                structure.bonus
            )
            deductions = (
                structure.provident_fund +
                structure.professional_tax +
                structure.income_tax
            )

            return {
                "effective_from": structure.effective_from,
                "effective_to": structure.effective_to,
                "basic_salary": float(structure.basic_salary),
                "hra": float(structure.hra),
                "special_allowance": float(structure.special_allowance),
                "bonus": float(structure.bonus),
                "provident_fund": float(structure.provident_fund),
                "professional_tax": float(structure.professional_tax),
                "income_tax": float(structure.income_tax),
                "gross_earnings": float(gross),
                "total_deductions": float(deductions)
            }
        except NoResultFound:
            return None

@tool
def get_payroll_summary(employee_code: str) -> List[Dict]:
    """
    Get payroll history summary for the employee (all months).

    Returns most recent records first.

    Args:
        employee_code: Unique employee code

    Returns:
        List of payroll summaries (most recent first)
        Example item:
        {
            "payroll_month": "YYYY-MM-DD",
            "gross_salary": float,
            "deductions": float,
            "net_salary": float,
            "status": str,          # Pending / Paid / Failed
            "payment_date": str or None
        }
    """
    with SessionLocal() as db:
        stmt = (
            select(Payroll)
            .join(Employee)
            .where(Employee.employee_code == employee_code)
            .order_by(desc(Payroll.payroll_month))
        )

        payrolls = db.scalars(stmt).all()

        return [
            {
                "payroll_month": p.payroll_month.isoformat(),
                "gross_salary": float(p.gross_salary),
                "deductions": float(p.total_deductions),
                "net_salary": float(p.net_salary),
                "status": p.payment_status,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None
            }
            for p in payrolls
        ]

@tool
def get_leave_balances(employee_code: str) -> List[Dict]:
    """
    Get current leave balance for all leave types of an employee.

    Args:
        employee_code: Unique employee code

    Returns:
        List of leave balances
        Example item:
        {
            "leave_type": str,
            "allocated": int,
            "used": int,
            "remaining": int,
            "last_updated": str (ISO datetime)
        }
    """
    with SessionLocal() as db:
        stmt = (
            select(LeaveBalance, LeaveType.leave_name)
            .join(LeaveType)
            .join(Employee)
            .where(Employee.employee_code == employee_code)
            .order_by(LeaveType.leave_name)
        )

        results = db.execute(stmt).all()

        return [
            {
                "leave_type": leave_name,
                "allocated": lb.total_allocated,
                "used": lb.used,
                "remaining": lb.remaining,
                "last_updated": lb.last_updated.isoformat()
            }
            for lb, leave_name in results
        ]

@tool
def get_leave_history(employee_code: str) -> List[Dict]:
    """
    Retrieve leave application history for an employee (most recent first).
    """
    with SessionLocal() as db:
        EmployeeOwner = aliased(Employee)
        EmployeeApprover = aliased(Employee)

        stmt = (
            select(
                LeaveHistory,
                LeaveType.leave_name,
                EmployeeApprover.full_name.label("approver_name")
            )
            .join(LeaveType, LeaveType.leave_type_id == LeaveHistory.leave_type_id)
            .join(
                EmployeeOwner,
                EmployeeOwner.employee_id == LeaveHistory.employee_id
            )
            .outerjoin(
                EmployeeApprover,
                EmployeeApprover.employee_id == LeaveHistory.approved_by
            )
            .where(EmployeeOwner.employee_code == employee_code)
            .order_by(desc(LeaveHistory.applied_on))
        )

        results = db.execute(stmt).all()

        return [
            {
                "leave_id": str(lh.leave_id),
                "leave_type": leave_name,
                "start_date": lh.start_date.isoformat(),
                "end_date": lh.end_date.isoformat(),
                "number_of_days": lh.number_of_days,
                "status": lh.leave_status,
                "applied_on": lh.applied_on.isoformat(),
                "approved_by": approver_name,
                "remarks": lh.remarks
            }
            for lh, leave_name, approver_name in results
        ]

@tool
def get_all_employees() -> List[Dict]:
    """
    Return a list of all the employees with their
    - employee_id
    - employee_code
    - full_name
    - department
    - designation
    - date_of_joining
    - employment_status
    """
    with SessionLocal() as db:

        stmt = select(Employee)

        result = db.execute(stmt).scalars().all()

        return [ 
            {
                "employee_id": str(emp.employee_id),
                "employee_code": emp.employee_code,
                "full_name": emp.full_name,
                "department": emp.department,
                "designation": emp.designation,
                "date_of_joining": emp.date_of_joining,
                "employment_status": emp.employment_status
            } 
            for emp in result
        ]