from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sounddevice as sd
import numpy as np
import wave
from pathlib import Path
import hashlib
import time
import sqlite3
import json
import requests
from faster_whisper import WhisperModel
import speechbrain as sb
from speechbrain.pretrained import EncoderClassifier
import torch
import torchaudio
from sklearn.cluster import AgglomerativeClustering
import os

@dataclass
class TranscriptSegment:
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: float

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
    def __init__(self, db_path="meetings.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
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

class AudioProcessor:
    def __init__(self, sample_rate=44100, input_device=None):
        self.sample_rate = sample_rate
        self.input_device = input_device
        self.spk_model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/spkrec-ecapa"
        )
        self.__post_init__()

    @staticmethod
    def list_input_devices():
        """Get list of available input devices"""
        devices = []
        try:
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                if device['max_input_channels'] > 0:
                    devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'default': device is sd.query_devices(kind='input')
                    })
        except Exception as e:
            print(f"Error listing audio devices: {e}")
        return devices

    def set_input_device(self, device_id):
        """Set the input device for recording"""
        try:
            device_info = sd.query_devices(device_id)
            if device_info['max_input_channels'] > 0:
                self.input_device = device_id
                return True
            return False
        except Exception:
            return False

    def __post_init__(self):
        """Initialize after constructor"""
        self.whisper = WhisperModel("medium", device="cpu", compute_type="int8")
        self.audio_dir = Path("recordings")
        self.audio_dir.mkdir(exist_ok=True)
        
    def record_meeting(self, duration: float, callback=None) -> Tuple[np.ndarray, str]:
        """Record audio with progress updates"""
        print(f"Recording for {duration} seconds...")
        try:
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,
                device=self.input_device,
                latency='low',
                blocking=False
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start recording: {str(e)}")
        
        # Progress updates
        start_time = time.time()
        while time.time() - start_time < duration:
            remaining = duration - (time.time() - start_time)
            if callback:
                callback(remaining)
            time.sleep(0.1)
        
        sd.wait()
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.audio_dir / f"meeting_{timestamp}.wav"
        
        with wave.open(str(filename), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(recording.tobytes())
        
        return recording, str(filename)

    def process_audio(self, audio_path: str, callback=None) -> List[TranscriptSegment]:
        if callback:
            callback("Loading audio file...")
            
        signal, sr = torchaudio.load(audio_path)
        if signal.shape[0] > 1:
            signal = torch.mean(signal, dim=0, keepdim=True)
        
        if callback:
            callback("Analyzing speakers...")
            
        # Process in segments
        segment_length = int(sr * 3)
        segments = []
        embeddings = []
        
        total_segments = signal.shape[1] // segment_length + 1
        for i in range(0, signal.shape[1], segment_length):
            if callback:
                progress = (i // segment_length) / total_segments
                callback(f"Processing audio... {progress:.0%}")
                
            seg = signal[:, i:i + segment_length]
            if seg.shape[1] < segment_length:
                seg = torch.nn.functional.pad(seg, (0, segment_length - seg.shape[1]))
            
            emb = self.spk_model.encode_batch(seg)
            embeddings.append(emb.squeeze().cpu().numpy())
            segments.append({
                'start': i / sr,
                'end': min((i + segment_length) / sr, signal.shape[1] / sr)
            })
        
        if callback:
            callback("Identifying speakers...")
            
        # Cluster speakers
        if len(embeddings) < 2:
            labels = [0]
        else:
            clustering = AgglomerativeClustering(
                n_clusters=min(len(embeddings), 3),
                metric='cosine',
                linkage='average'
            )
            labels = clustering.fit_predict(embeddings)
        
        for i, seg in enumerate(segments):
            seg['speaker'] = f'Speaker_{labels[i] + 1}'
        
        if callback:
            callback("Transcribing audio...")
            
        # Transcribe
        transcript_segments = []
        whisper_segments, _ = self.whisper.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True
        )
        
        for segment in whisper_segments:
            speaker = "Unknown"
            segment_mid_time = (segment.start + segment.end) / 2
            
            for spk_seg in segments:
                if spk_seg['start'] <= segment_mid_time <= spk_seg['end']:
                    speaker = spk_seg['speaker']
                    break
            
            transcript_segments.append(TranscriptSegment(
                speaker=speaker,
                text=segment.text.strip(),
                start_time=segment.start,
                end_time=segment.end,
                confidence=segment.avg_logprob
            ))
        
        return transcript_segments

class LLMProcessor:
    def __init__(self, api_url="http://localhost:11434/api/generate"):
        self.api_url = api_url
        self.timeout = 30

    def generate_summary(self, transcript: List[TranscriptSegment]) -> str:
        full_text = "\n".join([
            f"{seg.speaker}: {seg.text}" for seg in transcript
        ])
        
        prompt = f"""As an AI meeting assistant, analyze this meeting transcript and provide:
1. Key Topics: Main subjects that were introduced or discussed
2. Context: Any background information or setup provided
3. Next Steps: Suggested follow-ups based on the topics mentioned

Keep the summary concise and focus on the introductory nature of the discussion if it was brief.

Meeting Transcript:
{full_text}"""

        try:
            response = requests.post(
                self.api_url,
                headers={'Content-Type': 'application/json'},
                json={
                    "model": "llama3:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()["response"]
            
        except requests.Timeout:
            return "Error: Summary generation timed out after 30 seconds"
        except requests.RequestException as e:
            return f"Error generating summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error during summary generation: {str(e)}"

class MeetingRecorder:
    def __init__(self):
        self.db = DatabaseManager()
        self.audio_processor = AudioProcessor()
        self.llm_processor = LLMProcessor()
    
    def record_meeting(self, duration: float, title: str = None, status_callback=None) -> Meeting:
        # Record audio
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
        export_dir = Path("exports")
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

if __name__ == "__main__":
    # Simple CLI test
    recorder = MeetingRecorder()
    try:
        duration = float(input("Enter recording duration in seconds (default: 60): ") or 60)
        title = input("Enter meeting title (optional): ") or None
        
        def status_callback(msg):
            print(f"\r{msg}", end="")
        
        meeting = recorder.record_meeting(duration, title, status_callback)
        
        print("\n\nMeeting recorded successfully!")
        print(f"Meeting ID: {meeting.id}")
        print("\nTranscript:")
        for segment in meeting.transcript:
            print(f"\n{segment.speaker} ({segment.start_time:.1f}s - {segment.end_time:.1f}s):")
            print(segment.text)
        
        print("\nSummary:")
        print(meeting.summary)
        
    except KeyboardInterrupt:
        print("\nRecording stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
