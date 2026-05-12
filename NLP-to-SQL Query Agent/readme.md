## FLOW

<img width="763" height="299" alt="image" src="https://github.com/user-attachments/assets/168da5ad-f42c-45c7-9b49-7304e9b2b88c" />

System Architecture: NLP-to-SQL Agent
The workflow follows a linear execution path from user input to database execution:

1. Trigger: Chat Message Received
The process begins when a user sends a natural language query (e.g., "How many users signed up last week?"). This acts as the entry point for the automation.

2. Delay: Wait Step
There is a brief Wait state. In these types of automation flows, this is often used to ensure all message metadata is fully processed or to prevent rate-limiting before hitting the AI model.

3. Core: AI Agent
The AI Agent acts as the "brain" of the operation. It is connected to three critical components that allow it to function:

Model (Google Gemini Chat Model): The Large Language Model (LLM) that interprets the English text and generates the corresponding SQL syntax.

Memory (Simple Memory): This allows the agent to remember previous parts of the conversation, enabling follow-up questions (e.g., "And how many of them were from New York?").

Tools (PostgresDB & SQL_executor): Instead of just giving the user the code, the agent is equipped with a tool to actually run the query.

4. Action: Database Execution
The agent uses the PostgresDB executeQuery tool and the SQL_executor to:

Connect to the database.

Run the generated SQL code.

Retrieve the raw data results to be formatted and sent back to the user.
