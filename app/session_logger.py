"""
Session logging + email notification for Aarav voicebot.

Every completed session is:
  1. Written as a JSON file under logs/sessions/
  2. Emailed to NOTIFY_EMAIL via Resend API (HTTPS - works on HuggingFace Spaces)

Admin view: GET /admin/sessions?token=<ADMIN_TOKEN>
"""
from __future__ import annotations

import json
import logging
import os
import socket
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

# ── Where logs are stored ──────────────────────────────────────────────────
_BASE = Path(os.getenv("LOG_DIR", "/tmp/aarav_sessions"))
_BASE.mkdir(parents=True, exist_ok=True)

# ── Email config (from .env / HF secrets) ─────────────────────────────────
_NOTIFY_EMAIL  = os.getenv("NOTIFY_EMAIL", "")
_RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")


def log_session(session_data: dict) -> Path:
    """Persist a completed session to disk as JSON. Returns the file path."""
    session_id = session_data.get("session_id", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = _BASE / f"{ts}_{session_id}.json"
    try:
        path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Session saved → %s", path)
    except Exception as e:
        log.warning("Could not write session log: %s", e)
    return path


def send_startup_ping() -> None:
    """Fire a single test email on server boot so you know email is working."""
    if not _NOTIFY_EMAIL or not _RESEND_API_KEY:
        log.info("Startup ping skipped - NOTIFY_EMAIL or RESEND_API_KEY not set.")
        return
    _send_via_resend(
        subject="[Aarav] Space is live - email notifications active",
        html="<p>Aarav started up and email is working via Resend. You'll receive a session report after each conversation.</p>",
        plain="Aarav started up and email is working via Resend.",
    )
    log.info("Startup ping sent → %s", _NOTIFY_EMAIL)


def send_session_email(session_data: dict) -> bool:
    """Send a session transcript email via Resend. Returns True if sent."""
    if not _NOTIFY_EMAIL or not _RESEND_API_KEY:
        log.info("Email skipped - NOTIFY_EMAIL or RESEND_API_KEY not set.")
        return False
    subject, plain, html = _build_email(session_data)
    return _send_via_resend(subject=subject, html=html, plain=plain)


def _send_via_resend(*, subject: str, html: str, plain: str) -> bool:
    """Send email via Resend REST API (HTTPS - never blocked by HF Spaces)."""
    import httpx
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {_RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Aarav Voicebot <onboarding@resend.dev>",
                "to": [_NOTIFY_EMAIL],
                "subject": subject,
                "html": html,
                "text": plain,
            },
            timeout=15.0,
        )
        if resp.status_code in (200, 201):
            log.info("Email sent via Resend → %s", _NOTIFY_EMAIL)
            return True
        log.warning("Resend returned %d: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        log.error("Resend call failed: %s", e)
        return False


def get_all_sessions(limit: int = 50) -> list[dict]:
    """Read the most recent `limit` session JSON files, newest first."""
    files = sorted(_BASE.glob("*.json"), reverse=True)[:limit]
    sessions = []
    for f in files:
        try:
            sessions.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return sessions


# ── Email builders ─────────────────────────────────────────────────────────

def _build_email(s: dict) -> tuple[str, str, str]:
    session_id = s.get("session_id", "?")
    ts         = s.get("ended_at", "unknown time")
    turns      = s.get("turns", 0)
    languages  = ", ".join(s.get("languages", [])) or "—"
    state      = s.get("final_state", "—")
    p50        = s.get("latency_p50_ms", "—")
    guardrails = s.get("guardrail_triggers", [])
    escalations= s.get("escalations", [])
    transcript = s.get("transcript", [])
    host       = s.get("host", "—")

    subject = f"[Aarav] New session - {turns} turns · {state} · {ts[:16]}"

    lines = [
        f"Session: {session_id}",
        f"Time:    {ts}",
        f"Host:    {host}",
        f"Turns:   {turns}",
        f"Stage reached: {state}",
        f"Language(s): {languages}",
        f"Latency p50: {p50} ms",
        "",
    ]
    if guardrails:
        lines.append(f"Guardrails triggered: {', '.join(guardrails)}")
    if escalations:
        lines.append(f"Escalated: {', '.join(escalations)}")
    lines += ["", "── TRANSCRIPT ──", ""]
    for turn in transcript:
        role = "Customer" if turn["role"] == "user" else "Aarav   "
        lines.append(f"{role}: {turn['content']}")
    plain = "\n".join(lines)

    tr_rows = ""
    for turn in transcript:
        is_bot  = turn["role"] == "assistant"
        bg      = "#1e2a3a" if is_bot else "#12181f"
        label   = "Aarav" if is_bot else "Customer"
        color   = "#7c5cff" if is_bot else "#00d4aa"
        tr_rows += (
            f'<tr style="background:{bg};">'
            f'<td style="padding:8px 12px;color:{color};font-weight:600;'
            f'white-space:nowrap;vertical-align:top;font-size:13px;">{label}</td>'
            f'<td style="padding:8px 12px;color:#e6edf3;font-size:14px;line-height:1.5;">'
            f'{_esc(turn["content"])}</td></tr>\n'
        )

    guard_html = ""
    if guardrails:
        items = "".join(f'<li style="color:#ff6b6b;">{_esc(g)}</li>' for g in guardrails)
        guard_html = f'<p style="color:#ff6b6b;">⚠ Guardrails triggered:<ul>{items}</ul></p>'

    esc_html = ""
    if escalations:
        items = "".join(f'<li style="color:#ffb454;">{_esc(e)}</li>' for e in escalations)
        esc_html = f'<p style="color:#ffb454;">→ Routed to advisor for:<ul>{items}</ul></p>'

    html = f"""
<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#0e1116;
font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;color:#e6edf3;">
<div style="max-width:680px;margin:0 auto;">
  <h2 style="margin:0 0 4px;font-size:20px;">Aarav · Session Report</h2>
  <p style="color:#8b95a6;margin:0 0 20px;font-size:13px;">
    {_esc(ts)} &nbsp;·&nbsp; Session {_esc(session_id)} &nbsp;·&nbsp; {_esc(host)}
  </p>

  <table style="width:100%;border-collapse:collapse;background:#151b24;
                border-radius:10px;overflow:hidden;margin-bottom:20px;">
    <tr><td style="padding:8px 14px;color:#8b95a6;font-size:12px;text-transform:uppercase;letter-spacing:.07em;width:140px;">Turns</td>
        <td style="padding:8px 14px;font-weight:600;">{turns}</td></tr>
    <tr style="background:#1a2230;"><td style="padding:8px 14px;color:#8b95a6;font-size:12px;text-transform:uppercase;letter-spacing:.07em;">Stage reached</td>
        <td style="padding:8px 14px;font-weight:600;">{_esc(state)}</td></tr>
    <tr><td style="padding:8px 14px;color:#8b95a6;font-size:12px;text-transform:uppercase;letter-spacing:.07em;">Language(s)</td>
        <td style="padding:8px 14px;">{_esc(languages)}</td></tr>
    <tr style="background:#1a2230;"><td style="padding:8px 14px;color:#8b95a6;font-size:12px;text-transform:uppercase;letter-spacing:.07em;">Avg response</td>
        <td style="padding:8px 14px;">{p50} ms</td></tr>
  </table>

  {guard_html}{esc_html}

  <h3 style="font-size:13px;text-transform:uppercase;letter-spacing:.08em;
             color:#8b95a6;margin:0 0 8px;">Transcript</h3>
  <table style="width:100%;border-collapse:collapse;background:#151b24;
                border-radius:10px;overflow:hidden;">
    {tr_rows}
  </table>
</div></body></html>"""

    return subject, plain, html


def _esc(s: object) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_session_data(session, ended_reason: str = "reset") -> dict:
    """Build the dict we log + email from a SessionMetrics object."""
    summary = session.summary()
    return {
        "session_id":        session.session_id,
        "ended_at":          datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ended_reason":      ended_reason,
        "host":              _get_host(),
        "turns":             summary["turns"],
        "final_state":       summary.get("current_state", "—"),
        "languages":         summary.get("languages", []),
        "latency_p50_ms":    summary.get("latency_p50_ms"),
        "latency_p95_ms":    summary.get("latency_p95_ms"),
        "guardrail_triggers":summary.get("guardrail_triggers", []),
        "escalations":       summary.get("escalations", []),
        "transcript":        session.history,
    }


def _get_host() -> str:
    hf = os.getenv("SPACE_ID") or os.getenv("SPACE_HOST")
    if hf:
        return f"HuggingFace · {hf}"
    return socket.gethostname()
