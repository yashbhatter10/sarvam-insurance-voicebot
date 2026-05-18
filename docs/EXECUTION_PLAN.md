# Execution Plan — Sarvam CS Assignment

_Yashwardhan Bhatter · Sarvam AI Customer Success Round 2_
_Submission deadline: Monday, 18 May 2026 · 3 days to ship._

## TL;DR

- **Part 1 chosen:** Option 2 — Insurance Sales Voicebot.
- **Route chosen:** C (Hybrid). Build the agent on Sarvam APIs (Saaras v3 STT → Sarvam-30B LLM → Bulbul v3 TTS) with a browser front-end, RAG over an insurance brochure, and a production-ready `livekit_agent.py` variant. Frame Samvaad as the enterprise route I'd recommend to a real Sarvam customer.
- **Part 2:** Market-research thesis on AI in India + Sarvam's positioning, current to May 2026.
- **Deliverable:** Live local browser demo Anand can run in 60 seconds + PDF report + GitHub-ready folder.

## Why this route, not Samvaad-first

Samvaad is **contact-sales gated**, used by Tata Capital, deploys an enterprise voicebot in <24 hours via a forward-deployed engineer. You cannot self-serve build a Samvaad agent in 3 days. Attempting to "use the Sarvam UI" would mean using the developer **playground** (single-prompt LLM/TTS testing), which is not a voicebot. The honest CS answer is: "Samvaad is what I'd recommend to the customer; for this exercise I built the same agent on Sarvam's developer stack, which is the path Sarvam's own docs and cookbooks teach (LiveKit / Pipecat / SDK)." See `SARVAM_PLATFORM_ROUTE.md` for the full verified surface.

## Three-day timeline

### Day 1 — Friday 15 May (today)
- [x] Verify Sarvam platform surface (Samvaad, Arya, dashboard, models, pricing, voice-agent docs) — done.
- [ ] Yash logs into dashboard.sarvam.ai, grabs API key, takes 4 screenshots (see `SARVAM_DASHBOARD_PLAYBOOK.md`).
- [ ] Voicebot scaffold v1 working locally: mic → Saaras → Sarvam-30B → Bulbul → speaker, with RAG over the sample brochure.
- [ ] First draft of the voicebot system prompt + sample conversation tested by hand against Sarvam-30B in the playground.

### Day 2 — Saturday 16 May
- [ ] Refine voicebot: barge-in handling, repair prompts, latency display, voice/language selector, guardrails, escalation flow.
- [ ] Add `livekit_agent.py` production reference variant (40 lines, with Sarvam's documented best-practice flags).
- [ ] Write Part 2 market-research thesis (5–7 pages).
- [ ] Draft Anand email (do not send).
- [ ] Loom test recording.

### Day 3 — Sunday 17 May
- [ ] Polish the final report (HTML + PDF).
- [ ] Polish the browser UI (clean layout, transcript, latency widget, source-citation panel).
- [ ] Final dry run: fresh machine, just `.env` + `pip install` + `uvicorn` + open browser. Time it.
- [ ] Submission checklist.

### Day 4 — Monday 18 May
- [ ] Final review with Yash.
- [ ] Send to Anand.

## Success criteria (what "done well" looks like)

A Sarvam interviewer should walk away from the demo + report thinking:

1. **He gets voicebots.** He talks about latency budget in milliseconds, not just "fast". He distinguishes turn-detection from VAD. He knows barge-in is a product decision, not just a technical one.
2. **He gets Sarvam.** He knows Saaras vs Bulbul vs Sarvam-30B vs Samvaad vs Arya vs Akshar without prompting. He understands which surface a real customer would pick.
3. **He thinks like CS.** He doesn't just build — he frames "what would I tell a real Bajaj Allianz buyer?" He has analytics in the demo (containment, escalation, latency, RAG-no-answer rate).
4. **He's compliance-aware.** The bot doesn't promise claim approval, doesn't invent premiums, doesn't give tax advice. Escalation is explicit.
5. **He can ship.** The local demo works first try. The repo is clean.

## Test cases the demo must handle

1. **Happy path (English):** "Hi, I'm 35, looking for term insurance for my family." → discovery → pitch → policy Q&A → next steps.
2. **Hinglish:** "Bhai, mujhe ek health insurance chahiye, monthly premium kitna hoga?" → bot responds in Hinglish, redirects premium-quote question to "I'll have an advisor confirm — can I get your name and city?"
3. **Pure Hindi:** "Aapki policy mein claim kaise file karte hain?" → answers from the brochure, in Hindi.
4. **Compliance trap:** "Will my pre-existing diabetes claim definitely be approved?" → bot refuses to promise, cites general waiting-period language, escalates.
5. **Off-policy question:** "Tax savings under 80C with this product?" → "I'm not able to give tax advice — connecting you with an advisor."
6. **Barge-in:** user starts speaking mid-bot-response → bot stops speaking, takes the new turn.
7. **STT noise:** user mumbles, STT confidence low → bot says "Sorry, I caught 'health policy' — could you repeat the rest?"

## Risks and how we're handling them

| Risk | Mitigation |
|---|---|
| Sarvam key delayed / Yash can't sign up | Scaffold has a `mock=True` mode that returns canned responses so the architecture demo still works. |
| Browser mic permissions flaky on demo day | We have a "text-mode" fallback so Anand can type if mic fails. |
| Anand wants telephony, not browser | Frame it in the report: "Production path is Samvaad-on-telephony or LiveKit + Twilio/Exotel. Demo is browser-WebRTC for the same reason the Sarvam docs use WebRTC — telephony adds spend with no demo benefit." Do not provision a number. |
| Anand expects Hindi-first | Default the demo to English but ship a language toggle. Bulbul v3 handles all 11 IN languages. |
| Latency on local laptop is too high to feel real-time | Use Bulbul v3 streaming (WebSocket) + show the latency budget prominently in the UI so the gap from "demo latency" to "production latency" is explicit. |

## What I will and won't ask Anand

I will ask:
1. Eval weighting — working demo vs architecture thinking vs market research?
2. Browser voice acceptable or callable phone number?

I will not ask:
- "What does Sarvam Samvaad do?" — embarrassing.
- "Can I use the Sarvam UI?" — I already know the answer.
- "Should I use Sarvam APIs?" — obviously yes.
- "Should I make it multilingual?" — Sarvam is the Indic-AI company; default yes.

The email is one short message: short context, one route recommendation, two questions. See `ANAND_EMAIL.md`.
