# Verification Steps

I am downloading the Whisper model now. It might take a minute.
Meanwhile, please prepare for verification.

## 1. Configure API Key
Open `config.yaml` and update the `access_key` under `wake_word` with your Picovoice Porcupine key.

## 2. Run Tests
Run these commands in your terminal:

```bash
# Activate Environment
source venv/bin/activate

# Test 1: Wake Word
python3 tests/test_wake_word.py
# -> Expected: "WAKE WORD DETECTED" when you say "computer"

# Test 2: Audio Recording
python3 tests/test_audio.py
# -> Expected: Plays back your voice

# Test 3: Transcription
python3 tests/test_stt.py
# -> Expected: Prints what you said in Test 2
```

## 3. Launch App
If all tests pass:
```bash
python3 main.py
```

Let me know if you encounter any errors!
