from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from requests import RequestException


SERVER_URL = os.environ.get("AUTOPAY_SERVER_URL", "http://127.0.0.1:8009").rstrip("/")
DEVICE_ID = os.environ.get("AUTOPAY_DEVICE_ID", "android-test-1")
DOWNLOAD_DIR = Path(os.environ.get("AUTOPAY_DOWNLOAD_DIR", "/sdcard/Download"))
TASKER_INTENT_ACTION = os.environ.get("AUTOPAY_TASKER_INTENT_ACTION", "").strip()
TASKER_DIRECT_TASK = os.environ.get("AUTOPAY_TASKER_TASK", "").strip()
CLEAN_OLD_QR = os.environ.get("AUTOPAY_CLEAN_OLD_QR", "0") == "1"
HTTP_TIMEOUT = int(os.environ.get("AUTOPAY_HTTP_TIMEOUT", "20"))
HTTP_RETRIES = int(os.environ.get("AUTOPAY_HTTP_RETRIES", "2"))


def post_status(job_id: str, status: str, message: str = "") -> None:
    url = f"{SERVER_URL}/job/{job_id}/status"
    payload = {"device_id": DEVICE_ID, "status": status, "message": message}
    resp = requests.post(url, json=payload, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()


def request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    last_exc: Exception | None = None
    kwargs.setdefault("timeout", HTTP_TIMEOUT)
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            resp = requests.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except RequestException as exc:
            last_exc = exc
            if attempt < HTTP_RETRIES:
                print(f"Conexion fallida intento {attempt}/{HTTP_RETRIES}: {exc}")
                time.sleep(2)
    raise RuntimeError(
        f"No pude conectar con {SERVER_URL}. Revisa Tailscale en Android, "
        f"que la VPS responda /health y que AUTOPAY_SERVER_URL sea correcto. "
        f"Ultimo error: {last_exc}"
    )


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


def clean_old_qrs() -> None:
    if not CLEAN_OLD_QR:
        return
    for pattern in ("PAY-*.png", "TX-*.png", "TEST-*.png"):
        for path in DOWNLOAD_DIR.glob(pattern):
            try:
                path.unlink()
            except OSError:
                pass


def launch_tasker(job_id: str, payment_id: str, tx_code: str, qr_path: Path) -> str | None:
    if TASKER_INTENT_ACTION:
        cmd = [
            "am",
            "broadcast",
            "-a",
            TASKER_INTENT_ACTION,
            "--es",
            "job_id",
            job_id,
            "--es",
            "payment_id",
            payment_id,
            "--es",
            "tx_code",
            tx_code,
            "--es",
            "qr_path",
            str(qr_path),
        ]
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        return (result.stdout + result.stderr).strip()
    if TASKER_DIRECT_TASK:
        cmd = [
            "am",
            "broadcast",
            "-a",
            "net.dinglisch.android.tasker.ACTION_TASK",
            "-e",
            "task_name",
            TASKER_DIRECT_TASK,
        ]
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        return (result.stdout + result.stderr).strip()
    return None


def main() -> int:
    resp = request_with_retry(
        "GET",
        f"{SERVER_URL}/job/next",
        params={"device_id": DEVICE_ID},
    )
    job = resp.json().get("job")
    if not job:
        print("No hay jobs disponibles.")
        return 0

    job_id = job["job_id"]
    payment_id = job["payment_id"]
    tx_code = job["tx_code"]
    qr_url = urljoin(SERVER_URL + "/", job["qr_url"].lstrip("/"))
    filename = f"{payment_id}.png"
    target = DOWNLOAD_DIR / filename
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    clean_old_qrs()

    print(f"Job asignado: {job_id} ({payment_id})")
    print(f"Descargando QR: {qr_url}")
    qr_resp = request_with_retry("GET", qr_url)
    target.write_bytes(qr_resp.content)
    refresh_android_media(target)

    post_status(job_id, "QR_DOWNLOADED", f"Guardado en {target}")
    print(f"QR guardado en: {target}")
    tasker_out = launch_tasker(job_id, payment_id, tx_code, target)
    if tasker_out is not None:
        post_status(job_id, "TASKER_INTENT_SENT", tasker_out[-300:])
        print("Tasker lanzado.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
