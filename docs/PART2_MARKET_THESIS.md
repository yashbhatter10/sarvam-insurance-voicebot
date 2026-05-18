# Part 2 — Market Research Thesis: AI in India and Sarvam's Position

_Yashwardhan Bhatter · May 2026 · prepared for Sarvam AI CS Round 2_
_Current to May 2026 — sources cited inline._

## Thesis in one paragraph

India has, in 2026, made an explicit strategic bet on sovereign AI — not as protectionism, but as the only way to ensure a billion-plus Indian-language speakers get AI built for them rather than translated to them. The bet is being executed across four levers: subsidised compute (38,000+ GPUs deployed under the IndiaAI Mission at ₹150/hour for startups), funded foundation models (Sarvam selected to build the sovereign LLM, alongside 11 other organisations), a digital-public-infrastructure (DPI) playbook that AI is being grafted onto (Aadhaar/UPI/DigiLocker), and an unusually pragmatic policy stance ("regulate harms, not models"). Sarvam is the company positioned closest to the bullseye of this bet: Indic-first, voice-first, full-stack (models + APIs + applications + enterprise platform), already serving Tata Capital in production, and with an open-weights Apache 2.0 release of its 30B and 105B models in March 2026. The risks are real (execution against well-funded global incumbents, infrastructure dependency on imported GPUs, monetisation in a price-sensitive market). But the opportunity surface — a US$17B Indian AI market by 2027 with the deepest concentration of Indic-language enterprise demand — is what makes Sarvam plausibly the most consequential Indian AI company of this cycle.

## 1. Strategic imperatives for sovereign AI in India

Three reasons it matters that India build its own AI stack, in priority order:

**1.1 Language coverage is the moat that global frontier labs won't naturally close.** GPT-class models trained on web data underperform materially on Indian languages — particularly low-resource scripts (Bodo, Santali, Maithili, Sindhi, Manipuri, Kashmiri, Konkani) and on the code-mixing patterns that actually dominate Indian speech (Hinglish, Tanglish, Banglish). India has 22 scheduled languages and 1,600+ dialects. A frontier lab in San Francisco optimising for English benchmarks has no commercial reason to fix this. An Indian lab does. (Sarvam's Saaras v3 supports 22 languages; Bulbul v3 ships 11; Akshar reads 23. Frontier labs cover ~5 well.)

**1.2 Data sovereignty is becoming a real procurement criterion.** The DPDP Act (2023, in force) imposes data-residency obligations for sensitive personal data. Public-sector buyers, banking, healthcare, and large enterprises are increasingly RFP-mandating "data must not leave Indian jurisdiction." A US-hosted closed model can comply contractually but cannot comply architecturally. An India-hosted open-weight model can do both. Sarvam's "Sovereign by design — built and operated entirely in India with no offshore dependencies" pitch on the Arya page is targeting exactly this procurement reality.

**1.3 Cost-per-call is the gating factor for the 1B+ user opportunity.** OpenAI's frontier pricing translates to ~₹50-100 per voice-call-minute for a real-time agent. That doesn't work for an Indian collections call where the call itself is being made because someone is ₹2,000 overdue. Sarvam-30B at ₹2.5 per million input tokens is roughly **40-100× cheaper** than frontier models. Saaras at ₹30/hour of STT is comparable. This is the unit-economics moat that makes voice-AI viable in BFSI, citizen services, and edtech where unit economics live or die at the call-minute level.

The honest sovereign-AI counter-argument: India doesn't need to own *every* layer — it could just buy US frontier models and operate them in Indian VPCs. The counter-counter-argument is that the open-weight pivot (Sarvam-30B/105B released under Apache 2.0 in March 2026; Mistral, Llama, Qwen on the global side) has changed the math. India can now build on open weights with full inspectability, fine-tune on Indian data, and not be at the mercy of a single foreign vendor's pricing or policy changes.

## 2. Policy landscape (current to May 2026)

### 2.1 IndiaAI Mission
Approved by the Cabinet in March 2024 at a five-year outlay of **₹10,371.9 crore (~US$1.2B)**, the mission is the central plank of India's AI policy. Seven pillars: compute capacity (largest allocation at ₹4,563 cr), foundation models (₹1,971 cr), startup financing (₹1,943 cr), AI Innovation Centres, datasets platform, applications, and safe & trusted AI. Run by **IndiaAI**, an Independent Business Division under the Digital India Corporation, under MeitY oversight.

**Execution reality** (per MediaNama, April 2026): Only ₹400 cr disbursed in the first two years. ₹1,000 cr earmarked for FY27. The mission is making real moves (38,000+ GPUs deployed at subsidised ₹150/hour rates for startups; Sarvam, Gnani, Fractal, BharatGen and 8 others selected for foundation-model grants) — but at slower pace than the headline outlay suggests. This is a watch-item for any vendor selling into the public AI ecosystem.

