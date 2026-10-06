\# VoiceQL 🎙️ → 🗄️



\## AI-Powered Natural Language and Voice-to-SQL Query Generator



VoiceQL is an AI-powered Django application that allows users to interact with a PostgreSQL database using \*\*natural language or voice commands\*\* instead of manually writing SQL queries.



The system understands a user's request, analyzes the available database schema, identifies the intended operation, applies semantic and metric-based reasoning when appropriate, generates a valid PostgreSQL query, validates the query, and returns the database result.



VoiceQL is designed to make database interaction easier for both technical and non-technical users.



\---



\## 🚀 Overview



Traditional database interaction requires users to know SQL syntax and understand the underlying database structure.



For example, instead of manually writing:



```sql

SELECT \* FROM product WHERE product\_price > 5000;

```



a user can simply ask:



> Show me products that cost more than 5000



VoiceQL processes the request and converts the natural-language instruction into an appropriate SQL query.



The application also supports voice interaction.



A user can say:



> Show me all products



The voice input is transcribed into text using \*\*Faster-Whisper\*\*, and the resulting text is processed through the same natural-language-to-SQL pipeline.



\---



\# ✨ Key Features



\## 1. Natural Language to SQL



Users can describe database operations using normal language instead of SQL syntax.



Examples:



```text

Show all products

```



```text

Find products above 5000

```



```text

What is the average product price?

```



```text

How many products are available?

```



The AI analyzes the request and generates PostgreSQL-compatible SQL.



\---



\## 2. Voice-to-SQL



VoiceQL supports voice-based database queries.



The processing flow is:



```text

User Voice

&#x20;   ↓

Audio Input

&#x20;   ↓

Faster-Whisper

&#x20;   ↓

Transcribed Text

&#x20;   ↓

AI Query Processing

&#x20;   ↓

SQL Generation

&#x20;   ↓

SQL Validation

&#x20;   ↓

PostgreSQL

&#x20;   ↓

Result

```



The system uses \*\*Faster-Whisper\*\* for speech-to-text transcription.



The application does not require the user to manually write the query.



\---



\## 3. PostgreSQL Database Integration



VoiceQL is designed to work with PostgreSQL.



Instead of hard-coding the database structure into the AI prompt, the application reads the database schema dynamically.



The schema information includes:



\- Table names

\- Column names

\- Data types



The system retrieves this information from PostgreSQL's:



```text

information\_schema.columns

```



Only application-related tables are considered while generating SQL.



Django internal tables such as:



```text

django\_\*

auth\_\*

```



are excluded from the schema provided to the AI.



\---



\# 🧠 AI-Powered Query Generation



The core of VoiceQL is the AI SQL generation layer.



The system provides the AI model with:



1\. User's natural-language request

2\. Available PostgreSQL database schema

3\. SQL generation rules

4\. Operation restrictions

5\. Semantic requirements

6\. Database reasoning requirements



The model then generates SQL based on the available schema.



\---



\## Example



User:



```text

Show all products

```



The system analyzes the available schema and may generate:



```sql

SELECT \* FROM product;

```



The generated SQL is then passed through validation before execution.



\---



\# 🔍 Semantic Layer



VoiceQL includes a semantic layer that helps map natural-language terminology to actual database structures.



Users may not know the exact database terminology.



For example, a user might say:



```text

Show me all items

```



while the database contains:



```text

product

```



The semantic layer helps the AI understand the relationship between user terminology and the database schema.



This makes the system more flexible than a simple keyword-based SQL generator.



\---



\## Semantic Layer Responsibilities



The semantic layer helps with:



\- Understanding user terminology

\- Mapping concepts to database tables

\- Mapping natural-language terms to columns

\- Understanding equivalent expressions

\- Reducing dependency on exact database naming

\- Providing schema context to the AI



\---



\# 📊 Metrics Layer



VoiceQL also includes a metrics layer for commonly requested database calculations.



Instead of relying entirely on AI-generated SQL for predefined metrics, the system can identify known metric requests and use the corresponding metric definition.



