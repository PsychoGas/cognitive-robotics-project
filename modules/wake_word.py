import pvporcupine
import struct
import logging

class WakeWordDetector:
    """
    Handles wake word detection using Picovoice Porcupine.
    Processes audio frames and returns True when wake word is detected.
    """
    
    def __init__(self, access_key: str, keyword: str, sensitivity: float = 0.5):
        """
        Initialize Porcupine wake word detector.
        
        Args:
            access_key: Picovoice access key from console.picovoice.ai
            keyword: Wake word (e.g., "computer", "jarvis")
            sensitivity: Detection sensitivity 0.0-1.0
        """
        self.logger = logging.getLogger("WakeWord")
        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=[keyword],
                sensitivities=[sensitivity]
            )
            self.logger.info(f"Porcupine initialized with keyword '{keyword}'")
        except Exception as e:
            self.logger.error(f"Failed to initialize Porcupine: {e}")
            raise

    def process_frame(self, audio_frame: bytes) -> bool:
        """
        Process a single audio frame (512 samples at 16kHz).
        
        Args:
            audio_frame: Raw audio bytes (512 samples * 2 bytes = 1024 bytes)
            
        Returns:
            True if wake word detected, False otherwise
        """
        try:
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, audio_frame)
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                self.logger.info("Wake word detected")
                return True
            return False
        except struct.error as e:
            self.logger.error(f"Error unpacking audio frame: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return False

    def cleanup(self):
        """Release Porcupine resources"""
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()
            self.logger.info("Porcupine resources released")
