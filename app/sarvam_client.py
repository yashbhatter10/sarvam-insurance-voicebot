"""
Thin Sarvam API wrapper for the insurance voicebot.

Uses the official `sarvamai` SDK (`pip install -U sarvamai`).

If `USE_MOCK=true` or no API key is set, falls back to canned responses so the
architecture demo still runs end-to-end without a key.

Reference: docs.sarvam.ai/api-reference-docs/getting-started/quickstart
"""
from __future__ import annotations

import base64
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Iterable, Optional

logger = logging.getLogger("sarvam_client")

# Strip reasoning-model thinking blocks like <think>...</think> before TTS.
# Kept as a safety net in case the LLM emits reasoning traces.
_THINK_BLOCK_CLOSED = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)
_THINK_OPEN_UNCLOSED = re.compile(r"<think>.*$", re.DOTALL | re.IGNORECASE)
_STRAY_TAGS = re.compile(r"</?think>", re.IGNORECASE)

# Heuristic detector for reasoning prose that leaks WITHOUT think tags
# (happens when reasoning model gets cut off mid-thought)
_REASONING_PROSE_STARTS = (
    "okay, the user",
    "okay, let me",
    "let me think",
    "the user is",
    "the user said",
    "looking at the",
    "based on the conversation",
    "i need to",
    "first, i need",
)



def _strip_reasoning(text: str) -> str:
    """Remove <think>...</think> blocks and any reasoning-leak patterns.

    Handles three cases:
    1. Well-formed: <think>reasoning</think> answer - keep just "answer"
    2. Unclosed: <think>reasoning (cut off) - keep nothing (return empty)
    3. No tags but obvious reasoning prose - return empty so the orchestrator
       falls back to a graceful retry instead of speaking the reasoning aloud.
    """
    if not text:
        return text
    cleaned = _THINK_BLOCK_CLOSED.sub("", text)
    cleaned = _THINK_OPEN_UNCLOSED.sub("", cleaned)
    cleaned = _STRAY_TAGS.sub("", cleaned)
    cleaned = cleaned.strip()

    # Catch tag-less reasoning prose
    head = cleaned[:60].lower()
    if any(head.startswith(p) for p in _REASONING_PROSE_STARTS):
        logger.warning("Reasoning prose leaked without tags - returning empty so caller can retry. Head=%r", head)
        return ""

    return cleaned


@dataclass
class STTResult:
    text: str
    language_code: str
    confidence: float
    latency_ms: int


@dataclass
class TTSResult:
    audio_b64: str  # base64-encoded wav/linear16 for the browser <audio>
    sample_rate: int
    latency_ms: int