Examples include:



| Metric | Database Operation |

|---|---|

| Total Products | `COUNT` |

| Maximum Price | `MAX` |

| Minimum Price | `MIN` |

| Average Price | `AVG` |



\---



\## Example Metric Requests



Users can ask:



```text

How many products are there?

```



```text

What is the total number of products?

```



```text

Give me the product count

```



These can map to:



```text

total\_products

```



Similarly:



```text

What is the highest product price?

```



can map to:



```text

max\_price

```



And:



```text

What is the average product price?

```



can map to:



```text

avg\_price

```



\---



\# 🤖 AI Classification



One important part of the architecture is determining whether a user request should be handled as a metric request or as a normal database operation.



For example:



```text

How many products are there?

```



should be treated as a metric.



However:



```text

Show all products

```



should continue through normal SQL generation.



Likewise:



```text

Insert a new product

```



must not accidentally be interpreted as a metric request.



The system therefore distinguishes between:



```text

Metric Query

&#x20;     ↓

Metric Layer

```



and:



```text

Normal Query

&#x20;     ↓

Semantic Layer

&#x20;     ↓

AI SQL Generator

```



This prevents metric logic from incorrectly taking over CRUD operations.



\---



\# 📝 CRUD Operations



VoiceQL supports database operations including:



\- `SELECT`

\- `INSERT`

\- `UPDATE`

\- `DELETE`



The AI is instructed to generate PostgreSQL SQL based on the user's requested operation.



\---



\## SELECT



Example:



```text

Show all products

```



Possible generated query:



```sql

SELECT \* FROM product;

```



\---



\## INSERT



Example:



```text

Add a product named Laptop with price 72000

```



The generated query can be:



```sql

INSERT INTO product (product\_name, product\_price)

VALUES ('Laptop', 72000);

```



The primary key does not need to be supplied when the database uses a serial/auto-generated ID.



\---



\## UPDATE



Example:



```text

Update the price of Laptop to 75000

```



The system generates an appropriate `UPDATE` query based on the available schema.



The system also considers whether the requested value already exists before performing the update.



\---



\## DELETE



Example:



```text

Delete the product Laptop

```



The system generates an appropriate `DELETE` query after analyzing the request.



\---



\# 🔎 Existence and State Checking



For `INSERT` and `UPDATE` operations, VoiceQL performs additional reasoning.



The system should not blindly execute every generated mutation.



For example, if the user requests:



```text

Add Laptop with price 72000

```



but the product already exists, the system should identify that the requested record already exists rather than blindly inserting a duplicate.



Similarly, if the user requests:



```text

Update Laptop price to 72000

```



and the product already has a price of `72000`, another update is unnecessary.



This reasoning helps prevent:



\- Duplicate records

\- Unnecessary updates

\- Incorrect database modifications



\---



\# 🛡️ SQL Validation



Generated SQL is not executed blindly.



VoiceQL includes SQL validation before execution.



The validation layer checks the generated query and prevents unsupported or dangerous SQL operations.



The allowed operations are:



```text

SELECT

INSERT

UPDATE

DELETE

```



The validation layer blocks operations such as:



```text

DROP

ALTER

TRUNCATE

CREATE

GRANT

REVOKE

```



\---



\## Example



The following query should be rejected:



```sql

DROP TABLE product;

```



The validation layer detects the prohibited operation and raises an error instead of executing it.



\---



\# 🔐 Query Safety



The validation process provides an additional safety layer between AI-generated SQL and the database.



The general processing pipeline is:



```text

Natural Language

&#x20;      ↓

AI SQL Generation

&#x20;      ↓

Generated SQL

&#x20;      ↓

SQL Validation

&#x20;      ↓

Allowed?

&#x20;  ↙       ↘

&#x20;YES        NO

&#x20; ↓          ↓

Execute     Reject

```



This reduces the possibility of accidentally executing unsupported database commands generated by the AI.



\---



\# ⚠️ Confirmation for Database Modifications



