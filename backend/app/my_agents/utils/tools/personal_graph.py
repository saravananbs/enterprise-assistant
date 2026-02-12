from typing import Any
import json
from datetime import date
from sqlalchemy import select, and_, desc, text
from sqlalchemy.orm import aliased
from sqlalchemy import or_
from sqlalchemy.exc import NoResultFound
from ..db.models import (
    Employee, SalaryStructure, Payroll,
    LeaveType, LeaveBalance, LeaveHistory
)
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from ..db.connection import AsyncSessionLocal
from pydantic import BaseModel, Field

class QuerySchema(BaseModel):
    sql: str = Field(
        description="The raw PostgreSQL string. Example: SELECT * FROM table WHERE col = 'val'. Use single quotes for SQL values."
    )
    
@tool(args_schema=QuerySchema)
async def query_database(sql: str, config: RunnableConfig) -> str:
    """Execute a SQL query on the database."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id")
    user_role = configurable.get("user_role")

    forbidden = ["drop", "truncate", "alter"] 
    if any(cmd in sql.lower() for cmd in forbidden):
        return "Error: This action is not allowed"

    emp_forbidden = ["delete", "update", "insert"]
    if any(cmd in sql.lower() for cmd in emp_forbidden) and user_role != "HR Lead":
        return "Error: Unauthorized command for your role."

    if user_role != "HR" and user_role != "HR Lead":
        if user_id not in sql:
            return f"Error: Security violation. All queries must filter by your employee_code: {user_id}."

    async with AsyncSessionLocal() as db:
        try:
            clean_sql = sql.replace("```sql", "").replace("```", "").strip()
            result = await db.execute(text(clean_sql)) 
            
            if clean_sql.lower().startswith("select"):
                rows = result.fetchall()
                return json.dumps([dict(zip(result.keys(), r)) for r in rows], default=str) if rows else "no data found"
            
            await db.commit()
            return "Operation successful."
        except Exception as e:
            await db.rollback()
            return f"Database error: {str(e)}"