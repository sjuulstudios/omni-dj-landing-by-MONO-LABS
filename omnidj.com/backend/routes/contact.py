"""POST /api/contact — role-routed contact form."""
import os
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.mime.text import MIMEText

from flask import Blueprint, current_app, jsonify, request

contact_bp = Blueprint("contact", __name__)

# Where to route by role
ROLE_INBOX = {
    "DJ": os.getenv("CONTACT_INBOX_DJ", os.getenv("CONTACT_INBOX_DEFAULT", "support@omnidj.com")),
    "Talent manager": os.getenv("CONTACT_INBOX_TALENT", os.getenv("CONTACT_INBOX_DEFAULT", "support@omnidj.com")),
    "Videographer or editor": os.getenv("CONTACT_INBOX_VIDEO", os.getenv("CONTACT_INBOX_DEFAULT", "support@omnidj.com")),
    "Event organiser": os.getenv("CONTACT_INBOX_EVENT", os.getenv("CONTACT_INBOX_DEFAULT", "support@omnidj.com")),
    "Record label": os.getenv("CONTACT_INBOX_LABEL", os.getenv("CONTACT_INBOX_DEFAULT", "support@omnidj.com")),
    "Other": os.getenv("CONTACT_INBOX_DEFAULT", "support@omnidj.com"),
}

ROLE_TAG = {
    "DJ": "[DJ]",
    "Talent manager": "[TALENT]",
    "Videographer or editor": "[VIDEO]",
    "Event organiser": "[EVENT]",
    "Record label": "[LABEL]",
    "Other": "[OTHER]",
}


def _send_email(to_addr: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM", user or "no-reply@omnidj.com")

    if not host or not user or not password:
        # In dev without SMTP configured we just log
        print(f"[SMTP DRY RUN] to={to_addr} subject={subject!r}\n{body}\n---")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, password)
        s.sendmail(from_addr, [to_addr], msg.as_string())


@contact_bp.post("/contact")
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    role = (data.get("role") or "Other").strip()
    company = (data.get("company") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or "@" not in email or not message:
        return jsonify({"error": "invalid"}), 400

    # Persist
    con = sqlite3.connect(current_app.config["DB_PATH"])
    cur = con.cursor()
    cur.execute(
        "INSERT INTO contact_messages(name, email, role, company, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, role, company, message, datetime.now(timezone.utc).isoformat()),
    )
    con.commit()
    con.close()

    # Notify
    inbox = ROLE_INBOX.get(role, ROLE_INBOX["Other"])
    tag = ROLE_TAG.get(role, "[OTHER]")
    subject = f"{tag} New contact from {name}"
    body = (
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Role: {role}\n"
        f"Company: {company}\n"
        f"\n"
        f"{message}\n"
    )
    try:
        _send_email(inbox, subject, body)
    except Exception as e:  # noqa: BLE001
        print(f"[contact] SMTP send failed: {e}")

    return jsonify({"ok": True})