Read operations such as:



```sql

SELECT

```



can be executed normally.



Operations that modify data require confirmation.



These include:



```sql

INSERT

UPDATE

DELETE

```



The intended flow is:



```text

User Request

&#x20;    ↓

AI Generates SQL

&#x20;    ↓

SQL Validation

&#x20;    ↓

Modification Detected

&#x20;    ↓

Ask User for Confirmation

&#x20;    ↓

User Confirms

&#x20;    ↓

Execute SQL

```



This provides an additional layer of protection against accidental database modifications.



\---



\# 🎤 Voice Processing



VoiceQL uses Faster-Whisper for voice transcription.



The voice processing pipeline is:



```text

Microphone

&#x20;   ↓

Audio File

&#x20;   ↓

Faster-Whisper

&#x20;   ↓

Text Transcription

&#x20;   ↓

VoiceQL Query Pipeline

```



The transcribed text is then treated like a normal user query.



For example:



```text

Voice:

"Show me all products"

```



becomes:



```text

Transcribed Text:

Show me all products

```



and is then passed to the SQL generation system.



\---



\# 🏗️ System Architecture



The application can be viewed as several logical layers.



```text

&#x20;                   ┌─────────────────────┐

&#x20;                   │       User          │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                    Text or Voice Input

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │   Django API Layer  │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │ Voice Transcription │

&#x20;                   │   Faster-Whisper    │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                        User Query

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │ Query Classification│

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;               ┌──────────────┴──────────────┐

&#x20;               │                             │

&#x20;       Metric Request                 Normal Request

&#x20;               │                             │

&#x20;       ┌───────▼────────┐           ┌────────▼────────┐

&#x20;       │ Metrics Layer  │           │ Semantic Layer  │

&#x20;       └───────┬────────┘           └────────┬────────┘

&#x20;               │                             │

&#x20;               │                     ┌────────▼────────┐

&#x20;               │                     │   AI SQL Model  │

&#x20;               │                     └────────┬────────┘

&#x20;               │                             │

&#x20;               └──────────────┬──────────────┘

&#x20;                              │

&#x20;                      Generated SQL

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │    SQL Validation   │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                     ┌────────▼────────┐

&#x20;                     │   Confirmation  │

&#x20;                     │  if CRUD change │

&#x20;                     └────────┬────────┘

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │     PostgreSQL      │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                        Query Result

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │    API Response     │

&#x20;                   └─────────────────────┘

```



\---



\# 🔄 Complete Request Flow



A normal text request follows this flow:



```text

User

&#x20;↓

Natural Language Request

&#x20;↓

Django API

&#x20;↓

Query Processing

&#x20;↓

Schema Retrieval

&#x20;↓

Semantic Understanding

&#x20;↓

AI Reasoning

&#x20;↓

SQL Generation

&#x20;↓

SQL Validation

&#x20;↓

PostgreSQL

&#x20;↓

Result

&#x20;↓

API Response

```



A voice request follows:



```text

User

&#x20;↓

Voice

&#x20;↓

Faster-Whisper

&#x20;↓

Transcribed Text

&#x20;↓

Query Processing

&#x20;↓

Semantic / Metrics Layer

&#x20;↓

AI Reasoning

&#x20;↓

SQL Generation

&#x20;↓

Validation

&#x20;↓

PostgreSQL

&#x20;↓

Result

```



\---



\# 🧩 Project Structure



The project is organized around a Django backend and service-based processing.



A typical structure is:



```text

voiceql/

│

├── backend/

│   │

│   ├── manage.py

│   │

│   ├── <django\_project>/

│   │   ├── settings.py

│   │   ├── urls.py

│   │   ├── asgi.py

│   │   └── wsgi.py

│   │

│   └── <application>/

│       │

│       ├── views.py

│       │

│       ├── urls.py

│       │

│       └── service/

│           ├── ai\_service.py

│           ├── voiceservice.py

│           └── metricservice.py

│

└── README.md

```



The repository currently contains a dedicated `backend` directory.



