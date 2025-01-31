import hashlib
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from .audio import AudioProcessor
from .db import DatabaseManager, Meeting
from .llm import LLMProcessor

class MeetingRecorder:
    def __init__(self):
        self.db = DatabaseManager()
        self.audio_processor = AudioProcessor()
        self.llm_processor = LLMProcessor()
        self.current_recording = None
        self.recording_start_time = None
        self.status_callback = None

    def start_recording(
        self, 
        title: str = None,
        status_callback: Optional[Callable] = None
    ) -> bool:
        """Start recording a new meeting"""
        try:
            self.status_callback = status_callback
            self.recording_start_time = datetime.now()
            self.title = title
            self.current_recording = self.audio_processor.start_recording()
            if status_callback:
                status_callback("Recording started...")
            return True
        except Exception as e:
            self.current_recording = None
            self.recording_start_time = None
            self.status_callback = None
            raise e

    def stop_recording(self) -> str:
        """Stop recording and return the audio path"""
        if not self.current_recording:
            raise RuntimeError("No active recording")

        try:
            # Stop recording and get audio path
            audio_path = self.audio_processor.stop_recording(self.current_recording)

            # Clear recording state
            self.current_recording = None
            self.recording_start_time = None
            self.status_callback = None

            return audio_path

        except Exception as e:
            # Clean up recording state on error
            self.current_recording = None
            self.recording_start_time = None
            self.status_callback = None
            raise e

    def record_meeting(
        self, 
        duration: float, 
        title: str = None, 
        status_callback: Optional[Callable] = None, 
        audio_data=None
    ) -> Meeting:
        """Record and process a meeting with provided audio data"""
        if not audio_data:
            raise ValueError("Audio data is required")

        audio_array, sample_rate = audio_data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.audio_processor.audio_dir / f"meeting_{timestamp}.wav"
        
        with wave.open(str(filename), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_array.tobytes())
        
        # Process audio
        transcript = self.audio_processor.process_audio(str(filename), status_callback)
        
        if status_callback:
            status_callback("Generating summary...")
        
        # Generate meeting ID
        meeting_id = hashlib.md5(
            f"{filename}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        # Create meeting object
        meeting = Meeting(
            id=meeting_id,
            title=title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            date=datetime.now(),
            duration=duration,
            audio_path=str(filename),
            transcript=transcript
        )
        
        # Generate summary
        meeting.summary = self.llm_processor.generate_summary(transcript)
        
        # Save to database
        if status_callback:
            status_callback("Saving meeting...")
        self.db.save_meeting(meeting)
        
        return meeting

    def export_meeting(self, meeting_id: str, format: str = 'txt') -> str:
        """Export meeting to file"""
        meeting = self.db.get_meeting(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
            
        # Create exports directory if it doesn't exist
        from utils import setup_python_path
        setup_python_path()
        from config.config import BASE_DIR
        export_dir = BASE_DIR / "data/exports"
        export_dir.mkdir(exist_ok=True)
        
        filename = export_dir / f"meeting_{meeting.date.strftime('%Y%m%d_%H%M')}_{meeting.id[:8]}.{format}"
        
        with open(filename, 'w') as f:
            f.write(f"Meeting: {meeting.title}\n")
            f.write(f"Date: {meeting.date}\n")
            f.write(f"Duration: {meeting.duration} seconds\n\n")
            f.write("Transcript:\n")
            for seg in meeting.transcript:
                f.write(f"\n{seg.speaker} ({seg.start_time:.1f}s - {seg.end_time:.1f}s):\n")
                f.write(f"{seg.text}\n")
            f.write("\nSummary:\n")
            f.write(meeting.summary)
        
        return str(filename)
