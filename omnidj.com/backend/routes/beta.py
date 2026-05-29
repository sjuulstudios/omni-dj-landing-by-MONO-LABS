"""POST /api/beta-signup — email signup with SQLite persistence."""
import os
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.mime.text import MIMEText

from flask import Blueprint, current_app, jsonify, request

beta_bp = Blueprint("beta", __name__)


def _send_welcome(email: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM", user or "no-reply@omnidj.com")

    if not host or not user or not password:
        print(f"[SMTP DRY RUN] welcome → {email}")
        return

    body = (
        "You are on the Omni DJ beta list.\n\n"
        "We will let you know the moment we open another batch of slots.\n\n"
        "Have a set you want to test? Just reply to this email.\n\n"
        "— Omni DJ, by MONO LABS\n"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Welcome to the Omni DJ beta"
    msg["From"] = from_addr
    msg["To"] = email

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, password)
        s.sendmail(from_addr, [email], msg.as_string())


@beta_bp.post("/beta-signup")
def beta_signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if "@" not in email or len(email) > 254:
        return jsonify({"error": "invalid email"}), 400

    ua = request.headers.get("User-Agent", "")[:512]

    con = sqlite3.connect(current_app.config["DB_PATH"])
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO beta_signups(email, user_agent, created_at) VALUES (?, ?, ?)",
            (email, ua, datetime.now(timezone.utc).isoformat()),
        )
        con.commit()
    except sqlite3.IntegrityError:
        # already on list — idempotent success
        pass
    finally:
        con.close()

    try:
        _send_welcome(email)
    except Exception as e:  # noqa: BLE001
        print(f"[beta] SMTP welcome failed: {e}")

    return jsonify({"ok": True})
