# Sarvam Dashboard Playbook — what Yash does in 15 minutes

The point of this is twofold: (1) get an API key so the scaffold actually talks, (2) gather screenshots and dashboard facts the report can cite. Do this once, today.

## Step 1 — Sign up (3 min)

1. Open https://dashboard.sarvam.ai/ in a browser. **Use a real email** (work or personal).
2. Sign up. You should receive ₹1,000 free credits automatically. **Screenshot the credits balance.**
3. Confirm the email if prompted.

## Step 2 — Create the API key (1 min)

1. Navigate to **API Keys** in the sidebar.
2. Create a new key labelled `insurance-voicebot-demo-yashwardhan`.
3. Copy the key. Add to `.env` locally as `SARVAM_API_KEY=sk_…`. **Never commit it.**
4. **Screenshot the key list (key value redacted)** — shows you have key-level usage tracking, a thing released in October 2025.

## Step 3 — Tour the platform surface (5 min, screenshots matter)

Visit each of the following and capture a screenshot for the report:

| URL | What to capture |
|---|---|
| `dashboard.sarvam.ai/playground` (or the playground tab) | The no-code playground — test a Hindi or Hinglish prompt against Sarvam-30B. Try one TTS sample with Bulbul v3 voice "anand" or "priya". |
| `dashboard.sarvam.ai/usage` | The usage analytics page — even if it's empty after signup. |
| `dashboard.sarvam.ai/vision` (if visible) | The Sarvam Vision try page — shows Akshar/OCR. |
| `studio.sarvam.ai` | Try the dubbing or translation flow on a 30-second clip if it lets you (no purchase). |
| `akshar.sarvam.ai` | Try Akshar on a single PDF page — confirms the doc-digitisation flow. |

**What I'm checking for, write down honestly:**
- Is there an **agent builder** (named "agent", "bot", "samvaad", "voice agent", "conversational agent") visible **after login**? Yes / No / "Talk to Sales" only.
- Does the dashboard let me upload a **knowledge base document / file** for grounding? Yes / No.
- Are there any **prebuilt templates** for sales / collections / support agents? Yes / No.
- Is there a **phone-number / telephony** section, or only API + WebRTC? Note exactly.

## Step 4 — Quick API smoke test (5 min, optional but recommended)

In a terminal:

```bash
export SARVAM_API_KEY="sk_your_key"
pip install -U sarvamai

python - <<'PY'
from sarvamai import SarvamAI
c = SarvamAI(api_subscription_key="sk_your_key")  # or pulls from env
# 1. LLM
r = c.chat.completions.create(
    model="sarvam-30b",
    messages=[{"role":"user","content":"Greet a customer who is asking about a family floater health policy. One sentence."}]
)
print("LLM:", r)

# 2. TTS
audio = c.text_to_speech.convert(
    text="Namaste, main aapka insurance advisor hoon.",
    target_language_code="hi-IN",
    model="bulbul:v3",
    speaker="anand"
)
print("TTS bytes:", len(audio.audios[0]) if hasattr(audio, "audios") else "ok")
PY
```

If both calls succeed, the scaffold will work end-to-end when we plug the same key into it. If anything errors (wrong model name, wrong param), paste the error into the chat and I'll patch.

## Step 5 — Send Yash the key (don't send to anyone else)

Once the key works, set it locally in `sarvam-insurance-voicebot/.env`:

```
SARVAM_API_KEY=sk_…
```

The scaffold reads it from there. **Do not put the key in the repo, in the report, or in the email to Anand.**

## Findings to capture in a single message

Reply in chat with:
1. Did the dashboard show an agent-builder UI after login? (yes / no / "Contact Sales" only)
2. KB / document upload visible? (yes / no)
3. Any surprise that doesn't match the public docs?
4. Confirm the smoke test passed (or paste the error).

That's all I need to lock the report's "what I verified" section.
