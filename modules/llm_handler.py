import requests
import json
import logging

class LLMHandler:
    """
    Handles communication with the Groq LLM API.
    Expects JSON responses with 'response' and 'mood' keys.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the LLM handler.
        
        Args:
            config: LLM configuration from config.yaml
        """
        self.logger = logging.getLogger("LLMHandler")
        self.config = config
        self.api_key = config.get("api_key")
        self.model = config.get("model", "llama-3.1-70b-versatile")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.max_history = config.get("max_history", 5)
        self.history = []
        
    def generate_response(self, text: str) -> dict:
        """
        Send text to Groq and get a structured response.
        
        Args:
            text: Transcribed user speech
            
        Returns:
            dict: {"response": str, "mood": str}
        """
        if not text:
            return {"response": "", "mood": "neutral"}
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": self.config.get("system_prompt", "")}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": text})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 150)
        }
        
        try:
            self.logger.info(f"Sending request to Groq ({self.model})...")
            response = requests.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            llm_output = result["choices"][0]["message"]["content"].strip()
            
            # Attempt to parse JSON
            try:
                parsed = json.loads(llm_output)
                response_text = parsed.get("response", "I didn't quite get that.")
                mood = parsed.get("mood", "neutral")
                
                # Basic validation
                valid_moods = ["happy", "neutral", "sad", "excited", "thinking", "curious", "angry", "proud"]
                if mood not in valid_moods:
                    mood = "neutral"
                    
                self.logger.info(f"LLM Response: {response_text} [MOOD: {mood}]")
                self.history.append({"role": "user", "content": text})
                self.history.append({"role": "assistant", "content": response_text})
                # Trim to last N exchanges (2 messages per exchange)
                if len(self.history) > self.max_history * 2:
                    self.history = self.history[-(self.max_history * 2):]
                return {"response": response_text, "mood": mood}
                
            except json.JSONDecodeError:
                self.logger.warning(f"LLM didn't return valid JSON. Raw output: {llm_output}")
                return {"response": llm_output, "mood": "neutral"}
                
        except Exception as e:
            if 'response' in locals() and hasattr(response, 'text'):
                self.logger.error(f"LLM request failed: {e} - Response: {response.text}")
            else:
                self.logger.error(f"LLM request failed: {e}")
            return {"response": "Sorry, I had trouble connecting to my brain.", "mood": "sad"}
