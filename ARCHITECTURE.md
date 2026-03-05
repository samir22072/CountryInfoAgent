# Country Info Agent: Architecture & Design Deep Dive

This document provides a technical overview of the Country Info Agent, exploring its internal mechanics, agentic workflows, and considerations for production deployment.

---

## 🏗 Overall Architecture

The system follows a classic **Micro-Frontend/Service** pattern, decoupled via a RESTful API and an asynchronous task queue for handling LLM latency.

```mermaid
graph TD
    User((User)) -->|React Web App| Frontend[Next.js Frontend]
    Frontend -->|POST /chat| API[FastAPI Gateway]
    API -->|Background Task| Worker[LangGraph Agent Worker]
    API -->|destination| index[/api/index.py]
    Worker -->|Invoke| LLM[Google Gemini LLM]
    Worker -->|Fetch| Tool[REST Countries API]
    Worker -->|Update Status| DB[(In-Memory Task Store)]
    Frontend -->|GET /chat/task_id| API
    API -->|Read| DB
```

### Components:
1.  **Backend (FastAPI)**: A Python-based API structured for Vercel deployment. All logic resides in the `api/` directory to satisfy Vercel's serverless function requirements.
2.  **Frontend (Next.js)**: A React-based client that manages chat state and polls the backend for agent "thoughts" and final results.
3.  **Agent Worker (LangGraph)**: The "brain" of the system. It maintains a state machine that controls the sequence of LLM calls and tool executions.
4.  **External Context**:
    *   **LLM**: Gemini-2.0-flash is used for intent extraction, synthesis, and validation.
    *   **REST Countries API**: The single source of truth for geographical and political data.

---

## 🧠 Agent Flow & Logic

The agent is organized as a **StateGraph**, where each node represents a specific functional step and edges represent conditional transitions.

### 1. Intent Identification (`identify_intent`)
*   **Input**: Full chat history.
*   **Logic**: Uses structured output (Pydantic) to extract:
    *   `country`: The target entity.
    *   `intent_fields`: Specific facts requested.
    *   `dynamic_instructions`: Contextual hints for the synthesis stage.
*   **Example**: 
    *   *Query*: "How many people live in Frnce?"
    *   *Extraction*: `country="Frnce"`, `intent_fields=["population"]`.

### 2. Tool Invocation & Correction Loop
*   **`invoke_tool`**: Attempts to fetch data for the extracted country name.
*   **`correct_country_name`**: If the API returns a 404, the agent loops here. The LLM suggests a fix (e.g., "Frnce" -> "France").
*   **Edge Case Handling**: The system allows for up to 2 correction attempts before failing gracefully.

### 3. Synthesis & Validation Loop
*   **`synthesize_answer`**: Generates a natural language response using the API data and `dynamic_instructions`.
*   **`validate_answer`**: A "Critic" node that reviews the output against the raw API data. 
    *   If correctly grounded -> `VALID` -> **END**.
    *   If hallucinating or missing info -> `INVALID` -> Loop back to **Synthesis** with feedback.

---

## 📂 Agent Flow Examples

### Case A: Success Path
1.  **User**: "Capital of Japan?"
2.  **Intent**: `country="Japan"`, `fields=["capital"]`.
3.  **Tool**: Returns `Tokyo`.
4.  **Synthesis**: "The capital of Japan is Tokyo."
5.  **Validator**: Returns `VALID`.

### Case B: Auto-Correction Path
1.  **User**: "What is the currency of Swizerland?"
2.  **Tool**: Fails (404).
3.  **Correction**: Corrects "Swizerland" to "Switzerland".
4.  **Tool (Retry)**: Returns `CHF (Swiss Franc)`.
5.  **Synthesis**: "Switzerland uses the Swiss Franc (CHF)."

---

## 🚀 Production Behavior

In a production environment, the following considerations are implemented:

-   **Asynchronous Processing**: Chat requests are processed in background threads. The frontend receives a `task_id` and polls for progress, ensuring a responsive UI even if the LLM is slow.
-   **Stateful Memory**: While currently in-memory, the `AgentState` is designed to be easily Serializable, allowing persistence in Redis or PostgreSQL for long-running sessions.
-   **Observability**: "Thoughts" from each node are streamed to the client, giving users visibility into the agent's reasoning process.
-   **Retry Strategy**: Nodes are wrapped in retry logic (specifically for the correction and validation loops) to handle transient API failures or stochastic LLM outputs.

---

## ⚠️ Limitations & Trade-offs

| Feature | Limitation | Trade-off / Solution |
| :--- | :--- | :--- |
| **Data Recency** | Limited by REST Countries API update frequency. | Real-time data is prioritised over LLM training data. |
| **Latency** | Multiple LLM chain calls (Intent + Synthesis + Validate) increase response time. | Used `gemini-2.0-flash` for speed and background polling for UX. |
| **API Dependency** | If REST Countries API is down, the agent can only provide general info or fail. | Implemented `synthesize_error` node for graceful degradation. |
| **Cost** | Validation loops (Self-Correction) double token usage per request. | Trade-off: High accuracy vs lower cost. Essential for "hallucination-free" answers. |
| **Scalability** | Current `task_store` is in-memory. | Production would require a Redis/SQS back-end for the task queue. |
