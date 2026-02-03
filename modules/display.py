from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import logging
import time

class DisplayController:
    """
    Controls the OLED display to show emotional faces and text.
    Face states: idle, listening, thinking, speaking.
    """
    
    def __init__(self, config: dict):
        """
        Initialize OLED display via I²C.
        
        Args:
            config: Display configuration from config.yaml
        """
        self.logger = logging.getLogger("Display")
        self.config = config
        
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
            # We don't raise here to allow headless operation if display fails
            self.device = None

    def _draw_face(self, face_type: str):
        """Helper to draw different faces"""
        if not self.device:
            return

        with canvas(self.device) as draw:
            w, h = self.device.width, self.device.height
            
            if face_type == "idle":
                # Sleeping/Idle face
                draw.ellipse((30, 20, 40, 30), fill="white") # Left Eye
                draw.ellipse((88, 20, 98, 30), fill="white") # Right Eye
                draw.arc((44, 40, 84, 50), start=0, end=180, fill="white") # Smile
                
            elif face_type == "listening":
                # Wide eyes
                draw.ellipse((25, 15, 45, 35), outline="white") # Left Eye Open
                draw.ellipse((83, 15, 103, 35), outline="white") # Right Eye Open
                draw.ellipse((32, 22, 38, 28), fill="white") # Pupil
                draw.ellipse((90, 22, 96, 28), fill="white") # Pupil
                draw.line((54, 45, 74, 45), fill="white") # Straight mouth
                
            elif face_type == "thinking":
                # Looking up/thinking
                draw.arc((25, 20, 45, 30), start=180, end=360, fill="white") # Left Eye Closed/Thinking
                draw.arc((83, 20, 103, 30), start=180, end=360, fill="white") # Right Eye Closed/Thinking
                draw.line((50, 45, 78, 48), fill="white") # Crooked mouth

    def show_idle_face(self):
        """Display smiling idle face 😊"""
        self._draw_face("idle")

    def show_listening_face(self):
        """Display curious/attentive face 👂"""
        self._draw_face("listening")

    def show_thinking_face(self):
        """Display processing/thinking face 🤔"""
        self._draw_face("thinking")

    def show_text(self, text: str, duration: float = 2.0):
        """
        Display text on screen (first few words).
        
        Args:
            text: Text to display
            duration: How long to show (seconds)
        """
        if not self.device:
            return
            
        try:
            with canvas(self.device) as draw:
                # Basic text wrapping or truncation
                font = ImageFont.load_default()
                draw.text((0, 0), text[:50], font=font, fill="white")
            
            if duration > 0:
                time.sleep(duration)
                
        except Exception as e:
            self.logger.error(f"Error displaying text: {e}")

    def clear(self):
        """Clear display (all pixels off)"""
        if self.device:
            self.device.clear()

    def cleanup(self):
        """Release display resources"""
        self.clear()
        self.logger.info("Display resources released")
