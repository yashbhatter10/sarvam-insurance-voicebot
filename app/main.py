"""
FastAPI server for the insurance voicebot demo.

Run:
    uvicorn app.main:app --host 127.0.0.1 --port 8000

Open:
    http://127.0.0.1:8000/
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

# Configure logging so app-level INFO/WARNING/ERROR logs print to the Terminal.
# Without this, our sarvam_client.* and other module loggers are silent.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

from app.agent.orchestrator import Orchestrator, SessionMetrics
from app.rag import BrochureRAG
from app.sarvam_client import SarvamClient
from app.session_logger import build_session_data, get_all_sessions, log_session, send_session_email, send_startup_ping

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

_ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

app = FastAPI(title="Sarvam Insurance Voicebot - Aarav", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")

# Singletons - fine for the demo, would be a session pool in production
_sarvam = SarvamClient()
_rag = BrochureRAG()
_orchestrator = Orchestrator(_sarvam, _rag)
_sessions: dict[str, SessionMetrics] = {}

# Fire a startup ping so we know email is wired correctly the moment the Space boots
send_startup_ping()


def _get_session(session_id: str) -> SessionMetrics:
    if session_id not in _sessions:
        _sessions[session_id] = SessionMetrics(session_id=session_id)
    return _sessions[session_id]


# --------------------------- Routes ---------------------------

@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((FRONTEND / "index.html").read_text(encoding="utf-8"))


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "mock_mode": _sarvam.mock,
        "brochure_snippets": len(_rag.snippets),
        "sessions": len(_sessions),
    }


@app.post("/api/session/start")
def session_start(session_id: str = Form(...), gender_pref: str = Form("male")) -> JSONResponse:
    session = _get_session(session_id)
    payload = _orchestrator.first_greeting(session, gender_pref=gender_pref)
    return JSONResponse(payload)


@app.post("/api/turn")
async def turn(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    language_hint: str = Form("unknown"),
    gender_pref: str = Form("male"),
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
) -> JSONResponse:
    """Process one turn. Accepts either an audio blob or a text fallback."""
    session = _get_session(session_id)
    if audio is not None:
        audio_bytes = await audio.read()
    elif text:
        # Text fallback path - used for unit tests and the demo's "type instead" mode
        return await _text_turn(session, text, language_hint, gender_pref, background_tasks)
    else:
        return JSONResponse({"error": "either `audio` file or `text` field required"}, status_code=400)

    payload = _orchestrator.handle_turn(
        session, audio_bytes, language_hint=language_hint, gender_pref=gender_pref
    )
    _maybe_email_on_handoff(session, background_tasks)
    return JSONResponse(payload)


def _maybe_email_on_handoff(session: SessionMetrics, background_tasks: BackgroundTasks) -> None:
    """Fire a session email the moment the conversation reaches HANDOFF or CLOSED state.

    This runs server-side after every turn, so it does not depend on the user
    closing the tab or clicking a reset button. Guards against duplicate emails
    with a flag on the session object.
    """
    from app.agent.orchestrator import State
    if session.state not in (State.HANDOFF, State.CLOSED):
        return
    if getattr(session, "_email_sent", False):
        return  # already fired for this session
    if not session.turns:
        return
    session._email_sent = True  # type: ignore[attr-defined]
    data = build_session_data(session, ended_reason="handoff")
    log_session(data)
    background_tasks.add_task(send_session_email, data)


async def _text_turn(
    session: SessionMetrics, text: str, language_hint: str, gender_pref: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> JSONResponse:
    """Bypass STT for text-mode turns (typed input)."""
    from app.agent.orchestrator import State, TurnMetrics
    from app.agent.policy import build_messages, apply_guardrails, SYSTEM_PROMPT
    from app.agent.voice_design import pick_profile, slow_for_detail
    import time, uuid

    t_start = time.time()
    prior = session.state
    session.state = _orchestrator._next_state(session.state, text)

    t_ret = time.time()
    snippets = []
    if session.state in (State.PITCH, State.QA, State.DISCOVERY):
        # Same threshold as handle_turn - allow short conversational queries through.
        snippets = _rag.retrieve(text, k=3, min_score=1.5)
    retrieval_ms = int((time.time() - t_ret) * 1000)

    messages = build_messages(
        system_prompt=SYSTEM_PROMPT,
        history=session.history,
        user_turn=text,
        detected_language=language_hint if language_hint != "unknown" else "en-IN",
        retrieved_snippets=_rag.format_for_prompt(snippets),
    )
    t_llm = time.time()
    raw = _sarvam.llm(messages)
    llm_ms = int((time.time() - t_llm) * 1000)
    guarded = apply_guardrails(raw)
    bot_text = guarded.text

    profile = pick_profile(language_hint if language_hint != "unknown" else "en-IN", gender_pref=gender_pref)
    if session.state == State.QA:
        profile = slow_for_detail(profile)
    tts = _sarvam.tts(bot_text, language=profile.target_language_code, voice=profile.voice, pace=profile.pace)

    session.history.append({"role": "user", "content": text})
    session.history.append({"role": "assistant", "content": bot_text})

    total_ms = int((time.time() - t_start) * 1000)
    session.turns.append(
        TurnMetrics(
            turn_id=uuid.uuid4().hex[:8],
            state=session.state,
            stt_ms=0,
            retrieval_ms=retrieval_ms,
            llm_ms=llm_ms,
            tts_ms=tts.latency_ms,
            total_ms=total_ms,
            stt_confidence=1.0,
            detected_language=language_hint if language_hint != "unknown" else "en-IN",
            guardrail_triggers=guarded.triggered,
            rag_hit=bool(snippets),
        )
    )
    if guarded.triggered:
        session.escalation_reasons.extend(guarded.triggered)

    if background_tasks is not None:
        _maybe_email_on_handoff(session, background_tasks)

    return JSONResponse(
        {
            "user_text": text,
            "bot_text": bot_text,
            "audio_b64": tts.audio_b64,
            "sample_rate": tts.sample_rate,
            "language": language_hint if language_hint != "unknown" else "en-IN",
            "voice": profile.voice,
            "pace": profile.pace,
            "state_from": prior.value,
            "state_to": session.state.value,
            "sources": [{"id": s.id, "section": s.section, "text": s.short()} for s in snippets],
            "guardrails": guarded.triggered,
            "latency": {
                "stt_ms": 0,
                "retrieval_ms": retrieval_ms,
                "llm_ms": llm_ms,
                "tts_ms": tts.latency_ms,
                "total_ms": total_ms,
            },
            "metrics_so_far": session.summary(),
        }
    )


@app.get("/api/session/{session_id}/metrics")
def metrics(session_id: str) -> dict:
    if session_id not in _sessions:
        return {"error": "no such session"}
    return _sessions[session_id].summary()


@app.post("/api/session/{session_id}/reset")
def reset(session_id: str, background_tasks: BackgroundTasks) -> dict:
    session = _sessions.pop(session_id, None)
    if session and session.turns:
        data = build_session_data(session, ended_reason="reset")
        log_session(data)
        background_tasks.add_task(send_session_email, data)
    return {"ok": True}


@app.get("/api/test-email")
def test_email() -> dict:
    """Debug endpoint - fires a real email synchronously and returns the result.

    Visit /api/test-email in the browser to confirm SMTP works from this host.
    No auth required (harmless - sends to the configured NOTIFY_EMAIL only).
    """
    import os
    notify = os.getenv("NOTIFY_EMAIL", "")
    resend_key = os.getenv("RESEND_API_KEY", "")
    if not notify or not resend_key:
        return {"ok": False, "reason": "NOTIFY_EMAIL or RESEND_API_KEY not set"}

    dummy_data = {
        "session_id": "test-debug",
        "ended_at": "2026-01-01T00:00:00",
        "ended_reason": "test",
        "host": "hf-space-test",
        "turns": 1,
        "final_state": "test",
        "languages": ["en-IN"],
        "latency_p50_ms": 0,
        "latency_p95_ms": 0,
        "guardrail_triggers": [],
        "escalations": [],
        "transcript": [
            {"role": "user", "content": "This is a test conversation turn."},
            {"role": "assistant", "content": "Test reply from Aarav."},
        ],
    }
    ok = send_session_email({
        "session_id": "test-debug",
        "ended_at": "2026-01-01T00:00:00",
        "ended_reason": "test",
        "host": "hf-space-test",
        "turns": 1,
        "final_state": "test",
        "languages": ["en-IN"],
        "latency_p50_ms": 0,
        "latency_p95_ms": 0,
        "guardrail_triggers": [],
        "escalations": [],
        "transcript": [
            {"role": "user", "content": "Test turn."},
            {"role": "assistant", "content": "Test reply."},
        ],
    })
    return {"ok": ok, "sent_to": notify}


@app.get("/admin/sessions", response_class=HTMLResponse)
def admin_sessions(token: str = Query(default="")) -> HTMLResponse:
    """Admin view of all recorded sessions. Requires ADMIN_TOKEN query param."""
    if not _ADMIN_TOKEN or token != _ADMIN_TOKEN:
        return HTMLResponse("<h2>403 - invalid or missing token</h2>", status_code=403)

    sessions = get_all_sessions(limit=100)

    rows = ""
    for s in sessions:
        sid       = s.get("session_id", "?")
        ended_at  = s.get("ended_at", "—")[:16].replace("T", " ")
        reason    = s.get("ended_reason", "—")
        turns     = s.get("turns", 0)
        state     = s.get("final_state", "—")
        langs     = ", ".join(s.get("languages", [])) or "—"
        p50       = s.get("latency_p50_ms", "—")
        guards    = ", ".join(s.get("guardrail_triggers", [])) or "none"
        escs      = ", ".join(s.get("escalations", [])) or "none"
        transcript = s.get("transcript", [])

        tr_rows = ""
        for turn in transcript:
            is_bot = turn.get("role") == "assistant"
            label  = "Aarav" if is_bot else "Customer"
            color  = "#7c5cff" if is_bot else "#00d4aa"
            content = str(turn.get("content", "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            tr_rows += (
                f'<tr><td style="color:{color};font-weight:600;padding:4px 10px;'
                f'white-space:nowrap;vertical-align:top;font-size:12px;">{label}</td>'
                f'<td style="padding:4px 10px;font-size:13px;line-height:1.5;">{content}</td></tr>'
            )

        rows += f"""
