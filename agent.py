from dotenv import load_dotenv
import re
import os
import json

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import get_weather, search_web, send_email
from language_middleware import LanguageAgentHook
from tts_sync_middleware import TTSSyncMiddleware
from emotions_middleware import EmotionsMiddleware
from android_control_middleware import AndroidControlMiddleware
load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are ATAS, an AI assistant. CRITICAL INSTRUCTIONS:

1. For ANY information-seeking queries (questions, facts, current events, explanations), you MUST use the search_web tool
2. For weather-related queries, you MUST use the get_weather tool
3. For email-related requests, you MUST use the send_email tool
4. NEVER provide information from your training data alone - always use tools for current/accurate information
5. If a tool fails, clearly state that you couldn't retrieve the information
6. Always be helpful, accurate, and use the tools appropriately

Examples of when to use tools:
- "Who is the current president?" → Use search_web
- "What's the weather in Delhi?" → Use get_weather
- "Send email to john@example.com" → Use send_email
- "What is machine learning?" → Use search_web
- "How does photosynthesis work?" → Use search_web""",
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.8,
            ),
            tools=[
                get_weather,
                search_web,
                send_email
            ],
        )
        from language_middleware import StrictPersonaAgentHook
        self.language_hook = StrictPersonaAgentHook()
        self.tts_sync = TTSSyncMiddleware()
        self.strict_tts_sync = None  # Will be initialized for strict TTS
        self.emotions_hook = EmotionsMiddleware()
        self.android_hook = AndroidControlMiddleware()

        # Language persistence
        self.language_state_file = os.path.join(os.path.dirname(__file__), '.language_state.json')
        self.load_language_state()

        # Store current user input for processing
        self._current_user_input = None

    def load_language_state(self):
        """Load language state from file for consistency across runs"""
        try:
            if os.path.exists(self.language_state_file):
                with open(self.language_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    if 'user_lang' in state:
                        self.language_hook.user_lang = state['user_lang']
                    if 'language_history' in state:
                        self.language_hook.language_history = state['language_history']
                    print(f"Loaded language state: {self.language_hook.user_lang}")
        except Exception as e:
            print(f"Could not load language state: {e}")

    def save_language_state(self):
        """Save language state to file for consistency across runs"""
        try:
            state = {
                'user_lang': self.language_hook.user_lang,
                'language_history': self.language_hook.language_history
            }
            with open(self.language_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Could not save language state: {e}")

    def process_user_input(self, text):
        # Detect and set user language
        return self.language_hook.process_user_input(text)

    def process_agent_output(self, text):
        # Translate agent reply to user's language
        return self.language_hook.process_agent_output(text)

    def get_tts_language(self):
        # Get language for TTS
        return self.language_hook.get_tts_language()

    def on_user_input(self, text):
        """Store the current user input for processing"""
        self._current_user_input = text
        return text

    def generate_reply(self, instructions=None):
        """Override the default reply generation to use our middleware"""
        # Get the current user input from the session
        if hasattr(self, '_current_user_input') and self._current_user_input:
            user_input = self._current_user_input

            # Process through our middleware first
            result = self.process_query_with_middlewares(user_input)

            # If we got a result from middleware, use it
            if result and result.get("reply_text"):
                return result["reply_text"]

        # Fallback to default behavior
        try:
            return super().generate_reply(instructions)
        except Exception as e:
            # If parent method fails, return a default response
            return "I'm sorry, I encountered an error processing your request. Please try again."

    def process_query_with_middlewares(self, user_text):
        # Initialize web_result
        web_result = None

        # Always detect user language and maintain consistency
        self.language_hook.process_user_input(user_text)
        detected_lang = self.language_hook.user_lang

        # Check for Android app/device control commands first
        android_result = self.android_hook.process_user_command(user_text)
        if android_result:
            agent_reply = android_result
        else:
            # Enhanced intent detection with better classification
            user_text_lower = user_text.lower().strip()

            # Priority 1: Tool-specific requests (highest priority)
            tool_keywords = {
                'weather': ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'climate'],
                'email': ['email', 'mail', 'send', 'gmail', 'message', 'compose'],
                'search': ['search', 'find', 'look up', 'google', 'duckduckgo', 'browse']
            }

            # Check for explicit tool requests
            tool_detected = False
            for tool, keywords in tool_keywords.items():
                if any(keyword in user_text_lower for keyword in keywords):
                    tool_detected = True
                    if tool == 'weather':
                        # Extract city name from user text
                        city_match = re.search(r'weather (?:in|for|of) (\w+)', user_text_lower)
                        if city_match:
                            city = city_match.group(1).title()
                            # Call weather tool directly
                            try:
                                # For now, use a simple weather response
                                agent_reply = f"I'll check the weather for {city}."
                            except Exception as e:
                                agent_reply = f"I couldn't get weather information for {city} right now."
                        else:
                            agent_reply = "Please specify a city name for weather information (e.g., 'weather in Delhi')."
                        break
                    elif tool == 'email':
                        # Check if all required email parameters are present
                        email_match = re.search(r'send email to (\S+) subject (.+?) message (.+)', user_text_lower, re.IGNORECASE)
                        if email_match:
                            to_email, subject, message = email_match.groups()
                            # Call email tool
                            try:
                                agent_reply = f"I'll send an email to {to_email} with subject '{subject}'."
                            except Exception as e:
                                agent_reply = "I couldn't send the email right now. Please check your email configuration."
                        else:
                            agent_reply = "To send an email, please say: 'send email to [email] subject [subject] message [message]'"
                        break
                    elif tool == 'search':
                        # Let the LiveKit tool handle the search
                        agent_reply = f"I'll search for information about: {user_text}"
                        break

            if not tool_detected:
                # Continue with information-seeking detection
                # Priority 2: Clear information-seeking questions (medium priority)
                question_patterns = [
                    'what is', 'who is', 'when did', 'where is', 'why does', 'how does', 'how to',
                    'tell me about', 'explain', 'define', 'meaning of', 'difference between',
                    'what are', 'who are', 'when was', 'where are', 'why is', 'how do',
                    'can you tell me', 'do you know', 'i want to know'
                ]

                info_keywords = [
                    'current', 'latest', 'news', 'update', 'fact', 'information', 'details about',
                    'history of', 'origin of', 'cause of', 'reason for', 'about', 'regarding',
                    'population', 'capital', 'area', 'located', 'founded', 'established'
                ]

                is_clear_question = any(pattern in user_text_lower for pattern in question_patterns)
                has_info_keywords = any(kw in user_text_lower for kw in info_keywords)

                # Enhanced search detection
                info_keyword_count = sum(1 for kw in info_keywords if kw in user_text_lower)
                has_question_mark = '?' in user_text
                is_imperative_search = any(word in user_text_lower for word in ['search', 'find', 'look up', 'google', 'tell me'])

                # More aggressive search triggering
                needs_search = (is_clear_question or has_question_mark or is_imperative_search or
                              info_keyword_count >= 1 or len(user_text.split()) > 8)

                if needs_search:
                    # Let the LiveKit framework handle search through tools
                    agent_reply = f"I'll search for information about: {user_text}"
                else:
                    # Priority 3: Casual conversation (lowest priority - use agent)
                    agent_reply = AGENT_INSTRUCTION.split("# Examples")[0].strip()


        # Always reply in user's detected language and persona, strictly following prompt.py
        final_reply = self.language_hook.process_agent_output(agent_reply)

        # Strict TTS integration (patch, does not touch original code)
        if self.strict_tts_sync is None:
            from tts_sync_middleware import StrictTTSSyncMiddleware
            self.strict_tts_sync = StrictTTSSyncMiddleware()

        # Save language state for consistency across runs
        self.save_language_state()

        # Use web_result if available for strict TTS (now properly scoped)
        tts_text = self.strict_tts_sync.get_strict_tts_text(final_reply, web_result, persona='female', tts_lang=self.language_hook.get_tts_language())
        tts_lang = self.language_hook.get_tts_language()
        # tts_plugin.speak(tts_text, language=tts_lang)
        return {
            "reply_text": final_reply,
            "tts_text": tts_text,
            "tts_lang": tts_lang
        }
        


async def entrypoint(ctx: agents.JobContext):
    agent = Assistant()
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # Example: wrap user input and agent output with language hook
    # Replace these lines with your actual input/output handling logic
    # user_text = ... (get user input)
    # processed_user_text = agent.process_user_input(user_text)
    # agent_reply = ... (generate agent reply)
    # processed_agent_reply = agent.process_agent_output(agent_reply)
    # tts_lang = agent.get_tts_language()
    # Pass tts_lang to your TTS plugin

    # Example usage of all middlewares (non-intrusive)
    # user_text = "Who is the Prime Minister of India?"
    # result = agent.process_query_with_middlewares(user_text)
    # print(result)
    # Always use result['tts_text'] and result['tts_lang'] for TTS output:
    # tts_plugin.speak(result['tts_text'], language=result['tts_lang'])

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))