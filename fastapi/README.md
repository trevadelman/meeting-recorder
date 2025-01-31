# FastAPI Backend for Meeting Recorder

This directory contains a FastAPI implementation of the Meeting Recorder backend, which can run alongside the existing Flask application. It provides a modern, async REST API with automatic OpenAPI documentation.

## Features

- Full REST API for Meeting Recorder functionality
- Automatic OpenAPI documentation (Swagger UI)
- Async request handling
- Background task processing
- CORS support for frontend integration
- Reuses core functionality from the main application

## Installation

1. Create and activate a virtual environment (requires Python 3.11.11):
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

The FastAPI server requires Python 3.11 (same as the main application). To ensure the correct Python version is used:

```bash
# Using the run script (recommended)
./run.py

# Or explicitly with Python 3.11
python3.11 run.py
```

The server will be available at:
- API: `http://localhost:8001/api`
- Documentation: `http://localhost:8001/docs`
- Alternative docs: `http://localhost:8001/redoc`

## API Documentation

Visit `http://localhost:8001/docs` for interactive API documentation, where you can:
- View all available endpoints
- Test API calls directly
- See request/response schemas
- Download OpenAPI specification

## Key Endpoints

### Audio Devices
- `GET /api/devices` - List available input devices
- `POST /api/devices/select` - Select input device

### Meetings
- `POST /api/meetings/start` - Start recording
- `POST /api/meetings/stop` - Stop recording
- `GET /api/meetings/status` - Get recording status
- `POST /api/meetings/upload` - Upload recording
- `GET /api/meetings` - List all meetings
- `GET /api/meetings/{meeting_id}` - Get meeting details
- `GET /api/meetings/{meeting_id}/audio` - Get meeting audio
- `GET /api/meetings/{meeting_id}/export` - Export meeting
- `DELETE /api/meetings/{meeting_id}` - Delete meeting

### Tags
- `GET /api/tags` - List all tags
- `POST /api/meetings/{meeting_id}/tags` - Add tag to meeting
- `DELETE /api/meetings/{meeting_id}/tags/{tag}` - Remove tag from meeting

## Running Both Servers

You can run both the Flask and FastAPI servers simultaneously:

1. Flask Server (Terminal 1):
   ```bash
   cd ..  # Go to main directory
   python3.11 src/app.py  # Runs on port 5002
   ```

2. FastAPI Server (Terminal 2):
   ```bash
   cd fastapi
   ./run.py  # Runs on port 8001
   ```

This allows you to:
- Continue using the Flask web interface on port 5002
- Develop and test the FastAPI backend on port 8001
- Gradually migrate frontend code to React

## Development Notes

1. Core Functionality:
   - Both implementations share the same core modules from `src/core`
   - Database and file storage are shared
   - Audio processing pipeline remains unchanged

2. Key Differences from Flask Implementation:
   - Async request handling
   - Background task processing for long operations
   - Better type checking with Pydantic
   - Automatic API documentation
   - More structured error responses

3. CORS Configuration:
   - Currently allows all origins for development
   - Should be restricted in production

4. Future Improvements:
   - WebSocket support for real-time updates
   - Rate limiting
   - Authentication/Authorization
   - Request validation middleware
   - Response caching
