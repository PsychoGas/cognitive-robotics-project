# TTS Implementation Plan

## Goal

Add text-to-speech to Cog so the LLM response is spoken aloud through the USB speaker connected to the Raspberry Pi 4 (4GB RAM). Must run locally, be fast enough for real-time, and sound decent — not robotic.

---

## Research Summary

### Constraints

- Raspberry Pi 4, 4GB RAM, ARM Cortex-A72 (quad-core)
- Faster-Whisper (tiny.en) already loaded — uses ~200-300MB RAM
- PyAudio already in use for mic input
- Piper is off the table (dependency hell)
- Must be fully offline (no cloud API calls for synthesis)

### Options Evaluated

| Engine | Voice Quality | RTF on RPi4 (2 threads) | RAM | Model Size | Status |
|--------|--------------|-------------------------|-----|------------|--------|
| **sherpa-onnx (VITS)** | Natural (neural) | ~0.48 | ~180MB | 38-75MB | Active, stable |
| **Picovoice Orca** | Natural (neural) | Unknown (no published RPi4 RTF) | Unknown | Proprietary | Active, needs API key |
| **KittenTTS** | Natural (neural) | ~0.69 on Colab CPU (slower on RPi4) | <1GB | 23MB | Developer preview (v0.1) |
| **eSpeak-NG** | Robotic | Instant (~0) | <5MB | <5MB | Stable, mature |
| **MeloTTS** | Natural | Not benchmarked on RPi4 | Unknown | Unknown | Only officially supports RPi5+ |
| **Coqui TTS** | Excellent | >6.0 (unusable) | GBs | GBs | Defunct company, community-only |
| **Mimic 3** | Decent (neural) | ~1.0 | Moderate | Moderate | Maintained but stale |

RTF = Real-Time Factor. Below 1.0 means faster than real-time (good). Above 1.0 means the user waits.

### Detailed RTF benchmarks for sherpa-onnx VITS on RPi4 Model B

From official documentation (tested on RPi4 Rev 1.5):

| Model | 1 thread | 2 threads | 3 threads | 4 threads |
|-------|----------|-----------|-----------|-----------|
| vits-piper-en_US-glados | 0.812 | 0.480 | 0.391 | 0.349 |
| vits-piper-en_US-libritts_r-medium | 0.790 | 0.493 | 0.392 | 0.357 |
| en_US-lessac-medium | 0.774 | 0.482 | 0.390 | 0.357 |
| ljspeech | 6.057 | 3.517 | 2.535 | 2.206 |
| VCTK (multi-speaker) | 6.079 | 3.483 | 2.537 | 2.226 |

The piper-compatible VITS models (top 3) all achieve RTF ~0.35-0.49 with 2+ threads — comfortably faster than real-time. The ljspeech/VCTK models are much heavier and unsuitable.

---

## Recommendation: sherpa-onnx with VITS-piper models

### Why sherpa-onnx

1. **Proven RPi4 performance**: Official benchmarks show RTF 0.35-0.49 — a 1-2 sentence response (~3s of audio) synthesizes in ~1-1.5s
2. **Simple install**: `pip install sherpa-onnx` has pre-built ARM64 (aarch64) wheels on PyPI — no compilation, no dependency hell
3. **ONNX runtime**: The project already depends on `onnxruntime` via faster-whisper, so the heavy dependency is already present
4. **Runs piper ONNX models**: Gets piper-quality voices via ONNX format without piper's native dependency chain
5. **Fully offline**: No API keys, no internet, no license validation
6. **~180MB RAM**: Fits within the 4GB budget alongside Whisper
7. **Active project**: Regular releases, 12+ programming language bindings, extensive docs

### Voice model choice

**`vits-piper-en_US-lessac-medium`** — best balance of quality and speed:
- RTF 0.48 with 2 threads on RPi4
- Single English female voice, natural sounding
- ~38MB model file (medium quality tier)
- 22050 Hz output sample rate

Alternative: `vits-piper-en_US-glados` if a different voice character is preferred (similar performance).

### Fallback: eSpeak-NG

Keep eSpeak-NG as a zero-resource fallback if sherpa-onnx fails to initialize (model missing, OOM, etc.). It's a single `apt install espeak-ng` and produces instant output, just robotic. This matches the project's existing pattern of graceful degradation (like display being optional).

---

## Implementation Design

### New module: `modules/tts_handler.py`

```
TTSHandler
├── __init__(config: dict)          # Load sherpa-onnx VITS model
├── synthesize(text: str) -> bytes  # Text → raw PCM audio (int16)
├── speak(text: str)                # Synthesize + play through speaker
├── cleanup()                       # Release resources
```

