---
title: Aarav - Star Health Insurance Voicebot
emoji: 🎙️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Aarav — Star Health Insurance Voicebot

> Sarvam AI · CS Round 2 · Yashwardhan Bhatter · May 2026

Aarav is a multilingual insurance sales voicebot that speaks Hinglish, knows the Star Health Comprehensive Insurance Policy cold, and routes customers to a human advisor — without hallucinating a single premium figure.

---

## Demo

Hosted on HuggingFace Spaces → **[yashbhatter-sarvam-insurance-voicebot.hf.space](https://yashbhatter-sarvam-insurance-voicebot.hf.space)**

Click the mic. Speak in Hindi, English, or Hinglish. Aarav handles it.

---

## Stack

| Layer | What |
|---|---|
| STT | Sarvam Saaras v3 — multilingual, Hinglish-aware |
| LLM | Gemini 2.5 Flash — 1M context, grounded by RAG |
| TTS | Sarvam Bulbul v3 — natural Indian voice |
| RAG | BM25-style retriever over the Star Health brochure (203 snippets, 17 sections) |
| Guardrails | 14 post-filter rules — script safety, compliance, no hallucination |

---

## Run locally

```bash
cp .env.example .env          # add SARVAM_API_KEY + GEMINI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --port 8000
# open http://localhost:8000
```

No keys? It falls back to mock mode — the UI and architecture still run end-to-end.

---

## What to try

- Ask about premiums for a family of four
- Say you're 68 years old (triggers senior citizen product routing + co-pay disclosure)
- Ask about pre-existing diseases, waiting periods, maternity cover
- Try asking about car insurance — Aarav declines cleanly
- The right panel shows RAG sources, latency breakdown, and session analytics live

---

## Structure

```
app/
├── main.py              FastAPI routes
├── sarvam_client.py     STT + TTS via Sarvam; LLM via Gemini
├── rag.py               Brochure retriever (BM25-ish, zero dependencies)
└── agent/
    ├── orchestrator.py  State machine + session metrics
    ├── policy.py        System prompt + 14 compliance guardrails
    └── voice_design.py  Voice + pace selection per language/gender

data/
└── sample_insurance_policy.txt   Star Health brochure (RAG corpus, 17 sections, 203 snippets)

frontend/
└── index.html           Single-page app — mic, transcript, sources, metrics
```

---

## Docs

- `docs/SUBMISSION_NOTE.md` — one-page build summary and deliberate trade-offs
- `docs/VOICE_AGENT_ARCHITECTURE.md` — block diagram + production migration path
- `docs/VOICEBOT_PRODUCT_SPEC.md` — Aarav's persona, conversation flow, guardrail design
