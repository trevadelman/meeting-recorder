import sqlite3
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from .audio import TranscriptSegment

@dataclass
class Meeting:
    id: str
    title: str
    date: datetime
    duration: float
    audio_path: str
    transcript: List[TranscriptSegment]
    summary: Optional[str] = None

class DatabaseManager:
    def __init__(self):
        from utils import setup_python_path
        setup_python_path()
        from config.config import BASE_DIR
        self.db_path = BASE_DIR / "data/db/meetings.db"
        self.init_database()

    def init_database(self):
        """Initialize the SQLite database with required tables"""
        self.db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    date TEXT,
                    duration REAL,
                    audio_path TEXT,
                    transcript JSON,
                    summary TEXT
                )
            """)

    def save_meeting(self, meeting: Meeting):
        """Save or update a meeting in the database"""
        with sqlite3.connect(self.db_path) as conn:
            transcript_json = json.dumps([{
                'speaker': seg.speaker,
                'text': seg.text,
                'start_time': seg.start_time,
                'end_time': seg.end_time,
                'confidence': seg.confidence
            } for seg in meeting.transcript])
            
            conn.execute("""
                INSERT OR REPLACE INTO meetings
                (id, title, date, duration, audio_path, transcript, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting.id,
                meeting.title,
                meeting.date.isoformat(),
                meeting.duration,
                meeting.audio_path,
                transcript_json,
                meeting.summary
            ))

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Retrieve a meeting by its ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
            
            if result:
                transcript_data = json.loads(result['transcript'])
                transcript = [
                    TranscriptSegment(
                        speaker=seg['speaker'],
                        text=seg['text'],
                        start_time=seg['start_time'],
                        end_time=seg['end_time'],
                        confidence=seg['confidence']
                    ) for seg in transcript_data
                ]
                
                return Meeting(
                    id=result['id'],
                    title=result['title'],
                    date=datetime.fromisoformat(result['date']),
                    duration=result['duration'],
                    audio_path=result['audio_path'],
                    transcript=transcript,
                    summary=result['summary']
                )
        return None

    def get_all_meetings(self) -> List[Meeting]:
        """Retrieve all meetings ordered by date"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute("SELECT * FROM meetings ORDER BY date DESC").fetchall()
            meetings = []
            for result in results:
                transcript_data = json.loads(result['transcript'])
                transcript = [
                    TranscriptSegment(
                        speaker=seg['speaker'],
                        text=seg['text'],
                        start_time=seg['start_time'],
                        end_time=seg['end_time'],
                        confidence=seg['confidence']
                    ) for seg in transcript_data
                ]
                
                meetings.append(Meeting(
                    id=result['id'],
                    title=result['title'],
                    date=datetime.fromisoformat(result['date']),
                    duration=result['duration'],
                    audio_path=result['audio_path'],
                    transcript=transcript,
                    summary=result['summary']
                ))
            return meetings

    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
                return True
        except Exception as e:
            print(f"Error deleting meeting: {e}")
            return False
