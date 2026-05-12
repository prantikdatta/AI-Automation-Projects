# NLP-to-SQL Agent (n8n Workflow)

AI-powered natural language to SQL workflow built with n8n, Google Gemini, PostgreSQL, and AI Agents.

This workflow:

* Converts natural language into SQL queries
* Maintains conversational memory
* Executes SQL directly against PostgreSQL
* Returns live database results to users

---

# Workflow Overview

The workflow allows users to ask database questions in plain English.

Example:

```text id="4jx9p6"
How many users signed up last week?
```

The AI Agent:

1. Understands the request
2. Generates SQL
3. Executes the query
4. Returns formatted results

---

# Workflow Architecture

```text id="t6sz7h"
When Chat Message Received
        │
        ▼
      Wait
        │
        ▼
    AI Agent
    ├── Google Gemini Chat Model
    ├── Simple Memory
    ├── PostgresDB
    └── SQL_executor
```

---

# System Architecture

## 1. Trigger — Chat Message Received

### Purpose

Acts as the workflow entry point.

Whenever a user sends a natural language query, the workflow begins execution.

### Example Inputs

```text id="wcrb4l"
How many customers placed orders this month?
```

```text id="0b0m7f"
Show total revenue for last quarter.
```

```text id="fe3d5f"
Which products are selling the most?
```

---

# 2. Wait

## Purpose

Introduces a short delay before processing.

This step is commonly used to:

* Prevent API rate limiting
* Ensure metadata is fully available
* Improve workflow stability

## Configuration

| Setting | Value                     |
| ------- | ------------------------- |
| Delay   | `1–5 Seconds Recommended` |

---

# 3. AI Agent

## Purpose

Acts as the core reasoning engine of the workflow.

The AI Agent:

* Interprets natural language
* Understands user intent
* Generates SQL queries
* Uses tools to execute queries
* Returns database insights

---

# AI Agent Components

The AI Agent connects to four critical systems:

---

## A. Google Gemini Chat Model

### Purpose

Provides the Large Language Model (LLM) responsible for:

* NLP understanding
* SQL generation
* Query reasoning
* Response formatting

## Recommended Model

```text id="1l6lh0"
gemini-1.5-pro
```

or

```text id="uk12i0"
gemini-2.0-flash
```

## Responsibilities

The model converts:

```text id="nt0t5q"
How many users signed up last week?
```

into SQL like:

```sql id="n55fkr"
SELECT COUNT(*)
FROM users
WHERE created_at >= NOW() - INTERVAL '7 days';
```

---

## B. Simple Memory

### Purpose

Enables conversational memory.

The agent remembers previous user interactions, allowing follow-up questions without repeating context.

---

## Example Conversation

### User

```text id="a7s2l6"
How many users signed up last week?
```

### AI

```text id="m4q9n7"
1,284 users signed up last week.
```

### User

```text id="u4zjz0"
How many were from New York?
```

The memory system allows the agent to understand:

```text id="3teo11"
"them" = users who signed up last week
```

---

## C. PostgresDB Tool

## Purpose

Provides direct PostgreSQL database access.

The AI Agent uses this tool to:

* Connect securely
* Run generated SQL
* Fetch live database results

---

## Required Credentials

| Setting  | Example         |
| -------- | --------------- |
| Host     | `localhost`     |
| Port     | `5432`          |
| Database | `analytics_db`  |
| Username | `postgres`      |
| Password | `your_password` |

---

# D. SQL_executor Tool

## Purpose

Executes generated SQL queries safely.

This tool acts as the execution layer between:

```text id="3lgvqs"
AI-generated SQL
```

and

```text id="8r4kko"
PostgreSQL database
```

---

# Workflow Execution Flow

## Step 1 — User Sends Query

Example:

```text id="xvjlwm"
What were our top-selling products this month?
```

---

## Step 2 — AI Agent Interprets Intent

The Gemini model analyzes:

* User intent
* Database structure
* Context from memory

