import sys
import os
import time
import struct
import pyaudio
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.wake_word import WakeWordDetector
from modules.audio_handler import AudioHandler
import yaml

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    print("Testing Wake Word Detection...")
    config = load_config()
    
    # Initialize Audio
    # We use a raw PyAudio stream here to test integration like the main app does
    # or we can use AudioHandler
    
    try:
        # Check Access Key
        if config["wake_word"]["access_key"] == "YOUR_PORCUPINE_ACCESS_KEY":
            print("ERROR: Please set 'access_key' in config.yaml")
            return

        detector = WakeWordDetector(
            config["wake_word"]["access_key"],
            config["wake_word"]["keyword"],
            config["wake_word"]["sensitivity"]
        )
        print(f"Detector initialized for keyword: {config['wake_word']['keyword']}")
        
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=config["audio"]["sample_rate"],
            channels=config["audio"]["channels"],
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=config["audio"]["chunk_size"],
            input_device_index=config["audio"]["input_device_index"]
        )
        print("Audio stream started. Say the wake word!")
        
        try:
            while True:
                pcm = audio_stream.read(config["audio"]["chunk_size"], exception_on_overflow=False)
                if detector.process_frame(pcm):
                    print(">>> WAKE WORD DETECTED! <<<")
                    # Visual beep
                    time.sleep(0.5) 
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            audio_stream.stop_stream()
            audio_stream.close()
            pa.terminate()
            detector.cleanup()
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
