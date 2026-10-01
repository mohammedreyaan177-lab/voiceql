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
- Before generating INSERT or UPDATE, analyze whether the requested data or related data already exists.
- Do not INSERT data that already exists.
- Do not UPDATE data if the requested data is already in the desired state.
- Before generating INSERT or UPDATE, check whether required information is missing.
- Do not invent missing values.
- Primary key columns named "id" are auto-generated serial/identity columns.
- Never ask the user to provide an "id" value for INSERT operations.
- Never include the "id" column in an INSERT statement unless the user explicitly requests a specific id.
- For text/string comparisons in WHERE clauses, use case-insensitive comparison.
- Prefer LOWER(column) = LOWER(value) when comparing text values.
- Do not rely on the capitalization used in the user's request to identify existing records.
- For UPDATE and DELETE operations, match existing text values case-insensitively.
- If required information is missing, return:

MISSING_COLUMNS: [column1, column2]

- Do not include auto-generated "id" columns in MISSING_COLUMNS.
- Otherwise return only the SQL query.
- Return exactly ONE SQL statement and nothing else.
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
        if word in upper_sql:
            raise ValueError(
                f"{word} operation is not allowed."
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