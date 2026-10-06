import os
import re
import logging
from django.db import connection
from groq import Groq
from dotenv import load_dotenv
from .metricservice import calculate_metric, find_metric
from .voiceservice import transcribe_audio

load_dotenv()

logger = logging.getLogger("voiceql")

# -----------------------------------------------------#

# GroqAI Service
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    logger.critical("GROQ_API_KEY missing")
    raise ValueError("GROQ_API_KEY is not configured")


# ----------------------------------------------------------#

def generate_sql(user_query):
    dangerous_patterns = [
        r"\bdelete\s+all\b",
        r"\bdelete\s+everything\b",
        r"\bdelete\s+all\s+products\b",
        r"\bdelete\s+all\s+records\b",
        r"\bclear\s+(the\s+)?table\b",
        r"\bempty\s+(the\s+)?table\b",
        r"\bdrop\s+(the\s+)?table\b",
        r"\bdrop\s+(the\s+)?database\b",
        r"\btruncate\b",
        r"\b1\s*=\s*1\b",
        r"\b0\s*=\s*0\b",
        r"\bdelete\b.*\btrue\b",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, user_query, re.IGNORECASE):
            logger.warning("Unsafe pattern detected")
            raise ValueError(
                "Unsafe SQL operation detected."
            )

    try:
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
    except Exception as e:
        logger.error(f"Failed to fetch schema: {e}")
        raise

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
- For product names, ignore all spaces and whitespace when comparing.
- Treat product names as the same if they differ only by capitalization or spaces.
- For example, "Acer Aspire 5", "acer aspire 5", "AcerAspire5" and "ACER  ASPIRE  5" must be treated as the same product.
- Do not INSERT a record if the same record already exists.
- Do not assume that one existing record means all requested records already exist.
- Insert only the records that do not already exist.
- If some requested records already exist and some do not, only generate INSERT statements for the records that do not exist.
- If all requested records already exist, do not generate INSERT statements for them.

INSERT VALIDATION:
- Before generating INSERT statements, analyze whether the requested data or related data already exists.
- Do not INSERT data that already exists.
- For product names, ignore spaces and capitalization when checking for duplicates.
- Before generating INSERT statements, check whether required information is missing.
- Do not invent missing values.
- Product names inserted into the database must be lowercase and must not contain spaces or whitespace.
- Remove all spaces and whitespace from the product name before generating the INSERT statement.
- For example:
  - "Acer Aspire 5" must be inserted as "aceraspire5".
  - "ACER ASPIRE 5" must be inserted as "aceraspire5".
  - "acer aspire 5" must be inserted as "aceraspire5".
  - "AcerAspire5" must be inserted as "aceraspire5".

UPDATE VALIDATION:
- Before generating UPDATE statements, check whether the requested record exists.
- For product names, compare case-insensitively and ignore all spaces and whitespace.
- Do not UPDATE data if the requested data is already in the desired state.
- If the record does not exist, do not invent a record to update.
- Before generating UPDATE statements, check whether required information is missing.
- Do not invent missing values.
- When updating a product name, store the product name in lowercase with no spaces or whitespace.
- For example:
  - "Acer Aspire 5" must become "aceraspire5".
  - "ACER ASPIRE 5" must become "aceraspire5".
  - "acer aspire 5" must become "aceraspire5".
- When updating a product's price, rating, or other fields, modify only the fields requested by the user.

DELETE VALIDATION:
- Before generating DELETE statements, check whether the requested record exists.
- If the requested record does not exist, do not generate a DELETE statement for it.
- Match existing text values case-insensitively.
- For product names, ignore all spaces and whitespace when comparing.
- Never generate DELETE without WHERE.
- Never generate DELETE using always-true conditions such as:
  - 1=1
  - 0=0
  - TRUE
  - FALSE=FALSE
  - NOT FALSE
  - equivalent always-true conditions
- Never generate SQL that deletes every record from a table.
- Never generate SQL that deletes the entire database.

