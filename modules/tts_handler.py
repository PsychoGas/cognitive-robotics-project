import logging
import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np

try:
    import sherpa_onnx
except Exception:  # pragma: no cover - runtime import handling
    sherpa_onnx = None


class TTSHandler:
    """
    Text-to-Speech handler using sherpa-onnx VITS models.
    Falls back to espeak-ng if sherpa-onnx isn't available.
    """

    def __init__(self, config: dict, audio_handler):
        self.logger = logging.getLogger("TTSHandler")
        self.config = config
        self.audio = audio_handler
        self.engine = config.get("engine", "sherpa-onnx")
        self.available = False
        self.tts = None
        self.sample_rate = 22050
        self.espeak_path = None

        if self.engine == "sherpa-onnx":
            if sherpa_onnx is None:
                self.logger.warning("sherpa-onnx not available, falling back to espeak-ng")
                self.engine = "espeak-ng"
            else:
                try:
                    self._init_sherpa()
                except Exception as e:
                    self.logger.warning(f"Failed to initialize sherpa-onnx: {e}")
                    self.engine = "espeak-ng"

        if self.engine == "espeak-ng":
            self.espeak_path = shutil.which("espeak-ng")
            if not self.espeak_path:
                self.logger.error("espeak-ng not found; TTS disabled")
                self.available = False
            else:
                self.available = True

    def _init_sherpa(self):
        model_path = self.config.get("model_path", "")
        if not model_path:
            raise ValueError("TTS model_path is not set")

        model_dir = os.path.abspath(model_path)
        tokens_file = os.path.join(model_dir, "tokens.txt")
        data_dir = os.path.join(model_dir, "espeak-ng-data")

        # Find the .onnx model file (name varies per voice)
        onnx_files = [f for f in os.listdir(model_dir) if f.endswith(".onnx")]
        if not onnx_files:
            raise FileNotFoundError(f"No .onnx model file found in {model_dir}")
        model_file = os.path.join(model_dir, onnx_files[0])

        # Lexicon is optional — piper models use espeak-ng-data instead
        lexicon_file = os.path.join(model_dir, "lexicon.txt")
        lexicon = lexicon_file if os.path.exists(lexicon_file) else ""

        missing = [p for p in [model_file, tokens_file, data_dir] if not os.path.exists(p)]
        if missing:
            raise FileNotFoundError(f"Missing TTS model files: {', '.join(missing)}")

        vits = sherpa_onnx.OfflineTtsVitsModelConfig(
            model=model_file,
            lexicon=lexicon,
            tokens=tokens_file,
            data_dir=data_dir,
        )

        model_config = sherpa_onnx.OfflineTtsModelConfig(
            vits=vits,
            num_threads=self.config.get("num_threads", 2),
            debug=False,
        )

        tts_config = sherpa_onnx.OfflineTtsConfig(model=model_config)
        self.tts = sherpa_onnx.OfflineTts(tts_config)
        self.sample_rate = getattr(self.tts, "sample_rate", 22050)
        self.available = True
        self.logger.info("sherpa-onnx TTS initialized")

    def synthesize(self, text: str) -> np.ndarray | None:
        if not text or not self.available or self.engine != "sherpa-onnx":
            return None

        try:
            speed = self.config.get("speed", 1.0)
            audio = self.tts.generate(text, sid=0, speed=speed)
            samples = audio.samples
            if samples is None or len(samples) == 0:
                return None
            # sherpa-onnx returns float samples in [-1, 1] as a list
            samples = np.array(samples, dtype=np.float32)
            samples = np.clip(samples, -1.0, 1.0)
            return (samples * 32767).astype(np.int16)
        except Exception as e:
            self.logger.error(f"TTS synthesis failed: {e}")
            return None

    def _speak_espeak(self, text: str) -> bool:
        if not self.espeak_path or not self.audio:
            return False

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name

            voice = self.config.get("espeak_voice", "en")
            subprocess.run(
                [self.espeak_path, "-v", voice, "-w", temp_path, text],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            with wave.open(temp_path, "rb") as wav_file:
                if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2:
                    self.logger.error("Unsupported WAV format from espeak-ng")
                    return False
                audio_bytes = wav_file.readframes(wav_file.getnframes())
                self.audio.play_audio(audio_bytes, wav_file.getframerate(), channels=1)
            return True
        except Exception as e:
            self.logger.error(f"espeak-ng TTS failed: {e}")
            return False
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def speak(self, text: str) -> bool:
        if not text or not self.available or not self.audio:
            return False

        if self.engine == "sherpa-onnx":
            samples = self.synthesize(text)
            if samples is None:
                return False
            self.audio.play_audio(samples, self.sample_rate, channels=1)
            return True

        if self.engine == "espeak-ng":
            return self._speak_espeak(text)

        return False

    def cleanup(self):
        if self.tts is not None:
            self.tts = None
        self.logger.info("TTS resources released")
