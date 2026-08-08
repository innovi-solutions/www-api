import logging
from datetime import datetime, timedelta, timezone

import resend

from app.config import settings
from app.services.db import get_client

logger = logging.getLogger("innovi.email")
resend.api_key = settings.resend_api_key

SESSION_LABELS = {
    "discovery": "Discovery Call, 30 minutes",
    "technical": "Technical Deep-Dive, 60 minutes",
}
SESSION_SHORT = {
    "discovery": "Discovery Call (30 min)",
    "technical": "Technical Deep-Dive (60 min)",
}

# ── Theme tokens ────────────────────────────────────────────────────
ACCENT = "#2563eb"
FG = "#0a0a0a"
MUTED = "#6b7280"
BORDER = "#e5e7eb"
BG = "#f4f4f5"
CARD = "#ffffff"
MONO = "'Courier New', Courier, monospace"
SANS = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"

# Hosted logo (Supabase public bucket now; switch to the site URL after deploy)
LOGO_URL = "https://innovi-solutions.com/innovi-logo.png"

SAST = timezone(timedelta(hours=2))  # South Africa Standard Time


def _esc(s: str) -> str:
    """Escape user text so it can't inject HTML into the email."""
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def _label(text: str, size: int = 12) -> str:
    return (
        f'<span style="font-family:{MONO};font-size:{size}px;letter-spacing:2px;'
        f'text-transform:uppercase;color:{MUTED};">{text}</span>'
    )


def _numbered_row(n: str, label: str, value: str, last: bool = False) -> str:
    border = "" if last else f"border-bottom:1px solid {BORDER};"
    return f"""
      <tr>
        <td style="padding:16px 0;{border}width:48px;vertical-align:top;">
          <span style="font-family:{MONO};font-size:13px;color:{ACCENT};">{n}<span style="color:{MUTED};">/</span></span>
        </td>
        <td style="padding:16px 0;{border}vertical-align:top;">
          {_label(label)}
          <div style="margin-top:6px;font-family:{SANS};font-size:16px;color:{FG};">{value}</div>
        </td>
      </tr>"""


def build_lead_email(lead_id: str, payload) -> str:
    name = _esc(payload.name)
    first_name = name.split(" ")[0] if name else "lead"
    email = _esc(payload.email)
    company = _esc(payload.company)
    message = _esc(payload.message)
    received = datetime.now(SAST).strftime("%d %b %Y &middot; %H:%M").upper()

    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:{BG};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:32px 12px;">
    <tr><td align="center">

      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;background:{CARD};border:2px solid {ACCENT};">

        <!-- header: logo + NEW LEAD badge -->
        <tr>
          <td style="padding:28px 36px 22px 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="left" style="vertical-align:middle;">
                  <img src="{LOGO_URL}" alt="INNOVI SOLUTIONS" width="170"
                       style="display:block;border:0;max-width:170px;height:auto;">
                </td>
                <td align="right" style="vertical-align:middle;">
                  <span style="display:inline-block;background:#eff6ff;border:1px solid {ACCENT};
                               padding:6px 12px;font-family:{MONO};font-size:11px;
                               letter-spacing:2px;text-transform:uppercase;color:{ACCENT};">
                    New Lead
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- eyebrow + name + company + session -->
        <tr>
          <td style="padding:14px 36px 0 36px;">
            {_label("New session request")}
            <h1 style="margin:12px 0 0 0;font-family:{SANS};font-size:34px;font-weight:800;
                       letter-spacing:-0.5px;line-height:1.1;color:{FG};">
              {name}
            </h1>
            <p style="margin:10px 0 0 0;font-family:{MONO};font-size:13px;
                      letter-spacing:2px;text-transform:uppercase;color:{MUTED};">
              {company}
            </p>
            <p style="margin:16px 0 0 0;font-family:{SANS};font-size:16px;color:{ACCENT};">
              &mdash; {SESSION_LABELS[payload.session]}
            </p>
          </td>
        </tr>

        <!-- numbered details -->
        <tr>
          <td style="padding:26px 36px 0 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="border-top:1px solid {BORDER};">
              {_numbered_row("01", "Email",
                  f'<a href="mailto:{email}" style="color:{ACCENT};text-decoration:none;">{email}</a>')}
              {_numbered_row("02", "Preferred date", payload.date.strftime("%A, %d %B %Y"))}
              {_numbered_row("03", "Project type", payload.type, last=True)}
            </table>
          </td>
        </tr>

        <!-- message as a quote -->
        <tr>
          <td style="padding:22px 36px 0 36px;">
            {_label("The problem, in their words")}
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;">
              <tr>
                <td style="width:36px;vertical-align:top;font-family:{SERIF};font-size:44px;
                           line-height:1;color:{ACCENT};font-weight:700;">&ldquo;</td>
                <td style="vertical-align:top;font-family:{SERIF};font-size:18px;font-style:italic;
                           line-height:1.65;color:{FG};white-space:pre-wrap;padding-top:8px;">{message}</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- full-width reply button -->
        <tr>
          <td style="padding:30px 36px 0 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:{ACCENT};" align="center">
                  <a href="mailto:{email}"
                     style="display:block;padding:16px 24px;font-family:{MONO};font-size:14px;
                            letter-spacing:3px;text-transform:uppercase;color:#ffffff;
                            text-decoration:none;font-weight:700;">
                    Reply to {first_name} &nbsp;&rarr;
                  </a>
                </td>
              </tr>
            </table>
            <p style="margin:12px 0 0 0;font-family:{SANS};font-size:13px;color:{MUTED};">
              Or just hit reply &mdash; this message replies straight to the client.
            </p>
          </td>
        </tr>

        <!-- footer -->
        <tr>
          <td style="padding:22px 36px 24px 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="border-top:1px solid {BORDER};">
              <tr>
                <td style="padding-top:16px;" align="left">
                  <span style="font-family:{MONO};font-size:11px;letter-spacing:2px;
                               text-transform:uppercase;color:{MUTED};">INNOVI Solutions</span>
                </td>
                <td style="padding-top:16px;" align="right">
                  <span style="font-family:{MONO};font-size:11px;letter-spacing:2px;
                               text-transform:uppercase;color:{MUTED};">Received {received}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>

      <p style="margin:16px 0 0 0;font-family:{MONO};font-size:10px;letter-spacing:2px;
                text-transform:uppercase;color:{MUTED};">
        Lead ID {lead_id} &middot; POPIA consent given at submission
      </p>

    </td></tr>
  </table>
</body>
</html>"""


def send_lead_notification(lead_id: str, payload) -> None:
    """Runs in the background AFTER the lead is stored. Never raises."""
    subject = f"[LEAD] {SESSION_SHORT[payload.session]} — {payload.name} ({payload.company})"

    try:
        resend.Emails.send({
            "from": f"INNOVI SOLUTIONS Leads <{settings.from_email}>",
            "to": settings.stakeholder_list,
            "reply_to": payload.email,
            "subject": subject,
            "html": build_lead_email(lead_id, payload),
        })
    except Exception:
        logger.exception("Email send failed for lead %s", lead_id)
        return  # lead is already safe in the DB — do not crash, do not retry here

    try:
        get_client().table("leads").update({"email_sent": True}).eq("id", lead_id).execute()
    except Exception:
        logger.exception("Could not flip email_sent for lead %s", lead_id)