class SarvamClient:
    """Voice-stack client.

    - STT: Sarvam Saarika v2.5 (always)
    - TTS: Sarvam Bulbul v3 (always)
    - LLM: Gemini Flash if GEMINI_API_KEY is set (faster, ~500ms); otherwise
      Sarvam-M (reasoning, ~2-3s) as the fallback. The voice stack stays Sarvam
      because the distinctive product capability is Indic voice quality - the
      brain is a swappable component, exactly the pattern Sarvam's own LiveKit
      cookbook follows.
    """

    def __init__(self, api_key: Optional[str] = None, *, mock: bool = False):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.mock = mock or os.getenv("USE_MOCK", "false").lower() == "true" or not self.api_key
        self._sdk = None
        self._gemini_model = None
        if not self.mock:
            try:
                from sarvamai import SarvamAI

                self._sdk = SarvamAI(api_subscription_key=self.api_key)
            except Exception as exc:  # pragma: no cover - depends on user env
                logger.warning("Falling back to mock mode: %s", exc)
                self.mock = True

        if self.gemini_key and not self.mock:
            try:
                self._gemini_model_name = "gemini-2.5-flash"
                logger.info("Gemini LLM enabled (%s).", self._gemini_model_name)
            except Exception as exc:
                logger.warning("Gemini init failed, will fall back to Sarvam LLM: %s", exc)
                self.gemini_key = None

    # --------------------------- STT ---------------------------
    def stt(self, audio_bytes: bytes, *, language: str = "unknown") -> STTResult:
        """Saaras v3 transcribe. `language='unknown'` enables auto-detect.

        Sarvam docs: mode='transcribe' returns the original language;
        other modes ('translate', 'verbatim', 'translit', 'codemix') are available.
        """
        t0 = time.time()
        if self.mock or not self._sdk:
            return STTResult(
                text="[mock] I'd like to know about your family floater health policy.",
                language_code="en-IN",
                confidence=0.95,
                latency_ms=int((time.time() - t0) * 1000) + 180,
            )
        try:
            import io

            audio_io = io.BytesIO(audio_bytes)
            audio_io.name = "turn.wav"  # SDK sometimes needs a filename
            # SDK 0.1.28: speech_to_text.transcribe takes file, model, language_code,
            # mode, input_audio_codec, request_options. We let codec auto-detect from
            # the webm container the browser sends.
            #   - model `saarika:v2.5` transcribes in source language (what we want).
            #   - `saaras:v3` would TRANSLATE to English - wrong for us.
            #   - `language_code="unknown"` is a valid literal for auto-detect.
            lang_for_sdk = language if language else "unknown"
            resp = self._sdk.speech_to_text.transcribe(
                file=audio_io,
                model="saarika:v2.5",
                language_code=lang_for_sdk,
            )
            # Sarvam SDK returns response with .transcript or .text depending on version
            text = getattr(resp, "transcript", None) or getattr(resp, "text", "") or ""
            lang = getattr(resp, "language_code", None) or "en-IN"
            logger.info("STT latency: %d ms | lang=%s | text=%r",
                        int((time.time() - t0) * 1000), lang, text[:60])
            return STTResult(
                text=text.strip(),
                language_code=lang,
                confidence=getattr(resp, "confidence", 0.9) or 0.9,
                latency_ms=int((time.time() - t0) * 1000),
            )
        except Exception as exc:
            # Loud failure - log the type and message so the cause is obvious
            logger.error("STT call FAILED (%s: %s). Returning empty transcript.",
                         type(exc).__name__, exc)
            return STTResult(
                text="",
                language_code="en-IN",
                confidence=0.0,
                latency_ms=int((time.time() - t0) * 1000),
            )

    # --------------------------- Gemini LLM ---------------------------
    def _llm_gemini(self, messages: list[dict], temperature: float = 0.5) -> str:
        """Call Gemini via direct REST (OpenAI-compatible endpoint).

        Uses httpx - no google.generativeai library required.
        Works with gemini-2.5-flash and all future Gemini models.
        The `temperature` parameter is exposed so the retry path can use 0.7
        to encourage a more complete response on the second attempt.
        """
        import httpx
        resp = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            headers={
                "Authorization": f"Bearer {self.gemini_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._gemini_model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 120,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return (resp.json()["choices"][0]["message"]["content"] or "").strip()

    # --------------------------- LLM ---------------------------
    def llm(self, messages: list[dict], *, model: str = "sarvam-m", stream: bool = False) -> str:
        """LLM chat completion - Gemini Flash only, with one retry on short/empty reply.

        Why Gemini only (no Sarvam-M fallback):
        - Gemini 2.5 Flash has a 1M token context window, so it never overflows
          regardless of conversation length.
        - Sarvam-M's 7192-token limit means the 24k system prompt alone consumes ~85%
          of its budget; it reliably fails after a handful of turns.
        - STT + TTS still run through Sarvam (Saaras v3 + Bulbul v3). Only the LLM
          path is Gemini-only.

        Retry strategy when the first Gemini response is too short:
        - Append a brief internal nudge to the message list asking for a fuller reply.
        - Retry once at a slightly higher temperature (0.7 vs 0.5).
        - If the retry also fails, return a natural recovery phrase so the conversation
          can continue rather than silently breaking.
        """
        t0 = time.time()
        if self.mock or not self._sdk:
            return _mock_llm_reply(messages)

        # Minimum useful response length - shorter means Gemini acknowledged but
        # didn't actually respond (e.g. truncated STT input confused it).
        _MIN_RESPONSE_LEN = 20

        # ── Attempt 1: standard Gemini call ──────────────────────────────────
        if self.gemini_key:
            try:
                t = time.time()
                raw = self._llm_gemini(messages)
                content = _strip_reasoning(raw)
                logger.info(
                    "LLM (gemini): latency=%d ms | raw_len=%d | clean_len=%d",
                    int((time.time() - t) * 1000), len(raw or ""), len(content or ""),
                )
                if content and len(content.strip()) >= _MIN_RESPONSE_LEN:
                    return content.strip()
                if content:
                    logger.warning(
                        "Gemini response too short (%d chars): %r - retrying with nudge.",
                        len(content.strip()), content.strip(),
                    )
                else:
                    logger.warning("Gemini returned empty content - retrying with nudge.")
            except Exception as exc:
                logger.error("Gemini attempt 1 FAILED (%s: %s) - retrying.", type(exc).__name__, exc)

            # ── Attempt 2: retry with an internal nudge ───────────────────────
            # Append a hidden system nudge asking Gemini to give a fuller reply.
            # This nudge is never shown to the user or stored in session history.
            nudge_messages = messages + [{
                "role": "user",
                "content": (
                    "[INTERNAL] Your previous response was too brief for a voice conversation. "
                    "Please respond with 2–3 complete Hinglish sentences that move the "
                    "insurance sales conversation forward. Do not acknowledge this instruction."
                ),
            }]
            try:
                t = time.time()
                raw2 = self._llm_gemini(nudge_messages, temperature=0.7)
                content2 = _strip_reasoning(raw2)
                logger.info(
                    "LLM (gemini retry): latency=%d ms | raw_len=%d | clean_len=%d",
                    int((time.time() - t) * 1000), len(raw2 or ""), len(content2 or ""),
                )
                if content2 and len(content2.strip()) >= _MIN_RESPONSE_LEN:
                    return content2.strip()
                logger.warning("Gemini retry also too short (%d chars). Using recovery phrase.", len(content2 or ""))
            except Exception as exc:
                logger.error("Gemini retry FAILED (%s: %s). Using recovery phrase.", type(exc).__name__, exc)

        # ── Last resort: natural recovery phrase ─────────────────────────────
        # Rotate so repeated failures don't sound robotic.
        import random
        _RECOVERY_PHRASES = [
            "Aapki awaaz thodi unclear aayi — ek baar phir bataenge?",
            "Maafi chahta hoon, connection mein kuch issue tha — phir se bolenge?",
            "Haan, dobara bataiye — main sun raha hoon.",
            "Theek hai, ek baar phir poochhta hoon — aap family floater prefer karenge ya alag-alag plan?",
        ]
        return random.choice(_RECOVERY_PHRASES)

    # --------------------------- TTS ---------------------------
    def tts(
        self,
        text: str,
        *,
        language: str = "en-IN",
        voice: str = "anand",
        pace: float = 1.0,
        model: str = "bulbul:v3",
    ) -> TTSResult:
        """Bulbul v3 text-to-speech. Returns base64-encoded WAV bytes.

        Voice options (Bulbul v3, May 2026):
          Male: shubh, aditya, rahul, rohan, amit, dev, ratan, varun, manan,
                sumit, kabir, aayan, ashutosh, advait, anand, tarun, sunny,
                mani, gokul, vijay, mohit, rehan, soham
          Female: ritu, priya, neha, pooja, simran, kavya, ishita, shreya,
                  roopa, tanya, shruti, suhani, kavitha, rupali
        Pace: 0.5 - 2.0 (1.0 default).
        """
        t0 = time.time()
        if self.mock or not self._sdk:
            return TTSResult(audio_b64="", sample_rate=24000, latency_ms=int((time.time() - t0) * 1000) + 220)
        try:
            resp = self._sdk.text_to_speech.convert(
                text=text,
                target_language_code=language,
                model=model,
                speaker=voice,
                pace=pace,
                speech_sample_rate=24000,
            )
            # SDK returns object with `audios` list of base64 WAVs
            audio_b64 = resp.audios[0] if hasattr(resp, "audios") and resp.audios else ""
            # `audios` are base64 strings of raw audio bytes already
            if isinstance(audio_b64, bytes):
                audio_b64 = base64.b64encode(audio_b64).decode("ascii")
            return TTSResult(
                audio_b64=audio_b64,
                sample_rate=24000,
                latency_ms=int((time.time() - t0) * 1000),
            )
        except Exception as exc:
            logger.exception("TTS failed: %s", exc)
            return TTSResult(audio_b64="", sample_rate=24000, latency_ms=int((time.time() - t0) * 1000))


# --------------------------- Mock helpers ---------------------------

_MOCK_REPLIES = {
    "greeting":        "Namaste! Aarav here from Star Health. Do you have two minutes?",
    "discovery":       "Samajh aaya. Quick one — what's your age, and is anyone in the family on regular medication?",
    "discovery_ages":  "Theek hai, got it. Kisi ko regular medication chal rahi hai, ya koi pre-existing condition hai?",
    "pitch_floater":   (
        "Based on that, I'd recommend our family floater — ten lakh cover for the whole family, "
        "single sum insured, no room rent cap. It covers maternity after twenty-four months too. "
        "Shall I connect you with an advisor for the exact quote?"
    ),
    "pitch_25lakh":    (
        "For a family with senior parents — especially with diabetes — I'd suggest twenty-five lakh "
        "floater or above. It gives enough buffer for hospitalisation costs. "
        "Advisor will run the numbers. Want me to set that up?"
    ),
    "pitch_individual": (
        "For a single adult aged twenty-eight, five to ten lakh individual cover is the sweet spot. "
        "Star Health Comprehensive gives cashless access at fourteen thousand plus hospitals. "
        "Want me to connect you with an advisor for a quote?"
    ),
    "qa_pre_existing": (
        "Pre-existing conditions like diabetes have a thirty-six month waiting period in this plan. "
        "Claims after that go through standard underwriting. There is an optional rider to reduce "
        "it to one year — advisor can explain that."
    ),
    "qa_premium":      (
        "Honest answer — I cannot give an exact figure. For a family like yours the range is "
        "usually fifteen to twenty-five thousand a year. The advisor will run the actual quote. "
        "Want me to set that up?"
    ),
    "qa_claim":        (
        "Claims go through underwriting and waiting periods — the claims team makes the final call, "
        "so I cannot promise approval. Pre-existing conditions have a three-year waiting period. "
        "I can flag this for our advisor to walk you through it."
    ),
    "qa_sum_insured":  (
        "For your profile, I'd recommend ten lakh for starters. "
        "If you have senior parents, go for twenty-five lakh and above. "
        "The advisor will suggest the right number after a proper assessment."
    ),
    "handoff":         "Theek hai. Can I have your name and city so the advisor can reach you?",
    "objection_cost":  (
        "Samajh aaya. Think of it this way — ten lakh family cover costs about fifty rupees a day. "
        "That's less than a chai and samosa. What's the specific concern — premium amount, "
        "cover level, or timing?"
    ),
    "objection_probe": (
        "Theek hai, fair point. Which part feels expensive — the premium amount, the sum insured, "
        "or the timing? Let me know and I'll address it specifically."
    ),
    "guardrail_competitor": (
        "Main kisi aur company se compare nahi kar sakta — IRDAI guidelines hain. "
        "But I can have our advisor do a proper side-by-side for you. Want that?"
    ),
    "guardrail_ivf":   (
        "IVF, IUI, and all assisted reproduction treatments are not covered under this policy — "
        "it is listed as an exclusion. Cover nahi milta. "
        "Do you have other questions about what is covered?"
    ),
    "guardrail_aadhaar": (
        "I cannot collect Aadhaar or any ID over a call — that goes through a secure document "
        "upload process with the advisor. Please don't share it here."
    ),
    "guardrail_tax":   (
        "80D benefits hain is policy mein, but tax savings ka amount aapke CA se confirm karo. "
        "Main tax advice nahi de sakta — yeh CA ka kaam hai."
    ),
    "guardrail_medical_test": (
        "Medical test requirements depend on age and health profile — main phone pe confirm "
        "nahi kar sakta. Advisor will tell you exactly what's needed after reviewing your details."
    ),
    "guardrail_discount": (
        "Premium rates are IRDAI-regulated — main koi special deal ya discount arrange nahi kar "
        "sakta. Jo rate hai woh standard hai across all channels."
    ),
    "guardrail_renewal": (
        "Lifelong renewability is a policy feature — as long as premiums are paid on time and "
        "policy terms are met. Main personally guarantee nahi kar sakta, but the policy document "
        "commits to this. Advisor can walk you through the terms."
    ),
    "guardrail_jailbreak": (
        "Haan bhai, I'm Aarav — Star Health advisor. Main aapki insurance ke baare mein "
        "help karna chahta hoon. Kya aapke paas koi health cover hai abhi?"
    ),
    "redirect_offtopic": (
        "Ha ha, cricket toh main follow karta hoon, but abhi insurance pe focus karte hain. "
        "Aapko health cover ke baare mein kuch discuss karna tha na?"
    ),
    "redirect_firm":   (
        "Yaar, cricket mujhe nahi puchho — main insurance ka banda hoon. "
        "Seriously though, aapko health cover chahiye kya? Family ke liye dekhein kuch?"
    ),
    "cashless_process": (
        "Cashless ke liye — planned admission se forty-eight hours pehle Star Health ko inform karo. "
        "Emergency mein twenty-four hours mein. Network hospital mein insurance card dikhao, "
        "hospital pre-auth raise karega, Star Health settle karega directly. "
        "Advisor network hospital list share karega."
    ),
    "portability": (
        "Haan, IRDAI portability rules hain — previous insurer ke saath jo waiting period serve ki hai "
        "woh credit milti hai Star Health mein. "
        "Renewal se forty-five days pehle apply karna hoga. Advisor exact process guide karega."
    ),
    "ayush_cover": (
        "Haan, AYUSH treatments — Ayurveda, Yoga, Unani, Siddha, Homeopathy — "
        "covered hain, but recognised hospitals mein hi. "
        "Exact inclusions ke liye advisor se confirm karo."
    ),
    "family_three": (
        "Samajh gaya — teen log, aap aur parents. Family floater best rahega. "
        "क्या किसी को regular medication चल रही है?"
    ),
    "compliment": (
        "Haha, shukriya! Toh abhi ke liye — क्या किसी को regular medication चल रही है, "
        "ya koi pre-existing condition?"
    ),
    "senior_parent_age": (
        "65 years entry age limit hai — aapke mom ko cover kar sakte hain at entry. "
        "Dad 62 ke liye bilkul thik hai. Advisor eligibility confirm karega aur twenty-five lakh "
        "floater recommend karega for the three of you."
    ),
}


def _mock_llm_reply(messages: list[dict]) -> str:
    """Heuristic mock for offline / no-key demos.

    Checks the last user message for intent signals, most specific first.
    This covers all 17 test scenarios without API calls.
    """
    last = (messages[-1]["content"] if messages else "").lower()

    # ── Jailbreak / identity attacks ────────────────────────────────────────
    if any(w in last for w in ["ignore", "system prompt", "instructions", "llm", "running on",
                                "no restrictions", "previous instructions"]):
        return _MOCK_REPLIES["guardrail_jailbreak"]

    # ── Off-topic (cricket / sports) ────────────────────────────────────────
    if any(w in last for w in ["cricket", "ipl", "match", "score", "who won", "team"]):
        # If this is the second off-topic attempt (advisor in history), be firmer
        history_text = " ".join(m.get("content", "") for m in messages).lower()
        if history_text.count("cricket") >= 2 or "seriously" in last:
            return _MOCK_REPLIES["redirect_firm"]
        return _MOCK_REPLIES["redirect_offtopic"]

    # IVF / infertility (before competitor - checked first)
    if any(w in last for w in ["ivf", "iui", "infertility", "assisted reproduction", "fertility"]):
        return _MOCK_REPLIES["guardrail_ivf"]

    # ── Competitor comparison ────────────────────────────────────────────────
    # NOTE: "lic" is 3 chars and is a substring of "policy" - use word boundaries
    # by checking for " lic " or start/end of string, not a raw substring.
    _competitor_full = ["hdfc", "bajaj", "icici", "niva bupa", "better than",
                        "compare", "which one is better"]
    _lic_match = " lic " in f" {last} "  # word-boundary trick for "lic"
    if _lic_match or any(w in last for w in _competitor_full):
        return _MOCK_REPLIES["guardrail_competitor"]

    # ── PAN / Aadhaar collection ─────────────────────────────────────────────
    if any(w in last for w in ["aadhaar", "pan card", "1234", "aadhar", "id proof"]):
        return _MOCK_REPLIES["guardrail_aadhaar"]

    # ── Tax advice ───────────────────────────────────────────────────────────
    if any(w in last for w in ["80c", "80d", "tax", "tax saving", "deduction"]):
        return _MOCK_REPLIES["guardrail_tax"]

    # ── Medical test ─────────────────────────────────────────────────────────
    if any(w in last for w in ["medical test", "test nahi", "no test", "direct le", "koi test"]):
        return _MOCK_REPLIES["guardrail_medical_test"]

    # ── Discount ─────────────────────────────────────────────────────────────
    if any(w in last for w in ["discount", "special deal", "special rate", "offer"]):
        return _MOCK_REPLIES["guardrail_discount"]

    # ── Guaranteed renewal ───────────────────────────────────────────────────
    if any(w in last for w in ["guarantee", "always renew", "guaranteed renewal", "guarantee kar"]):
        return _MOCK_REPLIES["guardrail_renewal"]

    # ── Cashless / claim process ─────────────────────────────────────────────
    if any(w in last for w in ["cashless", "how does claim work", "hospital mein kya",
                                "how to claim", "claim process", "go to hospital"]):
        return _MOCK_REPLIES["cashless_process"]

    # ── Portability ──────────────────────────────────────────────────────────
    if any(w in last for w in ["portability", "switch", "port", "existing policy",
                                "pehle se", "already have", "transfer"]):
        return _MOCK_REPLIES["portability"]

    # ── AYUSH / alternative medicine ─────────────────────────────────────────
    if any(w in last for w in ["ayush", "ayurveda", "homeopathy", "yoga", "unani",
                                "alternative", "naturopathy"]):
        return _MOCK_REPLIES["ayush_cover"]

    # ── Compliment / casual ───────────────────────────────────────────────────
    if any(w in last for w in ["wah", "nice", "great point", "straight to the point",
                                "i like that", "well said", "good one"]):
        return _MOCK_REPLIES["compliment"]

    # ── Senior parent age at limit ────────────────────────────────────────────
    if any(w in last for w in ["65-year", "65 year", "65 saal", "can my parent",
                                "can my 65", "include my"]):
        return _MOCK_REPLIES["senior_parent_age"]

    # ── Three-person family (single + parents) ────────────────────────────────
    if any(w in last for w in ["three of us", "teen log", "me and my parents",
                                "all three", "hum teeno", "parents ke saath"]):
        return _MOCK_REPLIES["family_three"]

    # ── Parents with conditions → pitch 25 lakh (before generic PED check) ──
    # When user mentions parents + a health condition, it's a pitch opportunity,
    # not just a waiting-period Q - we recommend 25 lakh+ floater first.
    if any(w in last for w in ["parents", "mummy", "papa", "maa", "pitaji"]):
        return _MOCK_REPLIES["pitch_25lakh"]

    # ── Pre-existing / waiting period ────────────────────────────────────────
    if any(w in last for w in ["diabetes", "pre-existing", "preexisting", "bp", "blood pressure",
                                "waiting period", "koi waiting", "no waiting", "kab se cover"]):
        return _MOCK_REPLIES["qa_pre_existing"]

    # ── Claim approval ───────────────────────────────────────────────────────
    if any(w in last for w in ["claim", "approve", "approved", "settle", "heart surgery",
                                "guarantee it", "yes or no"]):
        return _MOCK_REPLIES["qa_claim"]

    # ── Premium / cost (must come AFTER claim/discount checks) ──────────────
    if any(w in last for w in ["premium kitna", "exact premium", "exactly premium",
                                "exact figure", "just tell me the number",
                                "no ranges", "kitna hoga"]):
        return _MOCK_REPLIES["qa_premium"]
    if any(w in last for w in ["premium", "cost", "price", "kitna", "kitne"]):
        return _MOCK_REPLIES["qa_premium"]

    # ── Sum insured / recommendation ─────────────────────────────────────────
    if any(w in last for w in ["how much cover", "sum insured", "kitna cover", "what cover",
                                "cover lena chahiye", "what sum", "what do you recommend",
                                "recommend", "suggest", "which plan"]):
        return _MOCK_REPLIES["qa_sum_insured"]

    # ── Handoff / setup call ─────────────────────────────────────────────────
    if any(w in last for w in ["set up", "setup", "call kar do", "kar do call", "what's next",
                                "sounds good", "okay set", "advisor", "human agent", "call back"]):
        return _MOCK_REPLIES["handoff"]

    # ── Objection handling ───────────────────────────────────────────────────
    # First objection ("expensive" language) → reframe as daily cost
    if any(w in last for w in ["expensive", "bahut zyada", "bahut mehnga", "too costly"]):
        return _MOCK_REPLIES["objection_cost"]
    # Second / persistent objection → probe what specifically
    if any(w in last for w in ["still feels", "still too", "too much", "feels too"]):
        return _MOCK_REPLIES["objection_probe"]

    # Pitch signals - specific profiles
    if any(w in last for w in ["parents", "mummy", "papa", "senior", "65", "62", "60"]):
        return _MOCK_REPLIES["pitch_25lakh"]
    if any(w in last for w in ["single", "alone", "just me", "individual", "28 saal",
                                "i'm 28", "looking for basic"]):
        return _MOCK_REPLIES["pitch_individual"]
    if any(w in last for w in ["low cover", "sirf 3 lakh", "company ka insurance",
                                "floater", "family of four", "family cover",
                                "health policy", "health plan", "insurance plan",
                                "unka bhi", "cover chahiye", "same policy"]):
        return _MOCK_REPLIES["pitch_floater"]

    # Discovery signals - ages / family info
    if any(w in last for w in ["wife", "husband", "kids", "children", "married",
                                "bachche", "ghar mein", "family", "log hain"]):
        return _MOCK_REPLIES["discovery_ages"]
    if any(w in last for w in ["years old", "saal ka", "saal ki", "my name", "city",
                                "age", "teen log", "income", "lakh", "earning"]):
        return _MOCK_REPLIES["discovery"]

    # ── Greetings ────────────────────────────────────────────────────────────
    if any(w in last for w in ["hello", "namaste", "hey", "haan", "yes", "okay", "theek"]):
        return _MOCK_REPLIES["discovery"]

    return _MOCK_REPLIES["discovery"]
