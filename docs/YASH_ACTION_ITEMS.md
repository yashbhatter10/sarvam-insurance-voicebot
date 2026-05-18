# Sunday Evening — Your 30-Minute Checklist

> Submission is Monday morning. Everything below is copy-paste.
> Open a Terminal, follow the steps in order.

---

## Step 1 — Clean up the broken .git and initialize fresh (2 min)

A partial git repo was created by the AI sandbox but it's broken (permissions issue on macOS mounts). Fix it:

```bash
cd ~/Desktop/sarvam-insurance-voicebot
rm -rf .git
git init
git branch -M main
git config user.name "Yashwardhan Bhatter"
git config user.email "yashwardhanbhatter.22@micamail.in"
git add .
git status   # confirm: .env is NOT listed. If it is, stop and tell me.
git commit -m "Initial commit — Aarav voicebot for Sarvam CS Round 2 (May 2026)"
```

---

## Step 2 — Push to GitHub (5 min)

1. Go to https://github.com/new
2. Name: `sarvam-insurance-voicebot` (or `aarav-insurance-voicebot`)
3. Visibility: **Public**
4. Skip README, .gitignore, license (you already have them)
5. Click **Create repository**
6. Copy the repo URL (looks like `https://github.com/yashbhatter/sarvam-insurance-voicebot.git`)

Back in Terminal:

```bash
cd ~/Desktop/sarvam-insurance-voicebot
git remote add origin https://github.com/<your-username>/sarvam-insurance-voicebot.git
git push -u origin main
```

7. Open the repo on github.com. Confirm:
   - `.env` is **not** in the file list ✓
   - `README.md`, `app/`, `docs/`, `reports/`, `Dockerfile` are all there ✓

---

## Step 3 — Deploy to Hugging Face Spaces (10 min)

1. Go to https://huggingface.co/new-space
2. Name: `aarav-insurance-voicebot`
3. SDK: **Docker** → template: **Blank**
4. Hardware: **CPU basic (free)**
5. Visibility: **Public**
6. Click **Create Space**

Add your API keys as secrets (Settings → Repository secrets):
- `SARVAM_API_KEY` → your `sk_cnd17ia5_...` key
- `GEMINI_API_KEY` → your `AIzaSy...` key

Push the code to the Space:

```bash
cd ~/Desktop
git clone https://huggingface.co/spaces/<your-hf-username>/aarav-insurance-voicebot hf-space
cd hf-space
cp -r ../sarvam-insurance-voicebot/. .
rm -f .env        # IMPORTANT: never push real keys
git add .
git commit -m "Deploy Aarav voicebot"
git push          # Enter your HF username + token (hf_...) when prompted
```

Wait ~4 minutes for the build. When status shows **Running**, open:
`https://<your-hf-username>-aarav-insurance-voicebot.hf.space`

Quick smoke test on that URL:
- Say "Hi, I'm 35, two kids, looking for health cover" → Aarav should respond
- Type "just tell me the exact premium" → must give a range, not a number
- Say "will my diabetes claim be approved?" → must refuse to promise

---

## Step 4 — Send the submission email Monday morning (2 min)

See `docs/ANAND_SUBMISSION_EMAIL.md` — it's ready to send, just fill in the two links.

---

## If anything breaks

- Bot silent / weird accent → already fixed. Make sure `USE_MOCK=false` in `.env`.
- HuggingFace build fails → check build logs. Most likely a missing package in `requirements.txt`. Paste the error here.
- GitHub shows `.env` → run: `git rm --cached .env && git commit -m "Remove .env" && git push`
- Sarvam 429 error → you have 151 credits left, should be fine for the demo.

---

## What I'm handling

- All code is done. Tests pass 25/25.
- Adversarial eval prompt is at `docs/GEMINI_ADVERSARIAL_TEST_PROMPT.md` — paste it into AI Studio after submission if you want to stress-test further.
- Submission email is drafted and ready at `docs/ANAND_SUBMISSION_EMAIL.md`.

---

## Remember after submission

- Rotate `SARVAM_API_KEY` at dashboard.sarvam.ai (both keys were visible in this session)
- Rotate `GEMINI_API_KEY` at aistudio.google.com
