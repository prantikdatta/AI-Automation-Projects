"""
Canonical Skill Dictionary

Purpose
-------
Maps multiple aliases of the same technology or skill
to one canonical representation.

This file should NOT contain scoring logic.

It should only normalize terminology.

Example

PowerBI
↓

power bi

Microsoft Power BI
↓

power bi
"""

SKILL_ALIASES = {

    # ==========================================================
    # PYTHON
    # ==========================================================

    "python": "python",
    "python3": "python",
    "python 3": "python",
    "python programming": "python",

    # ==========================================================
    # SQL
    # ==========================================================

    "sql": "sql",
    "mysql": "sql",
    "postgres": "sql",
    "postgresql": "sql",
    "tsql": "sql",
    "t-sql": "sql",
    "sql server": "sql",
    "mssql": "sql",
    "oracle sql": "sql",
    "teradata": "sql",
    "sqlite": "sql",

    # ==========================================================
    # POWER BI
    # ==========================================================

    "power bi": "power bi",
    "powerbi": "power bi",
    "microsoft power bi": "power bi",
    "ms power bi": "power bi",
    "pbi": "power bi",

    # ==========================================================
    # TABLEAU
    # ==========================================================

    "tableau": "tableau",
    "tableau desktop": "tableau",
    "tableau server": "tableau",

    # ==========================================================
    # EXCEL
    # ==========================================================

    "excel": "excel",
    "advanced excel": "excel",
    "ms excel": "excel",
    "microsoft excel": "excel",

    # ==========================================================
    # DAX
    # ==========================================================

    "dax": "dax",
    "power bi dax": "dax",

    # ==========================================================
    # POWER QUERY
    # ==========================================================

    "power query": "power query",
    "m language": "power query",
    "power query m": "power query",

    # ==========================================================
    # FABRIC
    # ==========================================================

    "microsoft fabric": "fabric",
    "fabric": "fabric",
    "fabric analytics": "fabric",

    # ==========================================================
    # AZURE
    # ==========================================================

    "azure": "azure",
    "azure data factory": "azure data factory",
    "adf": "azure data factory",
    "azure synapse": "azure synapse",

    # ==========================================================
    # AWS
    # ==========================================================

    "aws": "aws",
    "amazon web services": "aws",

    # ==========================================================
    # GCP
    # ==========================================================

    "gcp": "gcp",
    "google cloud": "gcp",

    # ==========================================================
    # DATABRICKS
    # ==========================================================

    "databricks": "databricks",

    # ==========================================================
    # SNOWFLAKE
    # ==========================================================

    "snowflake": "snowflake",

    # ==========================================================
    # DBT
    # ==========================================================

    "dbt": "dbt",
    "data build tool": "dbt",

    # ==========================================================
    # AIRFLOW
    # ==========================================================

    "apache airflow": "airflow",
    "airflow": "airflow",

    # ==========================================================
    # ETL
    # ==========================================================

    "etl": "etl",
    "elt": "etl",

    # ==========================================================
    # MACHINE LEARNING
    # ==========================================================

    "machine learning": "machine learning",
    "ml": "machine learning",

    # ==========================================================
    # AI
    # ==========================================================

    "artificial intelligence": "artificial intelligence",
    "ai": "artificial intelligence",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "generative ai": "generative ai",
    "llm": "large language models",
    "large language models": "large language models",
    "prompt engineering": "prompt engineering",

    # ==========================================================
    # DATA ENGINEERING
    # ==========================================================

    "data engineering": "data engineering",
    "data engineer": "data engineering",

    # ==========================================================
    # DATA ANALYTICS
    # ==========================================================

    "data analytics": "data analytics",
    "analytics": "data analytics",
    "business analytics": "business analytics",
    "product analytics": "product analytics",

    # ==========================================================
    # PMO
    # ==========================================================

    "pmo": "project management office",
    "project management office": "project management office",
    "program management": "program management",
    "project management": "project management",

    # ==========================================================
    # AGILE
    # ==========================================================

    "agile": "agile",
    "scrum": "scrum",
    "kanban": "kanban",

    # ==========================================================
    # VERSION CONTROL
    # ==========================================================

    "git": "git",
    "github": "github",
    "gitlab": "gitlab",

    # ==========================================================
    # PROGRAMMING
    # ==========================================================

    "r": "r",
    "powershell": "powershell",

    # ==========================================================
    # REPORTING
    # ==========================================================

    "dashboard": "dashboarding",
    "dashboarding": "dashboarding",
    "reporting": "reporting",
    "visualization": "data visualization",
    "data visualization": "data visualization",

    # ==========================================================
    # SOFT SKILLS
    # ==========================================================

    "stakeholder management": "stakeholder management",
    "communication": "communication",
    "problem solving": "problem solving",
    "leadership": "leadership",
    "team management": "team management",
}