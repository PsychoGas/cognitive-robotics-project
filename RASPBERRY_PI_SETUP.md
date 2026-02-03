# Raspberry Pi Setup Guide 🍓

Follow these steps to set up your Voice Assistant on the Raspberry Pi after pulling the repository.

## 1. System Dependencies
Install the required system libraries for audio and video processing.

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev libatlas-base-dev
# Additional libraries for Faster-Whisper/Av
sudo apt install -y pkg-config libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev
```

## 2. Python Environment
Set up the virtual environment and install Python packages.

```bash
# Navigate to the project folder
cd cog

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## 3. Configuration
You need to add your Access Key to the configuration file.

1.  Open `config.yaml`:
    ```bash
    nano config.yaml
    ```
2.  Find `wake_word` -> `access_key`.
3.  Replace `"YOUR_PORCUPINE_ACCESS_KEY"` with your actual key from [Picovoice Console](https://console.picovoice.ai/).
4.  Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

## 4. Hardware Verification
Ensure your hardware is correctly detected.

```bash
# Check Microphone (Input)
arecord -l
# Make sure your USB mic index matches 'input_device_index' in config.yaml

# Check Speakers (Output)
aplay -l
# Make sure your speaker index matches 'output_device_index' in config.yaml
```

## 5. Download Model
Pre-download the Whisper model to avoid delays on first run.

```bash
python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en', device='cpu', compute_type='int8')"
```

## 6. Run It! 🚀

**Test Individual Modules:**
```bash
python3 tests/test_wake_word.py  # Say "computer"
python3 tests/test_audio.py      # Records 3s and plays back
python3 tests/test_stt.py        # Transcribes the recording
```

**Run Main Assistant:**
```bash
python3 main.py
```

## Troubleshooting
- **Microphone Error**: If `pyaudio` fails to find the device, check `arecord -l` and update the index in `config.yaml`.
- **Permission Denied**: If you can't access the microphone, you might need to add your user to the audio group: `sudo usermod -a -G audio $USER` then reboot.
- **Slow Transcription**: The Pi 4 CPU is limited. Ensure `tiny.en` is used.
