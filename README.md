# Meeting Recorder

A Flask-based application for recording, transcribing, and summarizing meetings with speaker diarization.

The application is available at: https://github.com/trevadelman/meeting-recorder.git

## Features

- **Audio Recording**
  - Client-side recording using browser's microphone
  - Support for all client audio input devices
  - Real-time recording progress tracking
  - Customizable recording duration
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

## Usage

1. Start the application:
   ```bash
   python src/app.py
   ```

2. Access the web interface:
   - Local: `https://localhost:5002`
   - Network: `https://<server-ip>:5002`
   
   Note: When accessing over HTTPS, you'll need to accept the security warning for the self-signed certificate.

3. Recording a Meeting:
   - Allow microphone access when prompted
   - Select your preferred input device from your computer's available microphones
   - Set the meeting duration
   - Click "Start Recording"
   - Wait for processing to complete

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
│   ├── core/          # Core functionality
│   │   ├── audio.py   # Audio processing
│   │   ├── db.py      # Database operations
│   │   ├── llm.py     # LLM processing
│   │   └── recorder.py # Meeting recorder
│   └── utils/         # Utility functions
├── config/            # Configuration files
│   ├── config.py      # Main configuration
│   └── ssl/           # SSL certificates
├── web/              # Web-related files
│   ├── static/       # Static assets
│   │   └── js/       # JavaScript modules
│   └── templates/    # HTML templates
├── data/             # Data storage
│   ├── recordings/   # Audio recordings
│   ├── exports/      # Exported files
│   └── db/           # Database files
├── models/           # ML models
│   └── pretrained/   # Pretrained model files
├── tests/            # Test files
├── requirements.txt  # Python dependencies
└── README.md        # Documentation
```

## Development

The application is structured into several main components:

- **AudioProcessor**: Handles audio processing and transcription
- **DatabaseManager**: Manages meeting storage and retrieval
- **MeetingRecorder**: Coordinates recording and processing
- **LLMProcessor**: Handles meeting summarization
- **Client-side Recording**: Browser-based audio capture using Web Audio API

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
