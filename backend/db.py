import aiosqlite
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "agentready.db")


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

            CREATE INDEX IF NOT EXISTS idx_scans_domain ON scans(domain);
            CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans(ip_address);
            CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at);
        """)
        await db.commit()
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
