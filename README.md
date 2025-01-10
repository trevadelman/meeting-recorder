# Meeting Recorder

A Flask-based application for recording, transcribing, and summarizing meetings with speaker diarization.

## Features

- **Audio Recording**
  - Configurable input device selection
  - Support for multiple audio input devices
  - Real-time recording progress tracking
  - Customizable recording duration

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

- Python 3.11+
- Flask
- SoundDevice
- SpeechBrain
- Faster Whisper
- PyTorch
- Additional dependencies in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd meeting-recorder
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the application:
   ```bash
   python app.py
   ```

## Configuration

The application can be configured through several files:

- `config.py`: Main configuration file
  - Audio settings
  - Recording parameters
  - Export configurations
  - Flask application settings

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Access the web interface at `http://localhost:5000`

3. Recording a Meeting:
   - Select your preferred audio input device
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
├── app.py              # Flask application entry point
├── config.py           # Configuration settings
├── core.py            # Core functionality
├── requirements.txt    # Python dependencies
├── templates/         # HTML templates
│   ├── base.html
│   ├── index.html
│   └── meeting_detail.html
├── static/            # Static assets
├── recordings/        # Stored recordings
└── exports/          # Exported files
```

## Development

The application is structured into several main components:

- **AudioProcessor**: Handles recording and audio processing
- **DatabaseManager**: Manages meeting storage and retrieval
- **MeetingRecorder**: Coordinates recording and processing
- **LLMProcessor**: Handles meeting summarization

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
