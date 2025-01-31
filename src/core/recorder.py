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
    
    def record_meeting(
        self, 
        duration: float, 
        title: str = None, 
        status_callback: Optional[Callable] = None, 
        audio_data=None
    ) -> Meeting:
        """Record and process a new meeting"""
        # Record audio or use provided audio data
        if audio_data:
            audio_array, sample_rate = audio_data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.audio_processor.audio_dir / f"meeting_{timestamp}.wav"
            
            with wave.open(str(filename), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_array.tobytes())
            
            audio_path = str(filename)
        else:
            _, audio_path = self.audio_processor.record_meeting(duration, status_callback)
        
        # Process audio
        transcript = self.audio_processor.process_audio(audio_path, status_callback)
        
        if status_callback:
            status_callback("Generating summary...")
        
        # Generate meeting ID
        meeting_id = hashlib.md5(
            f"{audio_path}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        # Create meeting object
        meeting = Meeting(
            id=meeting_id,
            title=title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            date=datetime.now(),
            duration=duration,
            audio_path=audio_path,
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
