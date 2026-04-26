from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests


SERVER_URL = os.environ.get("AUTOPAY_SERVER_URL", "http://127.0.0.1:8009").rstrip("/")
DEVICE_ID = os.environ.get("AUTOPAY_DEVICE_ID", "android-test-1")
DOWNLOAD_DIR = Path(os.environ.get("AUTOPAY_DOWNLOAD_DIR", "/sdcard/Download"))


def post_status(job_id: str, status: str, message: str = "") -> None:
    url = f"{SERVER_URL}/job/{job_id}/status"
    payload = {"device_id": DEVICE_ID, "status": status, "message": message}
    resp = requests.post(url, json=payload, timeout=20)
    resp.raise_for_status()


def refresh_android_media(path: Path) -> None:
    try:
        subprocess.run(
            [
                "am",
                "broadcast",
                "-a",
                "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                "-d",
                f"file://{path}",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass


def main() -> int:
    resp = requests.get(
        f"{SERVER_URL}/job/next",
        params={"device_id": DEVICE_ID},
        timeout=20,
    )
    resp.raise_for_status()
    job = resp.json().get("job")
    if not job:
        print("No hay jobs disponibles.")
        return 0

    job_id = job["job_id"]
    payment_id = job["payment_id"]
    qr_url = urljoin(SERVER_URL + "/", job["qr_url"].lstrip("/"))
    filename = f"{payment_id}.png"
    target = DOWNLOAD_DIR / filename
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Job asignado: {job_id} ({payment_id})")
    print(f"Descargando QR: {qr_url}")
    qr_resp = requests.get(qr_url, timeout=20)
    qr_resp.raise_for_status()
    target.write_bytes(qr_resp.content)
    refresh_android_media(target)

    post_status(job_id, "QR_DOWNLOADED", f"Guardado en {target}")
    print(f"QR guardado en: {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
