# Voicebot Product Spec — Insurance Sales Agent ("Aarav")

> A consultative, document-grounded insurance sales voicebot for the Indian market. Built on Sarvam's developer stack. Production migration path: Sarvam Samvaad.

## 1. Persona

**Name:** Aarav.
**Role:** Insurance advisor for ShieldCare Insurance (fictional carrier — placeholder for any HDFC Life / Bajaj Allianz / SBI Life style brand).
**Tone:** Warm, unhurried, consultative — not a tele-caller. Sounds like a junior advisor who knows the brochure cold but defers to a human for premiums and underwriting.
**What Aarav will do:** discover need, recommend the right brochure product, answer policy questions with citation, hand off cleanly.
**What Aarav will not do:** invent premiums, promise claim approval, give tax / legal / medical / investment advice, push a hard close.

## 2. Conversation flow

The flow is implemented as a state machine in `app/agent/orchestrator.py`. State transitions are driven by Sarvam-30B classifying user turns into intents.

```
1. GREETING ──→ 2. DISCOVERY ──→ 3. PITCH ──→ 4. Q&A ──→ 5. NEXT_STEPS / HANDOFF
                      ↓                 ↓        ↓             ↓
                  (objection)      (objection) (out-of-scope) (escalation)
                      └────────→ OBJECTION_REPAIR ←──┘
```

### State 1 — Greeting
- "Namaste, I'm Aarav from ShieldCare. I help families pick the right insurance cover. How can I help today?"
- Single sentence. Single question.

### State 2 — Discovery (3–5 short turns)
- Age, family situation, existing cover, primary concern (health / term / accident / family floater).
- One question at a time. No survey-style monologues.
- Acknowledge each answer before next question ("Got it — so two kids and you're 35. Anything else I should know about your health?").

### State 3 — Pitch
- Maps need → product (Family Floater Health, Term, Accident — all defined in the brochure).
- Spoken pitch: one product, one sentence why it fits, one cited feature ("ShieldCare Family Floater covers up to ₹10 lakh for a family of four — that's in line with what you mentioned").
- Does not quote a specific premium. Routes that to advisor handoff.

### State 4 — Policy Q&A
- All answers grounded in the brochure (retrieved via RAG).
- When the brochure doesn't cover a question, the bot says so explicitly: *"The brochure doesn't cover that specifically — I'll flag it for the advisor."*
- Each factual claim should be traceable to a brochure snippet (the UI shows the cited source).

### State 5 — Next steps / handoff
- "Should I set up a 10-minute call with an advisor to confirm the premium and walk through underwriting?"
- Captures name + city + best time. Hands off.

### Objection repair (any state)
- "I need to think about it" → "Of course — would it help if I sent the brochure summary to your WhatsApp first?"
- "It's too expensive" → "Premium varies by age and history — the advisor will run the actual quote, but families like yours typically see ₹X-Y range. Want me to set that up?"

## 3. Voice-AI depth — what the spec covers

### 3.1 Latency budget (target: <1.2 sec from end-of-speech to first audio)
| Stage | Target | Sarvam capability |
|---|---|---|
| End-of-speech detection | 50–100 ms | Sarvam STT plugin emits start/end-of-speech events; `min_endpointing_delay=0.07` in LiveKit. |
| STT (streaming Saaras v3) | 150–250 ms | ~70 ms processing latency; WebSocket streaming. |
| Retrieval (RAG over brochure) | 50–150 ms | Local FAISS / cosine over 30-snippet brochure — sub-100 ms easy. |
| LLM first-token (Sarvam-30B) | 300–500 ms | Streaming `chat.completions.create`. |
| TTS first-audio (Bulbul v3) | 200–400 ms | WebSocket streaming; 24 kHz output. |
| **Total time-to-first-audio** | **~750–1300 ms** | Samvaad benchmark: <500 ms. We are within 2× on dev stack — acceptable for demo, callout in report. |

**Streaming vs non-streaming trade-off:** The browser demo uses the simple non-streaming path for clarity (REST). The `livekit_agent.py` reference uses streaming end-to-end via WebSocket — that's the production migration story.

