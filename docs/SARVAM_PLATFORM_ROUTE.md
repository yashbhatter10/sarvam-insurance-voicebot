# Sarvam Platform Route — Verified Findings

_Last verified: 15 May 2026 (Yashwardhan Bhatter)_
_Sources: sarvam.ai (Samvaad, Studio, Akshar, Arya, Models, Pricing), docs.sarvam.ai (Quickstart, Changelog, LiveKit + Pipecat integration guides)._

## The headline

Sarvam offers three surfaces a customer could use to build the insurance voicebot. They are **not interchangeable**, and picking the right one is the whole assignment from a CS perspective.

| Surface | What it is | Self-serve? | Right for this assignment? |
|---|---|---|---|
| **Sarvam Samvaad** | Enterprise conversational-agent platform. Voice + WhatsApp + Web + in-app. KB, telephony, multi-agent orchestration, analytics, CRM integration. <500ms latency, 11 languages. Used by Tata Capital. | **No — Contact Sales gated.** | This is what I would recommend to a real Sarvam customer (Bajaj/HDFC Life). Not realistic for a 3-day candidate exercise. |
| **Sarvam Developer Dashboard** (dashboard.sarvam.ai) | API key management, usage analytics, no-code playground for STT/TTS/LLM/Translate. ₹1,000 free credits on signup, never expire. | **Yes.** | Useful for testing models, getting API keys, prototyping prompts in the playground. Not a full agent-builder UI. |
| **Sarvam APIs orchestrated via LiveKit or Pipecat** | Sarvam's own *documented* path to build a real-time voice agent. Official `livekit-agents[sarvam,...]` and `pipecat-ai[...,sarvam]` plugins with documented best practices. | **Yes.** | **This is the route.** Same architecture Sarvam's developer customers ship to production. Demonstrates voice-AI depth + product familiarity in 3 days. |

## Verified Sarvam product surface (May 2026)

### Conversational / agent products
- **Sarvam Samvaad** — voice-first conversational agents for India. 11 languages, <500ms latency, runs on voice / WhatsApp / web / in-app. Built-in KB, telephony, CRM hooks, real-time analytics. Pilot in <24 hrs, prod in weeks. Contact-sales. Built on Sarvam Cloud / VPC / on-prem. Customer: Tata Capital.
- **Sarvam Arya** — enterprise AI agents platform (workflow automation: compliance, KYC, document processing, contract review, loan ops, claims). Forward-deployed engineers. **Bring-your-own-model** — supports any LLM provider, instant A/B switching. Checkpointed long-running workflows. Get-Started link points to dashboard.sarvam.ai.

### Content / document products
- **Sarvam Studio** (studio.sarvam.ai) — AI dubbing + translation for video and documents, voice cloning, layout-preserving doc translation, 11 langs. Used by PMO, NCERT, IndiaAI.
- **Sarvam Akshar** (akshar.sarvam.ai) — doc digitisation / Indic OCR, 23 languages, agent-driven corrections, visual grounding. Free to try.
- **Sarvam Indus** (indus.sarvam.ai) — separate hosted property, unverified scope.

### Models (verified current, May 2026)
- **Sarvam-105B** — flagship multilingual LLM, 128k context. ₹4 / 1M input tokens, ₹16 / 1M output. Open source under Apache 2.0 (released March 2026, Hugging Face + AIKosh).
- **Sarvam-30B** — high-performance multilingual LLM, 32k context. ₹2.5 / 1M input, ₹10 / 1M output.
- **Saaras v3** — streaming STT, 22 Indian languages, code-mixed, low-latency, ~70ms processing latency in the LiveKit plugin. Supports `transcribe / translate / verbatim / translit / codemix` modes.
- **Bulbul v3** — TTS, 11 languages, 37 voices (23 male, 14 female). ₹30 / 10K chars. Pace controls 0.5–2.0. Sample rates up to 48 kHz.
- **Sarvam Vision** — 3B VLM for doc understanding, OCR. ₹1.50 / page.
- **Sarvam Translate v1** + **Mayura v1** — translation (open-weights and managed). ₹20 / 10K chars.
- **Sarvam-M** — 24B hybrid reasoning LLM, **now marked deprecated** on the models page. Do not pitch this as the LLM choice.