<details style="margin-bottom:16px;background:#151b24;border-radius:8px;overflow:hidden;">
  <summary style="padding:12px 16px;cursor:pointer;list-style:none;display:flex;
                  gap:16px;align-items:center;flex-wrap:wrap;">
    <span style="font-weight:700;color:#e6edf3;">{ended_at}</span>
    <span style="color:#8b95a6;font-size:13px;">#{sid}</span>
    <span style="background:#1e2a3a;border-radius:4px;padding:2px 8px;
                 font-size:12px;color:#7c5cff;">{state}</span>
    <span style="color:#8b95a6;font-size:12px;">{turns} turns · {langs} · p50={p50}ms · {reason}</span>
    {"<span style='color:#ff6b6b;font-size:12px;'>⚠ " + guards + "</span>" if guards != "none" else ""}
  </summary>
  <div style="padding:12px 16px;border-top:1px solid #1e2a3a;">
    <table style="width:100%;border-collapse:collapse;">{tr_rows}</table>
  </div>
</details>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Aarav · Session Admin</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px; background: #0e1116;
         font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
         color: #e6edf3; }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  p.sub {{ color: #8b95a6; font-size: 13px; margin: 0 0 24px; }}
  details > summary::-webkit-details-marker {{ display: none; }}
</style>
</head><body>
<div style="max-width:860px;margin:0 auto;">
  <h1>Aarav · Session Admin</h1>
  <p class="sub">{len(sessions)} session(s) - newest first</p>
  {rows if rows else '<p style="color:#8b95a6;">No sessions recorded yet.</p>'}
</div>
</body></html>"""
    return HTMLResponse(html)


# --------------------------- Local entry ---------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