PRIMARY KEY:
- Primary key columns named "id" are auto-generated serial/identity columns.
- Never ask the user to provide an "id" value for INSERT operations.
- Never include the "id" column in an INSERT statement unless the user explicitly requests a specific id.
- Do not include auto-generated "id" columns in MISSING_COLUMNS.

TEXT COMPARISON:
- For normal text/string comparisons in WHERE clauses, use case-insensitive comparison.
- For product name comparisons, ignore all spaces and whitespace.
- When comparing product names, remove spaces from BOTH the database column value and the user's requested product name before comparing.
- Product name comparisons must use PostgreSQL REPLACE().
- Use this pattern for product name comparisons:

LOWER(REPLACE(product, ' ', '')) = LOWER(REPLACE('user product name', ' ', ''))

- Treat these as the same product:
  - "Acer Aspire 5"
  - "acer aspire 5"
  - "AcerAspire5"
  - "ACER  ASPIRE  5"
  - "aCeR aSpIrE 5"
- Do not remove spaces from other text fields unless explicitly required.
- Preserve lowercase and no-space format for product names when inserting or updating.

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

PRODUCT NAME EXAMPLE:
User request:
"Delete aceraspire5"

If the database contains:
"Acer Aspire 5"

Treat them as the same product.

The comparison should use:

LOWER(REPLACE(product, ' ', '')) =
LOWER(REPLACE('aceraspire5', ' ', ''))

Do not insert another record if it already exists.

OUTPUT:
- Return all valid SQL statements required for the user's request.
- If there are multiple operations, return multiple SQL statements.
- Return statements in the same order as the user's requested operations.
- If required information is missing, return MISSING_COLUMNS: [column1, column2].
- Return exactly one response containing the SQL statement or statements.
- Do not return explanations.
- If the request does not name a table, query the main application table.
"""

    try:
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
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        raise

    if sql.startswith("```"):
        sql = sql.replace("```sql", "")
        sql = sql.replace("```SQL", "")
        sql = sql.replace("```", "")
        sql = sql.strip()

    logger.info(f"Generated SQL: {sql}")
    return sql


def validate_sql(sql):
    if not sql or not sql.strip():
        logger.warning("Empty SQL query")
        raise ValueError(
            "AI returned an empty SQL query."
        )

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
            logger.warning(f"Blocked word: {word}")
            raise ValueError(
                f"{word} operation is not allowed."
            )

    statements = [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]

    if not statements:
        logger.warning("No valid statements")
        raise ValueError(
            "AI returned an empty SQL query."
        )

    for statement in statements:
        upper_statement = statement.upper().strip()

        if upper_statement.startswith("DELETE"):
            if not re.search(r"\bWHERE\b", upper_statement):
                logger.warning("DELETE missing WHERE")
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
                    logger.warning("Unsafe DELETE condition")
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
                logger.warning("Unsafe DELETE condition")
                raise ValueError(
                    "Unsafe DELETE condition detected."
                )

    return sql


def execute_sql(sql):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)

            if sql.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                logger.info(f"SELECT returned {len(rows)} rows")
                return [
                    dict(zip(columns, row))
                    for row in rows
                ]

            connection.commit()

            logger.info("SQL executed successfully")
            return {
                "message": "Operation successful",
                "affected_rows": cursor.rowcount
            }
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        raise


def ask_database(user_query):
    try:
        metric_name = find_metric(user_query)

        if metric_name:
            logger.info(f"Found metric: {metric_name}")
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

            logger.info(f"Missing columns: {missing_columns}")
            return {
                "status": "missing_information",
                "missing_columns": missing_columns
            }

        sql = validate_sql(sql)

        if not sql:
            logger.warning("Empty SQL generated")
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
                logger.info("Operation cancelled by user")
                return {
                    "message": "Operation cancelled"
                }

        return execute_sql(sql)
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Ask database failed: {e}")
        return {
            "status": "error",
            "message": "An error occurred while processing your request."
        }