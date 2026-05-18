# Email to Anand — DRAFT (do not send without Yash's approval)

> Tone target: informed, concise, product-aware. Two questions max. Reads like a candidate who already knows the answer to most of his own questions.

---

**Subject:** Sarvam CS Round 2 — quick alignment before I lock the demo

Hi Anand,

Quick note before I finalise the submission for Monday.

For Part 1 (Option 2 — Insurance Sales Voicebot), I looked at Sarvam's surface and there are three honest routes: Samvaad (enterprise, sales-gated — what I'd recommend to a real customer), the developer dashboard (great for prototyping but not a full agent builder), and Sarvam's documented voice-agent pattern (Saaras → Sarvam-30B → Bulbul via the LiveKit / Pipecat plugins, or direct SDK). I'm building option three — same architecture Sarvam's developer customers ship to production — with an insurance-brochure RAG layer, browser voice via WebRTC, and a parallel `livekit_agent.py` showing the production migration. The report will frame Samvaad as the route I'd take a real Bajaj / HDFC Life pilot down.

Two questions where your steer would sharpen things:

1. For evaluation, what's the bigger signal — a polished working demo, or the architecture-and-CS-thinking depth in the writeup? I'm prioritising the demo but I want to be sure.
2. Is browser-WebRTC voice acceptable for the demo, or are you expecting a callable phone number (i.e., Twilio / Exotel + Sarvam)? I've scoped to browser to avoid telephony spend, but happy to wire SIP if it matters.

Defaulting to multilingual (English + Hinglish + Hindi via Saaras auto-detect), document-grounded answers with explicit escalation for premium / underwriting / tax — let me know if any of that should change.

Will send the final package on Monday morning.

Thanks,
Yashwardhan

---

## Why these two questions and no more

- **Question 1** lets him tell me whether to over-invest in the demo or the writeup. Either way I'm shipping both, but the marginal hour goes to whichever he says.
- **Question 2** is the only question that could cause real wasted work — building telephony when he wanted browser, or vice versa.

## Things I deliberately did NOT ask

- "What's Samvaad?" / "Should I use the Sarvam platform?" — answering this in the email itself shows I already explored it.
- "What languages should it support?" — Sarvam is the Indic-AI company; defaulting to multilingual is the right read.
- "Should answers be document-grounded?" — yes, obviously, for an insurance product.
- "Should I use Sarvam APIs?" — yes, obviously, for a Sarvam assignment.
- "Will I get an API key from your side?" — I can self-serve via dashboard.sarvam.ai; no need to make him expense it.

## When to send

Only after Yash reviews. The email is short on purpose. If Yash wants to add personal context (background, why he wants the role), append a single paragraph above the questions — but the email's strength is brevity.

## If Anand doesn't reply in 24 hours

Don't follow up. Ship Monday regardless. The email is risk-mitigation, not blocker-resolution.
