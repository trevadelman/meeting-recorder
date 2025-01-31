import sqlite3
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Set
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
    tags: Set[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()

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
            # Create meetings table
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
            
            # Create tags table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            # Create meeting_tags junction table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meeting_tags (
                    meeting_id TEXT,
                    tag_id INTEGER,
                    PRIMARY KEY (meeting_id, tag_id),
                    FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
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
            
            # Save meeting
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
            
            # Save tags
            if meeting.tags:
                for tag in meeting.tags:
                    # Insert or get tag ID
                    cursor = conn.execute(
                        "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                        (tag,)
                    )
                    if cursor.rowcount == 0:
                        cursor = conn.execute(
                            "SELECT id FROM tags WHERE name = ?",
                            (tag,)
                        )
                    tag_id = cursor.lastrowid or cursor.fetchone()[0]
                    
                    # Link tag to meeting
                    conn.execute("""
                        INSERT OR IGNORE INTO meeting_tags (meeting_id, tag_id)
                        VALUES (?, ?)
                    """, (meeting.id, tag_id))

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Retrieve a meeting by its ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
            
            if result:
                # Get tags
                tags = set()
                tag_rows = conn.execute("""
                    SELECT t.name FROM tags t
                    JOIN meeting_tags mt ON mt.tag_id = t.id
                    WHERE mt.meeting_id = ?
                """, (meeting_id,)).fetchall()
                tags = {row[0] for row in tag_rows}
                
                # Parse transcript
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
                    summary=result['summary'],
                    tags=tags
                )
        return None

    def get_all_meetings(
        self, 
        tag_filters: Optional[List[str]] = None,
        title_search: Optional[str] = None,
        transcript_search: Optional[str] = None
    ) -> List[Meeting]:
        """
        Retrieve all meetings ordered by date with optional filters:
        - tag_filters: List of tags (AND logic)
        - title_search: Case-insensitive partial match on title
        - transcript_search: Case-insensitive search in transcript text
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Base query
            query = "SELECT DISTINCT m.* FROM meetings m"
            params = []
            where_clauses = []
            
            # Add tag filtering
            if tag_filters:
                tag_placeholders = ','.join(['?' for _ in tag_filters])
                query += f"""
                    WHERE m.id IN (
                        SELECT mt.meeting_id
                        FROM meeting_tags mt
                        JOIN tags t ON t.id = mt.tag_id
                        WHERE t.name IN ({tag_placeholders})
                        GROUP BY mt.meeting_id
                        HAVING COUNT(DISTINCT t.name) = ?
                    )
                """
                params.extend(tag_filters)
                params.append(len(tag_filters))
            
            # Add title search
            if title_search:
                where_clause = "LOWER(m.title) LIKE LOWER(?)"
                params.append(f"%{title_search}%")
                where_clauses.append(where_clause)
            
            # Add transcript search
            if transcript_search:
                where_clause = """
                    m.id IN (
                        SELECT m2.id
                        FROM meetings m2, json_each(m2.transcript) as je
                        WHERE LOWER(json_extract(je.value, '$.text')) LIKE LOWER(?)
                    )
                """
                params.append(f"%{transcript_search}%")
                where_clauses.append(where_clause)
            
            # Combine where clauses
            if where_clauses:
                if tag_filters:
                    query += " AND "
                else:
                    query += " WHERE "
                query += " AND ".join(where_clauses)
            
            # Add ordering
            query += " ORDER BY m.date DESC"
            
            # Execute query
            results = conn.execute(query, params).fetchall()
            
            meetings = []
            for result in results:
                # Get tags for each meeting
                tag_rows = conn.execute("""
                    SELECT t.name FROM tags t
                    JOIN meeting_tags mt ON mt.tag_id = t.id
                    WHERE mt.meeting_id = ?
                """, (result['id'],)).fetchall()
                tags = {row[0] for row in tag_rows}
                
                # Parse transcript
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
                    summary=result['summary'],
                    tags=tags
                ))
            return meetings

    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Meeting tags will be deleted automatically due to CASCADE
                conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
                return True
        except Exception as e:
            print(f"Error deleting meeting: {e}")
            return False

    def get_all_tags(self) -> List[str]:
        """Get list of all tags"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM tags ORDER BY name")
            return [row[0] for row in cursor.fetchall()]

    def add_meeting_tag(self, meeting_id: str, tag: str) -> bool:
        """Add a tag to a meeting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert or get tag ID
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                    (tag,)
                )
                if cursor.rowcount == 0:
                    cursor = conn.execute(
                        "SELECT id FROM tags WHERE name = ?",
                        (tag,)
                    )
                tag_id = cursor.lastrowid or cursor.fetchone()[0]
                
                # Link tag to meeting
                conn.execute("""
                    INSERT OR IGNORE INTO meeting_tags (meeting_id, tag_id)
                    VALUES (?, ?)
                """, (meeting_id, tag_id))
                return True
        except Exception as e:
            print(f"Error adding tag: {e}")
            return False

    def remove_meeting_tag(self, meeting_id: str, tag: str) -> bool:
        """Remove a tag from a meeting and clean up unused tags"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove tag from meeting
                conn.execute("""
                    DELETE FROM meeting_tags
                    WHERE meeting_id = ? AND tag_id IN (
                        SELECT id FROM tags WHERE name = ?
                    )
                """, (meeting_id, tag))
                
                # Delete tag if it's no longer used by any meeting
                conn.execute("""
                    DELETE FROM tags
                    WHERE name = ? AND NOT EXISTS (
                        SELECT 1 FROM meeting_tags
                        WHERE tag_id = tags.id
                    )
                """, (tag,))
                
                return True
        except Exception as e:
            print(f"Error removing tag: {e}")
            return False