### Pricing reality for this assignment
- ₹1,000 free credits on signup, never expire.
- For a 3-day demo with ~50 test calls @ 90 sec each: STT ≈ ₹37, LLM ≈ negligible, TTS ≈ ₹100. **Well within free credits.**
- No need to provision telephony — browser-based voice (WebRTC mic) is enough for a demo.

## What Sarvam itself documents as "build a voice agent"

The official docs (docs.sarvam.ai/api-reference-docs/integration) document **exactly two paths**:

### Path 1: LiveKit + Sarvam plugin (recommended for production)
- `pip install "livekit-agents[sarvam,openai,silero]" python-dotenv`
- ~40 lines of Python. Sarvam STT (Saaras v3) + LLM (OpenAI gpt-4o in the example, swappable) + Sarvam TTS (Bulbul v3).
- Best-practice flags Sarvam explicitly calls out:
  - `flush_signal=True` on STT → enables clean start/end-of-speech events
  - `turn_detection="stt"` on `AgentSession` → Sarvam plugin handles turn-taking
  - `min_endpointing_delay=0.07` → matches Sarvam STT's ~70ms processing latency
  - **Do not pass VAD** to `AgentSession` — Sarvam plugin handles VAD internally
- Auto-language detection with `language="unknown"`.
- Code-mixed (Hinglish, Tanglish) handled natively.

### Path 2: Pipecat + Sarvam services
- `pip install "pipecat-ai[daily,openai,sarvam]" python-dotenv`
- ~80 lines. Same model stack, different orchestration framework. Daily.co or WebRTC transport.

### Path 3 (not officially documented but real): direct REST/WebSocket via the `sarvamai` SDK
- `pip install -U sarvamai`
- `client.speech_to_text.transcribe(...)`, `client.text_to_speech.convert(...)`, `client.chat.completions.create(...)`.
- WebSocket support for streaming STT/TTS (released June 2025).
- Lower-level — you implement turn-taking yourself. Good for proving understanding; worse for production latency.

## What changed in the API platform in the last 12 months (changelog highlights)

- **Oct 2025** — Per-API-key usage tracking on the dashboard.
- **Sep 2025** — STT WebSocket flush signal, 8 kHz sample rate (telephony), TTS WebSocket end signal, GST invoices, flexible pricing tiers.
- **Jun 2025** — Real-time STT and TTS WebSocket (Python + JS SDKs), `sarvam-m` introduced (now deprecated), Saaras/Saarika v2.5, batch transcription alpha.
- **May 2025** — Unified developer dashboard with no-code playground (LLM, TTS, STT, Translate testing).
- **Apr 2025** — Bulbul v2, 24 kHz audio, batch ASR (20 files × 60 min), 3× faster real-time, WebSocket beta.

**Implication:** The Sarvam API surface is mature enough for production voicebots. Streaming, turn-taking, telephony sample rates, batch — all shipped. No need to invent.

## Recommendation

**Route C (Hybrid), executed as:**

1. **Primary deliverable** — a working browser-based insurance voicebot built on Sarvam APIs (Saaras v3 → Sarvam-30B → Bulbul v3), with an insurance-brochure RAG layer, demonstrating voice-AI depth (latency budget, barge-in handling, repair prompts, voice design, guardrails).
2. **Production-ready variant** — a parallel `livekit_agent.py` file showing how the same agent would deploy via LiveKit + Sarvam plugin, with Sarvam's documented best-practice flags. Not run as part of the demo — included as proof I know the production pattern.
3. **Report frames the strategic choice** — "Samvaad is the right enterprise route; for a CS-candidate exercise this is the developer-stack equivalent, which is what Sarvam's own cookbooks teach. Here's the architecture, the latency budget, the guardrails, the analytics, the production migration path."

This answers "do you understand the voice AI stack?", "do you understand Sarvam's product surface?", and "can you think like a customer?" — all three.

## Open questions only Yash can answer from inside the dashboard

These can't be verified from public docs and need a 10-minute dashboard tour (see SARVAM_DASHBOARD_PLAYBOOK.md):

1. Does the no-code playground let you save a multi-turn agent configuration, or is it one-shot only?
2. Is there any Samvaad self-serve trial behind login, or is it entirely sales-gated?
3. What's the actual rate limit on the free tier? (60 rpm per pricing page — confirm.)
4. Does the dashboard surface conversation transcripts / analytics for agents you build, or only API usage?

None of these block the build — they sharpen the report.
