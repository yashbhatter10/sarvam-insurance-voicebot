# Monday Morning Submission Checklist
**Do this in order. No skipping. Estimated total time: 55–65 minutes.**

---

## PART 1 — Before you touch anything else (5 min)

### 1.1 — Make sure the bot is working locally right now
Open Terminal, go to your project, run the server:
```
cd ~/Desktop/sarvam-insurance-voicebot
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000` in Chrome. Click "Start conversation." Speak one sentence. Confirm Aarav responds with audio. If it works → move on.

---

## PART 2 — Gmail App Password setup (5 min)
*This gives you email notifications every time Anand (or anyone) tests the bot.*

1. Go to: https://myaccount.google.com/apppasswords
   - Sign in with whatever Gmail you want to use as the sender
   - If you don't see "App passwords", you need to enable 2-Step Verification first (Settings → Security → 2-Step Verification → turn on)
2. In the App passwords page:
   - "Select app" → choose **Mail**
   - "Select device" → choose **Other** → type "Aarav Bot"
   - Click **Generate**
   - You'll get a 16-character code like `abcd efgh ijkl mnop` — copy it
3. Open the file `/Users/yashbhatter/Desktop/sarvam-insurance-voicebot/.env` in TextEdit or VS Code
4. Fill in these three lines (they're already there, just blank):
   ```
   NOTIFY_EMAIL=yashwardhanbhatter.22@micamail.in
   GMAIL_FROM=yourgmail@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```
   Replace `yourgmail@gmail.com` with your Gmail address, and paste the 16-char code.
5. Save the file. **Do NOT commit this file to Git** — it's already in `.gitignore`.

**Test it:** Run the bot locally, have a short conversation, click Reset. Within 30 seconds you should get an email with the transcript. If you get it → ✅

---

## PART 3 — Push to GitHub (15 min)

### 3.1 — Create the GitHub repo (2 min)
1. Go to https://github.com/new
2. Repository name: `sarvam-insurance-voicebot`
3. Set it to **Public** (easiest — Anand can view it without needing to log in). If you prefer private, set it to Private and after creating the repo go to Settings → Collaborators → Add anand@sarvam.ai so he can access it.
4. Do NOT initialize with README, .gitignore, or license — your project already has these
5. Click **Create repository**
6. GitHub will show you a page with commands. Keep this page open.

### 3.2 — Run these exact commands in Terminal (10 min)

Open a NEW Terminal window. Copy and paste each block one at a time:

```bash
cd ~/Desktop/sarvam-insurance-voicebot
```

```bash
git init
```

```bash
git add .
```

```bash
git status
```
**→ PAUSE HERE.** Look at the list of files. Make sure you do NOT see `.env` in the list. If you do — stop and tell Claude before continuing.

```bash
git commit -m "Initial commit — Aarav voicebot v1"
```

```bash
git branch -M main
```

Now go back to the GitHub page you kept open. Copy the line that looks like:
```
git remote add origin https://github.com/YOUR_USERNAME/sarvam-insurance-voicebot.git
```
Paste and run it in Terminal.

Then run:
```bash
git push -u origin main
```

GitHub will ask for your username + password. For password, use a GitHub **Personal Access Token** (not your GitHub login password):
- Go to https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Give it a name like "Aarav push"
- Check the `repo` scope
- Generate → copy the token
- Paste it as your "password" in Terminal

**Verify:** Go to `https://github.com/YOUR_USERNAME/sarvam-insurance-voicebot` — you should see all your files there.

**⚠️ Double-check .env is NOT there.** Click through the file list. If `.env` appears, stop immediately.

---

## PART 4 — Deploy to HuggingFace Spaces (15 min)

### 4.1 — Create the Space (3 min)
1. Go to https://huggingface.co → click your profile → "New Space"
2. Space name: `sarvam-insurance-voicebot` (or any name)
3. License: MIT
4. **SDK: Docker** ← important, don't pick Gradio or Streamlit
5. Hardware: CPU Basic (free)
6. Visibility: **Public** (so Anand can open it without logging in)
7. Click **Create Space**

### 4.2 — Check if you have a Dockerfile (1 min)
Run in Terminal:
```bash
ls ~/Desktop/sarvam-insurance-voicebot/Dockerfile
```
If you see "No such file" — run Claude now to create one before continuing.

If the file exists → continue.

### 4.3 — Push your code to HuggingFace (5 min)
HuggingFace Spaces works like a Git repo. Run these commands:

```bash
cd ~/Desktop/sarvam-insurance-voicebot
```

```bash
git remote add hf https://huggingface.co/spaces/YOUR_HF_USERNAME/sarvam-insurance-voicebot
```
(Replace YOUR_HF_USERNAME with your HuggingFace username)

```bash
git push hf main
```

HuggingFace will ask for your username + password. Use your HuggingFace login password (or a HF Access Token from https://huggingface.co/settings/tokens).

The build will start. Go to your Space URL — you'll see a "Building" status. It takes 2–5 minutes.

### 4.4 — Add secrets to HuggingFace (5 min)
*This is where you put your API keys — do NOT put them in the code or .env in Git.*

1. Go to your Space → Settings tab → "Repository secrets" section
2. Add each of these one by one (click "New secret" for each):

| Secret Name | Value |
|---|---|
| `SARVAM_API_KEY` | Your Sarvam API key from dashboard.sarvam.ai |
| `GEMINI_API_KEY` | Your Gemini API key from aistudio.google.com |
| `NOTIFY_EMAIL` | `yashbhatter10@gmail.com` |
| `GMAIL_FROM` | `yashbhatter10@gmail.com` |
| `GMAIL_APP_PASSWORD` | `pwxynydsvinebtbt` |
| `ADMIN_TOKEN` | `aarav_admin_2024` (or change to something secret) |

3. After adding all secrets, go to the Space → click the three dots (⋯) → "Restart space" to apply them.

### 4.5 — Test the live Space (5 min)
1. Wait for the status to show "Running" (green)
2. Open the Space URL: `https://huggingface.co/spaces/YOUR_HF_USERNAME/sarvam-insurance-voicebot`
3. Click "Start conversation" — Aarav should greet you in Hindi
4. Speak a few words — confirm you get a response
5. Click Reset — check your email for the session transcript

**If the Space shows an error:** Go to the "Logs" tab in the Space to read what went wrong.

---

## PART 5 — What to send to Anand (5 min)

### 5.1 — The email
Send this email (plain text is fine, or use Gmail):

---
**Subject:** Aarav — Sarvam Insurance Voicebot | Assignment Submission

Hi Anand,

Sharing the completed Sarvam Insurance Voicebot assignment.

**Live demo:** [your HuggingFace Space URL]
**GitHub repo:** [your GitHub repo URL]

**What to expect:**
- Click "Start conversation" — Aarav introduces himself in Hinglish
- Allow microphone access when the browser asks
- Speak naturally in Hindi, English, or Hinglish — auto-detected
- The right panel shows real-time analytics: latency breakdown, conversation stage, policy sources retrieved
- Try asking about premiums, pre-existing conditions, waiting periods, family cover

**Architecture highlights:**
- Sarvam Saaras v3 for STT (multilingual, Hinglish-aware)
- Gemini 2.5 Flash for conversation (typically 4–7s end-to-end: STT + LLM + TTS pipeline)
- Sarvam Bulbul v3 for TTS with Devanagari/Roman script routing
- RAG over the Star Health brochure (lightweight BM25-style retriever)
- 14 IRDAI compliance guardrails as post-filters
- Continuous VAD (voice activity detection) — no push-to-talk needed
- Full session logging with email transcript on every session end

Happy to walk through the code on a call if helpful.

Best,
Yash

---

### 5.2 — How to send it
- **Email** is the default. If Anand prefers WhatsApp, send it there.
- Send it before 9am Monday so it's the first thing he sees.
- Don't attach any files — just the two links.

---

## PART 6 — After sending (watch for these)

### Things to monitor
- **Email notifications:** Every time Anand tests the bot, you'll get an email with the full transcript. Read them — they'll tell you exactly what he said and how Aarav responded.
- **Admin view:** Open `[your-hf-space-url]/admin/sessions?token=aarav_admin_2024` to see all sessions in a dashboard.
- **HuggingFace logs:** If Anand reports it's broken, check the Logs tab on your Space immediately.

### If Anand says the bot isn't working
Most likely causes (in order):
1. **Mic permission blocked** — Chrome sometimes blocks mic on first load. Tell him to click the lock icon in the address bar → Allow microphone.
2. **Space went to sleep** — HuggingFace free tier sleeps after inactivity. The first load takes 30–60 seconds. Tell him to wait and refresh.
3. **API key expired** — Check HF secrets are still there and restart the Space.

---

## PART 7 — After submission: Security cleanup (do this within 48 hours)

The Sarvam and Gemini API keys were visible in chat history during this session. Rotate them:

1. **Sarvam key:** Go to https://dashboard.sarvam.ai → API Keys → Revoke the current key → Create new → Update in HuggingFace secrets
2. **Gemini key:** Go to https://aistudio.google.com → API Keys → Delete current → Create new → Update in HuggingFace secrets

This takes 5 minutes and protects you from any accidental credit burn.

---

## Summary: Exact order, estimated times

| Step | What | Time |
|---|---|---|
| 1 | Test bot locally | 2 min |
| 2 | Gmail App Password setup | 5 min |
| 3 | Test email notification locally | 3 min |
| 4 | Create GitHub repo | 2 min |
| 5 | Git init + push to GitHub | 10 min |
| 6 | Verify .env not on GitHub | 1 min |
| 7 | Create HuggingFace Space | 3 min |
| 8 | Push code to HuggingFace | 5 min |
| 9 | Add HF secrets | 5 min |
| 10 | Wait for Space to build | 5 min |
| 11 | Test live on HuggingFace | 5 min |
| 12 | Write and send email to Anand | 5 min |
| **Total** | | **~51 min** |

---

## ⚠️ Things that will fail silently if you skip them

- **No Dockerfile** → HuggingFace won't know how to run your app. Confirm it exists before pushing.
- **.env committed to Git** → Your API keys are public. Always check `git status` before committing.
- **Secrets not added to HF** → App will start in mock mode and Aarav won't respond with real audio.
- **Space not restarted after adding secrets** → Secrets don't take effect until restart.
- **Gmail App Password not set** → You won't know when/how Anand tests. File logs still save locally on HF, but they're ephemeral (lost on restart).
