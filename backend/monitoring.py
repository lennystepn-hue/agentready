import logging
import os
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from db import get_db, get_user_by_id, get_scan
from scanner.orchestrator import run_scan

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@agentcheck.org")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


async def run_monitoring_cycle():
    """Runs weekly monitoring scans for all active Pro users."""
    logger.info("Starting monitoring cycle...")
    db = await get_db()
    try:
        # Get all active monitors where the user has a pro plan
        cursor = await db.execute(
            """
            SELECT m.id as monitor_id, m.domain, m.email, m.last_scan_id, m.user_id
            FROM monitoring m
            JOIN users u ON m.user_id = u.id
            WHERE m.is_active = 1 AND u.plan = 'pro'
            """
        )
        monitors = [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()

    logger.info(f"Found {len(monitors)} active monitors to process.")

    for monitor in monitors:
        try:
            domain = monitor["domain"]
            monitor_id = monitor["monitor_id"]

            # Get old score if there was a previous scan
            old_score = None
            if monitor["last_scan_id"]:
                old_scan = await get_scan(monitor["last_scan_id"])
                if old_scan and old_scan["total_score"] is not None:
                    old_score = old_scan["total_score"]

            # Run new scan
            scan_id = str(uuid.uuid4())
            from db import create_scan as db_create_scan
            await db_create_scan(scan_id, domain, "monitoring")
            await run_scan(scan_id, domain)

            # Get new score
            new_scan = await get_scan(scan_id)
            new_score = new_scan["total_score"] if new_scan else None

            # Update last_scan_id on monitor
            db = await get_db()
            try:
                await db.execute(
                    "UPDATE monitoring SET last_scan_id = ? WHERE id = ?",
                    (scan_id, monitor_id),
                )
                await db.commit()
            finally:
                await db.close()

            # Send email if score changed
            if old_score is not None and new_score is not None and old_score != new_score:
                await send_score_email(
                    to_email=monitor["email"],
                    domain=domain,
                    old_score=old_score,
                    new_score=new_score,
                    scan_id=scan_id,
                )

            logger.info(f"Monitor {monitor_id}: {domain} scanned. Score: {old_score} -> {new_score}")

        except Exception:
            logger.exception(f"Error processing monitor {monitor.get('monitor_id')}")


async def send_score_email(
    to_email: str,
    domain: str,
    old_score: int,
    new_score: int,
    scan_id: str,
):
    """Send email notification about score change."""
    if not SMTP_HOST or not SMTP_USER:
        logger.warning("SMTP not configured, skipping score change email.")
        return

    direction = "improved" if new_score > old_score else "decreased"
    diff = abs(new_score - old_score)
    scan_url = f"{FRONTEND_URL}/scan/{scan_id}"

    subject = f"AgentCheck: {domain} score {direction} by {diff} points"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>AgentCheck Score Update</h2>
        <p>Your monitored domain <strong>{domain}</strong> has {direction}.</p>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 8px 16px; border: 1px solid #ddd;">Previous Score</td>
                <td style="padding: 8px 16px; border: 1px solid #ddd; font-weight: bold;">{old_score}/100</td>
            </tr>
            <tr>
                <td style="padding: 8px 16px; border: 1px solid #ddd;">New Score</td>
                <td style="padding: 8px 16px; border: 1px solid #ddd; font-weight: bold;">{new_score}/100</td>
            </tr>
        </table>
        <p><a href="{scan_url}" style="background: #4f46e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px;">View Full Report</a></p>
        <p style="color: #666; font-size: 12px; margin-top: 30px;">You are receiving this because you have monitoring enabled for {domain} on AgentCheck.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(f"{domain} score {direction}: {old_score} -> {new_score}. View: {scan_url}", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info(f"Score email sent to {to_email} for {domain}.")
    except Exception:
        logger.exception(f"Failed to send score email to {to_email}")
