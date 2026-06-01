# Query-based Speech Retrieval

Query-based Speech Retrieval is an interactive learning platform designed to make video and book content accessible and searchable. It leverages AI to provide transcription, summarization, translation, and question-answering capabilities for your media library.

## Project Structure

*   **`frontend/`**: A Dash-based web application that provides the user interface for browsing videos/books and interacting with the content.
*   **`backend/`**: The core logic handling API requests (FastAPI), database interactions (PostgreSQL), and AI inference (Embeddings/RAG).
*   **`processVideo/`**: Data ingestion pipeline. Contains scripts to process new videos/books, transcribe audio, generate embeddings, and populate the database.
*   **`DevAndRes/`**: Development and Research folder containing scripts for testing and evaluating new features.
*   **`ASR/`**: Automatic Speech Recognition module to transcribe audio using OpenAI Whisper.

## Key Features

*   **Video & Book Library**: Organize and browse your educational content.
*   **Smart Q&A**: Ask questions about the content of a video or book and get precise answers with timestamps.
*   **Transcription & Translation**: Automatically generate transcripts and translations for videos.
*   **Summarization**: Get quick summaries of long content.
*   **Semantic Search**: Find relevant audio segment using natural language queries.

## Prerequisites

*   **Python 3.11+**
*   **PostgreSQL**: with `pgvector` extension enabled.
*   **FFmpeg**: For video/audio processing.
