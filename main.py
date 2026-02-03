import yaml
import time
import logging
import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.wake_word import WakeWordDetector
from modules.audio_handler import AudioHandler
from modules.speech_to_text import SpeechToText
from modules.llm_handler import LLMHandler
from modules.display import DisplayController
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/voice_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Main")

def resolve_env_vars(config):
    r"""Recursively replace ${VAR} with environment variables."""
    if isinstance(config, dict):
        for k, v in config.items():
            config[k] = resolve_env_vars(v)
    elif isinstance(config, list):
        return [resolve_env_vars(v) for v in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.getenv(env_var, config)
    return config

def load_config(path="config.yaml"):
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            return resolve_env_vars(config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

def main():
    logger.info("Initializing Voice Assistant...")
    
    # Load configuration
    config = load_config()
    
    # Initialize modules with error handling
    try:
        try:
            display = DisplayController(config.get("display", {}))
        except Exception as e:
            logger.warning(f"Display not initialized (likely not connected): {e}")
            display = None
            
        audio = AudioHandler(config.get("audio", {}))
        
        # Check for placeholder key
        access_key = config["wake_word"]["access_key"]
        if access_key == "YOUR_PORCUPINE_ACCESS_KEY":
            logger.warning("Please set your Porcupine Access Key in config.yaml!")
            print("\nERROR: Porcupine Access Key not set in config.yaml\n")
            return

        wake_word = WakeWordDetector(
            access_key,
            config["wake_word"]["keyword"],
            config["wake_word"]["sensitivity"]
        )
        
        stt = SpeechToText(config.get("stt", {}))
        llm = LLMHandler(config.get("llm", {}))
        
    except Exception as e:
        logger.critical(f"Initialization failed: {e}")
        return

    # Start audio stream
    try:
        audio.start_input_stream()
    except Exception as e:
        logger.critical(f"Failed to start audio: {e}")
        return
    
    # Initial state
    state = "IDLE"
    display.show_idle_face()
    print("\nVoice Assistant Ready! Say 'computer' to activate.\n")
    
    try:
        while True:
            if state == "IDLE":
                # Read audio frame
                frame = audio.read_frame()
                
                # Check for wake word
                if wake_word.process_frame(frame):
                    logger.info("Wake word detected!")
                    print("\n[WAKE WORD DETECTED]")
                    state = "WAKE_DETECTED"
            
            elif state == "WAKE_DETECTED":
                # Show listening animation
                if display: display.show_listening_face()
                print("Listening...")
                state = "LISTENING"
            
            elif state == "LISTENING":
                # Record until silence or timeout
                audio_buffer = audio.record_until_silence(
                    max_duration=config["recording"]["max_duration"],
                    silence_threshold=config["recording"]["silence_threshold"],
                    silence_duration=config["recording"]["silence_duration"]
                )
                print("Recording complete.")
                state = "PROCESSING"
            
            elif state == "PROCESSING":
                # Show thinking animation
                if display: display.show_thinking_face()
                print("Processing speech...")
                
                # Transcribe
                text = stt.transcribe(audio_buffer)
                
                if text:
                    # Feed to LLM
                    llm_data = llm.generate_response(text)
                    response_text = llm_data["response"]
                    mood = llm_data["mood"]
                    
                    # Show mood-based talking face
                    if display: display.show_mood_face(mood)
                    
                    print(f"\n[AI RESPONSE]")
                    print(f">>> {response_text}")
                    print(f"[MOOD: {mood.upper()}]\n")
                    
                    # Show text on top of animation (or instead of)
                    # Note: show_text in our newer display.py handles the overlay/pause logic
                    if display: display.show_text(response_text)
                else:
                    print("\n>>> (No speech detected)\n")
                    if display: display.show_text("???")
                
                # Return to idle
                time.sleep(1)
                state = "IDLE"
                if display: display.show_idle_face()
                print("Ready for next command.")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        if 'audio' in locals(): audio.cleanup()
        if 'wake_word' in locals(): wake_word.cleanup()
        if 'display' in locals() and display: 
            display.clear()
            display.cleanup()
        if 'stt' in locals(): stt.cleanup()
        print("Goodbye!")

if __name__ == "__main__":
    main()
