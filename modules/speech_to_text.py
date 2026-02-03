from faster_whisper import WhisperModel
import numpy as np
import logging
import os

class SpeechToText:
    """
    Transcribes audio to text using Faster-Whisper.
    Runs locally on CPU with int8 quantization for speed.
    """
    
    def __init__(self, config: dict):
        """
        Initialize Faster-Whisper model.
        
        Args:
            config: STT configuration from config.yaml
        """
        self.logger = logging.getLogger("SpeechToText")
        self.config = config
        
        model_size = config.get("model", "tiny.en")
        device = config.get("device", "cpu")
        compute_type = config.get("compute_type", "int8")
        
        self.logger.info(f"Loading Whisper model: {model_size} on {device} ({compute_type})")
        
        try:
            self.model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type,
                download_root=os.path.join(os.path.expanduser("~"), ".cache/huggingface/hub")
            )
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_data: Raw audio bytes (WAV format / PCM)
            sample_rate: Audio sample rate (default 16000)
            
        Returns:
            str: Transcribed text
        """
        if not audio_data:
            return ""
            
        try:
            # Convert audio bytes to numpy float32 array normalized to [-1, 1]
            # faster-whisper expects float32
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            segments, info = self.model.transcribe(
                audio_np, 
                beam_size=self.config.get("beam_size", 5),
                language=self.config.get("language", "en"),
                vad_filter=True
            )
            
            # segments is a generator, so we need to iterate to get text
            text_segments = [segment.text for segment in segments]
            full_text = " ".join(text_segments).strip()
            
            self.logger.info(f"Transcription: '{full_text}' (prob: {info.language_probability:.2f})")
            return full_text
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return ""

    def cleanup(self):
        """Clean up model resources"""
        # Faster-whisper doesn't have explicit cleanup, but we can delete the object
        if hasattr(self, 'model'):
            del self.model
            self.logger.info("STT resources released")
