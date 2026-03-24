# Meditation Guide Services

Personalized meditation audio generation backend.

## Overview
This is a FastAPI-based backend service for generating and managing personalized meditation audio. It leverages Google GenAI for generation and SQLAlchemy for asynchronous database operations.

## Features
- **Session Management:** Endpoints for starting and handling meditation sessions.
- **Meditation Engine:** Generation of personalized meditation scripts and audio.
- **Music Blocks:** Integration of pre-generated background music blocks.
- **Static Assets:** Serves generated audio files automatically.

## Requirements
- Python 3.9+
- Database backend compatible with `asyncpg` (e.g., PostgreSQL)

## Installation & Setup

1. **Clone the project repository.**
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables:**
   Create a `.env` file in the root directory (never commit this) and provide the necessary configuration, such as your GenAI keys and Database URL.

## Running the Application

Start the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Once running, interactive API documentation is automatically accessible at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Project Structure
- `app/` - The core application package
  - `routes/` - FastAPI endpoints (session, meditation, music)
  - `schemas/` - Pydantic models for request/response validation
  - `services/` - Business logic and core features
  - `database/` - SQLAlchemy models and connection configuration
  - `config/` - Application configurations
- `storage/` - Directory storing generated meditation audio files
- `venv/` - Virtual environment