\---



\# 🔧 Main Components



\## `views.py`



The Django views provide the API endpoints.



Responsibilities include:



\- Receiving HTTP requests

\- Reading JSON request data

\- Receiving voice/audio input

\- Calling the appropriate service

\- Returning JSON responses

\- Handling API errors



\---



\## `ai\_service.py`



This service contains the core natural-language-to-SQL processing.



Responsibilities include:



\- Reading database schema

\- Building the AI prompt

\- Processing user queries

\- Generating SQL

\- Applying semantic reasoning

\- Handling database operations

\- Performing query validation

\- Handling CRUD-related reasoning



\---



\## `metricservice.py`



This service handles predefined database metrics.



Responsibilities include:



\- Identifying metric requests

\- Finding matching metrics

\- Calculating metric values

\- Supporting different natural-language variations



Example:



```text

"How many products?"

```



can be mapped to:



```text

total\_products

```



\---



\## `voiceservice.py`



This service handles speech-to-text processing.



Responsibilities include:



\- Receiving audio input

\- Passing audio to Faster-Whisper

\- Transcribing speech

\- Returning the transcription



The transcription is then passed to the main query-processing pipeline.



\---



\# 🌐 API Endpoints



\## Health Check



\### Endpoint



```http

GET /health

```



\### Purpose



Checks whether the Django API is running.



\### Example response



```json

{

&#x20;   "status": "ok"

}

```



\---



\# Ask Database



\### Endpoint



```http

POST /ask

```



\### Purpose



Accepts a natural-language database request.



Example request:



```json

{

&#x20;   "user\_query": "Show all products"

}

```



The backend processes the request and returns the generated SQL and/or query result depending on the implementation.



\---



\# Voice Query



\### Endpoint



```http

POST /voice

```



\### Purpose



Accepts an audio input and converts the user's speech into text using Faster-Whisper.



The resulting transcription is then processed by the VoiceQL query pipeline.



\---



\# 📮 Testing with Postman



VoiceQL APIs can be tested using Postman.



\## Testing `/health`



Method:



```text

GET

```



URL:



```text

http://127.0.0.1:8000/health

```



Expected response:



```json

{

&#x20;   "status": "ok"

}

```



\---



\## Testing `/ask`



Method:



```text

POST

```



URL:



```text

http://127.0.0.1:8000/ask

```



Headers:



```text

Content-Type: application/json

```



Body:



```json

{

&#x20;   "user\_query": "Show all products"

}

```



\---



\## Testing `/voice`



Method:



```text

POST

```



URL:



```text

http://127.0.0.1:8000/voice

```



Use:



```text

Body → form-data

```



and upload the audio file using the field expected by the API.



The request is then processed through Faster-Whisper.



\---



\# ⚙️ Requirements



The project requires Python and the following major technologies:



\- Python

\- Django

\- Django REST Framework

\- PostgreSQL

\- AI/LLM provider

\- Faster-Whisper

\- Python environment management

\- Environment variables



\---



\# 🐍 Python Environment Setup



It is recommended to create a virtual environment before installing dependencies.



\### Create virtual environment



```bash

python -m venv .venv

```



\### Windows



```bash

.venv\\Scripts\\activate

```



\### Linux/macOS



```bash

source .venv/bin/activate

```



\---



\# 📦 Install Dependencies



From the backend directory:



```bash

pip install -r requirements.txt

```



If dependencies are managed using `uv`, install them according to the project's environment configuration.



\---



\# 🔑 Environment Variables



Sensitive credentials should not be hard-coded into the source code.



Create a:



```text

.env

```



file inside the backend project where the application expects environment configuration.



Example:



```env

GROQ\_API\_KEY=your\_api\_key\_here

```



Database configuration should also be provided through environment variables if the project configuration uses them.



Example:



```env

DB\_NAME=your\_database

DB\_USER=your\_username

DB\_PASSWORD=your\_password

DB\_HOST=localhost

DB\_PORT=5432

```