---

## Step 3 — SQL Generation

The AI converts the request into SQL.

Example:

```sql id="ttv2j2"
SELECT product_name, SUM(quantity) AS total_sales
FROM orders
WHERE created_at >= date_trunc('month', CURRENT_DATE)
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 10;
```

---

## Step 4 — Database Execution

The generated SQL is executed against PostgreSQL using:

* PostgresDB
* SQL_executor

---

## Step 5 — Response Returned

The workflow sends formatted results back to the user.

Example:

```text id="8phzcb"
Top-selling products this month:

1. Wireless Mouse — 1,204 sales
2. Mechanical Keyboard — 987 sales
3. USB-C Hub — 811 sales
```

---

# Suggested AI Agent Prompt

Use a system prompt similar to:

```text id="v1hb5x"
You are an expert PostgreSQL assistant.

Your responsibilities:
- Convert natural language into valid PostgreSQL queries
- Use only safe SQL
- Avoid destructive operations
- Return concise explanations
- Use conversational memory when available

Never execute:
- DROP
- DELETE
- TRUNCATE
- ALTER

Only generate safe SELECT queries unless explicitly authorized.
```

---

# Recommended Safety Rules

## Restrict Dangerous SQL

Prevent execution of:

```sql id="2g6gmx"
DROP TABLE
DELETE FROM
TRUNCATE
ALTER TABLE
UPDATE
```

---

## Use Read-Only Database Users

Recommended permissions:

```text id="h8ksd8"
SELECT only
```

---

## Add Query Validation

Validate generated SQL before execution.

---

# Recommended Enhancements

## Schema-Aware Prompting

Provide the AI Agent with:

* Table names
* Column names
* Relationships

This dramatically improves SQL accuracy.

---

## Add Query Logging

Track:

* Generated SQL
* User prompts
* Execution times
* Errors

---

## Add Result Formatting

Use additional nodes to:

* Generate charts
* Create summaries
* Export CSVs
* Send reports

---

# Example Use Cases

## Analytics Assistant

```text id="x2krgn"
What was monthly revenue growth?
```

---

## Customer Insights

```text id="f32u8u"
Which customers spend the most?
```

---

## Sales Dashboard

```text id="wkhzmu"
Show today's total sales.
```

---

## Inventory Monitoring

```text id="h3mbpw"
Which products are low in stock?
```

---

# Tech Stack

* n8n
* Google Gemini
* PostgreSQL
* AI Agent Framework
* SQL Executor Tool

---

# Benefits

* No SQL knowledge required
* Conversational database access
* Real-time analytics
* Fast reporting workflows
* Memory-enabled follow-up queries

---

# Architecture Diagram

<img width="763" height="299" alt="image" src="https://github.com/user-attachments/assets/168da5ad-f42c-45c7-9b49-7304e9b2b88c" />
<br><br>

![Image](https://images.openai.com/static-rsc-4/WimQjBcY1yFaIsp43uoCQ84XhbablGA9XHMRpXjVMzQLFVG98uUjzUF3TwE5QUu1hJcV29q3RJunFNdeBncazN5kjf_3vBIl1z3kXYJE6uYiB1SNQHCLi1GdOk6DVMVLvhuEeTzuC8UqSgWixVSqnND1IQli8THtwFXng-mplgj7ZYWPg_iRud0kK8CA3sjJ?purpose=fullsize)

![Image](https://images.openai.com/static-rsc-4/w1sPbakDO-8fUlWkj-jgZjpVhANa4gNVb1PwuJvsZxR2ffSiBvi349XvOksC_Wtcxp-FXilPnQzvFz4loizrC5NAsia6_FWmLMlaXveaPYF8Zd1T250b6fwQ1YgF5NL407qe68RcEa34qAuTubxpPei_8ONDw1hnEdZ8bHv8AxtiuSi38lQCEx3KCfUi--G5?purpose=fullsize)

---

# License

MIT License

