from __future__ import annotations

import argparse
import base64
import sqlite3
import sys
from pathlib import Path

import requests


DEFAULT_BOT_DB = Path("/home/proyectos/ENTELPAY BOT/data/bot.db")
DEFAULT_PAY_DB = Path("/home/proyectos/ENTELPAY BOT/data/admin_payments.db")
DEFAULT_SERVER = "http://127.0.0.1:8009"


def row_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def find_order(bot_db: Path, tx_code: str | None) -> dict:
    with connect(bot_db) as con:
        if tx_code:
            row = con.execute(
                """
                SELECT *
                  FROM orders
                 WHERE tx_code=? AND qr_image IS NOT NULL AND qr_image != ''
                """,
                (tx_code,),
            ).fetchone()
        else:
            row = con.execute(
                """
                SELECT *
                  FROM orders
                 WHERE status='PENDING'
                   AND qr_image IS NOT NULL
                   AND qr_image != ''
                 ORDER BY created_at DESC
                 LIMIT 1
                """
            ).fetchone()
    data = row_dict(row)
    if not data:
        raise SystemExit("No encontre una orden PENDING con qr_image. Genera una orden real primero.")
    return data


def find_payment(pay_db: Path, tx_code: str) -> dict | None:
    if not pay_db.exists():
        return None
    with connect(pay_db) as con:
        row = con.execute("SELECT * FROM payments WHERE tx_code=?", (tx_code,)).fetchone()
    return row_dict(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa la ultima orden PENDING real al laboratorio autopay.")
    parser.add_argument("--tx-code", default=None, help="Importar un TX especifico en vez del ultimo PENDING.")
    parser.add_argument("--bot-db", type=Path, default=DEFAULT_BOT_DB)
    parser.add_argument("--pay-db", type=Path, default=DEFAULT_PAY_DB)
    parser.add_argument("--server", default=DEFAULT_SERVER)
    args = parser.parse_args()

    order = find_order(args.bot_db, args.tx_code)
    payment = find_payment(args.pay_db, order["tx_code"]) or {}
    payment_id = payment.get("payment_id") or f"TX-{order['tx_code'][:8]}"
    job_id = payment_id
    amount = float(order.get("qr_amount") or payment.get("qr_amount") or 0)
    qr_base64 = order["qr_image"]

    payload = {
        "job_id": job_id,
        "payment_id": payment_id,
        "tx_code": order["tx_code"],
        "amount": amount,
        "qr_base64": qr_base64,
        "status": "WAITING_DEVICE",
        "reset_assignment": True,
    }
    resp = requests.post(f"{args.server.rstrip('/')}/jobs/upsert", json=payload, timeout=30)
    resp.raise_for_status()
    out = resp.json()
    print(f"Importado: {payment_id} tx={order['tx_code']} qr_amount={amount:.2f}")
    print(f"Job: {out['job_id']} estado={out['status']} qr={out['qr_url']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