### 2.2 Sovereign-model funding
**12 organisations** funded by IndiaAI to build foundation models, including:
- **Sarvam AI** — selected to build "India's sovereign LLM" with dedicated compute. Released Sarvam-30B and Sarvam-105B as open-weights (Apache 2.0) on Hugging Face and AIKosh in March 2026. Presented at the India AI Impact Summit 2026 in New Delhi.
- **Gnani AI** — voice + speech.
- **Fractal Analytics** — enterprise analytics + AI.
- **BharatGen** (IIT Bombay consortium) — 22+ languages, sovereign init.
- Several others not publicly named in May 2026.

### 2.3 Digital Personal Data Protection Act (DPDP)
In force. Imposes consent, purpose limitation, and data-fiduciary obligations. Cross-border data transfers permitted but subject to government negative-list. Sensitive personal data (health, financial) effectively requires Indian residency in practice for risk-averse buyers. **Direct implication for Sarvam:** Samvaad's "Sarvam Cloud / VPC / on-premise / air-gapped" deployment matrix is not just a flexibility pitch — it's the DPDP procurement story.

### 2.4 Adjacent policy
- **Digital India Bhashini** — translation-mission corpus for Indian languages, useful raw data.
- **MeitY AI Advisory (March 2024, later softened)** — required "untested AI" to seek permission before deployment; walked back after industry pushback. Indicative of a regulatory posture that's still iterating.
- **Budget 2026** allocated ₹21,632.96 cr to MeitY overall, a 17% drop from FY26.
- **No India-specific AI safety / capability cap regime** as of May 2026 — India has explicitly *not* followed EU AI Act-style ex-ante regulation. The policy direction is "regulate harms in deployment, not capability of models." That is, on net, builder-friendly.

### 2.5 NASSCOM positioning
NASSCOM's "India Generative AI Startup Landscape 2025" report argues India should build a differentiated GenAI trajectory along three axes: **agents, vernacular LLMs, and DPI-linked AI**. The NASSCOM-BCG forecast pegs Indian AI market size at **US$17B by 2027**, growing 25-35% CAGR. Indian AI talent base estimated at 420,000 employees with 15% CAGR demand growth. NASSCOM specifically calls out the AI-on-DPI thesis (Aadhaar / UPI / DigiLocker / ONDC as substrates AI agents will be built on).

## 3. The Indian AI stack — by layer

A working map of who is building what in May 2026:

### 3.1 Compute / infrastructure layer
- **IndiaAI common compute** — 38,000+ GPUs deployed via Yotta, NxtGen, Ctrls, Tata Communications, others. ₹150/hr subsidised rate for selected startups.
- **NPCI / DPI infrastructure** — Aadhaar, UPI, DigiLocker, ONDC. Not AI per se but the substrate AI agents are being built on.
- **Private hyperscalers** — AWS Mumbai/Hyderabad, Azure India, GCP. Still where most production load runs.
- **Indigenous GPU manufacturing** — early-stage (Vedanta-Foxconn collapsed; Tata Electronics fab announced but years away). India remains GPU-import-dependent.

### 3.2 Foundation-model layer
- **Sarvam** — Sarvam-30B, Sarvam-105B (open-weights), Sarvam-M (24B, deprecated), Saaras v3 (STT), Bulbul v3 (TTS), Sarvam Vision (3B VLM), Sarvam Translate, Mayura.
- **Krutrim (Ola)** — 22-language LLM, 2T+ tokens, first Indian AI unicorn (~US$1B valuation, ~US$280M committed financing).
- **BharatGen** — 22+ languages, IIT Bombay consortium, sovereign-init.
- **AI4Bharat (IIT Madras)** — non-profit, foundational Indic-language research, IndicBERT, original Saaras lineage.
- **CoRover BharatGPT** — chat-oriented.
- **Tech-Mahindra Project Indus** — separate from Sarvam Indus; some confusion in market.
- **Reliance JioBrain / Tata Communications models** — internal-use enterprise plays.

### 3.3 Speech & multimodal
- **Sarvam** (Saaras, Bulbul) — most production-mature in 2026.
- **Gnani AI** — voice agents for BFSI; IndiaAI-funded.
- **CoRover** — vernacular voicebots.
- **Skit.ai (formerly Vernacular.ai)** — voice agents, more US-pivoted now.

