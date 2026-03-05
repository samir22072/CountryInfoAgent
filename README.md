# Country Information AI Agent 🌍

A full-stack application featuring a sophisticated AI agent that provides detailed information about countries using the [REST Countries API](https://restcountries.com/). The agent is built with **LangGraph** for powerful, stateful orchestration and **FastAPI** for a high-performance backend.

## 🚀 Key Features

- **Intelligent Intent Extraction**: Automatically identifies the country and specific information requested (population, capital, currency, etc.).
- **Auto-Correction**: Self-corrects misspelled country names using LLM-powered suggestions.
- **Answer Synthesis**: Combines real-time API data with LLM reasoning to provide human-like, accurate responses.
- **Response Validation**: A dedicated validator node ensures the final answer is accurate and matches the original user intent.
- **Modern UI**: A sleek, responsive chat interface built with **Next.js 15+** and **Tailwind CSS**.

---

## 🏗 Project Structure

```bash
country-info-agent/
├── backend/                # Python FastAPI Backend
│   ├── api/                # Backend API implementation
│   │   ├── index.py        # API Entry point
│   │   ├── graph.py        # LangGraph workflow
│   │   ├── nodes.py        # Graph node logic
│   │   ├── models.py       # Data models
│   │   ├── llm_factory.py  # LLM initialization
│   │   └── config.json     # Configuration and prompts
│   ├── .env                # Local environment variables
│   └── pyproject.toml      # Dependency management
├── frontend/               # Next.js Frontend
│   ├── src/                # React components and pages
│   ├── public/             # Static assets
│   ├── tailwind.config.ts  # Styling configuration
│   └── package.json        # Frontend dependencies
├── .gitignore              # Git exclusions
└── README.md               # You are here!
```

---

## 🧠 The AI Agent (LangGraph Workflow)

The backend utilizes **LangGraph** to manage the AI's "thought process" as a stateful directed graph. This allows for complex loops, such as correcting errors and validating answers before they reach the user.

### Workflow Nodes:
1.  **`identify_intent`**: Parses the user query to extract the `country` and `intent_fields` (e.g., "What is the population of France?" -> `France`, `["population"]`).
2.  **`invoke_tool`**: Fetches real-time data from the REST Countries API.
3.  **`correct_country_name`**: If the API returns a 404, this node attempts to fix the country name (e.g., "Frnce" -> "France") and retries the search.
4.  **`synthesize_answer`**: Merges the API data with the conversation history to generate a comprehensive markdown response.
5.  **`validate_answer`**: Acts as a "supervisor" to check if the generated answer is grounded in the API data and satisfies the user's question. If validation fails, it loops back to synthesis with specific feedback for refinement.

---

## 🛠 Tech Stack

- **Backend**: Python 3.10+, FastAPI, LangGraph, LangChain, Pydantic.
- **Frontend**: Next.js 15 (App Router), React 19, Tailwind CSS, Lucide React.
- **LLM**: Google Gemini (via `langchain-google-genai`).

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google API Key (for Gemini)

### 1. Backend Setup
```bash
cd backend
# Install dependencies
poetry install
# Enter the virtual environment
poetry shell
# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 2. Frontend Setup
```bash
cd frontend
# Install dependencies
npm install
```

---

## 🏃‍♂️ Running the Project

### Start the Backend
From the `backend` directory:
```bash
python api/index.py
# The API will be available at http://localhost:8000
```

### Start the Frontend
From the `frontend` directory:
```bash
npm run dev
# The UI will be available at http://localhost:3000
```

---

## 📝 Environment Variables

### Backend (`backend/.env`)
- `GOOGLE_API_KEY`: Your Google Gemini API key.
- `ALLOW_ORIGINS`: (Optional) Comma-separated list of allowed CORS origins.
- `MODEL_NAME`: (Optional) The LLM model to use (default: `gemini-2.0-flash`).

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_BASE_URL`: The URL of the backend API (default: `http://localhost:8000`).