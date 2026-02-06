# Cog Main Doc

This project is a small, friendly voice assistant built for a Raspberry Pi. It listens for a wake word, records what you say, turns speech into text, asks an online LLM for a response, and shows a little animated face on a tiny OLED screen while it talks back.

## The big idea (plain English)
- You say “computer” to wake it up.
- It listens, records your sentence, and stops when you go quiet.
- Your speech is turned into text on the Pi.
- The text goes to Groq’s LLM, which sends back a short reply plus a “mood”.
- The OLED face animates to match that mood while the response is spoken.

## What runs the show
The main loop lives in `main.py` and works like a simple state machine:
- **IDLE**: waiting for the wake word
- **WAKE_DETECTED**: switches the face to “listening”
- **LISTENING**: records audio until silence or timeout
- **PROCESSING**: transcribes speech, asks the LLM, plays the response, then returns to idle

## The main pieces (modules)
- `modules/audio_handler.py`: opens the microphone, reads audio frames, and detects silence.
- `modules/wake_word.py`: listens for the Porcupine wake word.
- `modules/speech_to_text.py`: turns audio into text with Faster-Whisper.
- `modules/llm_handler.py`: sends text to Groq and parses the JSON response.
- `modules/display.py`: plays animated GIF faces on the OLED.
- `modules/tts_handler.py`: speaks the response (sherpa-onnx first, espeak-ng fallback).

## Where the “mood” comes from
The LLM is told to reply in JSON like this:

```json
{
  "response": "your reply here",
  "mood": "happy"
}
```

The mood chooses which face animation to play. Valid moods include: happy, neutral, sad, excited, thinking, curious, angry, proud.

## Files you’ll care about
- `config.yaml`: all settings for audio, wake word, LLM, display, recording, and TTS.
- `.env` (create from `.env.example`): API keys for Porcupine and Groq.
- `modules/animations/clean/`: the pre-processed GIFs that the OLED plays.
- `tests/`: simple hardware tests you run by hand.

## Setup (short version)
Install system dependencies and Python packages, then add your keys.

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev libopenblas-dev
sudo apt install -y pkg-config libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then create a `.env` file:

```
PORCUPINE_ACCESS_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

## Run it
```bash
python main.py
```

You should see “Voice Assistant Ready! Say ‘computer’ to activate.”

## Quick tests (manual)
These are small scripts to check hardware. They are not pytest tests.

```bash
python tests/test_wake_word.py   # say “computer”
python tests/test_audio.py       # records 3s, plays it back
python tests/test_stt.py         # transcribes that recording
```

## Hardware notes
- A USB microphone and speakers are expected.
- The OLED is optional. If it’s not plugged in, the app still runs; it just skips the display.
- If audio devices don’t show up, use `arecord -l` / `aplay -l` and update `input_device_index` and `output_device_index` in `config.yaml`.

## TTS (talking back)
- The default TTS is **sherpa-onnx** with a VITS model.
- If sherpa-onnx isn’t available, it falls back to **espeak-ng**.
- You can switch or tweak this in `config.yaml` under `tts`.

## Where to look if something feels off
- Check `logs/voice_assistant.log` for errors.
- If wake word never triggers, confirm the Porcupine key in `.env` and the mic index.
- If the LLM doesn’t respond, confirm the Groq key and network access.

That’s it. This project is meant to be simple and hands-on — start it up, talk to it, and tweak the config until it feels right.
