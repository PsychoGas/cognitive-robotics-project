# AGENTS.md

This file documents how to build, test, and follow the coding conventions
for this repository. It is intended for agentic coding tools.

## Quick context
- Primary language: Python 3.12
- Entry point: `main.py`
- Modules live in `modules/`
- Manual/integration tests live in `tests/`
- Configuration is `config.yaml`
- Hardware-dependent features: microphone, wake word, OLED display

## Build, lint, and test commands
There is no formal build system or lint configuration detected.
Use direct Python invocations for running the app and tests.

### Run the app
- `python main.py`

### Tests (manual/integration style)
These are scripts, not pytest tests. They require hardware/audio.

- `python tests/test_audio.py`
- `python tests/test_stt.py`
- `python tests/test_wake_word.py`

### Single test
Run one test script directly, for example:
- `python tests/test_audio.py`

### Lint/format
No lint/format tooling is configured in the repo.
If you add formatting, keep changes minimal and consistent with existing style.

## System dependencies
The project needs system libraries for audio and ffmpeg-related deps.
From `setup_instructions.md` and `ACTION_REQUIRED.md`:

- `sudo apt update`
- `sudo apt install -y portaudio19-dev pkg-config libavformat-dev \
  libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev \
  libswresample-dev libavfilter-dev`

### TTS dependencies
Text-to-speech uses sherpa-onnx with VITS models and an espeak-ng fallback.

- `pip install sherpa-onnx`
- `sudo apt install -y espeak-ng`

Model download (store under `models/tts/`, gitignored):

- `wget https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2`
- `tar xjf vits-piper-en_US-lessac-medium.tar.bz2`

## Code style guidelines
Follow existing conventions in `main.py` and `modules/`.

### Imports
- Standard library imports first.
- Third-party imports next.
- Local imports last (e.g., `from modules...`).
- Avoid wildcard imports.
- Keep imports explicit and readable.

### Formatting
- 4-space indentation.
- Use blank lines between logical sections and top-level definitions.
- Keep lines reasonably short; wrap long calls with parentheses.
- Use single quotes in logging format strings; both quote styles appear.

### Naming
- Classes use `CamelCase` (e.g., `AudioHandler`).
- Functions and variables use `snake_case`.
- Constants are rarely used; if introduced, prefer `UPPER_SNAKE_CASE`.

### Types and hints
- Type hints are light and optional (e.g., `config: dict`).
- Add type hints where they improve clarity, but do not over-annotate.
- Keep type hints consistent with runtime usage (bytes vs str, etc.).

### Docstrings
- Classes and public methods include short docstrings.
- Keep docstrings concise and aligned with actual behavior.

### Error handling
- Use `try/except` around hardware initialization and I/O.
- Log exceptions with context and return safe defaults.
- Prefer returning empty values over raising for recoverable errors
  (see `SpeechToText.transcribe`).
- Use `raise` when initialization cannot proceed.

### Logging
- Use `logging.getLogger("<Name>")` per module/class.
- Log at `info` for normal flow, `warning` for recoverable issues,
  `error` for failures, and `critical` for fatal startup failures.
- `main.py` configures a file + stream handler; avoid reconfiguring
  logging in modules.

### Resource management
- Provide `cleanup()` methods and call them in `finally` blocks.
- Handle hardware resources defensively (audio, OLED, wake word engine).
- Avoid leaving audio streams open or porcupine instances alive.

## Configuration conventions
- Configuration lives in `config.yaml` and is loaded with `yaml.safe_load`.
- Access config with `.get()` where values are optional.
- Use explicit keys for required values (e.g., wake word access key).
- Keep config defaults in code aligned with `config.yaml` values.

## Tests and fixtures
- Test scripts are integration-style and may read/write files in repo root
  (e.g., `test_recording.wav`).
- Tests may use system tools (`aplay`) and require audio devices.
- Running tests on headless or CI hosts may fail without hardware.

## Project structure
- `main.py`: orchestration and state machine for the assistant.
- `modules/audio_handler.py`: audio I/O and silence detection.
- `modules/speech_to_text.py`: faster-whisper integration.
- `modules/wake_word.py`: Porcupine wake word detection.
- `modules/display.py`: OLED display rendering.
- `tests/`: manual test scripts.

## External dependencies (runtime)
Inferred from imports:
- `pyaudio`, `numpy`, `pvporcupine`, `faster_whisper`, `Pillow`,
  `luma.oled`, `yaml`.

## Behavioral expectations
- Expect hardware-specific failures; handle them without crashing.
- Keep startup robust; fail fast if access key is missing.
- Avoid long blocking operations in the main loop unless intended.

## Cursor and Copilot rules
- `.cursor/rules/`: not found in this repo.
- `.cursorrules`: not found in this repo.
- `.github/copilot-instructions.md`: not found in this repo.

## Notes for agentic contributors
- Do not assume pytest is configured; treat `tests/` as scripts.
- Avoid mass reformatting; keep diffs focused.
- Preserve user-local settings in `config.yaml` unless explicitly asked.
- If you add new dependencies, document install steps in a README or
  an update to this file.