#### Initialization

- Load the VITS ONNX model from a local path (configured in config.yaml)
- Configure thread count (default: 2 — leaves 2 cores for Whisper/main loop)
- Fall back to eSpeak-NG subprocess if model fails to load
- Output format: 16-bit PCM, mono, at the model's native sample rate (22050 Hz)

#### Synthesis

- Accept text string from LLM response
- Call `sherpa_onnx.OfflineTts.generate()` to produce audio samples
- Return raw audio as numpy array or bytes

#### Playback

- Use PyAudio output stream (device index from `config.yaml` `output_device_index`)
- Open a temporary output stream at the model's sample rate (22050 Hz)
- Write synthesized PCM data in chunks
- Close stream after playback completes
- Playback runs on the main thread (blocking is fine — it replaces the current `time.sleep(mood_duration)`)

#### Fallback path (eSpeak-NG)

- If sherpa-onnx init fails, log a warning and fall back to eSpeak-NG
- eSpeak-NG synthesis via subprocess: `espeak-ng -v en -w /tmp/tts_out.wav "text"` then play via PyAudio or `aplay`
- Same `speak()` interface, caller doesn't need to know which engine is active

### Model file management

- Store the downloaded model in `models/tts/` (gitignored)
- Provide a download script or document the one-time wget command
- Model URL: `https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2`

---

## Config Changes

Add to `config.yaml`:

```yaml
# Text-to-Speech configuration
tts:
  engine: "sherpa-onnx"              # "sherpa-onnx" or "espeak-ng"
  model_path: "models/tts/vits-piper-en_US-lessac-medium"
  num_threads: 2                     # CPU threads for inference (2 = half of RPi4 cores)
  speed: 1.0                         # Speech speed multiplier
  # espeak-ng fallback settings
  espeak_voice: "en"                 # eSpeak-NG voice for fallback
```

---

## State Machine Changes (main.py)

### Current PROCESSING state flow:
```
transcribe → LLM → show mood animation → sleep(mood_duration) → IDLE
```

### New PROCESSING state flow:
```
transcribe → LLM → show mood animation → tts.speak(response) → IDLE
```

The key change: **replace `time.sleep(mood_duration)` with `tts.speak(response_text)`**. The mood animation plays on the OLED in its background thread while the TTS audio plays on the main thread. When speech finishes, transition back to IDLE. This naturally synchronizes animation duration with speech duration instead of using a fixed 10-second sleep.

### Specific changes in main.py:

1. **Import**: Add `from modules.tts_handler import TTSHandler`
2. **Init**: Add `tts = TTSHandler(config.get("tts", {}))` alongside other modules
3. **PROCESSING state**: Replace `time.sleep(config["display"].get("mood_duration", 10.0))` with `tts.speak(response_text)`
4. **Cleanup**: Add `if 'tts' in locals(): tts.cleanup()` in the finally block
5. **Graceful degradation**: If TTS init fails, fall back to the existing `time.sleep()` behavior (print response to console only)

---

## Audio Playback Detail

The project already configures `output_device_index: 3` in config.yaml but never uses it. The TTSHandler will:

1. Open a PyAudio output stream at 22050 Hz (model native rate), mono, int16
2. Write the synthesized audio in chunks (4096 samples per write)
3. Close the stream when done

This avoids shelling out to `aplay` and keeps everything in-process via the existing PyAudio dependency. The output device index comes from `config.yaml` audio section.

Alternatively, the `play_audio()` method could live on `AudioHandler` since it already owns the PyAudio instance. TTSHandler would call `audio_handler.play_audio(samples, sample_rate)`. This avoids creating a second PyAudio instance.

### Recommended approach: Add `play_audio()` to AudioHandler

```python
def play_audio(self, audio_data: np.ndarray, sample_rate: int):
    """Play synthesized audio through the output device."""
    output_device = self.config.get("output_device_index", 3)
    stream = self.pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        output=True,
        output_device_index=output_device
    )
    # Convert float32 [-1, 1] to int16 if needed
    if audio_data.dtype == np.float32:
        audio_data = (audio_data * 32767).astype(np.int16)
    stream.write(audio_data.tobytes())
    stream.stop_stream()
    stream.close()
```

Then TTSHandler receives a reference to AudioHandler and calls `self.audio.play_audio(samples, 22050)`.

---

## Memory Budget

| Component | Estimated RAM |
|-----------|--------------|
| OS + Python runtime | ~400MB |
| Faster-Whisper (tiny.en, int8) | ~200-300MB |
| sherpa-onnx VITS (medium) | ~180MB |
| PyAudio + buffers | ~50MB |
| Main app + other modules | ~50MB |
| **Total** | **~900MB-1GB** |

