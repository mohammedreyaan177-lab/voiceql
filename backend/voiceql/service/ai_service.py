import os
from django.db import connection
from groq import Groq
from dotenv import load_dotenv
from .metricservice import calculate_metric, find_metric
from .voiceservice import transcribe_audio
load_dotenv()


#-----------------------------------------------------#

#GroqAI Service
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is not configured")


#----------------------------------------------------------#

def generate_sql(user_query):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name NOT LIKE 'django_%'
            AND table_name NOT LIKE 'auth_%'
            ORDER BY table_name, ordinal_position;
        """)

        tables = cursor.fetchall()

    schema = "\n".join(
        f"Table: {table}, Column: {column}, Type: {data_type}"
        for table, column, data_type in tables
    )

    prompt = f"""
You are an SQL generator.

Database schema:
{schema}

User request:
{user_query}

Rules:
- Generate PostgreSQL SQL only.
- Use only tables and columns from the schema.
- Do not generate DROP, ALTER, TRUNCATE, CREATE, GRANT or REVOKE.
- SELECT, INSERT, UPDATE and DELETE are allowed.

MULTIPLE OPERATIONS:
- The user may request multiple operations in a single message.
- Identify and process every operation in the user's request.
- Multiple operations may include combinations such as INSERT + DELETE, UPDATE + INSERT, DELETE + INSERT, or multiple INSERT operations.
- Execute all requested operations in the order specified by the user.
- Return all required SQL statements in the same response.
- Do not ignore any valid operation from the user's request.

MULTIPLE INSERT VALIDATION:
- When the user requests multiple products or multiple records to be inserted, validate EVERY record individually before generating INSERT statements.
- Check whether each requested record already exists in the database.
- Perform existence checks case-insensitively for text fields.
- Do not INSERT a record if the same record already exists.
- Do not assume that one existing record means all requested records already exist.
- Insert only the records that do not already exist.
- If some requested records already exist and some do not, only generate INSERT statements for the records that do not exist.
- If all requested records already exist, do not generate INSERT statements for them.

INSERT VALIDATION:
- Before generating INSERT statements, analyze whether the requested data or related data already exists.
- Do not INSERT data that already exists.
- Before generating INSERT statements, check whether required information is missing.
- Do not invent missing values.

UPDATE VALIDATION:
- Before generating UPDATE statements, check whether the requested record exists.
- Do not UPDATE data if the requested data is already in the desired state.
- If the record does not exist, do not invent a record to update.
- Before generating UPDATE statements, check whether required information is missing.
- Do not invent missing values.

DELETE VALIDATION:
- Before generating DELETE statements, check whether the requested record exists.
- If the requested record does not exist, do not generate a DELETE statement for it.
- Match existing text values case-insensitively.

PRIMARY KEY:
- Primary key columns named "id" are auto-generated serial/identity columns.
- Never ask the user to provide an "id" value for INSERT operations.
- Never include the "id" column in an INSERT statement unless the user explicitly requests a specific id.
- Do not include auto-generated "id" columns in MISSING_COLUMNS.

TEXT COMPARISON:
- For text/string comparisons in WHERE clauses, use case-insensitive comparison.
- Prefer LOWER(column) = LOWER(value) when comparing text values.
- Do not rely on the capitalization used in the user's request to identify existing records.
- For INSERT, UPDATE and DELETE validation, compare relevant text fields case-insensitively.

MISSING INFORMATION:
- If required information is missing for an operation, return:

MISSING_COLUMNS: [column1, column2]

- Do not generate SQL for an operation that has missing required information.
- If multiple operations exist, validate each operation separately.

MULTIPLE OPERATION EXAMPLE:
User request:
"Delete the product called Laptop and add a new product called Tablet with price 20000 and rating 4.5"

Process:
1. Check whether Laptop exists.
2. Generate DELETE for Laptop only if it exists.
3. Check whether Tablet already exists.
4. Generate INSERT for Tablet only if it does not exist.
5. Return both SQL statements if both operations are valid.

MULTIPLE INSERT EXAMPLE:
User request:
"Add Laptop with price 70000, add Tablet with price 20000, and add Phone with price 30000"

Process:
1. Check whether Laptop already exists.
2. Check whether Tablet already exists.
3. Check whether Phone already exists.
4. Insert only the products that do not already exist.
5. Do not ask for id values.
6. Do not insert products that already exist.

OUTPUT:
- Return all valid SQL statements required for the user's request.
- If there are multiple operations, return multiple SQL statements.
- Return statements in the same order as the user's requested operations.
- If required information is missing, return MISSING_COLUMNS: [column1, column2].
- Return exactly one response containing the SQL statement or statements.
- Do not return explanations.
- If the request does not name a table, query the main application table.
"""

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    sql = response.choices[0].message.content.strip()

    if sql.startswith("```"):
        sql = sql.replace("```sql", "")
        sql = sql.replace("```SQL", "")
        sql = sql.replace("```", "")
        sql = sql.strip()

    return sql


import re


def validate_sql(sql):
    sql = sql.strip()

    blocked = [
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE"
    ]

    upper_sql = sql.upper()

    for word in blocked:
        if re.search(rf"\b{word}\b", upper_sql):
            raise ValueError(
                f"{word} operation is not allowed."
            )

    statements = [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]

    for statement in statements:
        upper_statement = statement.upper().strip()

        if upper_statement.startswith("DELETE"):
            if not re.search(r"\bWHERE\b", upper_statement):
                raise ValueError(
                    "DELETE operation must include a WHERE condition."
                )

            dangerous_conditions = [
                r"\b1\s*=\s*1\b",
                r"\b0\s*=\s*0\b",
                r"\bTRUE\b",
                r"\bFALSE\s*=\s*FALSE\b",
                r"\bNOT\s+FALSE\b",
                r"\b1\s*<\s*2\b",
                r"\b2\s*>\s*1\b",
            ]

            for pattern in dangerous_conditions:
                if re.search(pattern, upper_statement):
                    raise ValueError(
                        "Unsafe DELETE condition detected."
                    )

            where_part = re.split(
                r"\bWHERE\b",
                upper_statement,
                maxsplit=1
            )[1]

            if re.search(
                r"(['\"])\s*=\s*\1",
                where_part
            ):
                raise ValueError(
                    "Unsafe DELETE condition detected."
                )

    return sql

def execute_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)

        if sql.strip().upper().startswith("SELECT"):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [
                dict(zip(columns, row))
                for row in rows
            ]

        connection.commit()

        return {
            "message": "Operation successful",
            "affected_rows": cursor.rowcount
        }


def ask_database(user_query):

    metric_name = find_metric(user_query)

    if metric_name:

        result = calculate_metric(metric_name)

        return {
            "metric": metric_name,
            "value": result
        }

    sql = generate_sql(user_query)

    if sql.startswith("MISSING_COLUMNS:"):

        missing_columns = sql.replace(
            "MISSING_COLUMNS:",
            ""
        ).strip()

        return {
            "status": "missing_information",
            "missing_columns": missing_columns
        }

    sql = validate_sql(sql)

    if not sql:
        return {
            "status": "error",
            "message": "The AI returned an empty query. Please rephrase your question."
        }

    operation = sql.split()[0].upper()

    if operation in ["INSERT", "UPDATE", "DELETE"]:
        confirmation = input(
            f"\nThis will execute:\n{sql}\n\n"
            "Do you want to continue? (yes/no): "
        )

        if confirmation.lower() != "yes":
            return {
                "message": "Operation cancelled"
            }

    return execute_sql(sql)