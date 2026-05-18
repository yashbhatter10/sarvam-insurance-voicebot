# Hugging Face Spaces Deployment — 20 minutes, ₹0

This is the path-to-action to turn the local FastAPI scaffold into a public URL Anand can open in his browser to talk to Aarav. Free, no credit card, persistent URL.

## Prerequisites

- You have already done these (from `YASH_ACTION_ITEMS.md`):
  - Signed up at `dashboard.sarvam.ai` and have an API key
  - Signed up at `huggingface.co` and have a write-access token
  - The scaffold runs locally and the 3 smoke-test conversations pass

## Why Hugging Face Spaces and not Render / Vercel

- HF Spaces is the only free tier with no cold-start delays (Render free spins down after 15 min of inactivity — Anand would dial in to a 30-second wake-up).
- Native Docker support means no rewriting our FastAPI scaffold as Gradio.
- The platform is built for AI demos and has WebRTC microphone access enabled by default with `secure context` (https).

## Step 1 — Create the Space (3 min)

1. Go to https://huggingface.co/new-space
2. Name: `aarav-shieldcare-insurance` (or whatever you prefer — this becomes the URL)
3. License: MIT
4. **Select Space SDK: Docker** (not Gradio, not Streamlit)
5. Docker template: **Blank**
6. Hardware: **CPU basic (free)**
7. Visibility: **Public** (Anand needs to access it without a HF login)
8. Click "Create Space"

You now have an empty Space at `https://huggingface.co/spaces/<your-username>/aarav-shieldcare-insurance`.

## Step 2 — Add the Sarvam API key as a Space secret (1 min)

1. On your Space page, click **Settings** (top right)
2. Scroll to **Repository secrets**
3. Click **Add a new secret**
4. Name: `SARVAM_API_KEY`
5. Value: paste your `sk_...` key
6. Save

The Docker container will see this as an environment variable. Do **not** commit the key to the repo.

## Step 3 — Push the code (5 min)

Hugging Face Spaces are just git repos. From the project folder on your machine:

```bash
# Clone the empty Space repo into a separate folder (so we don't mess up our main repo)
cd ~/Desktop  # or wherever you want
git clone https://huggingface.co/spaces/<your-username>/aarav-shieldcare-insurance hf-space
cd hf-space

# Copy the scaffold contents into this folder
cp -r /path/to/sarvam-insurance-voicebot/. .

# Make sure .env is NOT pushed (the secret is in HF Space settings)
echo ".env" >> .gitignore
echo ".venv/" >> .gitignore

# Commit and push
git add .
git commit -m "Initial commit — Aarav insurance voicebot"
git push
```

When prompted for credentials:
- Username: your HF username
- Password: your HF token (paste from huggingface.co/settings/tokens)

## Step 4 — Watch the build (5 min)

Go back to your Space page. You'll see "Building" at the top. The first build takes ~3-4 minutes (installing dependencies). Subsequent pushes rebuild in ~30 seconds.

Once status shows "Running", the URL `https://<your-username>-aarav-shieldcare-insurance.hf.space` is live.

## Step 5 — Test it (3 min)

1. Open the URL in Chrome on your laptop. The Aarav UI should load.
2. Click "Start conversation". Aarav should greet you in audio.
3. Hold the mic button, say "I'm 35 with two kids, looking for health cover", release. Aarav should respond.
4. Type a test question if the mic is being weird: "what is the waiting period for pre-existing conditions". Aarav should answer from the brochure.
5. The badge at the top of the page should read "Live · Sarvam APIs wired" — if it says "Mock mode", the API key wasn't picked up. Check Space secrets.

## Step 6 — Open it on your phone (2 min)

Hugging Face Spaces URLs work the same way on mobile browsers. Open the URL on your phone (on cellular, not the same WiFi as your laptop, to verify it works outside your network). The mic button should request mic permission — grant it. Talk to Aarav. If it works on your phone, it'll work for Anand.

## Step 7 — Share the URL in the submission email

Monday morning, the email to Anand opens with:

> "Here's the demo URL — open in Chrome and click the mic to talk to Aarav: `https://<your-username>-aarav-shieldcare-insurance.hf.space`"

That's the headline of the submission.

## Common Issues

**Build failed with "ModuleNotFoundError"** — A dependency is missing from `requirements.txt`. Check the build logs. Usually it's a transitive dep. Add it, push, rebuild.

**Mic permission denied** — HF Spaces serves over HTTPS so mic should work. If Chrome blocks, click the camera icon in the address bar and allow.

**Audio plays but it's choppy** — likely a network issue between HF Spaces (Europe) and India. Acceptable for a demo. Production would deploy on a Mumbai region.

**"Live · Sarvam APIs wired" never shows** — the API key isn't being picked up. Confirm the secret name is exactly `SARVAM_API_KEY` (case-sensitive). Restart the Space (Settings → Restart).

**Build times out** — HF free tier has a 30-min build limit. Our build should finish in ~4 min. If it's stuck, push an empty commit to retrigger.

**Space sleeps after inactivity** — HF free tier does sleep after 48 hours of inactivity. The Space wakes on first visit (~10 sec cold start). For Anand's evaluation window, this is fine — first visitor wakes it, subsequent visits are instant. If you want to be cautious, hit the URL once on Monday morning before sending the email.

## Optional — Keep it warm with a free uptime ping

If you want zero cold starts:

1. Sign up at https://uptimerobot.com (free)
2. Add a new monitor for your Space URL
3. Interval: 5 minutes
4. Done — the Space never sleeps.

Not necessary for the demo, but nice if you want belt-and-suspenders.

## What to verify before declaring it done

A 60-second checklist:

- [ ] URL loads in incognito (no HF login required)
- [ ] Greeting plays in audio when you click Start
- [ ] Hold-to-talk records and gets a response
- [ ] Bot refuses to quote a definite premium
- [ ] Bot refuses to promise claim approval
- [ ] Bot refuses PAN/Aadhaar request
- [ ] Switching language to Hindi via the selector produces Hindi response
- [ ] The metrics panel updates per turn
- [ ] Source citations show in the middle panel
- [ ] No console errors in browser DevTools
