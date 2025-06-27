# Zoo Management Platform

A demonstration project that integrates **LangChain** and **FastAPI** to control authenticated internal APIs using GenAI tool calling. The project simulates a zoo management platform that can be partially operated through natural language prompts interpreted by an AI agent.

## Project Structure

```
auth0-zoo-ai/
├── api/              # Internal API implementation (FastAPI)
├── agent/            # LangChain application with frontend and backend
├── poetry.lock       # Poetry lock file
├── pyproject.toml    # Poetry project configuration
└── requirements.txt  # Alternative requirements file
```

## Prerequisites

- Python 3.10 or higher
- Poetry (Python dependency management tool)

### Installing Poetry

If you don't have Poetry installed, you can install it using one of these methods:

**Using pip:**

```bash
pip install poetry
```

**Using the official installer:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**On macOS with Homebrew:**

```bash
brew install poetry
```

## Installation

1. **Install dependencies using Poetry:**

   ```bash
   poetry install
   ```

   This will install all dependencies defined in `pyproject.toml` and create a virtual environment.

## Running the Projects

### 1. API Server (Port 8000)

The API server provides the internal endpoints for zoo management operations.

**Start the API server:**
```bash
cd api
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```


The API will be available at: `http://localhost:8000`