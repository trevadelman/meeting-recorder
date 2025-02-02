# Meeting Recorder

A Flask-based application for recording, transcribing, and summarizing meetings with speaker diarization.

The application is available at: https://github.com/trevadelman/meeting-recorder.git

## Features

- **Audio Recording**
  - Client-side recording using browser's microphone
  - Support for all client audio input devices
  - Manual start/stop recording control
  - Real-time duration tracking
  - Visual recording status and progress indicators
  - Network-accessible recording capabilities

- **Speech Processing**
  - Automatic speech recognition using Whisper
  - Speaker diarization with SpeechBrain
  - Multi-speaker detection and labeling
  - High-accuracy transcription

- **Meeting Management**
  - Meeting organization and storage
  - Searchable meeting history
  - Detailed meeting information
  - Audio playback capability

- **Export Options**
  - Multiple export formats (TXT, JSON, Markdown)
  - Structured transcript formatting
  - Meeting summaries
  - Speaker-labeled segments

- **Email Notifications**
  - Automatic email notifications after recording completion
  - Manual email sending from meeting details
  - HTML-formatted meeting summaries
  - Direct links to meeting recordings

## Requirements

### Server Requirements
- Python 3.11.11
- Flask
- SpeechBrain
- Faster Whisper
- PyTorch
- Additional dependencies in `requirements.txt`

### Client Requirements
- Modern web browser with microphone support (Chrome, Firefox, Safari)
- HTTPS connection for microphone access

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/trevadelman/meeting-recorder.git
   cd meeting-recorder
   ```

2. Create and activate a virtual environment (requires Python 3.11.11):
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the application:
   ```bash
   python src/app.py
   ```

## Configuration

The application can be configured through several files in the config/ directory:

- `config.py`: Main configuration file
  - Audio settings
  - Recording parameters
  - Export configurations
  - Flask application settings
  - Email settings (SMTP configuration)

### Email Configuration

The application supports email notifications through SMTP. Configure the following environment variables in a `.env` file:

```bash
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
BASE_URL=https://localhost:5002  # Used for meeting links in emails
```

Note: For Gmail, you'll need to use an App Password if 2FA is enabled. You can generate one at: https://myaccount.google.com/apppasswords

Email functionality is optional - the application will run normally without email configuration, simply hiding email-related UI elements.

## Usage

The application provides two server implementations:

### Flask Server (Web Interface)
1. Start the Flask server:
   ```bash
   python src/app.py
   ```

2. Access the web interface:
   - Local: `https://localhost:5002`
   - Network: `https://<server-ip>:5002`
   
   Note: When accessing over HTTPS, you'll need to accept the security warning for the self-signed certificate.

### FastAPI Server (React Backend)
1. Start the FastAPI server:
   ```bash
   cd fastapi
   ./run.py
   ```

2. Access the API:
   - API Endpoints: `http://localhost:8001/api`
   - Interactive Documentation: `http://localhost:8001/docs`
   - Alternative Documentation: `http://localhost:8001/redoc`

Both servers can run simultaneously, sharing the same core functionality:
- Flask server provides the web interface
- FastAPI server provides a modern REST API for React frontend development

3. Recording a Meeting:
   - Allow microphone access when prompted
   - Select your preferred input device from your computer's available microphones
   - Click "Start Recording"
   - Monitor recording duration in real-time
   - Click "Stop Recording" when finished
   - Wait for processing to complete (progress indicators will show status)

4. Managing Recordings:
   - View all recordings on the main page
   - Play back audio recordings
   - Export transcripts and summaries
   - Delete unwanted recordings

## Project Structure

```
meeting-recorder/
├── src/                # Source code
│   ├── app.py         # Flask application entry point
│   ├── core/          # Core functionality (shared)
│   │   ├── audio.py   # Audio processing
│   │   ├── db.py      # Database operations
│   │   ├── llm.py     # LLM processing
│   │   └── recorder.py # Meeting recorder
│   └── utils/         # Utility functions
├── fastapi/           # FastAPI implementation
│   ├── main.py        # FastAPI application entry point
│   └── run.py         # Server runner script
├── config/            # Configuration files
│   ├── config.py      # Main configuration
│   └── ssl/           # SSL certificates
├── web/              # Flask web interface
│   ├── static/       # Static assets
│   │   └── js/       # JavaScript modules
│   └── templates/    # HTML templates
├── data/             # Data storage (shared)
│   ├── recordings/   # Audio recordings
│   ├── exports/      # Exported files
│   └── db/           # Database files
├── models/           # ML models (shared)
│   └── pretrained/   # Pretrained model files
├── tests/            # Test files
├── requirements.txt  # Python dependencies
└── README.md        # Documentation
```

## Development

The application provides two server implementations that share core functionality:

### Shared Components (src/core/):
- **AudioProcessor**: Handles audio processing and transcription
- **DatabaseManager**: Manages meeting storage and retrieval
- **MeetingRecorder**: Coordinates recording and processing
- **LLMProcessor**: Handles meeting summarization

### Flask Implementation (src/app.py):
- Web interface with HTML templates
- Client-side recording using Web Audio API
- Real-time status updates
- Traditional server-rendered pages

### FastAPI Implementation (fastapi/):
- Modern REST API for React frontend
- Async request handling
- Background task processing
- Automatic API documentation
- Type validation with Pydantic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- Whisper by OpenAI for speech recognition
- SpeechBrain for speaker diarization
- Flask framework
