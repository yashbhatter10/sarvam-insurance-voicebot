# Submission Checklist — Monday 18 May 2026

## What goes to Anand

A single email with three things attached / linked:

1. **`reports/sarvam-assignment-report.pdf`** — the headline deliverable. ~10 pages, both Part 1 and Part 2.
2. **GitHub repo link** — push the `sarvam-insurance-voicebot/` folder to a public repo (or private repo with Anand added). `.env` must NOT be in the repo. `.env.example` should be.
3. **(Optional) Loom recording link** — 2-3 minute walkthrough of the local demo if hosting it is messy.

## Pre-flight checks (do all of these Sunday evening)

- [ ] `git status` — no `.env`, no `*.pyc`, no `.venv/` committed
- [ ] Add `.env`, `.venv/`, `__pycache__/`, `.DS_Store` to `.gitignore`
- [ ] README front-matter clean
- [ ] Run `uvicorn app.main:app --host 127.0.0.1 --port 8000` on a fresh machine (or fresh `.venv`)
- [ ] Open http://127.0.0.1:8000/ — header should say "Live · Sarvam APIs wired" if the key is set
- [ ] Click "Start conversation" — Aarav's greeting plays
- [ ] Hold-to-talk and say "I'm 35, two kids, looking for health cover" → bot responds, source citations show on the right
- [ ] Type "will my diabetes claim be approved?" → bot refuses to promise + escalates (guardrail panel updates)
- [ ] Switch language to Hindi and try "Premium kitna hoga?" → bot responds in Hindi-Hinglish + refuses to commit
- [ ] Click "Reset" → state clears
- [ ] PDF opens cleanly in Preview / Adobe / browser
- [ ] All doc links in the report resolve

## What to say in the interview if Anand asks…

### "Why didn't you use Samvaad?"
> "I looked at it carefully — Samvaad is the right route for a real Sarvam customer like Bajaj Allianz, and it's what I'd recommend in a CS engagement. But it's contact-sales-gated and there's no self-serve agent builder for a 3-day candidate exercise. So I built on the developer stack — same Sarvam models, same architecture Sarvam's cookbooks teach via LiveKit and Pipecat. The custom build lets me show I understand the voice-AI depth; the parallel `livekit_agent.py` shows I know the production migration path. If you'd prefer I rebuild this in Samvaad, I can take that as a follow-up."

### "Why browser voice, not telephony?"
> "Two reasons. One, the Sarvam docs themselves use WebRTC in the cookbook for the same reason — telephony adds spend with no demo benefit. Two, the production migration is one line: LiveKit + SIP via Twilio or Exotel, or Samvaad's managed telephony. I scoped to browser to keep the demo runnable on any laptop with a mic. Happy to wire SIP if it's a blocker."

### "Is this running locally or hosted?"
> "Local. The scaffold is intentionally one-machine: clone, `pip install`, `uvicorn`, open browser. That's a deliberate decision — I wanted Anand and anyone reviewing to be able to run it in 60 seconds, not chase a deployed URL that might break. A hosted version is a one-day move if you want it."

### "Does it support Hindi / Tamil / Bengali?"
> "Saaras v3 auto-detects across 22 Indian languages — `language='unknown'` in the STT call. The default UI exposes English, Hindi, Tamil, Bengali, Marathi. Bulbul v3 ships 11 languages with 37 voices total, so we can speak in the same language the customer is speaking. Hinglish works natively because Sarvam's models are trained on code-mixed data. The voice profile stays consistent across languages — Anand the voice answers in English, Hindi, or Hinglish without character change."

### "How does it stay compliant for an insurance product?"
> "Three layers. First, the system prompt has explicit hard rules — never quote a final premium, never promise claim approval, never give tax / medical advice. Second, post-filter guardrails on the LLM reply catch the cases where the model slips, and rewrite the reply to a canonical safe escalation. Third, every factual policy answer is grounded in a retrieved brochure snippet, shown to the user in the UI as a source citation. The orchestrator tracks `rag_no_answer_rate` — when retrieval finds nothing useful, that's surfaced to the CSM so the customer knows their KB has a gap."

### "What's the latency story?"
> "On the dev stack, time-to-first-audio is ~750-1300 ms. Samvaad benchmarks under 500. The gap is mostly that the demo is REST-first, not streaming, and runs from a laptop. The UI surfaces a per-turn stacked latency bar so the gap is honest. Production migration via LiveKit + Sarvam plugin closes it — Sarvam STT has ~70 ms processing latency, WebSocket TTS first-audio is in the 200-400 ms band, and `min_endpointing_delay=0.07` matches the STT latency exactly. The `livekit_agent.py` file in the repo shows this with the four best-practice flags Sarvam's docs call out."

### "How would you sell this to a real customer?"
> "I'd map their use-case to Sarvam's surface. For a collections agent at a regional NBFC: Samvaad on Sarvam Cloud, Bulbul Hindi-Hinglish voice, brochure RAG, Twilio for telephony, CRM write-back to LeadSquared. For a regulated insurer like HDFC Life: same but Samvaad on VPC or on-prem for DPDP and IRDAI procurement. Pricing: ₹30/hour STT, Sarvam-30B is ₹2.5/M tokens — well inside their per-call economics. Implementation in &lt;24 hours per the Samvaad pitch. The metrics panel in this demo — containment, latency p95, RAG no-answer rate, escalation reasons — is what I'd walk them through every week of the pilot."

### "What did you ship today vs what would you build next?"
> "Shipped today: voicebot scaffold with real Sarvam API integration, RAG over the insurance brochure, voice-specific prompt with sample exchanges validated by hand, conversation state machine, compliance post-filters for the five insurance bright lines, browser UI with hold-to-talk, source citations, latency budget visualisation, session metrics panel. Production-pattern LiveKit variant in the repo. Plus the 5,000-word market thesis on AI-in-India and Sarvam's position. Next would be: streaming end-to-end via WebSocket (cuts latency in half), persistent multi-call memory, CRM webhook for handoff, and a fine-tuned RAG retriever using sarvam-embed when available."

## Demo discipline

- **Open the browser tab before the call starts.** Don't fumble at the start.
- **Have the PDF open in a second window** so you can switch.
- **Don't apologise for the dev-stack latency** — name the budget, show the UI bar, explain the production path. Be matter-of-fact.
- **If something breaks live**, switch to the text-input fallback immediately. Don't try to debug.
- **Lead with the route decision**, not with the code. The route decision is the CS signal.

## What I'm NOT submitting

- A Samvaad agent (would have required sales engagement first).
- A deployed URL (local demo is the contract).
- A telephony number (would have required spend not authorised).
- Multiple "variants" of the bot — one polished version is the signal.
