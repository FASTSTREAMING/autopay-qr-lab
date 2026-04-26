from __future__ import annotations

import sqlite3
import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import qrcode
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "autopay_test.db"
QR_PATH = DATA_DIR / "PAY-TEST-0001.png"

LEASE_SECONDS = 90

app = FastAPI(title="Autopay QR Test Lab", version="0.1.0")


class StatusBody(BaseModel):
    device_id: str
    status: str
    message: str = ""


class UpsertJobBody(BaseModel):
    job_id: str
    payment_id: str
    tx_code: str
    amount: float
    qr_base64: str
    status: str = "WAITING_DEVICE"
    reset_assignment: bool = True


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_qr() -> None:
    if QR_PATH.exists():
        return
    img = qrcode.make("AUTOPAY-TEST|PAY-TEST-0001|AMOUNT=1.00|NO_REAL_PAYMENT")
    img.save(QR_PATH)


def qr_filename_for(job_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in job_id)
    return f"{safe}.png"


def decode_qr_base64(qr_base64: str) -> bytes:
    raw = qr_base64.strip()
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        return base64.b64decode(raw, validate=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid qr_base64: {exc}") from exc


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_qr()
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                payment_id TEXT NOT NULL,
                tx_code TEXT NOT NULL,
                amount REAL NOT NULL,
                qr_filename TEXT NOT NULL DEFAULT 'PAY-TEST-0001.png',
                status TEXT NOT NULL,
                assigned_device TEXT,
                lease_until TEXT,
                message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
        if "qr_filename" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN qr_filename TEXT NOT NULL DEFAULT 'PAY-TEST-0001.png'")
        conn.execute(
            """
            INSERT OR IGNORE INTO jobs (
                job_id, payment_id, tx_code, amount, qr_filename, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "TEST-0001",
                "PAY-TEST-0001",
                "TX-TEST-0001",
                1.00,
                "PAY-TEST-0001.png",
                "WAITING_DEVICE",
                now_iso(),
                now_iso(),
            ),
        )


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "autopay-test", "time": now_iso()}


@app.get("/job/next")
def next_job(device_id: str = Query(..., min_length=2)) -> dict:
    init_db()
    lease_until = datetime.now(timezone.utc) + timedelta(seconds=LEASE_SECONDS)
    with db() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at LIMIT 20").fetchall()
        chosen = None
        for row in rows:
            expired_lease = parse_iso(row["lease_until"]) is not None and parse_iso(row["lease_until"]) < datetime.now(timezone.utc)
            if row["status"] == "WAITING_DEVICE":
                chosen = row
                break
            if row["status"] == "ASSIGNED" and row["assigned_device"] == device_id:
                chosen = row
                break
            if row["status"] == "ASSIGNED" and expired_lease:
                chosen = row
                break

        if chosen is None:
            return {"ok": True, "job": None}

        conn.execute(
            """
            UPDATE jobs
               SET status='ASSIGNED',
                   assigned_device=?,
                   lease_until=?,
                   updated_at=?
             WHERE job_id=?
            """,
            (device_id, lease_until.isoformat(), now_iso(), chosen["job_id"]),
        )
        row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (chosen["job_id"],)).fetchone()

    return {
        "ok": True,
        "job": {
            "job_id": row["job_id"],
            "payment_id": row["payment_id"],
            "tx_code": row["tx_code"],
            "amount": row["amount"],
            "status": row["status"],
            "qr_url": f"/job/{row['job_id']}/qr",
            "lease_until": row["lease_until"],
            "message": row["message"],
        },
    }


@app.get("/job/{job_id}/qr")
def job_qr(job_id: str) -> FileResponse:
    init_db()
    with db() as conn:
        row = conn.execute("SELECT job_id, qr_filename FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    path = DATA_DIR / row["qr_filename"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="qr image not found")
    return FileResponse(path, media_type="image/png", filename=f"{job_id}.png")


@app.post("/jobs/upsert")
def upsert_job(body: UpsertJobBody) -> dict:
    init_db()
    filename = qr_filename_for(body.job_id)
    path = DATA_DIR / filename
    path.write_bytes(decode_qr_base64(body.qr_base64))
    now = now_iso()
    with db() as conn:
        existing = conn.execute("SELECT job_id FROM jobs WHERE job_id=?", (body.job_id,)).fetchone()
        if existing:
            if body.reset_assignment:
                conn.execute(
                    """
                    UPDATE jobs
                       SET payment_id=?,
                           tx_code=?,
                           amount=?,
                           qr_filename=?,
                           status=?,
                           assigned_device=NULL,
                           lease_until=NULL,
                           message=NULL,
                           updated_at=?
                     WHERE job_id=?
                    """,
                    (body.payment_id, body.tx_code, body.amount, filename, body.status, now, body.job_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE jobs
                       SET payment_id=?,
                           tx_code=?,
                           amount=?,
                           qr_filename=?,
                           updated_at=?
                     WHERE job_id=?
                    """,
                    (body.payment_id, body.tx_code, body.amount, filename, now, body.job_id),
                )
        else:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, payment_id, tx_code, amount, qr_filename, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (body.job_id, body.payment_id, body.tx_code, body.amount, filename, body.status, now, now),
            )
    return {
        "ok": True,
        "job_id": body.job_id,
        "payment_id": body.payment_id,
        "tx_code": body.tx_code,
        "qr_url": f"/job/{body.job_id}/qr",
        "status": body.status,
    }


@app.post("/job/{job_id}/status")
def update_status(job_id: str, body: StatusBody) -> dict:
    init_db()
    allowed_prefixes: tuple[str, ...] = (
        "QR_DOWNLOADED",
        "TASKER_INTENT_SENT",
        "TASKER_STARTED",
        "QR_IMPORT_FAILED",
        "OPENING_TAKENOS",
        "LOGIN_REQUIRED",
        "SELECTING_QR",
        "QR_SELECTED",
        "PAYMENT_REVIEW",
        "NEEDS_HUMAN_CONFIRM",
        "PAYMENT_SUBMITTED",
        "PAYMENT_SUCCESS_SCREEN",
        "PAYMENT_FAILED",
        "BOT_DETECTED",
        "MANUAL_REQUIRED",
        "FAILED",
        "DONE",
    )
    if not body.status.startswith(allowed_prefixes):
        raise HTTPException(status_code=400, detail="invalid status")
    with db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="job not found")
        if row["assigned_device"] and row["assigned_device"] != body.device_id:
            raise HTTPException(status_code=409, detail="job assigned to another device")
        conn.execute(
            """
            UPDATE jobs
               SET status=?,
                   assigned_device=?,
                   message=?,
                   updated_at=?
             WHERE job_id=?
            """,
            (body.status, body.device_id, body.message, now_iso(), job_id),
        )
    return {"ok": True, "job_id": job_id, "status": body.status}


@app.post("/job/{job_id}/reset")
def reset_job(job_id: str) -> dict:
    init_db()
    with db() as conn:
        row = conn.execute("SELECT job_id FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="job not found")
        conn.execute(
            """
            UPDATE jobs
               SET status='WAITING_DEVICE',
                   assigned_device=NULL,
                   lease_until=NULL,
                   message=NULL,
                   updated_at=?
             WHERE job_id=?
            """,
            (now_iso(), job_id),
        )
    return {"ok": True, "job_id": job_id, "status": "WAITING_DEVICE"}


@app.get("/jobs")
def jobs() -> dict:
    init_db()
    with db() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at").fetchall()
    return {"ok": True, "jobs": [dict(row) for row in rows]}