> Never commit real API keys, database passwords, or other credentials to GitHub.



\---



\# 🗄️ PostgreSQL Setup



VoiceQL requires a PostgreSQL database.



Create a PostgreSQL database and configure Django to connect to it.



Example database configuration:



```text

Database:

PostgreSQL



Host:

localhost



Port:

5432



Database:

your\_database



User:

your\_user



Password:

your\_password

```



After configuring the database, Django can access the PostgreSQL schema through Django's database connection.



\---



\# ▶️ Running the Application



Navigate to the backend directory:



```bash

cd backend

```



Activate the virtual environment.



Then start Django:



```bash

python manage.py runserver

```



The development server will normally be available at:



```text

http://127.0.0.1:8000/

```



\---



\# 🧪 Example Queries



VoiceQL can process requests such as:



\### SELECT



```text

Show all products

```



```text

List all products

```



```text

Show me every product

```



\---



\### Filtering



```text

Show products costing more than 5000

```



```text

Find products below 10000

```



\---



\### Aggregation



```text

How many products are there?

```



```text

What is the average product price?

```



```text

What is the highest product price?

```



```text

What is the lowest product price?

```



\---



\### INSERT



```text

Add a new product named Laptop with price 72000

```



\---



\### UPDATE



```text

Update the Laptop price to 75000

```



\---



\### DELETE



```text

Delete the Laptop product

```



CRUD requests are subject to the application's validation and confirmation rules.



\---



\# 🧠 Database Schema Awareness



One of the important design decisions in VoiceQL is that the AI should not generate SQL using arbitrary table or column names.



Instead, the application reads the available PostgreSQL schema and provides that information to the SQL-generation process.



Conceptually:



```text

PostgreSQL

&#x20;   ↓

information\_schema.columns

&#x20;   ↓

Table / Column / Data Type

&#x20;   ↓

Schema Representation

&#x20;   ↓

AI Prompt

&#x20;   ↓

SQL

```



This helps the model generate SQL based on the actual database structure.



\---



\# 🛡️ Validation and Error Handling



VoiceQL uses validation at multiple levels.



\## Request Validation



The API verifies that the expected request data is available.



For example, if `/ask` expects:



```json

{

&#x20;   "user\_query": "..."

}

```



and the request does not contain the required value, the API can return a client error.



\---



\## SQL Validation



Generated SQL is checked before execution.



The system verifies:



\- SQL is not empty

\- SQL begins with an allowed operation

\- Restricted SQL commands are blocked

\- Only supported database operations are accepted



\---



\## Database Errors



Database-related exceptions can occur when:



\- A table does not exist

\- A column does not exist

\- Data has an invalid type

\- A constraint is violated

\- PostgreSQL is unavailable



These errors should be handled and returned as appropriate API responses.



\---



\## Value Errors



`ValueError` can be used when a supplied value is logically invalid.



For example:



```python

raise ValueError("Invalid SQL query")

```



The API layer can catch the exception and return an appropriate response rather than allowing the application to crash.



\---



\# 📝 Logging



Logging can be used throughout VoiceQL to monitor:



\- Incoming requests

\- Query processing

\- AI processing

\- Generated SQL

\- Validation failures

\- Database errors

\- Voice transcription errors

\- Unexpected exceptions



A typical logging flow is:



```text

Request

&#x20;↓

Log Request

&#x20;↓

Process

&#x20;↓

Log Important Events

&#x20;↓

Success / Error

&#x20;↓

Log Result

```



Logging is especially useful while debugging AI-generated SQL and voice-transcription issues.



\---



\# 🔒 Security Considerations



VoiceQL handles both AI-generated SQL and database access, so security is important.



Recommended practices include:



\### 1. Never expose API keys



Do not place API keys directly inside Python source code.



Use:



```text

.env

```



and environment variables.



\---



\### 2. Never commit `.env`



Add:



```text

.env

```



to `.gitignore`.



\---



\### 3. Validate AI-generated SQL



AI-generated SQL must always pass through validation before execution.