### 3.4 Application / vertical layer
- **BFSI** — Tata Capital (Sarvam Samvaad customer, public case study), HDFC Ergo, Bajaj Allianz, ICICI Lombard, Yes Bank — all running pilots.
- **Public services** — AI Sachiv (Panchayat services, Samvaad audio sample), citizen-services voicebots in multiple states.
- **EdTech** — Adda247, Eklavvya, BYJU's pivoted plays, ScalerEdu.
- **Healthcare** — Practo, Tata 1mg.
- **Customer support / contact centre** — Ozonetel, Knowlarity, MyOperator.

### 3.5 Tooling / platforms (where Sarvam Arya competes)
- **Sarvam Arya** — enterprise agent platform with sovereign-by-design positioning.
- **Cohere India**, **Glean**, **Tonkean**, **Cresta** — global tools landing in India.
- **Internal-build** — most large Indian banks/insurers are still hand-rolling agent platforms in 2025-26 because no enterprise tool quite fits the Indic-language requirement. This is Sarvam's biggest *enterprise* opportunity.

## 4. Sarvam's positioning

### 4.1 What Sarvam is (verified, May 2026)
- Founded 2023, Bengaluru. ~US$54M raised (Lightspeed, Peak XV, Khosla).
- Selected as the **sovereign LLM** builder under the IndiaAI Mission.
- **Five products, three layers:**
  - **Foundation models:** Sarvam-30B & Sarvam-105B (LLMs), Saaras v3 (STT), Bulbul v3 (TTS), Sarvam Vision, Sarvam Translate, Mayura.
  - **Developer platform:** dashboard.sarvam.ai — API keys, no-code playground, usage analytics. ₹1,000 free credits.
  - **Applications:** Samvaad (conversational agents), Studio (dubbing/translation), Akshar (doc digitisation), Arya (enterprise agent platform), Indus (separate property).
- **Open-source pivot:** Sarvam-30B & Sarvam-105B released Apache 2.0 in March 2026 on Hugging Face and AIKosh. Aggressive bet — gives away the model layer, monetises the platform layer.
- **SOC 2 Type II + ISO certified.**

### 4.2 Why Sarvam is positioned to win (or at least matter)

**Indic-first by design, not by translation.** Sarvam models are trained on Indic corpora and code-mixed data from day one. Bulbul v3's 37-voice library includes 14 female voices across 11 languages — orders of magnitude more native-Indian voice coverage than any global TTS provider.

**Voice-first.** The Indian conversational-AI market is voice-first in a way the US market isn't. ~80% of mass-market Indian users prefer voice over text for any non-trivial interaction (collection calls, healthcare, government services). Sarvam's Saaras+Bulbul stack is the only production-grade Indic voice stack at scale in 2026. Samvaad's <500ms latency and 100M+ conversations claim — even discounted — is a real moat against any competitor that has to build voice from scratch.

**Full-stack.** Most Indian AI companies are layer-specific (Krutrim is models, Gnani is voice agents, CoRover is bots). Sarvam goes models → APIs → applications → enterprise platform. The full-stack play has historical risk (companies that try to do everything often do nothing well) but in this market, the customers — Tata Capital, banks, government — explicitly want one vendor for the whole problem. The full-stack pitch is winning enterprise deals because the buyer doesn't want to integrate four vendors.

**Government tailwind.** Being IndiaAI's chosen sovereign-LLM builder is a procurement multiplier — every public-sector AI RFP that lists "sovereign Indian model" as a requirement is, in effect, a sole-source for Sarvam.

**Enterprise-grade from day one.** SOC 2 Type II, ISO, DPDP-aligned, VPC + on-prem deployment. This is unusual for a 2-year-old AI startup and reflects who their target buyer is — risk-averse, regulated, enterprise.

### 4.3 What Sarvam should worry about

**Foundation-model commoditisation.** If open-weight global models (Llama, Mistral, Qwen) close the Indic gap via fine-tuning on Bhashini-style corpora — and they will, eventually — Sarvam's model-layer moat compresses. The defense is to push moat upward: voice (which is harder to commoditise because it's data-and-compute heavy and demands native-speaker QA at scale), and applications (Samvaad, Arya).

**Enterprise GTM execution.** Selling to Indian BFSI and government is slow, relationship-driven, and procurement-heavy. The forward-deployed-engineer model that Samvaad and Arya pages emphasise is the right answer but it's expensive and people-bound. Scaling FDE while compute economics are still being worked out is the operational tension to watch.

**The "I'll just use ChatGPT in Hindi" buyer.** A meaningful share of Indian SMBs and prosumers will not pay for an Indic-specialised model if the price-quality gap closes on global frontier models. Sarvam's answer is unit economics (₹2.5 / 1M tokens vs ~₹100-1000 for frontier) and on-prem availability (which ChatGPT cannot offer).

**Hardware dependency.** Sarvam runs on imported GPUs, like everyone. If India's GPU supply gets squeezed (export controls, geopolitical), Sarvam's cost structure moves with it. Not a near-term risk but a strategic one.

