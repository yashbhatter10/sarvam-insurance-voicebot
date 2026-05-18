# Aarav — Sarvam Insurance Sales Voicebot

> CS Round 2 assignment — Yashwardhan Bhatter, May 2026.
> Built on Sarvam's developer stack (Saaras v3 STT · Sarvam-M LLM · Bulbul v3 TTS).
> A consultative, document-grounded insurance sales voicebot for ShieldCare Insurance.

## Why this build, not Samvaad

Sarvam offers three honest routes for a voicebot: **Samvaad** (the enterprise platform — contact-sales-gated, this is what I would recommend to a real Sarvam customer like HDFC Life), the **dashboard playground** (great for testing models but not a full agent builder), and the **developer stack** (Sarvam APIs orchestrated via LiveKit/Pipecat/SDK — what Sarvam's own cookbooks teach). I picked the third because it matches a 3-day candidate exercise and demonstrates I can ship on the same pattern Sarvam's developer customers use. See `docs/SARVAM_PLATFORM_ROUTE.md` for the full reasoning.

The custom browser scaffold here is the live demo. The parallel `agents/livekit_agent.py` shows the production-migration path with Sarvam's documented best-practice flags applied.

## Run the demo

```bash
# 1. Get a Sarvam API key (₹1,000 free credits, never expire)
#    https://dashboard.sarvam.ai → API Keys → create

# 2. Configure
cp .env.example .env
# edit .env and set SARVAM_API_KEY=sk_...

# 3. Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4. Run
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 5. Open
open http://127.0.0.1:8000/
```

Without a key, the scaffold falls back to **mock mode** so the UI/architecture demo still runs end-to-end.

## What's in the box

```
sarvam-insurance-voicebot/
├── README.md                          (this file)
├── requirements.txt                   FastAPI + sarvamai SDK
├── .env.example                       Key template
│
├── docs/
│   ├── SARVAM_PLATFORM_ROUTE.md       Verified surface (Samvaad / dashboard / dev stack)
│   ├── SARVAM_DASHBOARD_PLAYBOOK.md   15-min dashboard tour for Yash
│   ├── EXECUTION_PLAN.md              Route decision + 3-day timeline + risks
│   ├── VOICEBOT_PRODUCT_SPEC.md       Aarav persona, flow, latency budget, guardrails, metrics
│   ├── VOICEBOT_PROMPT.md             The system prompt and why it's voice-specific
│   ├── VOICE_AGENT_ARCHITECTURE.md    Block diagram + production migration path
│   ├── GEMINI_ADVERSARIAL_TEST_PROMPT.md  20-persona adversarial eval prompt for AI Studio
│   ├── ANAND_EMAIL.md                 Draft (do NOT send without approval)
│   └── SUBMISSION_CHECKLIST.md        What to send Monday and what to say in the interview
│
├── reports/
│   ├── sarvam-assignment-report.html  Full Part 1 + Part 2 report
│   └── sarvam-assignment-report.pdf   Print-ready PDF version
│
├── frontend/index.html                Single-page browser app (mic, transcript, sources, metrics)
│
├── app/                               FastAPI scaffold
│   ├── main.py                        Routes
│   ├── sarvam_client.py               STT/LLM/TTS wrapper, mock fallback
│   ├── rag.py                         Brochure RAG (BM25-ish, dependency-free)
│   └── agent/
│       ├── orchestrator.py            State machine + metrics
│       ├── policy.py                  System prompt + compliance guardrails (post-filters)
│       └── voice_design.py            Bulbul voice + pace selection
│
├── agents/
│   └── livekit_agent.py               Production-pattern variant (LiveKit + Sarvam plugin)
│
└── data/
    └── sample_insurance_policy.txt    ShieldCare brochure (RAG corpus)
```

## What the demo actually shows

| Voicebot concept | Where it shows up |
|---|---|
| **Latency budget** (STT/Retrieve/LLM/TTS) | Stacked latency bar per turn in the middle panel. |
| **Turn-taking & barge-in** | Press-and-hold mic; new audio cuts off bot mid-speech. |
| **Multilingual / Hinglish** | `language="unknown"` auto-detect on Saaras v3; same voice across English/Hindi/Hinglish. |
| **Voice design** | Voice selector in the UI (Anand / Priya / Simran). Pace slows in policy-detail state. |
| **RAG grounding** | Source snippets displayed for every policy Q&A turn. |
| **Compliance guardrails** | Post-filter rewrites for claim promises, definite premium quotes, tax / medical advice. |
| **Escalation** | Premium / underwriting / out-of-policy questions route to advisor handoff. |
| **CS analytics** | Session metrics panel: latency p50/p95, containment, escalation reasons, RAG no-answer rate, language distribution. |

## What I'd change for production

Read `docs/VOICE_AGENT_ARCHITECTURE.md` end of file. Short version: migrate to LiveKit + Sarvam plugin for streaming (cuts time-to-first-audio to <500 ms), plug in Twilio/Exotel for telephony, persist conversation memory, add CRM write-back. Or recommend the customer move to Samvaad if they want enterprise SLA and on-prem.
