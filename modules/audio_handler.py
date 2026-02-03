import pyaudio
import numpy as np
import logging
import time
import math
from collections import deque

class AudioHandler:
    """
    Manages audio input/output streams using PyAudio.
    Handles continuous recording and silence detection.
    """
    
    def __init__(self, config: dict):
        """
        Initialize PyAudio and configure audio parameters.
        
        Args:
            config: Audio configuration from config.yaml
        """
        self.logger = logging.getLogger("AudioHandler")
        self.config = config
        self.pa = pyaudio.PyAudio()
        self.stream = None
        
        # Audio parameters
        self.sample_rate = config.get("sample_rate", 16000)
        self.chunk_size = config.get("chunk_size", 512)
        self.format = pyaudio.paInt16
        self.channels = config.get("channels", 1)
        self.input_device = config.get("input_device_index", 3)
        
        # Validate device
        try:
            info = self.pa.get_device_info_by_index(self.input_device)
            self.logger.info(f"Using input device: {info['name']}")
        except IOError:
            self.logger.error(f"No audio input device found at index {self.input_device}")
            # Potentially scan for devices or raise
            
    def start_input_stream(self):
        """Start audio input stream from USB microphone"""
        try:
            self.stream = self.pa.open(
                rate=self.sample_rate,
                channels=self.channels,
                format=self.format,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=self.input_device
            )
            self.logger.info("Audio input stream started")
        except Exception as e:
            self.logger.error(f"Failed to start input stream: {e}")
            raise

    def read_frame(self) -> bytes:
        """
        Read one audio frame (512 samples).
        
        Returns:
            bytes: Raw audio data (1024 bytes for 512 int16 samples)
        """
        if self.stream is None or not self.stream.is_active():
            raise RuntimeError("Stream is not active")
            
        try:
            return self.stream.read(self.chunk_size, exception_on_overflow=False)
        except IOError as e:
            self.logger.warning(f"Audio overflow: {e}")
            return b'\x00' * (self.chunk_size * 2)

    def calculate_rms(self, audio_data: bytes) -> float:
        """
        Calculate RMS (Root Mean Square) for silence detection.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            float: RMS value (higher = louder)
        """
        try:
            # Convert bytes to numpy array of int16
            samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            # Calculate RMS
            rms = np.sqrt(np.mean(samples**2))
            return rms
        except Exception:
            return 0.0

    def record_until_silence(self, max_duration: float = 5.0, silence_threshold: int = 500, silence_duration: float = 1.5) -> bytes:
        """
        Record audio until silence or max duration.
        
        Args:
            max_duration: Maximum recording time in seconds
            silence_threshold: RMS threshold for silence
            silence_duration: Seconds of silence before auto-stop
            
        Returns:
            bytes: Complete audio recording as WAV bytes
        """
        self.logger.info("Started recording...")
        frames = []
        silent_frames = 0
        total_frames = 0
        
        max_frames = int(max_duration * self.sample_rate / self.chunk_size)
        silence_frame_limit = int(silence_duration * self.sample_rate / self.chunk_size)
        
        try:
            while total_frames < max_frames:
                data = self.read_frame()
                frames.append(data)
                total_frames += 1
                
                rms = self.calculate_rms(data)
                
                if rms < silence_threshold:
                    silent_frames += 1
                else:
                    silent_frames = 0
                    
                if silent_frames >= silence_frame_limit:
                    self.logger.info("Silence detected, stopping recording")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error during recording: {e}")
            
        self.logger.info(f"Recording finished. captured {len(frames)} frames")
        return b''.join(frames)
    
    def cleanup(self):
        """Terminate PyAudio"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pa.terminate()
        self.logger.info("Audio resources released")
