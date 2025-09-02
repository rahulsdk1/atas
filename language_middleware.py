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
    """Detect language from text with improved reliability."""
    if not text or not text.strip():
        return 'en'

    text = text.strip()

    # For very short texts, use heuristics
    if len(text.split()) < 3:
        # Check for common non-English characters
        if any(char in text for char in 'अआइईउऊएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'):
            return 'hi'  # Hindi
        elif any(char in text for char in 'অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহ'):
            return 'bn'  # Bengali
        elif any(char in text for char in 'அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநபமயரலவழளறன'):
            return 'ta'  # Tamil
        elif any(char in text for char in 'àâäéèêëïîôöùûüÿç'):
            return 'fr'  # French
        elif any(char in text for char in 'áéíóúüñ'):
            return 'es'  # Spanish
        elif any(char in text for char in 'äöüß'):
            return 'de'  # German
        elif any(char in text for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'):
            return 'ru'  # Russian
        elif any(char in text for char in '的一是不了人我在有他这为之大来以个中上们到说国和地也子时道出而要于得可你年生自会好用家学'):
            return 'zh-cn'  # Chinese

    # Use langdetect for longer texts
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else 'en'
    except Exception as e:
        # Fallback: check for common words in different languages
        text_lower = text.lower()

        # Hindi common words
        hindi_words = ['hai', 'hai', 'ka', 'ki', 'ke', 'se', 'mein', 'par', 'aur', 'ye', 'wo', 'kya', 'kaun', 'kahan', 'kab']
        if any(word in text_lower for word in hindi_words):
            return 'hi'

        # Bengali common words
        bengali_words = ['ami', 'tumi', 'se', 'ke', 'ei', 'o', 'ki', 'kare', 'kano', 'kothay']
        if any(word in text_lower for word in bengali_words):
            return 'bn'

        # Tamil common words
        tamil_words = ['nan', 'ne', 'avan', 'aval', 'ithu', 'athu', 'enna', 'epdi', 'engal']
        if any(word in text_lower for word in tamil_words):
            return 'ta'

        # Default to English
        return 'en'

def translate_text(text, dest_lang):
    """Translate text to destination language with improved reliability."""
    if not text or not text.strip():
        return text

    if dest_lang == 'en':
        return text

    # Clean the text
    text = text.strip()

    # Skip translation for very short texts that might not translate well
    if len(text.split()) < 2 and not any(char in text for char in '.,!?;:'):
        return text

    try:
        # Add timeout and retry logic
        result = translator.translate(text, dest=dest_lang, timeout=10)

        # Validate translation result
        if result and result.text and result.text.strip():
            translated = result.text.strip()

            # Check if translation is actually different (not just the same text)
            if translated.lower() != text.lower():
                return translated
            else:
                # Translation returned same text, might be an error
                return text
        else:
            return text

    except Exception as e:
        # Log the error for debugging
        import logging
        logging.warning(f"Translation error for '{text[:50]}...' to {dest_lang}: {e}")
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
    Maintains language consistency across multiple interactions.
    Does not touch original code.
    """
    def __init__(self):
        self.user_lang = 'en'
        self.confidence_threshold = 0.6  # Minimum confidence for language switching
        self.language_history = []  # Track language detection history
        self.max_history = 5  # Keep last 5 language detections

    def process_user_input(self, text):
        # Detect language with improved reliability
        detected_lang = detect_language(text)

        # Add to history for consistency checking
        self.language_history.append(detected_lang)
        if len(self.language_history) > self.max_history:
            self.language_history.pop(0)

        # Use majority voting for consistency (if we have enough history)
        if len(self.language_history) >= 3:
            from collections import Counter
            lang_counts = Counter(self.language_history[-3:])  # Last 3 detections
            most_common_lang = lang_counts.most_common(1)[0][0]

            # Only switch if the new detection is consistent with recent history
            # or if it's a clear language change (different from current)
            if most_common_lang == detected_lang or detected_lang != self.user_lang:
                self.user_lang = detected_lang
        else:
            # For initial interactions, be more responsive to language changes
            self.user_lang = detected_lang

        return text

    def process_agent_output(self, text):
        # Always apply persona and prompt instructions
        persona_prefix = "(female persona) " if "female" in AGENT_INSTRUCTION.lower() else ""

        # Keep the full text but ensure it ends with a period if needed
        reply = text.strip()
        if not reply.endswith('.') and not reply.endswith('!') and not reply.endswith('?'):
            reply = reply + '.'

        # Apply persona prefix
        reply = f"{persona_prefix}{reply}"

        # Always translate reply to user's detected language
        translated_reply = translate_text(reply, self.user_lang)

        # Ensure translation worked (fallback to original if translation failed)
        if not translated_reply or translated_reply == reply:
            # If translation failed, at least keep the persona
            return reply

        return translated_reply

    def get_tts_language(self):
        return self.user_lang

    def get_language_stats(self):
        """Get language detection statistics for debugging"""
        if not self.language_history:
            return {'current': self.user_lang, 'history': []}

        from collections import Counter
        lang_counts = Counter(self.language_history)
        return {
            'current': self.user_lang,
            'history': self.language_history,
            'most_common': lang_counts.most_common(1)[0][0] if lang_counts else 'en',
            'total_detections': len(self.language_history)
        }

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