## 5. Market size & forward look

**Top-line numbers (NASSCOM-BCG, Feb 2024 update, current to May 2026):**
- Indian AI market: **US$17B by 2027** (~30% CAGR).
- 420,000 AI workers in India; demand growing 15% CAGR.
- 1,700+ AI-focused companies / startups; ~US$2.9B in VC funding across top players in 2026.

**Where the spend actually goes:** BCG's analysis splits Indian AI spend roughly 40% BFSI, 25% IT-services internal, 15% retail/e-commerce, 10% public sector & healthcare, 10% other. **Voice + Indic-language workloads are over-indexed in BFSI** (collections, sales, claims) and **public sector** (citizen services) — the two segments where Sarvam is most credible.

**Forward-looking imperatives for Sarvam, IMO:**

1. **Productise Samvaad self-serve for mid-market.** Today's contact-sales model captures enterprise but leaves mid-market (regional NBFCs, mid-sized insurers, edtech) on the table. A self-serve Samvaad tier — even with a 14-day trial — would dramatically expand the funnel.
2. **Telephony abstraction.** Most buyers want a "Sarvam phone number" experience without integrating Twilio/Exotel themselves. Sarvam-managed SIP would close more deals.
3. **Stronger Sarvam-LLM-in-LiveKit story.** The official LiveKit cookbook still uses OpenAI gpt-4o as the LLM. As Sarvam's CS / developer-relations function matures, getting Sarvam-30B as the default in the cookbook is a high-leverage GTM move — every developer who reads the docs ends up using a Sarvam LLM by default.
4. **Vertical depth in BFSI.** A "Samvaad for Collections" pre-packaged template (with pre-built RAG over standard policy docs, pre-built escalation flows, pre-built compliance guardrails) would shorten the typical 4-6-week pilot to <2 weeks.
5. **Indic embeddings.** A native `sarvam-embed` model would let customers build Indic RAG without falling back to OpenAI/Cohere embeddings — closing the last layer where Indian developers reach for a US vendor.

## 6. So what — for a Sarvam CS hire

Customer Success at Sarvam in 2026 isn't just onboarding and retention. It's:
- **Translating buyer outcomes into Sarvam's product surface** — "you want a Hindi-Hinglish collections bot at <₹3/call → that's Samvaad on Sarvam Cloud, here's the latency budget, here's the compliance guardrail config."
- **Being the early-warning system on what's missing** — most enterprise customers in India are Sarvam's first deployment of a particular workflow; CS catches gaps before they become churn.
- **Owning the "explain Sarvam's stack to the buyer's risk team"** workflow — DPDP, SOC2, deployment modes, model-update SLAs. Heavy on artefacts.
- **Carrying expansion** — every deployed Samvaad customer is a candidate for Studio (content translation) or Arya (workflow agents). CS is the natural seller for these.

The CS role is positioned at the highest-leverage point in Sarvam's GTM right now, because the product is mature enough to deploy but the playbook for *who buys what when* is still being written. That's the role I'm applying for.

## Sources

- Sarvam product pages (Samvaad, Studio, Akshar, Arya, Models, Pricing) — sarvam.ai/products/* and sarvam.ai/api-pricing, accessed 15 May 2026
- Sarvam API docs (Quickstart, Changelog, LiveKit + Pipecat integration guides) — docs.sarvam.ai, accessed 15 May 2026
- Sarvam blog "India's sovereign LLM" — sarvam.ai/blogs/indias-sovereign-llm
- IndiaAI Mission Cabinet approval — indiaai.gov.in/news/cabinet-approves-india-ai-mission-at-an-outlay-of-rs-10-372-crore
- MediaNama: IndiaAI Mission disbursement update, April 2026
- TICE News: IndiaAI Mission FY26 spend
- Ensure IAS: IndiaAI Mission + MeitY Demand for Grants 2026-27
- Takshashila Institution: Budget analysis for India's AI priorities, Feb 2026
- Electronics for You: MeitY allocation in Budget 2026
- AICerts News: India Budget 2026 AI outlay analysis
- NASSCOM-BCG report "AI-Powered Tech Services: A Roadmap for Future Ready Firms" — indiaai.gov.in / nasscom.in / business-standard.com (Feb 2024 update)
- NASSCOM "India Generative AI Startup Landscape 2025"
- Rest of World: "India's frugal AI startups Sarvam and Krutrim build sovereign models", 2026
- IBTimes: "India's Top 10 AI Companies in 2026", Funding boom article
- PIB Press Release on Sarvam AI
- Wikipedia: Sarvam AI (cross-reference for funding and timelines)
- BharatGen: bharatgen.com
- AI4Bharat: ai4bharat.iitm.ac.in