\---



\### 4. Restrict dangerous SQL operations



Commands such as:



```text

DROP

ALTER

TRUNCATE

CREATE

GRANT

REVOKE

```



should remain blocked when they are outside the application's intended functionality.



\---



\### 5. Confirm destructive operations



`DELETE` and other data-modifying operations should require explicit user confirmation.



\---



\# 📈 Why VoiceQL?



Traditional SQL interfaces require users to understand:



```text

Database

&#x20;  +

Tables

&#x20;  +

Columns

&#x20;  +

SQL Syntax

```



VoiceQL attempts to reduce this barrier:



```text

Natural Language

&#x20;      ↓

AI Understanding

&#x20;      ↓

SQL

&#x20;      ↓

Database

```



With voice support:



```text

Voice

&#x20; ↓

Speech-to-Text

&#x20; ↓

Natural Language

&#x20; ↓

AI

&#x20; ↓

SQL

&#x20; ↓

Database

```



This makes database interaction more accessible to users who may not be familiar with SQL.



\---



\# 🎯 Use Cases



VoiceQL can be useful for:



\- Database exploration

\- Data analysis

\- Internal business tools

\- Rapid database queries

\- SQL learning

\- Natural-language database interfaces

\- Voice-enabled data access

\- AI-powered administrative tools

\- Prototyping database assistants



\---



\# 🧱 Technology Stack



| Technology | Purpose |

|---|---|

| Python | Core programming language |

| Django | Backend web framework |

| Django REST Framework | API development |

| PostgreSQL | Relational database |

| AI/LLM | Natural-language SQL generation |

| Faster-Whisper | Voice-to-text transcription |

| Python dotenv / Environment Variables | Configuration and secrets |

| Git | Version control |

| Postman | API testing |



\---



\# 📋 Development Workflow



The overall development workflow is:



```text

1\. User submits text or voice

&#x20;             ↓

2\. Django receives request

&#x20;             ↓

3\. Voice is transcribed if necessary

&#x20;             ↓

4\. Query intent is analyzed

&#x20;             ↓

5\. Metric request is identified when applicable

&#x20;             ↓

6\. Semantic understanding is applied

&#x20;             ↓

7\. Database schema is retrieved

&#x20;             ↓

8\. AI generates PostgreSQL SQL

&#x20;             ↓

9\. SQL is validated

&#x20;             ↓

10\. CRUD confirmation is requested when required

&#x20;             ↓

11\. SQL is executed

&#x20;             ↓

12\. Result is returned

```



\---



\# 🚧 Current Development Areas



Potential areas for future development include:



\- Improved natural-language understanding

\- More predefined metrics

\- Better semantic mappings

\- Improved voice recognition

\- Multi-language voice queries

\- Query history

\- Authentication

\- Role-based database permissions

\- Better SQL explanation

\- Query performance monitoring

\- Streaming voice interaction

\- More advanced database relationships and joins

\- Visualization of query results

\- Production deployment

\- Automated testing

\- Improved error classification



\---



\# 🔮 Future Enhancements



\## Multi-Database Support



Currently the system is designed around PostgreSQL.



Future versions could support:



```text

PostgreSQL

MySQL

SQLite

Microsoft SQL Server

```



\---



\## Advanced Analytics



Natural-language requests could eventually produce:



```text

Tables

Charts

Graphs

Aggregations

Reports

```



For example:



> Show the average price for each product category.



The system could return both the SQL query and a visualization.



\---



\## Query Explanation



VoiceQL could explain generated SQL.



For example:



```text

User:

Show products above 5000

```



Response:



```text

SQL:

SELECT \* FROM product

WHERE product\_price > 5000;

```



Explanation:



```text

The query retrieves all products whose price is greater than 5000.

```



\---



\# 🧪 Testing Strategy



Testing should cover the following areas:



\## API Tests



Test:



```text

/health

/ask

/voice

```



\---



\## SQL Validation Tests



Test valid queries:



```sql

SELECT ...

INSERT ...

UPDATE ...

DELETE ...

```



