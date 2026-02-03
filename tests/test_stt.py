import sys
import os
import time
import wave
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.speech_to_text import SpeechToText

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    print("Testing Speech-to-Text...")
    
    # Check for audio file
    filename = "test_recording.wav"
    if not os.path.exists(filename):
        print(f"Error: {filename} not found. Run test_audio.py first.")
        return

    try:
        config = load_config()
        stt = SpeechToText(config["stt"])
        
        print("Transcribing...")
        with open(filename, "rb") as f:
            # Skip header for raw processing if needed, but whisper can handle wav usually?
            # Our module expects raw bytes if called via transcribe(), but let's check.
            # Faster-whisper module implementation:
            # audio_np = np.frombuffer(audio_data, dtype=np.int16)
            # This implies raw PCM data, not WAV file bytes (which has header)
            
            # Read via wave module to be safe
            wf = wave.open(filename, "rb")
            audio_data = wf.readframes(wf.getnframes())
            wf.close()
            
        start = time.time()
        text = stt.transcribe(audio_data)
        duration = time.time() - start
        
        print(f"Transcription ({duration:.2f}s): '{text}'")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        if 'stt' in locals():
            stt.cleanup()

if __name__ == "__main__":
    main()
