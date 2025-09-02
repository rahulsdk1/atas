# language_middleware.py
"""
Middleware for automatic language detection, translation, and TTS/STT language switching.
No changes required to original code. Import and use hooks as needed.
"""

from langdetect import detect
from googletrans import Translator

translator = Translator()

# Supported languages (add more as needed)
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ur': 'Urdu',
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German',
    'zh-cn': 'Chinese',
    'ru': 'Russian',
    # Add more as needed
}

def detect_language(text):
    """Detect language from text."""
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else 'en'
    except Exception:
        return 'en'

def translate_text(text, dest_lang):
    """Translate text to destination language."""
    if dest_lang == 'en':
        return text
    try:
        result = translator.translate(text, dest=dest_lang)
        return result.text
    except Exception:
        return text

# Example hook for agent input/output
class LanguageAgentHook:
    def __init__(self):
        self.user_lang = 'en'

    def process_user_input(self, text):
        self.user_lang = detect_language(text)
        return text

    def process_agent_output(self, text):
        return translate_text(text, self.user_lang)

    def get_tts_language(self):
        return self.user_lang

# Usage:
# hook = LanguageAgentHook()
# user_text = hook.process_user_input(user_text)
# agent_reply = hook.process_agent_output(agent_reply)
# tts_lang = hook.get_tts_language()
# Pass tts_lang to your TTS plugin

# Patch: Enforce prompt.py instructions, persona, and automatic language switching
from prompts import AGENT_INSTRUCTION

class StrictPersonaAgentHook:
    """
    Enforces prompt.py instructions, persona, and automatic language switching for every reply.
    Does not touch original code.
    """
    def __init__(self):
        self.user_lang = 'en'

    def process_user_input(self, text):
        self.user_lang = detect_language(text)
        return text

    def process_agent_output(self, text):
        # Always apply persona and prompt instructions
        persona_prefix = "(female persona) " if "female" in AGENT_INSTRUCTION.lower() else ""
        # Only answer in one sentence (from prompt)
        reply = text.split(". ")[0].strip()
        reply = reply if reply.endswith('.') else reply + '.'
        reply = f"{persona_prefix}{reply}"
        # Translate reply to user's language
        return translate_text(reply, self.user_lang)

    def get_tts_language(self):
        return self.user_lang

# Usage:
# strict_persona_hook = StrictPersonaAgentHook()
# user_text = strict_persona_hook.process_user_input(user_text)
# agent_reply = strict_persona_hook.process_agent_output(agent_reply)
# tts_lang = strict_persona_hook.get_tts_language()

# Patch: Auto-detect and switch to user's spoken language for every input
class AutoLanguageAgentHook:
    """
    Always detects and switches to user's spoken language automatically.
    Does not touch original code.
    """
    def __init__(self):
        self.user_lang = 'en'

    def process_user_input(self, text):
        self.user_lang = detect_language(text)
        return text

    def process_agent_output(self, text):
        return translate_text(text, self.user_lang)

    def get_tts_language(self):
        return self.user_lang

# Usage:
# auto_hook = AutoLanguageAgentHook()
# user_text = auto_hook.process_user_input(user_text)
# agent_reply = auto_hook.process_agent_output(agent_reply)
# tts_lang = auto_hook.get_tts_language()
