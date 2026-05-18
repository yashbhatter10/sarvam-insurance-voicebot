"""
Voice and pace selection for Aarav.

Centralised so the UI selector and the orchestrator agree on the choices.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VoiceProfile:
    voice: str  # Bulbul v3 speaker id
    pace: float  # 0.5 - 2.0
    label: str  # human-readable
    target_language_code: str


# Curated picks (not exhaustive — Bulbul v3 ships 23 male + 14 female voices)
PROFILES: dict[str, VoiceProfile] = {
    # hi-IN target: Bulbul reads romanised Hinglish words ("main", "hain", "kya") as Hindi,
    # giving correct pronunciation. en-IN target for English-only turns.
    # LLM output is always Latin/Roman script (no Devanagari) — enforced in system prompt.
    "en-IN-male": VoiceProfile(voice="shubh", pace=1.0, label="Aarav (male)", target_language_code="en-IN"),
    "en-IN-female": VoiceProfile(voice="priya", pace=1.0, label="Aarti (female)", target_language_code="en-IN"),
    "hi-IN-male": VoiceProfile(voice="shubh", pace=1.0, label="Aarav (male)", target_language_code="hi-IN"),
    "hi-IN-female": VoiceProfile(voice="priya", pace=1.0, label="Aarti (female)", target_language_code="hi-IN"),
    "ta-IN-male": VoiceProfile(voice="shubh", pace=1.0, label="Aarav (male)", target_language_code="hi-IN"),
    "bn-IN-male": VoiceProfile(voice="shubh", pace=1.0, label="Aarav (male)", target_language_code="hi-IN"),
    "mr-IN-male": VoiceProfile(voice="shubh", pace=1.0, label="Aarav (male)", target_language_code="hi-IN"),
}


def pick_profile(language_code: str, gender_pref: str = "male") -> VoiceProfile:
    """Map detected language → curated profile. Falls back to English male."""
    key = f"{language_code}-{gender_pref}"
    if key in PROFILES:
        return PROFILES[key]
    # Fallback by language only
    for k, v in PROFILES.items():
        if k.startswith(language_code):
            return v
    return PROFILES["en-IN-male"]


def slow_for_detail(profile: VoiceProfile) -> VoiceProfile:
    """When reading policy details (numbers, terms), slow the pace slightly."""
    return VoiceProfile(
        voice=profile.voice,
        pace=max(0.85, profile.pace - 0.1),
        label=profile.label,
        target_language_code=profile.target_language_code,
    )
