# Backend Service

This directory contains the core backend logic for the Query-based Speech Retrieval platform, including the API, database interactions, and embedding generation.

## Structure

*   **`api/`**: Contains the FastAPI application endpoints.
    *   `main.py`: Entry point for the API.
    *   `inferenceAPI.py`: API logic for running inference/queries.
    *   `getTableInfoAPI.py`: API for retrieving data from the database.
*   **`DataBaseFunctions.py`**: Helper functions for interacting with the PostgreSQL database (create database, create tables, add row to a table, etc.).
*   **`InferenceQuery.py`**: Logic for performing semantic search and Q&A over the data of one video.
*   **`embedding.py`**: Functions to generate embedding of the user query using OpenAI or other models.
*   **`searchinDatabase.py`**: Utilities for searching in the database.
*   **`Dokcer`**: Docker configuration file.

## Setup

### Requirements

Install the dependencies:
```bash
pip install -r requirements.txt
```

### Database Configuration

The system expects a PostgreSQL database with `pgvector` enabled.
Default configuration (can be found in `DataBaseFunctions.py` or `frontend/app.py`):
*   **Host**: localhost
*   **Port**: 5433
*   **User**: postgres
*   **Password**: root
*   **Database**: SpeechDatabaseInfo

### Running the API

You can run the API from the root of the project using Uvicorn:

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Docker

To build and run the backend using Docker:

```bash
# Build the image
docker build -f Dokcer -t promptspeech-backend .

# Run the container
docker run -p 8000:8000 promptspeech-backend
```
