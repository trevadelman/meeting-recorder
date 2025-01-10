from pathlib import Path
import os

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Directory Configuration
RECORDINGS_DIR = BASE_DIR / "recordings"
EXPORTS_DIR = BASE_DIR / "exports"
DB_PATH = BASE_DIR / "meetings.db"

# Ensure directories exist
RECORDINGS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Audio Configuration
SAMPLE_RATE = 44100
CHANNELS = 1
WHISPER_MODEL = "medium"  # Options: tiny, base, small, medium, large
COMPUTE_TYPE = "int8"     # Options: int8, float16, float32

# Audio Input Configuration
DEFAULT_INPUT_DEVICE = None  # None means system default
INPUT_DEVICE_SETTINGS = {
    'latency': 'low',     # Options: low, high
    'dtype': 'int16',     # Data type for audio samples
    'blocksize': 1024     # Buffer size for audio blocks
}

# Speaker Diarization Configuration
MAX_SPEAKERS = 3
SEGMENT_LENGTH = 3  # seconds
SPEAKER_CLUSTERING_METRIC = 'cosine'
SPEAKER_CLUSTERING_LINKAGE = 'average'

# LLM Configuration
LLM_API_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "llama3:latest"
LLM_TIMEOUT = 30  # seconds

# Flask Configuration
class FlaskConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    TEMPLATES_AUTO_RELOAD = True
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = BASE_DIR / "flask_session"
    SESSION_PERMANENT = False
    
    # Custom settings
    MAX_RECORDING_DURATION = 3600  # 1 hour
    MIN_RECORDING_DURATION = 10    # 10 seconds
    DEFAULT_RECORDING_DURATION = 60 # 1 minute

# Export Configuration
EXPORT_FORMATS = {
    'txt': {
        'extension': '.txt',
        'mime_type': 'text/plain'
    },
    'json': {
        'extension': '.json',
        'mime_type': 'application/json'
    },
    'md': {
        'extension': '.md',
        'mime_type': 'text/markdown'
    }
}

# Summary Generation Prompts
SUMMARY_PROMPT_TEMPLATE = """As an AI meeting assistant, analyze this meeting transcript and provide:
1. Key Topics: Main subjects that were introduced or discussed
2. Context: Any background information or setup provided
3. Next Steps: Suggested follow-ups based on the topics mentioned

Keep the summary concise and focus on the introductory nature of the discussion if it was brief.

Meeting Transcript:
{transcript}"""

# Error Messages
ERROR_MESSAGES = {
    'recording_in_progress': 'A recording is already in progress',
    'invalid_duration': 'Invalid recording duration',
    'meeting_not_found': 'Meeting not found',
    'processing_error': 'Error processing audio',
    'summary_generation_error': 'Error generating summary',
    'export_error': 'Error exporting meeting',
    'database_error': 'Database error occurred',
    'device_error': 'Error accessing audio device',
    'no_devices': 'No input devices found'
}

# Cache Configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
}
