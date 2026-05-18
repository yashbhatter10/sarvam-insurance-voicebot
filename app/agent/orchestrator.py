"""
Conversation orchestrator for Aarav.

State machine + intent classification (lightweight) + metrics collection.

The state machine is intentionally simple. The LLM does the natural-language
heavy lifting; the state machine is for:
  - logging which state each turn landed in (analytics),
  - deciding whether to slow the pace (policy-detail state),
  - deciding when to capture handoff data,
  - tracking session-level metrics that a CSM would care about.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.agent.policy import SYSTEM_PROMPT, apply_guardrails, build_messages
from app.agent.voice_design import VoiceProfile, pick_profile, slow_for_detail
from app.rag import BrochureRAG, Snippet
from app.sarvam_client import SarvamClient, STTResult, TTSResult

# Common Hinglish/Hindi words that appear in Roman script and signal that the
# bot is speaking Hinglish — TTS should use hi-IN for these.
_HINGLISH_MARKERS = (
    "haan", "theek", "achha", "achha", "samajh", "nahi", "kya",
    "aapko", "aap", "batao", "bolo", "lakh", "saal", "ghar",
    "phir", "toh", "koi", "baar", "ji", "yaar", "bolenge",
)

_DEVANAGARI_RANGE = range(0x0900, 0x097F + 1)


def _hinglish_tts_language(text: str, stt_lang: str) -> str:
    """Choose TTS language code based on bot text content.

    Rules (in priority order):
    1. If text contains Devanagari characters → hi-IN  (Devanagari always needs hi-IN)
    2. If text contains ≥2 Hinglish marker words in Roman script → hi-IN
    3. Otherwise use the STT-detected language as-is
    """
    if not text:
        return stt_lang or "en-IN"
    # Devanagari present?
    if any(ord(c) in _DEVANAGARI_RANGE for c in text):
        return "hi-IN"
    # Roman Hinglish markers?
    lower = text.lower()
    hits = sum(1 for m in _HINGLISH_MARKERS if m in lower)
    if hits >= 2:
        return "hi-IN"
    return stt_lang or "en-IN"


class State(str, Enum):
    GREETING = "greeting"
    DISCOVERY = "discovery"
    PITCH = "pitch"
    QA = "qa"
    OBJECTION = "objection"
    HANDOFF = "handoff"
    CLOSED = "closed"


@dataclass
class TurnMetrics:
    turn_id: str
    state: State
    stt_ms: int
    retrieval_ms: int
    llm_ms: int
    tts_ms: int
    total_ms: int
    stt_confidence: float
    detected_language: str
    guardrail_triggers: list[str]
    rag_hit: bool
    barge_in: bool = False


@dataclass
class SessionMetrics:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    turns: list[TurnMetrics] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    state: State = State.GREETING
    name: Optional[str] = None
    city: Optional[str] = None
    handoff_captured: bool = False
    escalation_reasons: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        if not self.turns:
            return {
                "session_id": self.session_id,
                "turns": 0,
                "containment": None,
                "escalations": [],
                "languages": [],
                "guardrail_triggers": [],
                "latency_p50_ms": None,
                "latency_p95_ms": None,
                "rag_no_answer_rate": None,
            }
        totals = sorted(t.total_ms for t in self.turns)
        p50 = totals[len(totals) // 2]
        p95 = totals[int(len(totals) * 0.95)]
        rag_no_answer = sum(1 for t in self.turns if not t.rag_hit and t.state == State.QA)
        rag_qa_total = max(1, sum(1 for t in self.turns if t.state == State.QA))
        return {
            "session_id": self.session_id,
            "turns": len(self.turns),
            "containment": not self.handoff_captured,
            "escalations": self.escalation_reasons,
            "languages": sorted({t.detected_language for t in self.turns}),
            "guardrail_triggers": [g for t in self.turns for g in t.guardrail_triggers],
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "rag_no_answer_rate": round(rag_no_answer / rag_qa_total, 2),
            "current_state": self.state.value,
        }


class Orchestrator:
    """End-to-end one-turn handler. Called per user audio blob."""

    def __init__(self, client: SarvamClient, rag: BrochureRAG):
        self.client = client
        self.rag = rag

    # --------------------------- Public API ---------------------------
    def handle_turn(
        self,
        session: SessionMetrics,
        audio_bytes: bytes,
        *,
        language_hint: str = "unknown",
        gender_pref: str = "male",
    ) -> dict:
        """Run one full STT → retrieve → LLM → guardrails → TTS cycle.

        Returns a JSON-serialisable dict for the frontend.
        """
        t_start = time.time()

        # 1. STT
        stt: STTResult = self.client.stt(audio_bytes, language=language_hint)
        user_text = (stt.text or "").strip()

        # 1a. Empty audio / no speech detected — repair prompt, no LLM call needed
        if not user_text:
            bot_text = "Sorry, I did not catch that — could you say it again?"
            profile = pick_profile(stt.language_code or "en-IN", gender_pref=gender_pref)
            tts = self.client.tts(
                bot_text,
                language=profile.target_language_code,
                voice=profile.voice,
                pace=profile.pace,
            )
            return {
                "user_text": "",
                "bot_text": bot_text,
                "audio_b64": tts.audio_b64,
                "sample_rate": tts.sample_rate,
                "language": stt.language_code or "en-IN",
                "voice": profile.voice,
                "pace": profile.pace,
                "state_from": session.state.value,
                "state_to": session.state.value,
                "sources": [],
                "guardrails": ["empty_audio_repair"],
                "latency": {
                    "stt_ms": stt.latency_ms,
                    "retrieval_ms": 0,
                    "llm_ms": 0,
                    "tts_ms": tts.latency_ms,
                    "total_ms": int((time.time() - t_start) * 1000),
                },
                "metrics_so_far": session.summary(),
            }

        # 2. Update state from the new user turn
        prior_state = session.state
        session.state = self._next_state(session.state, user_text)

        # 3. Retrieve brochure snippets (only meaningful in QA / Pitch)
        t_ret_start = time.time()
        snippets: list[Snippet] = []
        if session.state in (State.PITCH, State.QA, State.DISCOVERY):
            snippets = self.rag.retrieve(user_text, k=2)
        retrieval_ms = int((time.time() - t_ret_start) * 1000)

        # 4. LLM
        retrieved_text = self.rag.format_for_prompt(snippets)
        messages = build_messages(
            system_prompt=SYSTEM_PROMPT,
            history=session.history,
            user_turn=user_text,
            detected_language=stt.language_code,
            retrieved_snippets=retrieved_text,
        )
        t_llm_start = time.time()
        raw_reply = self.client.llm(messages)
        llm_ms = int((time.time() - t_llm_start) * 1000)

        # 5. Guardrails
        guarded = apply_guardrails(raw_reply)
        bot_text = guarded.text

        # 6. Handoff capture (basic regex on PII)
        self._maybe_capture_handoff(session, user_text)

        # 7. TTS (slow the pace if we're in QA / detail-reading)
        # Use the STT-detected language as the base, but override to hi-IN when
        # the bot reply contains Hinglish — otherwise "haan haan" sounds like
        # English gibberish through the en-IN voice engine.
        tts_lang = _hinglish_tts_language(bot_text, stt.language_code)
        profile: VoiceProfile = pick_profile(tts_lang, gender_pref=gender_pref)
        if session.state == State.QA:
            profile = slow_for_detail(profile)
        tts: TTSResult = self.client.tts(
            bot_text,
            language=profile.target_language_code,
            voice=profile.voice,
            pace=profile.pace,
        )

        # 8. Update history + metrics
        session.history.append({"role": "user", "content": user_text})
        session.history.append({"role": "assistant", "content": bot_text})

        total_ms = int((time.time() - t_start) * 1000)
        m = TurnMetrics(
            turn_id=uuid.uuid4().hex[:8],
            state=session.state,
            stt_ms=stt.latency_ms,
            retrieval_ms=retrieval_ms,
            llm_ms=llm_ms,
            tts_ms=tts.latency_ms,
            total_ms=total_ms,
            stt_confidence=stt.confidence,
            detected_language=stt.language_code,
            guardrail_triggers=guarded.triggered,
            rag_hit=bool(snippets),
        )
        session.turns.append(m)
        if guarded.triggered:
            session.escalation_reasons.extend(guarded.triggered)

        return {
            "user_text": user_text,
            "bot_text": bot_text,
            "audio_b64": tts.audio_b64,
            "sample_rate": tts.sample_rate,
            "language": stt.language_code,
            "voice": profile.voice,
            "pace": profile.pace,
            "state_from": prior_state.value,
            "state_to": session.state.value,
            "sources": [
                {"id": s.id, "section": s.section, "text": s.short()} for s in snippets
            ],
            "guardrails": guarded.triggered,
            "latency": {
                "stt_ms": stt.latency_ms,
                "retrieval_ms": retrieval_ms,
                "llm_ms": llm_ms,
                "tts_ms": tts.latency_ms,
                "total_ms": total_ms,
            },
            "metrics_so_far": session.summary(),
        }

    def first_greeting(self, session: SessionMetrics, *, gender_pref: str = "male") -> dict:
        """Called once when a new session starts — Aarav opens the conversation.

        Modeled on the GreyLabs Vidya outbound-sales pattern: identify, establish
        context (website interest), drive to discovery in the same turn. Hinglish
        opener since that's authentic for an Indian sales call.
        """
        bot_text = "नमस्ते! मैं Aarav हूँ Star Health Insurance से — क्या मैं Anand ji से बात कर रहा हूँ?"
        profile = pick_profile("hi-IN", gender_pref=gender_pref)
        tts = self.client.tts(bot_text, language=profile.target_language_code, voice=profile.voice, pace=profile.pace)
        session.history.append({"role": "assistant", "content": bot_text})
        return {
            "user_text": "",
            "bot_text": bot_text,
            "audio_b64": tts.audio_b64,
            "sample_rate": tts.sample_rate,
            "language": "en-IN",
            "voice": profile.voice,
            "pace": profile.pace,
            "state_from": "init",
            "state_to": State.GREETING.value,
            "sources": [],
            "guardrails": [],
            "latency": {"stt_ms": 0, "retrieval_ms": 0, "llm_ms": 0, "tts_ms": tts.latency_ms, "total_ms": tts.latency_ms},
            "metrics_so_far": session.summary(),
        }

    # --------------------------- Internals ---------------------------
    @staticmethod
    def _next_state(current: State, user_text: str) -> State:
        """State transitions based on lightweight keyword intent + current state.

        Order matters — most specific first. Note: 'cover' alone isn't enough to
        jump to QA; we want the discovery turns to complete first. QA triggers
        only on explicit policy questions (premium amount, claim approval, specific
        waiting periods, exclusions, rider details).
        """
        t = user_text.lower()
        if not t:
            return current

        # Strong intent — these can fire from any state
        if any(k in t for k in ["call back", "callback", "advisor", "human agent",
                                  "my name is", "i'm based in", "city is", "i live in"]):
            return State.HANDOFF
        if any(k in t for k in ["expensive", "too much", "too costly", "don't trust",
                                  "scam", "later", "think about", "not interested"]):
            return State.OBJECTION

        # Policy Q&A — only on explicit policy questions, not just product mention
        qa_signals = [
            "what is the premium", "kya premium", "premium kitna",
            "will my claim", "claim approve", "claim settle",
            "what is the waiting period", "waiting period kitna",
            "what is not covered", "exclusion", "exclude",
            "rider", "ROP", "return of premium", "free look",
            "cashless", "network hospital", "section 80",
        ]
        if any(k in t for k in qa_signals):
            return State.QA

        # State progression
        if current == State.GREETING:
            return State.DISCOVERY
        if current == State.DISCOVERY:
            # If we've collected enough discovery signals, move to pitch
            discovery_signals = ["years old", "saal ka", "saal ki", "family", "wife",
                                  "husband", "kids", "children", "married", "single",
                                  "income", "lakh", "earning", "parents", "mummy",
                                  "papa", "father", "mother", "mom", "dad"]
            # Also trigger on age numbers alone (e.g. "65, 62" for parent ages)
            import re as _re
            has_ages = bool(_re.search(r"\b\d{2}\b", t))
            if (any(k in t for k in discovery_signals) or has_ages) and len(t.split()) >= 2:
                return State.PITCH
        return current

    @staticmethod
    def _maybe_capture_handoff(session: SessionMetrics, user_text: str) -> None:
        if session.handoff_captured or not user_text:
            return
        import re

        m_name = re.search(r"(?:my name is|i am|i'm)\s+([a-z][a-z\s]{1,30})", user_text, re.IGNORECASE)
        m_city = re.search(r"(?:from|in|based in)\s+([a-z][a-z\s]{1,30})", user_text, re.IGNORECASE)
        if m_name:
            session.name = m_name.group(1).strip().title()
        if m_city:
            session.city = m_city.group(1).strip().title()
        if session.name and session.city:
            session.handoff_captured = True
            session.state = State.HANDOFF
