from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import get_weather, search_web, send_email
from language_middleware import LanguageAgentHook
from search_middleware import SearchMiddleware
from tts_sync_middleware import TTSSyncMiddleware
from emotions_middleware import EmotionsMiddleware
from android_control_middleware import AndroidControlMiddleware
load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
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
        from search_middleware import FastSearchMiddleware
        self.search_hook = FastSearchMiddleware(timeout=5)
        self.tts_sync = TTSSyncMiddleware()
        self.strict_tts_sync = None  # Will be initialized for strict TTS
        self.emotions_hook = EmotionsMiddleware()
        self.android_hook = AndroidControlMiddleware()

    def process_user_input(self, text):
        # Detect and set user language
        return self.language_hook.process_user_input(text)

    def process_agent_output(self, text):
        # Translate agent reply to user's language
        return self.language_hook.process_agent_output(text)

    def get_tts_language(self):
        # Get language for TTS
        return self.language_hook.get_tts_language()

    def process_query_with_middlewares(self, user_text):
        # Always reset state for every query
        self.language_hook.user_lang = 'en'
        user_gender = "female"

        # Always detect user language and switch if changed
        self.language_hook.process_user_input(user_text)
        detected_lang = self.language_hook.user_lang

        # Check for Android app/device control commands first
        android_result = self.android_hook.process_user_command(user_text)
        if android_result:
            agent_reply = android_result
        else:
            # Strict intent detection for web search
            info_keywords = [
                'who', 'what', 'when', 'where', 'why', 'how', 'current', 'latest', 'news', 'update', 'fact', 'information', 'tell me about', 'show me', 'find', 'search', 'google', 'duckduckgo'
            ]
            user_text_lower = user_text.lower()
            needs_search = any(kw in user_text_lower for kw in info_keywords)

            if needs_search:
                # Only use web search result or fallback
                web_result = self.search_hook.process_user_query(user_text)
                if web_result and isinstance(web_result, str) and web_result.strip():
                    agent_reply = web_result
                else:
                    agent_reply = "Sorry, I couldn't find accurate information for your query."
            else:
                # Always use prompt instructions for non-search queries
                from prompts import AGENT_INSTRUCTION
                agent_reply = AGENT_INSTRUCTION.split("# Examples")[0].strip()


        # Always reply in user's detected language and persona, strictly following prompt.py
        final_reply = self.language_hook.process_agent_output(agent_reply)

        # Strict TTS integration (patch, does not touch original code)
        if self.strict_tts_sync is None:
            from tts_sync_middleware import StrictTTSSyncMiddleware
            self.strict_tts_sync = StrictTTSSyncMiddleware()
        # Use web_result if available for strict TTS
        web_result = None
        if 'web_result' in locals():
            web_result = web_result
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