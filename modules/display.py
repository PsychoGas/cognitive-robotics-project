from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import logging
import time
import os
import threading

class DisplayController:
    """
    Controls the OLED display to show animated faces and text.
    Uses GIF files from modules/animations/
    """
    
    def __init__(self, config: dict):
        """
        Initialize OLED display via I²C and setup animation thread.
        """
        self.logger = logging.getLogger("Display")
        self.config = config
        self.animation_dir = os.path.join(os.path.dirname(__file__), "animations", "clean")
        
        # Animation thread control
        self.current_animation = None
        self.stop_event = threading.Event()
        self.animation_thread = None
        self.lock = threading.Lock()
        
        try:
            # I2C configuration
            port = config.get("i2c_bus", 1)
            address = config.get("i2c_address", 0x3C)
            
            serial = i2c(port=port, address=address)
            self.device = ssd1306(serial, width=config.get("width", 128), height=config.get("height", 64))
            self.device.contrast(config.get("contrast", 255))
            
            self.logger.info(f"OLED display initialized at {port}:{hex(address)}")
            self.clear()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            self.device = None

    def _animation_loop(self, gif_path):
        """Background thread to play GIF animation"""
        try:
            with Image.open(gif_path) as img:
                # Pre-process frames for the display size
                frames = []
                for frame in ImageSequence.Iterator(img):
                    # Convert to grayscale, resize/crop to fit display, convert to 1-bit
                    # We preserve aspect ratio and center it
                    f = frame.convert("RGBA").convert("L")
                    # Scale to fit height
                    scale = self.device.height / f.height
                    new_size = (int(f.width * scale), self.device.height)
                    f = f.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Create blank black image and center the frame
                    canvas_img = Image.new("1", (self.device.width, self.device.height))
                    left = (self.device.width - f.width) // 2
                    canvas_img.paste(f.convert("1"), (left, 0))
                    
                    duration = frame.info.get('duration', 100) / 1000.0
                    frames.append((canvas_img, duration))

                while not self.stop_event.is_set():
                    for frame_img, duration in frames:
                        if self.stop_event.is_set():
                            break
                        with self.lock:
                            if self.device:
                                self.device.display(frame_img)
                        time.sleep(duration)
        except Exception as e:
            self.logger.error(f"Animation loop error: {e}")

    def play_animation(self, name: str):
        """Start playing a specific GIF animation from the animations folder"""
        if not self.device:
            self.logger.warning(f"Display not available, skipping animation: {name}")
            return

        gif_path = os.path.join(self.animation_dir, f"{name}.gif")
        if not os.path.exists(gif_path):
            self.logger.error(f"Animation file not found: {gif_path}")
            # Fallback to neutral if mood-based one missing
            if name not in ["idle", "listening", "thinking"]:
                self.play_animation("neutral")
            return

        if self.current_animation == name:
            return

        self.logger.info(f"Starting animation: {name}")
        self.stop_animation()
        
        self.current_animation = name
        self.stop_event.clear()
        self.animation_thread = threading.Thread(target=self._animation_loop, args=(gif_path,), daemon=True)
        self.animation_thread.start()

    def stop_animation(self):
        """Stop current animation thread"""
        self.stop_event.set()
        if self.animation_thread:
            self.animation_thread.join(timeout=0.5)
        self.current_animation = None

    def show_idle_face(self):
        self.play_animation("idle")

    def show_listening_face(self):
        self.play_animation("listening")

    def show_thinking_face(self):
        self.play_animation("thinking")

    def show_mood_face(self, mood: str):
        """Map LLM mood to a specific animation"""
        valid_moods = ["happy", "neutral", "sad", "excited", "thinking", "curious", "angry", "proud"]
        mood = mood.lower() if mood else "neutral"
        if mood not in valid_moods:
            mood = "neutral"
        self.play_animation(mood)

    def show_text(self, text: str, duration: float = 2.0):
        """Temporarily stop animation to show text, then resume"""
        if not self.device:
            return
        
        prev_anim = self.current_animation
        self.stop_animation()
        
        try:
            with canvas(self.device) as draw:
                font = ImageFont.load_default()
                # Simple multi-line wrap for 128x64
                lines = []
                words = text.split()
                line = ""
                for word in words:
                    if len(line + word) < 20: # Approx chars per line
                        line += word + " "
                    else:
                        lines.append(line)
                        line = word + " "
                lines.append(line)
                
                for i, l in enumerate(lines[:5]): # Max 5 lines
                    draw.text((0, i*12), l, font=font, fill="white")
            
            if duration > 0:
                time.sleep(duration)
        except Exception as e:
            self.logger.error(f"Error displaying text: {e}")
        
        if prev_anim:
            self.play_animation(prev_anim)

    def clear(self):
        self.stop_animation()
        if self.device:
            self.device.clear()

    def cleanup(self):
        self.clear()
        self.logger.info("Display resources released")
