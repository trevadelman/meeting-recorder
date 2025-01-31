import sounddevice as sd
import time
from datetime import datetime
import numpy as np
import wave
from pathlib import Path
import torch
import torchaudio
import logging
import warnings
# Configure logging
logging.getLogger('speechbrain').setLevel(logging.WARNING)
warnings.filterwarnings('ignore', category=UserWarning, module='speechbrain')
warnings.filterwarnings('ignore', category=FutureWarning, module='speechbrain')

from speechbrain.pretrained import EncoderClassifier
from sklearn.cluster import AgglomerativeClustering
from faster_whisper import WhisperModel
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class TranscriptSegment:
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: float

class AudioProcessor:
    def __init__(self, sample_rate=44100, input_device=None):
        self.sample_rate = sample_rate
        self.input_device = input_device
        self.spk_model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="models/pretrained/spkrec-ecapa"
        )
        self.frames = []
        self.stream = None
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
        from utils import setup_python_path
        setup_python_path()
        from config.config import BASE_DIR
        self.audio_dir = BASE_DIR / "data/recordings"
        self.audio_dir.mkdir(exist_ok=True)
        

    def start_recording(self) -> bool:
        """Start recording audio"""
        try:
            # Create input stream with callback
            self.frames = []
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,
                device=self.input_device,
                latency='low',
                callback=self._audio_callback
            )
            self.stream.start()
            return True
        except Exception as e:
            self.frames = []
            self.stream = None
            raise RuntimeError(f"Failed to start recording: {str(e)}")

    def _audio_callback(self, indata, frames, time, status):
        """Callback to collect audio data"""
        if status:
            print(f'Audio callback status: {status}')
        if len(indata) > 0:
            self.frames.append(indata.copy())

    def stop_recording(self, _) -> str:
        """Stop recording and save audio file"""
        try:
            if not self.stream:
                raise RuntimeError("No active recording stream")

            # Stop and close stream
            self.stream.stop()
            self.stream.close()
            self.stream = None

            # Combine all frames
            if not self.frames:
                raise RuntimeError("No audio data recorded")
            recording = np.concatenate(self.frames)
            self.frames = []

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.audio_dir / f"meeting_{timestamp}.wav"

            # Save to WAV file
            with wave.open(str(filename), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(recording.tobytes())

            return str(filename)
        except Exception as e:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            self.frames = []
            raise RuntimeError(f"Failed to stop recording: {str(e)}")

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
