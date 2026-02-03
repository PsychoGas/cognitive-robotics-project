import sys
import os
import time
import wave
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.audio_handler import AudioHandler

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    print("Testing Audio Recording...")
    try:
        config = load_config()
        handler = AudioHandler(config["audio"])
        handler.start_input_stream()
        
        print("Recording 3 seconds of audio...")
        # Override recording params for test
        audio_data = handler.record_until_silence(max_duration=3.0, silence_duration=3.0)
        
        filename = "test_recording.wav"
        print(f"Saving to {filename}...")
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(config["audio"]["channels"])
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(config["audio"]["sample_rate"])
            wf.writeframes(audio_data)
            
        print(f"Saved {len(audio_data)} bytes. Playing back...")
        os.system(f"aplay {filename}")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        if 'handler' in locals():
            handler.cleanup()

if __name__ == "__main__":
    main()