Leaves ~3GB free on a 4GB RPi4. Comfortable headroom.

Note: Whisper model is loaded once at startup and stays resident. The TTS model is also loaded once. They coexist in memory without issues.

---

## Implementation Steps

### Step 1: Download and verify model

```bash
mkdir -p models/tts
cd models/tts
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2
tar xjf vits-piper-en_US-lessac-medium.tar.bz2
rm vits-piper-en_US-lessac-medium.tar.bz2
```

Add `models/` to `.gitignore`.

### Step 2: Install dependencies

```bash
pip install sherpa-onnx
sudo apt install espeak-ng    # fallback + required by piper VITS models for phonemization
```

Add `sherpa-onnx` to `requirements.txt`.

Note: sherpa-onnx piper models use espeak-ng data files for text normalization/phonemization. The `espeak-ng-data` directory ships with the model tarball — no system espeak-ng install is strictly required for sherpa-onnx, but installing the system package ensures the fallback TTS path works too.

### Step 3: Create `modules/tts_handler.py`

Implement TTSHandler class with:
- `__init__`: Load sherpa-onnx model, configure threads, set up fallback
- `synthesize(text) -> np.ndarray`: Run inference, return audio samples
- `speak(text)`: Synthesize then play via AudioHandler
- `cleanup()`: Release model resources

### Step 4: Add `play_audio()` to `modules/audio_handler.py`

Add a method to play raw PCM audio through the configured output device using the existing PyAudio instance.

### Step 5: Update `config.yaml`

Add `tts:` section with engine, model path, thread count, speed.

### Step 6: Integrate into `main.py`

- Import and initialize TTSHandler
- Pass AudioHandler reference to TTSHandler
- Replace `time.sleep(mood_duration)` with `tts.speak(response_text)` in PROCESSING state
- Add cleanup in finally block

### Step 7: Update `.gitignore`

Add `models/` directory.

### Step 8: Test

- Verify model loads without errors
- Test synthesis of a short sentence, check output WAV
- Test full pipeline: wake word → record → transcribe → LLM → TTS playback
- Monitor RAM usage with `htop` during full pipeline run
- Test fallback: rename model dir, verify eSpeak-NG fallback activates

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| sherpa-onnx pip install fails on RPi4 | Pre-built aarch64 wheels exist on PyPI; verified v1.12.23 has `manylinux2014_aarch64` builds |
| Model too slow with 2 threads | Bump to 3 threads (RTF drops to ~0.39); or use a `-low` quality model variant instead of `-medium` |
| OOM with Whisper + TTS both loaded | tiny.en + VITS medium should fit in ~500MB combined; monitor with htop and downgrade to `-low` model if needed |
| Audio output crackling/stuttering | Use a buffer size that matches the output device; ensure sample rate matches (22050 Hz) |
| espeak-ng-data not found by model | The model tarball includes its own `espeak-ng-data/` directory; config points to it |

---

## File Changes Summary

| File | Change |
|------|--------|
| `modules/tts_handler.py` | **New** — TTSHandler class |
| `modules/audio_handler.py` | Add `play_audio()` method |
| `main.py` | Import TTSHandler, init, wire into PROCESSING state, cleanup |
| `config.yaml` | Add `tts:` section |
| `requirements.txt` | Add `sherpa-onnx` |
| `.gitignore` | Add `models/` |

---

## Sources

- [sherpa-onnx GitHub](https://github.com/k2-fsa/sherpa-onnx) — project repo with RPi4 support
- [sherpa-onnx VITS benchmarks](https://k2-fsa.github.io/sherpa/onnx/tts/pretrained_models/vits.html) — official RTF numbers on RPi4
- [sherpa-onnx PyPI](https://pypi.org/project/sherpa-onnx/) — pre-built ARM64 wheels
- [KittenTTS GitHub](https://github.com/KittenML/KittenTTS) — evaluated but slower than sherpa-onnx piper models
- [KittenTTS CPU speed comparison](https://github.com/KittenML/KittenTTS/issues/40) — RTF benchmarks vs Piper/Matcha/Kokoro
- [Picovoice Orca](https://picovoice.ai/blog/text-to-speech-on-raspberry-pi/) — evaluated but requires API key
- [Adafruit KittenTTS guide](https://learn.adafruit.com/speech-synthesis-on-raspberry-pi-with-kittentts/overview) — RPi4/5 testing
- [Circuit Digest TTS comparison](https://circuitdigest.com/microcontroller-projects/best-text-to-speech-tts-converter-for-raspberry-pi-espeak-festival-google-tts-pico-and-pyttsx3) — eSpeak/Festival/Pico comparison
