"""
Session logging + email notification for Aarav voicebot.

Every completed session is:
  1. Written as a JSON file under logs/sessions/
  2. Emailed to NOTIFY_EMAIL (if GMAIL_APP_PASSWORD is set in .env)

Admin view: GET /admin/sessions?token=<ADMIN_TOKEN>
"""
from __future__ import annotations

import json
import logging
import os
import smtplib
import socket
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

log = logging.getLogger(__name__)

# ── Where logs are stored ──────────────────────────────────────────────────
# /tmp works on HuggingFace Spaces; locally falls back to project-root/logs
_BASE = Path(os.getenv("LOG_DIR", "logs")) / "sessions"
_BASE.mkdir(parents=True, exist_ok=True)


# ── Email config (from .env) ───────────────────────────────────────────────
_NOTIFY_EMAIL      = os.getenv("NOTIFY_EMAIL", "")          # who to notify
_FROM_EMAIL        = os.getenv("GMAIL_FROM", _NOTIFY_EMAIL) # sender (same Gmail account)
_GMAIL_APP_PASS    = os.getenv("GMAIL_APP_PASSWORD", "")    # 16-char app password


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


def _smtp_587(from_addr: str, password: str, recipients: list, raw: str) -> None:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as s:
        s.ehlo(); s.starttls(); s.ehlo()
        s.login(from_addr, password)
        s.sendmail(from_addr, recipients, raw)


def _smtp_465(from_addr: str, password: str, recipients: list, raw: str) -> None:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
        s.login(from_addr, password)
        s.sendmail(from_addr, recipients, raw)


def send_startup_ping() -> None:
    """Fire a single test email on server boot so you know email is working."""
    if not _NOTIFY_EMAIL or not _GMAIL_APP_PASS:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[Aarav] Space is live — email notifications active"
    msg["From"]    = f"Aarav Voicebot <{_FROM_EMAIL}>"
    msg["To"]      = _NOTIFY_EMAIL
    body = "Aarav started up and email is working. You'll receive a session report after each conversation."
    msg.attach(MIMEText(body, "plain", "utf-8"))
    for _send in [_smtp_587, _smtp_465]:
        try:
            _send(_FROM_EMAIL, _GMAIL_APP_PASS, [_NOTIFY_EMAIL], msg.as_string())
            log.info("Startup ping sent → %s", _NOTIFY_EMAIL)
            return
        except Exception as e:
            log.warning("Startup ping failed: %s", e)


def send_session_email(session_data: dict) -> bool:
    """Send a session transcript email. Returns True if sent successfully."""
    if not _NOTIFY_EMAIL or not _GMAIL_APP_PASS:
        log.info("Email notification skipped — NOTIFY_EMAIL or GMAIL_APP_PASSWORD not set.")
        return False

    subject, plain, html = _build_email(session_data)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Aarav Voicebot <{_FROM_EMAIL}>"
    msg["To"]      = _NOTIFY_EMAIL
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))

    # Try port 587 (STARTTLS) first — allowed on most cloud hosts including HF Spaces.
    # Fall back to port 465 (SSL) for environments that prefer it.
    for attempt, _send in enumerate([_smtp_587, _smtp_465]):
        try:
            _send(_FROM_EMAIL, _GMAIL_APP_PASS, [_NOTIFY_EMAIL], msg.as_string())
            log.info("Session email sent → %s (attempt %d)", _NOTIFY_EMAIL, attempt + 1)
            return True
        except Exception as e:
            log.warning("Email attempt %d failed: %s", attempt + 1, e)
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

    subject = f"[Aarav] New session — {turns} turns · {state} · {ts[:16]}"

    # Plain text
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
        lines.append(f"⚠ Guardrails triggered: {', '.join(guardrails)}")
    if escalations:
        lines.append(f"→ Escalated: {', '.join(escalations)}")
    lines += ["", "── TRANSCRIPT ──", ""]
    for turn in transcript:
        role = "Customer" if turn["role"] == "user" else "Aarav   "
        lines.append(f"{role}: {turn['content']}")
    plain = "\n".join(lines)

    # HTML
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


# ── Assemble the session_data dict to log / email ──────────────────────────

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
        "transcript":        session.history,   # list of {role, content}
    }


def _get_host() -> str:
    """Best-effort: return HuggingFace Space name or local hostname."""
    hf = os.getenv("SPACE_ID") or os.getenv("SPACE_HOST")
    if hf:
        return f"HuggingFace · {hf}"
    return socket.gethostname()
