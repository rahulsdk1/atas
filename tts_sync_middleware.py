# tts_sync_middleware.py
"""
Middleware to ensure agent's TTS (voice output) always matches the accurate reply text (e.g., from web search).
No changes required to original code. Import and use hooks as needed.
"""

class TTSSyncMiddleware:
    def __init__(self):
        pass

    def get_tts_text(self, reply_text, web_result=None, persona='female'):
        """
        If web_result is provided, use it for TTS. Otherwise, use reply_text.
        Always ensure reply text uses female persona.
        """
        tts_text = web_result if web_result else reply_text
        # Ensure female persona in TTS output
        if persona == 'female' and 'female' not in tts_text.lower():
            tts_text = f"(female persona) {tts_text}"
        return tts_text

# Usage:
# tts_sync = TTSSyncMiddleware()
# tts_text = tts_sync.get_tts_text(agent_reply, web_result)
# Pass tts_text to your TTS plugin for speaking

# Strict patch: Always use final reply and correct language for TTS
from language_middleware import translate_text

class StrictTTSSyncMiddleware:
    """
    Ensures TTS output always matches the final reply (including web result) and uses the correct language.
    Does not touch original code.
    """
    def __init__(self):
        pass

    def get_strict_tts_text(self, reply_text, web_result=None, persona='female', tts_lang='en'):
        # Use web_result if present, else reply_text
        tts_text = web_result if web_result else reply_text
        # Translate TTS text to correct language
        tts_text = translate_text(tts_text, tts_lang)
        # Ensure female persona
        if persona == 'female' and 'female' not in tts_text.lower():
            tts_text = f"(female persona) {tts_text}"
        return tts_text

# Usage:
# strict_tts = StrictTTSSyncMiddleware()
# tts_text = strict_tts.get_strict_tts_text(final_reply, web_result, persona, tts_lang)
# Pass tts_text and tts_lang to your TTS plugin for speaking
