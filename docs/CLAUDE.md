# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cog is a voice assistant with an animated face display, built for Raspberry Pi 4. It chains: wake word detection (Porcupine) → speech-to-text (Faster-Whisper) → LLM response (Groq API with Llama 3.3 70B) → mood-based animated face on a 128x64 SSD1306 OLED display.

## Commands

### Run the assistant
```
python main.py
```

### Run tests (integration scripts, require hardware)
```
python tests/test_audio.py       # Records 3s audio, saves test_recording.wav, plays back
python tests/test_stt.py         # Transcribes test_recording.wav (run test_audio.py first)
python tests/test_wake_word.py   # Real-time wake word detection
```

### Install dependencies
```
sudo apt install -y portaudio19-dev pkg-config libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev
pip install -r requirements.txt
```

### Pre-process GIF animations
```
python modules/animations/threshold.py
```

No lint, format, or pytest tooling is configured.

## Architecture

### State Machine (main.py)

`IDLE` → wake word "computer" detected → `WAKE_DETECTED` → show listening face → `LISTENING` → record until silence/timeout → `PROCESSING` → transcribe → LLM → show mood animation for 10s → back to `IDLE`

### Module Pipeline

```
AudioHandler (PyAudio, USB mic)
    → WakeWordDetector (Porcupine, 512-sample frames)
    → SpeechToText (Faster-Whisper, tiny.en model, CPU int8)
    → LLMHandler (Groq API, returns JSON with "response" + "mood")
    → DisplayController (OLED via I2C, threaded GIF playback)
```

Each module receives its config section from `config.yaml` and must implement a `cleanup()` method called in `main.py`'s finally block.

### Configuration

- `config.yaml`: All runtime settings (audio, wake word, STT, LLM, display, recording)
- `.env`: API keys (`PORCUPINE_ACCESS_KEY`, `GROQ_API_KEY`) — resolved via `${VAR}` syntax in config.yaml
- `main.py` resolves env vars recursively before passing config to modules

### LLM Response Format

The LLM is prompted to return raw JSON: `{"response": "text", "mood": "emotion"}`. Valid moods: happy, neutral, sad, excited, thinking, curious. Fallback returns neutral mood if parsing fails.

### Display

- Animations are pre-processed GIFs in `modules/animations/clean/` (black & white threshold)
- Playback runs in a background thread with a stop event
- Display gracefully degrades — if OLED not connected, `display` is set to `None` and all display calls are guarded with `if display:`

## Code Conventions

- Python 3.12, 4-space indentation, no configured linter
- Classes: `CamelCase`, functions/variables: `snake_case`
- Imports: stdlib → third-party → local (`from modules...`)
- Logging: one logger per module via `logging.getLogger("<Name>")`, configured only in `main.py`
- Error handling: `try/except` around hardware I/O, return safe defaults for recoverable errors, `raise` for fatal init failures
- Type hints are light and optional
- Tests are standalone scripts (not pytest), require physical hardware (mic, OLED, speakers)
