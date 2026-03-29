"""
Voice pipeline: Sarvam STT → OpenAI gpt-4o-mini (with tools) → Sarvam TTS.
Handles the audio↔text conversion and LLM conversation loop.
"""

import json
import logging
import aiohttp
import base64
from openai import AsyncOpenAI
from krishirin_agents.voice_server.tools import (
    TOOL_DEFINITIONS,
    handle_tool_call,
    set_session_context,
    append_transcript,
)
from krishirin_agents.voice_server.voice_agent_prompt import (
    build_voice_system_prompt,
    DEFAULT_CLARIFICATION_QUESTIONS,
)
from krishirin_agents.shared.config import USE_SAMPLE_DATA

logger = logging.getLogger(__name__)

# Clients
_openai_client = None
_sarvam_api_key = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI()
    return _openai_client


def _get_sarvam_key():
    global _sarvam_api_key
    if _sarvam_api_key is None:
        import os
        _sarvam_api_key = os.getenv("SARVAMAI_API_KEY", os.getenv("SARVAM_API_KEY", ""))
    return _sarvam_api_key


class VoiceSession:
    """Manages a single voice call session."""

    def __init__(self, session_id: str, farmer_id: str, precall_analysis: dict):
        self.session_id = session_id
        self.farmer_id = farmer_id
        self.precall_analysis = precall_analysis

        # Build system prompt
        questions = precall_analysis.get("clarification_questions", DEFAULT_CLARIFICATION_QUESTIONS)
        self.system_prompt = build_voice_system_prompt(precall_analysis, questions)

        # Conversation history for OpenAI
        self.messages = [{"role": "system", "content": self.system_prompt}]

        # Format precall context as text for oncall agents
        self.precall_context = json.dumps(precall_analysis, indent=2, default=str)

        # Register session context for tools
        set_session_context(session_id, farmer_id, self.precall_context)

    async def stt(self, audio_bytes: bytes) -> str:
        """Sarvam STT: Hindi audio → English text."""
        key = _get_sarvam_key()
        if not key or USE_SAMPLE_DATA:
            return "[mock STT: farmer speaking in Hindi]"

        audio_b64 = base64.b64encode(audio_bytes).decode()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.sarvam.ai/speech-to-text-translate",
                headers={"api-subscription-key": key, "Content-Type": "application/json"},
                json={
                    "input": {"audio": audio_b64},
                    "config": {
                        "language": {"sourceLanguage": "hi"},
                        "audioFormat": "wav",
                        "encoding": "base64",
                    },
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("output", [{}])[0].get("source", "")
                logger.error(f"Sarvam STT error: {resp.status}")
                return ""

    async def process_text(self, user_text: str) -> str:
        """Send user text to OpenAI, handle tool calls, return response text."""
        if not user_text.strip():
            return ""

        # Add to conversation + transcript
        self.messages.append({"role": "user", "content": user_text})
        append_transcript(self.session_id, "Farmer", user_text)

        client = _get_openai()

        # LLM call with tools
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=300,
        )

        message = response.choices[0].message

        # Handle tool calls (may be multiple rounds)
        while message.tool_calls:
            self.messages.append(message.model_dump())

            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                result = await handle_tool_call(self.session_id, tc.function.name, args)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

            # Get next response after tool results
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=300,
            )
            message = response.choices[0].message

        # Final text response
        reply = message.content or ""
        self.messages.append({"role": "assistant", "content": reply})
        append_transcript(self.session_id, "Agent", reply)

        return reply

    async def tts(self, text: str) -> bytes:
        """Sarvam TTS: English/Hindi text → Hindi audio."""
        key = _get_sarvam_key()
        if not key or USE_SAMPLE_DATA:
            return b""  # Empty bytes in mock mode

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={"api-subscription-key": key, "Content-Type": "application/json"},
                json={
                    "input": text,
                    "config": {
                        "language": {"sourceLanguage": "hi"},
                        "voice": "meera",  # Sarvam Bulbul Hindi voice
                        "audioFormat": "wav",
                        "encoding": "base64",
                    },
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    audio_b64 = data.get("audio", "")
                    return base64.b64decode(audio_b64) if audio_b64 else b""
                logger.error(f"Sarvam TTS error: {resp.status}")
                return b""
