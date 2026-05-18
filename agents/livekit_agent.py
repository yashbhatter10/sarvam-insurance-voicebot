"""
Production-pattern voice agent — LiveKit + Sarvam plugin variant.

This is NOT what the demo runs. The demo uses the FastAPI scaffold in `app/`.
This file is included as the production-migration exhibit: the same Aarav
agent expressed in the framework Sarvam's official docs recommend for
real-time voice. See:
  https://docs.sarvam.ai/api-reference-docs/integration/build-voice-agent-with-live-kit

To run (not required for the demo):
  pip install "livekit-agents[sarvam,openai,silero]" python-dotenv
  # Set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, SARVAM_API_KEY
  python agents/livekit_agent.py dev

The four best-practice flags Sarvam explicitly calls out are applied here:
  1. No `vad=...` passed to AgentSession (Sarvam STT handles VAD).
  2. `flush_signal=True` on STT (clean start/end-of-speech events).
  3. `turn_detection="stt"` on AgentSession.
  4. `min_endpointing_delay=0.07` matches Sarvam STT's ~70ms processing latency.
"""
from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, sarvam

load_dotenv()

logger = logging.getLogger("aarav-livekit")
logger.setLevel(logging.INFO)

BROCHURE = (Path(__file__).resolve().parent.parent / "data" / "sample_insurance_policy.txt").read_text(encoding="utf-8")

AARAV_INSTRUCTIONS = f"""You are Aarav, a polite insurance advisor for Star Health Insurance.
You're on a VOICE call. Your text will be spoken. Use 2-3 short sentences max.
Ask one question at a time. Write numbers as words (ten lakh, not 10,00,000).

Never quote a final premium — frame as a range and route to advisor handoff.
Never promise claim approval — claims go through underwriting and waiting periods.
Never give tax / legal / medical advice — escalate.
Ground every policy answer in the brochure below. If it's not in the brochure,
say "The brochure I have doesn't cover that — I'll flag it for the advisor."

BROCHURE:
{BROCHURE}
"""


class AaravAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AARAV_INSTRUCTIONS,

            # Sarvam Saaras v3 — auto-detect language, code-mix friendly.
            # flush_signal=True per Sarvam's best practice for turn-taking.
            stt=sarvam.STT(
                language="unknown",
                model="saaras:v3",
                mode="transcribe",
                flush_signal=True,
            ),

            # LLM: OpenAI gpt-4o is what Sarvam's own LiveKit cookbook uses.
            # Swap to a Sarvam LLM when the LiveKit plugin supports it natively.
            llm=openai.LLM(model="gpt-4o"),

            # Sarvam Bulbul v3 — warm male voice for English/Hinglish.
            tts=sarvam.TTS(
                target_language_code="en-IN",
                model="bulbul:v3",
                speaker="anand",
                pace=1.0,
                speech_sample_rate=24000,
            ),
        )

    async def on_enter(self) -> None:
        """Aarav opens the conversation."""
        self.session.generate_reply()


async def entrypoint(ctx: JobContext) -> None:
    logger.info("User connected to room: %s", ctx.room.name)

    # Best practices:
    # - DO NOT pass vad=... (Sarvam STT handles VAD internally).
    # - turn_detection="stt" → Sarvam STT drives turn-taking.
    # - min_endpointing_delay=0.07 → matches Sarvam STT's ~70ms latency.
    session = AgentSession(
        turn_detection="stt",
        min_endpointing_delay=0.07,
    )
    await session.start(agent=AaravAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