Test blocked queries:



```sql

DROP ...

ALTER ...

TRUNCATE ...

CREATE ...

GRANT ...

REVOKE ...

```



\---



\## AI Query Tests



Test natural-language variations:



```text

Show all products

List all products

Give me every product

Display all products

```



The expected behavior should remain consistent.



\---



\## Metrics Tests



Test variations such as:



```text

How many products?

Total products?

Product count?

Number of products?

```



These should map to the appropriate metric.



\---



\## Voice Tests



Test:



\- Clear speech

\- Different accents

\- Background noise

\- Short queries

\- Long queries

\- Numbers

\- Product names

\- Similar-sounding words



\---



\# 🐛 Troubleshooting



\## Django server does not start



Make sure the virtual environment is active:



```bash

.venv\\Scripts\\activate

```



Then run:



```bash

python manage.py runserver

```



\---



\## PostgreSQL connection error



Check:



```text

Database name

Username

Password

Host

Port

PostgreSQL service

```



\---



\## AI API error



Check that the required API key is present in `.env`.



For example:



```env

GROQ\_API\_KEY=your\_api\_key

```



Also verify that the selected AI model is available to your API account.



\---



\## `/ask` returns 400 Bad Request



Check that the request contains the expected JSON structure.



Example:



```json

{

&#x20;   "user\_query": "Show all products"

}

```



Also make sure the request header contains:



```text

Content-Type: application/json

```



\---



\## `/voice` returns 404



Verify that the application URL configuration contains the voice endpoint and that the endpoint being called matches the configured route.



For example:



```text

/voice

```



instead of an incorrectly assumed route such as:



```text

/voice-query/

```



\---



\## Voice transcription fails



Check:



\- Audio file exists

\- Audio file format is supported

\- Faster-Whisper is installed

\- Required dependencies are installed

\- Temporary audio file is accessible

\- The audio file is not corrupted



\---



\# 📌 Important Design Principles



VoiceQL follows several important principles:



\### Schema-aware AI



The AI should generate SQL based on the actual database schema.



\### Controlled SQL



Generated SQL is validated before execution.



\### Separation of Responsibilities



Different services handle:



```text

AI processing

Metrics

Voice transcription

API handling

```



\### Confirmation Before Modification



Database-changing operations should require confirmation.



\### Dynamic Schema



The system reads database metadata instead of relying completely on hard-coded schema information.



\---



\# 📂 Repository



GitHub repository:



\[VoiceQL GitHub Repository](https://github.com/mohammedreyaan177-lab/voiceql.git?utm\_source=chatgpt.com)



\---



\# 👨‍💻 Project



\*\*Project Name:\*\* VoiceQL



\*\*Type:\*\* AI-Powered Natural Language and Voice-to-SQL Application



\*\*Backend:\*\* Django + Django REST Framework



\*\*Database:\*\* PostgreSQL



\*\*AI:\*\* LLM-based SQL Generation



\*\*Voice Processing:\*\* Faster-Whisper



\*\*Interface:\*\* REST API



\---



\# 📜 License



Add the appropriate license for the project if one has been selected.



For example:



```text

MIT License

```



If no license has been selected yet, this section should be updated before publishing the project as an open-source package.



\---



\# ⭐ Summary



VoiceQL is an AI-powered database assistant that combines:



```text

Natural Language

&#x20;      +

Voice Input

&#x20;      +

Faster-Whisper

&#x20;      +

Semantic Layer

&#x20;      +

Metrics Layer

&#x20;      +

AI SQL Generation

&#x20;      +

SQL Validation

&#x20;      +

CRUD Reasoning

&#x20;      +

PostgreSQL

```



The goal is to provide a simple interface where users can interact with a relational database using natural language or voice without needing to manually write SQL.



The project demonstrates how \*\*Django, REST APIs, PostgreSQL, Generative AI, semantic reasoning, metrics, SQL validation, and speech recognition\*\* can be combined to create an intelligent database interaction system.

