"""Outgoing email (used for password reset links).

- If SMTP_HOST is set in .env, mail is sent through that server (SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
  SMTP_FROM; STARTTLS on port 587).
- Otherwise (development), each email is saved as a text file in backend/outbox/ instead of being sent,
  so the reset flow can be tested without an email service. Open the newest file to find the link.
"""

import logging
import os
import re
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

OUTBOX = Path(__file__).resolve().parent / "outbox"
log = logging.getLogger("campus_customs")


def send_email(to: str, subject: str, body: str) -> None:
    sender = os.getenv("SMTP_FROM", "Campus Customs <no-reply@campuscustoms.example>")
    host = os.getenv("SMTP_HOST")
    if host:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = sender, to, subject
        msg.set_content(body)
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
            smtp.starttls()
            if user := os.getenv("SMTP_USER"):
                smtp.login(user, os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
        return

    OUTBOX.mkdir(exist_ok=True)
    safe_to = re.sub(r"[^a-z0-9]+", "-", to.lower()).strip("-")
    path = OUTBOX / f"{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1_000_000:06d}-{safe_to}.txt"  # unique per email
    path.write_text(f"From: {sender}\nTo: {to}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
    log.warning("No SMTP server configured; email to %s saved to %s", to, path)
