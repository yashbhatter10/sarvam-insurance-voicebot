# Voice Agent Architecture

## Block diagram

```
                          +--------------------------------------------------+
                          |                Browser (frontend/index.html)     |
                          |                                                  |
                          |   +---------+    +------------+   +----------+   |
                          |   |  Mic    |-->-| MediaRec.  |-->|  WS to   |   |
   user voice ----------->|   | (WebRTC)|    |  WAV blob  |   |  backend |   |
                          |   +---------+    +------------+   +----+-----+   |
                          |                                       |         |
                          |   +----------+  +-----------------+   |         |
                          |   | Speaker  |<-| <audio> stream  |<--+         |
                          |   +----------+  +-----------------+             |
                          |                                                  |
                          |   +------------------------------------------+   |
                          |   | Transcript / Latency / Citations / Metrics|   |
                          |   +------------------------------------------+   |
                          +--------------------------------------------------+
                                                  ^
                                                  | (WebSocket / SSE)
                                                  v
                          +--------------------------------------------------+
                          |            FastAPI (app/main.py)                 |
                          |                                                  |
                          |  +---------------+    +----------------------+   |
   audio blob ----------->|  | /turn handler |-->-| Orchestrator         |   |
                          |  +---------------+    | (state machine,      |   |
                          |                       |  intent, metrics)    |   |
                          |  +--------------+     +----+----------+------+   |
                          |  | Sarvam STT   |<---------+          |          |
                          |  | Saaras v3    |--+                  |          |
                          |  +--------------+  |                  |          |
                          |                    v                  v          |
                          |              +----------+      +---------------+ |
                          |              |  RAG     |      |  Gemini 2.5   | |
                          |              |  (BM25)  |----->|  Flash (LLM)  | |
                          |              +----------+      +------+--------+ |
                          |                                       |          |
                          |                              +--------v-------+  |
                          |                              | Sarvam TTS     |  |
                          |                              | Bulbul v3      |  |
                          |                              +--------+-------+  |
                          |                                       |          |
                          |   audio chunks <----------------------+          |
                          +--------------------------------------------------+
```

## Components

### `frontend/index.html`
Single-page browser app. WebRTC mic capture, simple state UI, transcript pane, source citations panel, metrics dashboard, voice/language toggles.

### `app/main.py`
FastAPI server. Two endpoints:
- `POST /turn` - one user audio blob in, bot audio (and transcript / state / sources) out. The simple demo path.
- `WS /stream` - bidirectional streaming for the production-ish path (used in the LiveKit reference variant).

### `app/agent/orchestrator.py`
State machine (Greeting / Discovery / Pitch / Q&A / Next Steps / Objection Repair / Handoff). Decides what to retrieve, what to prompt, where to log metrics.

### `app/agent/policy.py`
- `SYSTEM_PROMPT` - the full voice-agent prompt (in `app/agent/policy.py` directly).
- Guardrail post-filters: claim-promise detection, premium-quote detection, tax-advice detection. If the LLM slips, we rewrite the reply to the canonical escalation phrase.

### `app/agent/voice_design.py`
- Maps detected language to Bulbul v3 voice + pace.
- Centralizes voice config so the UI selector flows here.

### `app/sarvam_client.py`
Thin wrapper around Sarvam APIs:
- `stt(audio_bytes, language="unknown") -> (text, lang, confidence)`
- `llm(messages, stream=True) -> generator[str]`
- `tts(text, lang, voice, pace) -> bytes` (or WebSocket stream)
- `mock=True` mode for when there's no API key - returns canned audio + canned LLM responses so the architecture demo still runs.

### `app/rag.py`
- Loads `data/sample_insurance_policy.txt`.
- Splits into 203 snippets across 17 sections using a section-aware parser.
- BM25-style scoring (dependency-free - no FAISS, no sentence-transformers).
- `retrieve(query, k=3) -> list[snippet]`. Returns snippet text + section label so the UI can cite.

### `agents/livekit_agent.py`
40-line LiveKit + Sarvam plugin variant. Not part of the live demo - included as the "production migration path" exhibit.

### `data/sample_insurance_policy.txt`
Star Health Comprehensive Insurance Policy brochure - the RAG corpus. 17 sections covering eligibility, sum insured options, exclusions, riders, claim process, waiting periods, and compliance rules.

## Why this architecture is honest

- **It mirrors Sarvam's documented voice-agent pattern** (STT → LLM → TTS, with explicit turn-detection driven by STT, not VAD).
- **It uses Sarvam's actual current models** (Saaras v3, Bulbul v3) with Gemini 2.5 Flash as the LLM - hot-swappable.
- **It separates orchestration from models**, so swapping the LLM or migrating to a Samvaad managed agent is a single-file change.
- **It has a real escape hatch** - the `mock=True` mode lets us demo even if Sarvam's API has a hiccup or Yash's key isn't activated yet.
- **It surfaces metrics**, which is the CS angle. Most candidate demos don't bother.

## What a production migration looks like

1. **Move orchestration to LiveKit (or Pipecat)** - gets us proper streaming + turn-taking, drops time-to-first-audio under 500 ms, matches Samvaad benchmarks. The `agents/livekit_agent.py` file shows exactly this.
2. **Telephony via Twilio / Exotel** plugged into LiveKit SIP, or use Sarvam Samvaad-on-telephony directly.
3. **Persist conversations** to a database, surface in a CSM dashboard (the metrics we already compute become daily aggregates).
4. **Connect to the insurer's CRM** (LeadSquared, Salesforce) - Samvaad does this natively; a custom build needs a webhook layer.
5. **Eventually migrate to Samvaad** when the customer wants enterprise SLA, audit, on-prem deployment.

The demo is "month 1 of a Samvaad customer engagement, run by a CS-engineer-of-one."
