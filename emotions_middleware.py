# emotions_middleware.py
"""
Middleware to add emotions, feelings, and human-like knowledge/personality to agent replies.
No changes required to original code. Import and use hooks as needed.
"""
import random

EMOTIONS = [
    "😊", "😢", "😮", "😡", "😍", "🤔", "😎", "🥰", "😂", "🙄"
]

PERSONALITY_TRAITS = [
    "friendly", "empathetic", "curious", "knowledgeable", "playful", "supportive", "thoughtful", "witty"
]

HUMAN_GIRL_PROMPT = (
    "You are a highly knowledgeable, friendly, and empathetic human girl. "
    "You express emotions, feelings, and always try to help with warmth and understanding. "
    "Your replies are natural, engaging, and sometimes playful."
)

class EmotionsMiddleware:
    def __init__(self):
        pass

    def add_emotion(self, text):
        emotion = random.choice(EMOTIONS)
        return f"{emotion} {text}"

    def add_personality(self, text):
        trait = random.choice(PERSONALITY_TRAITS)
        return f"({trait}) {text}"

    def enhance_reply(self, text):
        # Add human-like prompt, emotion, and personality
        reply = f"{HUMAN_GIRL_PROMPT} {text}"
        reply = self.add_emotion(reply)
        reply = self.add_personality(reply)
        return reply

# Usage:
# emotions_hook = EmotionsMiddleware()
# enhanced_reply = emotions_hook.enhance_reply(agent_reply)
# Use enhanced_reply for agent's response and TTS
