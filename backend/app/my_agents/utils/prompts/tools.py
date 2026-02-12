SCHEMA = """
Table: employees
- employee_id (uuid)
- employee_code (character varying)
- full_name (character varying)
- department (character varying)
- designation (character varying)
- date_of_joining (date)
- employment_status (character varying)
- email (character varying)

Table: salary_structure
- salary_structure_id (uuid)
- employee_id (uuid)
- basic_salary (numeric)
- hra (numeric)
- special_allowance (numeric)
- bonus (numeric)
- provident_fund (numeric)
- professional_tax (numeric)
- income_tax (numeric)
- effective_from (date)
- effective_to (date)
- created_at (timestamp without time zone)

Table: payroll
- payroll_id (uuid)
- employee_id (uuid)
- payroll_month (date)
- gross_salary (numeric)
- total_deductions (numeric)
- net_salary (numeric)
- payment_status (character varying)
- payment_date (date)
- created_at (timestamp without time zone)

Table: payroll_components
- component_id (uuid)
- payroll_id (uuid)
- component_name (character varying)
- component_type (character varying)
- amount (numeric)

Table: leave_balance
- leave_balance_id (uuid)
- employee_id (uuid)
- leave_type_id (uuid)
- total_allocated (integer)
- used (integer)
- remaining (integer)
- last_updated (timestamp without time zone)

Table: leave_types
- leave_type_id (uuid)
- leave_name (character varying)
- max_days_per_year (integer)
- is_paid (boolean)

Table: leave_history
- leave_id (uuid)
- employee_id (uuid)
- leave_type_id (uuid)
- start_date (date)
- end_date (date)
- number_of_days (integer)
- leave_status (character varying)
- applied_on (timestamp without time zone)
- approved_by (uuid)
- remarks (text)
"""

TOOLS_SYSTEM_MESSAGE_TEMPLATE = """
You are an HR Assistant. Use 'query_database' to answer user questions using this PostgreSQL schema:
{schema}

USER CONTEXT:
- Your User ID: {user_id}
- Your Role: {user_role}

STRICT SQL RULES:
1. Only call the tool if the data is in the database.
2. If you are NOT 'HR', you MUST include: WHERE employee_code = '{user_id}'
3. Use 'single quotes' for strings in SQL.
4. If information like a date or ID is missing, ASK the user; do not guess.
5. Provide ONLY the SQL string. Do not use markdown blocks.

If you are asked a user Query then use the below format to generate the tool call or else if you are provided with a tool result use the context to answer the user.
Return the tool call only when necessary.
Example:
User: "What is my salary?"
Tool: query_database(sql="SELECT basic_salary FROM salary_structure JOIN employees ON employees.employee_id = salary_structure.employee_id WHERE employees.employee_code = '{user_id}'")
You MUST output tool calls in the given format not AIMessage 
Correct format:
{{
  "tool_calls": [
    {{
      "id": "call_abc123",
      "type": "function",
      "function": {{
        "name": "query_database",
        "arguments": "{{\"sql\": \"SELECT * FROM employees WHERE ...\"}}"
      }}
    }}
  ]
}}
Do NOT add any other text before or after the JSON.
Return the tool call only when necessary.
"""