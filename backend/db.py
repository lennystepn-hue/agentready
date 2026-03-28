import aiosqlite
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "agentcheck.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                total_score INTEGER,
                grade TEXT,
                report_json TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS monitoring (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                email TEXT NOT NULL,
                frequency TEXT NOT NULL DEFAULT 'weekly',
                is_active INTEGER NOT NULL DEFAULT 1,
                last_scan_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (last_scan_id) REFERENCES scans(id)
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT 'free',
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                scan_id TEXT,
                purchase_type TEXT NOT NULL,
                stripe_session_id TEXT,
                stripe_payment_intent_id TEXT,
                amount_cents INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comparisons (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                domains_json TEXT NOT NULL,
                results_json TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_scans_domain ON scans(domain);
            CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans(ip_address);
            CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
            CREATE INDEX IF NOT EXISTS idx_purchases_scan ON purchases(user_id, scan_id);
        """)
        await db.commit()

        # Add user_id column to scans if it doesn't exist yet
        try:
            await db.execute("ALTER TABLE scans ADD COLUMN user_id TEXT")
            await db.commit()
        except Exception:
            # Column already exists — ignore
            pass

        # Add user_id column to monitoring if it doesn't exist yet
        try:
            await db.execute("ALTER TABLE monitoring ADD COLUMN user_id TEXT")
            await db.commit()
        except Exception:
            pass

    finally:
        await db.close()


async def create_scan(scan_id: str, domain: str, ip_address: str) -> None:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO scans (id, domain, status, ip_address, created_at) VALUES (?, ?, 'pending', ?, ?)",
            (scan_id, domain, ip_address, now),
        )
        await db.commit()
    finally:
        await db.close()


async def update_scan_result(
    scan_id: str,
    status: str,
    total_score: int | None = None,
    grade: str | None = None,
    report_json: str | None = None,
) -> None:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """UPDATE scans
               SET status = ?, total_score = ?, grade = ?,
                   report_json = ?, completed_at = ?
               WHERE id = ?""",
            (status, total_score, grade, report_json, now, scan_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_scan(scan_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        await db.close()


async def count_scans_today(ip_address: str) -> int:
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM scans WHERE ip_address = ? AND created_at LIKE ?",
            (ip_address, f"{today}%"),
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 0
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

async def create_user(user_id: str, email: str, password_hash: str) -> None:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO users (id, email, password_hash, plan, created_at, updated_at) VALUES (?, ?, ?, 'free', ?, ?)",
            (user_id, email, password_hash, now, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_user_by_email(email: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_user_by_id(user_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def update_user_plan(
    user_id: str,
    plan: str,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
) -> None:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        if stripe_customer_id is not None and stripe_subscription_id is not None:
            await db.execute(
                "UPDATE users SET plan = ?, stripe_customer_id = ?, stripe_subscription_id = ?, updated_at = ? WHERE id = ?",
                (plan, stripe_customer_id, stripe_subscription_id, now, user_id),
            )
        elif stripe_customer_id is not None:
            await db.execute(
                "UPDATE users SET plan = ?, stripe_customer_id = ?, updated_at = ? WHERE id = ?",
                (plan, stripe_customer_id, now, user_id),
            )
        else:
            await db.execute(
                "UPDATE users SET plan = ?, updated_at = ? WHERE id = ?",
                (plan, now, user_id),
            )
        await db.commit()
    finally:
        await db.close()


async def create_purchase(
    purchase_id: str,
    user_id: str,
    scan_id: str | None,
    purchase_type: str,
    stripe_session_id: str | None,
    amount_cents: int | None,
) -> None:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO purchases (id, user_id, scan_id, purchase_type, stripe_session_id, amount_cents, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)",
            (purchase_id, user_id, scan_id, purchase_type, stripe_session_id, amount_cents, now),
        )
        await db.commit()
    finally:
        await db.close()


async def complete_purchase(stripe_session_id: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE purchases SET status = 'completed' WHERE stripe_session_id = ?",
            (stripe_session_id,),
        )
        await db.commit()
    finally:
        await db.close()


async def user_has_fix_access(user_id: str, scan_id: str) -> bool:
    """True if user has a completed fix_files purchase for that scan OR user plan is 'pro'."""
    db = await get_db()
    try:
        # Check plan first
        cursor = await db.execute("SELECT plan FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if row and row["plan"] == "pro":
            return True

        # Check for completed fix_files purchase for this scan
        cursor = await db.execute(
            "SELECT id FROM purchases WHERE user_id = ? AND scan_id = ? AND purchase_type = 'fix_files' AND status = 'completed' LIMIT 1",
            (user_id, scan_id),
        )
        row = await cursor.fetchone()
        return row is not None
    finally:
        await db.close()


async def get_user_scans(user_id: str, limit: int = 20) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, domain, status, total_score, grade, created_at, completed_at FROM scans WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def create_comparison(
    comp_id: str, user_id: str, domains_json: str, results_json: str | None
) -> None:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO comparisons (id, user_id, domains_json, results_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (comp_id, user_id, domains_json, results_json, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_user_comparisons(user_id: str, limit: int = 10) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM comparisons WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def add_user_id_to_scan(scan_id: str, user_id: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE scans SET user_id = ? WHERE id = ?",
            (user_id, scan_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_scan_history(domain: str, user_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id as scan_id, total_score as score, grade, created_at FROM scans WHERE domain = ? AND user_id = ? AND status = 'completed' ORDER BY created_at DESC",
            (domain, user_id),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def update_monitoring_user(monitoring_id: str, user_id: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE monitoring SET user_id = ? WHERE id = ?",
            (user_id, monitoring_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_user_monitors(user_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM monitoring WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def create_monitor(monitor_id: str, user_id: str, domain: str, email: str) -> None:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO monitoring (id, domain, email, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (monitor_id, domain, email, user_id, now),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_monitor(monitor_id: str, user_id: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE monitoring SET is_active = 0 WHERE id = ? AND user_id = ?",
            (monitor_id, user_id),
        )
        await db.commit()
    finally:
        await db.close()