### 3.2 Turn-taking
- **No VAD on AgentSession** (per Sarvam's docs — Sarvam STT handles VAD internally).
- **`turn_detection="stt"`** — turn detection is driven by STT's start/end-of-speech signals, not a separate VAD model.
- **`flush_signal=True`** on STT — clean segmentation between user turns.

### 3.3 Barge-in / interruption
- While Aarav is speaking, the mic stays open.
- A new STT start-of-speech event during TTS playback → stop the current audio buffer, cancel pending TTS chunks, treat new utterance as the next user turn.
- Implementation: front-end pauses the `<audio>` element; back-end cancels the pending generator.
- We do not implement "polite interrupt only" — pure barge-in is more natural for sales calls in India.

### 3.4 Silence / no-speech handling
- After 3 seconds of silence post-bot-response, re-prompt softly: *"Did I lose you there — should I repeat that?"*
- After 6 seconds, ask once more: *"Want me to call back later?"*
- After 10 seconds, end gracefully and offer WhatsApp follow-up.

### 3.5 STT-uncertainty repair
- Sarvam STT returns confidence; under threshold (~0.7), Aarav repairs:
  - "I caught 'family floater' but the second part wasn't clear — could you say it again?"
- Avoids the failure mode of "the bot confidently answered the wrong question."

### 3.6 Voice selection (Bulbul v3 picks)
- **English / Hinglish default:** `anand` — warm, mid-pitch male, sounds 30s, not too corporate.
- **Hindi:** `anand` again — consistent character across languages.
- **Female option for switch:** `priya` — calm, neutral.
- **Pace:** 1.0 default. Drop to 0.9 for policy-detail explanation (helps users follow numbers).
- Voice and pace are exposed in the UI so Anand can flip mid-demo.

### 3.7 Multilingual / Hinglish
- STT mode: `saaras:v3` with `language="unknown"` — auto-detects.
- LLM gets `detected_language` in the prompt prefix so Sarvam-30B responds in the same register.
- Bulbul `target_language_code` is set to the detected language; for Hinglish the practical choice is `hi-IN` with English tokens preserved (Bulbul handles code-mix natively).

## 4. Compliance & trust (insurance-specific guardrails)

| Hard rule | Why | Behavior |
|---|---|---|
| Never quote a final premium | Premium depends on age, health, sum assured, riders — none of which a sales pitch can know reliably. | "The advisor will run the actual quote — typically in the ₹X–Y range for someone your age." |
| Never promise claim approval | Claims are subject to underwriting, waiting periods, exclusions. Promising approval = IRDAI mis-selling. | "Claims are subject to the waiting period and underwriting — I can show you what the brochure says, but the claims team makes the final call." |
| Never hide exclusions on direct ask | Mis-selling under IRDAI guidelines. | If the brochure has an exclusion list, Aarav reads relevant exclusions when the user asks "what's not covered". |
| No tax / legal / medical / investment advice | Out of scope for an insurance sales agent. | "I can't advise on tax — your CA or our advisor can confirm 80D / 80C." |
| No final purchase | Mis-selling protection. | Always routes to advisor before purchase. |

Citations: every factual claim in the policy-Q&A state is grounded in a brochure snippet (shown in the UI's "Source" panel).

## 5. Customer-success / analytics — surfaced in the UI

The demo's right-side panel shows real metrics (these are what a CSM would track for Samvaad customers):

- **Containment rate** — % of conversations Aarav handled end-to-end without escalation. Target: >65%.
- **Escalation reasons** — bar chart of top 5 reasons (premium quote, underwriting, claim-likelihood question, etc.).
- **Latency distribution** — p50, p95, p99 of time-to-first-audio across the session.
- **Drop-off state** — which state did the user drop off at most (greeting / discovery / pitch / Q&A / handoff)?
- **Objection categories** — captured per turn.
- **RAG no-answer rate** — % of policy Q&A where retrieval returned no useful snippet → tells the customer "your brochure has gaps."
- **Language distribution** — auto-detected per turn.
- **STT correction rate** — % of turns where the bot asked the user to repeat.
- **Barge-in frequency** — how often the user interrupted.
- **Compliance refusals** — count of refused turns (e.g. tax advice, claim promise).

These are the same metrics a Samvaad CSM would walk a Bajaj/HDFC Life pilot through after week 1. Showing them in the demo is the CS signal.

## 6. Out of scope for this demo (but stated in the report)

- Outbound dialer / Twilio / Exotel integration (production path).
- CRM write-back (LeadSquared / Salesforce — production path).
- WhatsApp follow-up flow (Samvaad supports this natively).
- Persistent memory across calls (Samvaad does this; demo is in-session only).
- Fine-tuning the LLM on a carrier's product catalog (production decision, not demo material).
