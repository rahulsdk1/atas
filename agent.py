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
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.8,
                instructions=AGENT_INSTRUCTION,
            ),
            tools=[
                get_weather,
                search_web,
                send_email
            ],
            instructions=AGENT_INSTRUCTION
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

        # Language persistence setup

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

    # Removed on_user_input method - LiveKit handles user input directly

    def generate_reply(self, instructions=None):
        """Custom reply generation that properly handles search queries"""
        # This method will be called by LiveKit when it needs to generate a response
        # We can intercept and handle search queries here before falling back to default

        # For now, let LiveKit handle it with the tools we provided
        # The tools are registered and should be called automatically by the LLM
        return super().generate_reply(instructions)


    async def process_query_with_middlewares(self, user_text):
        """
        Improved: Handles Android commands, language switching, web search, and human-like conversation.
        Always replies in user's language and uses only tool/web search results for info queries.
        """
        web_result = None
        self.language_hook.process_user_input(user_text)
        detected_lang = self.language_hook.user_lang

        # Android device control
        android_result = self.android_hook.process_user_command(user_text)
        if android_result:
            agent_reply = android_result
        else:
            user_text_lower = user_text.lower().strip()
            # Tool keywords
            tool_keywords = {
                'weather': ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'climate'],
                'email': ['email', 'mail', 'send', 'gmail', 'message', 'compose'],
                'search': ['search', 'find', 'look up', 'google', 'duckduckgo', 'browse']
            }
            tool_detected = False
            for tool, keywords in tool_keywords.items():
                if any(keyword in user_text_lower for keyword in keywords):
                    tool_detected = True
                    if tool == 'weather':
                        city_match = re.search(r'weather (?:in|for|of) (\w+)', user_text_lower)
                        if city_match:
                            city = city_match.group(1).title()
                            try:
                                agent_reply = await get_weather(city)
                            except Exception:
                                agent_reply = f"I couldn't get weather information for {city} right now."
                        else:
                            agent_reply = "Please specify a city name for weather information (e.g., 'weather in Delhi')."
                        break
                    elif tool == 'email':
                        email_match = re.search(r'send email to (\S+) subject (.+?) message (.+)', user_text_lower, re.IGNORECASE)
                        if email_match:
                            to_email, subject, message = email_match.groups()
                            try:
                                agent_reply = await send_email(to_email, subject, message)
                            except Exception:
                                agent_reply = "I couldn't send the email right now. Please check your email configuration."
                        else:
                            agent_reply = "To send an email, please say: 'send email to [email] subject [subject] message [message]'"
                        break
                    elif tool == 'search':
                        try:
                            web_result = await search_web(user_text)
                            # Always use only the search result for reply
                            agent_reply = web_result if web_result else "No results found."
                        except Exception:
                            agent_reply = "I couldn't retrieve search results right now."
                        break

            if not tool_detected:
                # Info-seeking detection
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
                info_keyword_count = sum(1 for kw in info_keywords if kw in user_text_lower)
                has_question_mark = '?' in user_text
                is_imperative_search = any(word in user_text_lower for word in ['search', 'find', 'look up', 'google', 'tell me'])
                needs_search = (is_clear_question or has_question_mark or is_imperative_search or info_keyword_count >= 1 or len(user_text.split()) > 8)
                if needs_search:
                    try:
                        web_result = await search_web(user_text)
                        agent_reply = web_result if web_result else "No results found."
                    except Exception:
                        agent_reply = "I couldn't retrieve search results right now."
                else:
                    # Casual conversation: reply as a human, use persona
                    agent_reply = "Of course, Sir. How may I assist you today?" if user_text_lower in ["hi", "hello", "hey"] else AGENT_INSTRUCTION.split("# Examples")[0].strip()

        # Always reply in user's detected language
        translated_reply = self.language_hook.process_agent_output(agent_reply)
        if self.strict_tts_sync is None:
            from tts_sync_middleware import StrictTTSSyncMiddleware
            self.strict_tts_sync = StrictTTSSyncMiddleware()
        self.save_language_state()
        tts_text = self.strict_tts_sync.get_strict_tts_text(translated_reply, web_result, persona='female', tts_lang=self.language_hook.get_tts_language())
        tts_lang = self.language_hook.get_tts_language()
        return {
            "reply_text": translated_reply,
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