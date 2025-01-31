from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to access core modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.core import MeetingRecorder
from src.core.audio import TranscriptSegment
from config.config import BASE_DIR, EXPORT_FORMATS, ERROR_MESSAGES

# Initialize FastAPI app
app = FastAPI(
    title="Meeting Recorder API",
    description="API for recording, transcribing, and managing meetings with speaker diarization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recorder
recorder = MeetingRecorder()

# Pydantic models
class Meeting(BaseModel):
    id: str
    title: str
    date: datetime
    duration: float
    audio_path: str
    transcript: List[TranscriptSegment]
    summary: Optional[str] = None
    tags: Optional[List[str]] = None

    class Config:
        arbitrary_types_allowed = True

class DeviceInfo(BaseModel):
    id: str
    name: str
    default: bool

class RecordingStatus(BaseModel):
    status: str
    progress: Optional[str] = None
    meeting_id: Optional[str] = None

class TagOperation(BaseModel):
    tag: str

# API Routes
@app.get("/api/devices", response_model=List[DeviceInfo])
async def list_devices():
    """Get list of available input devices"""
    try:
        devices = recorder.audio_processor.list_input_devices()
        return [
            DeviceInfo(
                id=str(device['id']),
                name=device['name'],
                default=device['default']
            )
            for device in devices
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/devices/select")
async def select_device(device: DeviceInfo):
    """Select input device for recording"""
    try:
        if recorder.audio_processor.set_input_device(int(device.id)):
            return {"message": "Device selected successfully"}
        raise HTTPException(status_code=400, detail="Failed to select device")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/meetings/start")
async def start_recording(title: Optional[str] = None):
    """Start a new recording"""
    try:
        recorder.start_recording(title)
        return {"message": "Recording started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/meetings/stop")
async def stop_recording():
    """Stop the current recording"""
    try:
        audio_path = recorder.stop_recording()
        return {"message": "Recording stopped", "audio_path": audio_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meetings/status", response_model=RecordingStatus)
async def recording_status():
    """Get current recording status"""
    try:
        status = "recording" if recorder.current_recording else "idle"
        return RecordingStatus(
            status=status,
            progress=None,
            meeting_id=recorder.current_recording.id if recorder.current_recording else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/meetings/upload")
async def upload_recording(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    title: Optional[str] = None,
    duration: float = 0
):
    """Handle uploaded recording"""
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Process in background
        background_tasks.add_task(
            recorder.record_meeting,
            duration=duration,
            title=title,
            audio_data=audio_data
        )
        
        return {"message": "Recording uploaded for processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meetings", response_model=List[Meeting])
async def list_meetings(
    tags: Optional[List[str]] = None,
    title_search: Optional[str] = None,
    transcript_search: Optional[str] = None
):
    """Get all meetings with optional filters"""
    try:
        meetings = recorder.db.get_all_meetings(
            tag_filters=tags,
            title_search=title_search,
            transcript_search=transcript_search
        )
        return meetings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meetings/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str):
    """Get meeting details"""
    meeting = recorder.db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

@app.get("/api/meetings/{meeting_id}/audio")
async def get_audio(meeting_id: str):
    """Stream meeting audio file"""
    meeting = recorder.db.get_meeting(meeting_id)
    if not meeting or not Path(meeting.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        meeting.audio_path,
        media_type="audio/wav",
        filename=f"meeting_{meeting_id}.wav"
    )

@app.get("/api/meetings/{meeting_id}/export")
async def export_meeting(meeting_id: str, format: str = "txt"):
    if format not in EXPORT_FORMATS:
        raise HTTPException(status_code=400, detail="Invalid export format")
    """Export meeting in specified format"""
    try:
        filepath = recorder.export_meeting(meeting_id, format)
        return FileResponse(
            filepath,
            filename=Path(filepath).name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def cleanup_orphaned_recordings():
    """Clean up any recording files that don't have associated database entries"""
    try:
        # Get all meeting IDs from database
        all_meetings = recorder.db.get_all_meetings()
        valid_audio_paths = {meeting.audio_path for meeting in all_meetings}
        
        # Check recordings directory
        recordings_dir = BASE_DIR / "data/recordings"
        for recording_file in recordings_dir.glob("meeting_*.wav"):
            if str(recording_file) not in valid_audio_paths:
                try:
                    recording_file.unlink()
                except Exception as e:
                    print(f"Error deleting orphaned recording {recording_file}: {e}")
    except Exception as e:
        print(f"Error during orphaned recordings cleanup: {e}")

@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Delete a meeting and its associated files"""
    meeting = recorder.db.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    try:
        # Delete audio file
        audio_path = Path(meeting.audio_path)
        if audio_path.exists():
            audio_path.unlink()
        
        # Delete any exports
        export_pattern = f"meeting_*_{meeting_id[:8]}.*"
        export_dir = BASE_DIR / "data/exports"
        for export_file in export_dir.glob(export_pattern):
            export_file.unlink()
        
        # Delete from database
        recorder.db.delete_meeting(meeting_id)
        
        # Clean up any orphaned recordings
        await cleanup_orphaned_recordings()
        
        return {"message": "Meeting deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tags")
async def get_tags():
    """Get all available tags"""
    try:
        tags = recorder.db.get_all_tags()
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/meetings/{meeting_id}/tags")
async def add_tag(meeting_id: str, tag_op: TagOperation):
    """Add a tag to a meeting"""
    if not recorder.db.add_meeting_tag(meeting_id, tag_op.tag):
        raise HTTPException(status_code=500, detail="Failed to add tag")
    return {"message": "Tag added successfully"}

@app.delete("/api/meetings/{meeting_id}/tags/{tag}")
async def remove_tag(meeting_id: str, tag: str):
    """Remove a tag from a meeting"""
    if not recorder.db.remove_meeting_tag(meeting_id, tag):
        raise HTTPException(status_code=500, detail="Failed to remove tag")
    return {"message": "Tag removed successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
