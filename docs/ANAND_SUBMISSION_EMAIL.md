# Submission Email — Monday 19 May 2026

> This is the actual submission email, ready to send.
> Fill in [GITHUB_URL] and [HUGGINGFACE_URL] before sending.
> Attach: reports/sarvam-assignment-report.pdf

---

**To:** anand@sarvam.ai
**Subject:** CS Round 2 Submission — Aarav Insurance Voicebot (Yashwardhan Bhatter)

Hi Anand,

Submitting my Round 2 work. Three things attached / linked:

**Part 1 — Insurance Sales Voicebot (Aarav)**

Live demo: [HUGGINGFACE_URL]
GitHub: [GITHUB_URL]

Aarav is an outbound health insurance sales agent for Star Health. Built on Sarvam's developer stack — Saaras v2.5 STT, Sarvam-M + Gemini 2.5 Flash LLM, Bulbul v3 TTS. Key things it does:

- Speaks Hinglish natively; auto-detects language on every turn and switches voice language to match
- RAG over the Star Health brochure with source citations shown in the UI
- Fourteen IRDAI compliance guardrails as post-filters with canonical refusal rewrites — no premium quotes, no claim promises, no tax advice, no competitor comparisons, no ID collection over voice, and more
- Roman Hindi → Devanagari auto-correction so TTS never mispronounces Hindi words written in English script
- Continuous VAD (voice activity detection) — no push-to-talk, mic is always on and auto-sends after silence
- Full 20-persona adversarial eval prompt for Google AI Studio in the repo (`docs/GEMINI_ADVERSARIAL_TEST_PROMPT.md`)
- Session logging with email notifications and an admin transcript view (`/admin/sessions`)

**Design assumptions (documented here for transparency):**

The bot is built around a specific trigger: a prospect visits the Star Health website, browses health cover plans, and submits their contact. The voicebot then calls that person — so the conversation opens with established context ("you showed interest on our website") rather than a cold pitch, and the agent already knows the customer's name from the form submission.

A few other deliberate choices:

- *Customer name is known.* The flow assumes the name comes from the web lead (hardcoded as "Anand" for this demo; in production it's injected from the CRM at call time).
- *Right party check before recording notice.* IRDAI best practice — confirm identity first, then disclose the recording, then begin.
- *Wrong-party handling tries to convert.* If someone other than Anand answers, the bot asks if they're in the same household and attempts to pitch to them — treating them as a warm lead rather than ending the call.
- *No telephony integration.* The demo runs in a browser with Web Audio API VAD. Production would use Sarvam's Samvaad or a SIP trunk with a proper dial-out flow; the architecture is identical, only the audio I/O layer changes.
- *Brochure RAG is intentionally lightweight.* For a ~30-snippet brochure, a BM25-style overlap scorer is faster and more deterministic than sentence-transformers. The retriever swaps out in one line when Sarvam embeddings are available.
- *State machine is analytical, not conversational.* The LLM drives the natural language; the state machine (GREETING → DISCOVERY → PITCH → QA → OBJECTION → HANDOFF) only tracks analytics and pacing — it doesn't constrain what the bot can say.
- *Handoff does not re-collect the phone number.* Aarav is making the outbound call — the number was dialled from the CRM record, so it's already there. The advisor follow-up uses the same record. The bot's job at handoff is to confirm the callback time slot and optionally enrich the record with city (which the web form may not have captured).

I evaluated Samvaad carefully and it's what I'd recommend to a real Sarvam customer (HDFC Life, Bajaj, etc.) — managed telephony, enterprise SLA, on-prem option for DPDP/IRDAI. The custom scaffold here demonstrates the same underlying architecture Sarvam's own cookbooks teach, without requiring a sales engagement for a 3-day exercise.

**Part 2 — Market Thesis**

Included in the PDF report (pages 8–10) and at `docs/PART2_MARKET_THESIS.md` in the repo. Covers Sarvam's India-first positioning, the structural opportunity in regional-language voice AI, and the enterprise CS playbook I'd run to land pilots at BFSI customers.

**PDF Report**

Attached — covers both parts, architecture decisions, compliance rationale, and interview Q&A for common questions.

Happy to do a live demo call if that's helpful before a decision.

Thanks,
Yashwardhan Bhatter
yashwardhanbhatter.22@micamail.in

---

## Notes for Yash

- Fill in [GITHUB_URL] and [HUGGINGFACE_URL] from the links you get in Steps 2 and 3 of YASH_ACTION_ITEMS.md
- Attach `reports/sarvam-assignment-report.pdf` — it's already in the folder
- Send Monday morning, not Sunday night — a morning email reads more professional
- If the HF Space isn't up yet, send without the URL and add "Live URL to follow in ~30 minutes" — don't delay the email for a build
