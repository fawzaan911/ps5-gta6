"""سيرفر الحملة: /donate يُنشئ فاتورة ميسر ويحوّل لصفحة الدفع، و /total يُرجع مجموع المدفوع."""

import base64
import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SITE_URL = os.environ.get("SITE_URL", "https://fawzaan911.github.io/ps5-gta6/")
SECRET_KEY = os.environ["MOYASAR_SECRET_KEY"].strip()
AUTH = "Basic " + base64.b64encode(f"{SECRET_KEY}:".encode()).decode()
DESCRIPTION = "gta6+ps5"
CAMPAIGN = "ps5-gta6"
TOTAL_CACHE_SECONDS = 60

_total_cache = {"value": None, "at": 0.0}
_total_lock = threading.Lock()


def moyasar(path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        "https://api.moyasar.com/v1" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": AUTH,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ps5-gta6-donations/1.0",
        },
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.load(res)


def create_invoice() -> str:
    url = moyasar("/invoices", {
        "amount": 1000,
        "currency": "SAR",
        "description": DESCRIPTION,
        "success_url": SITE_URL + "thanks.html?status=paid",
        "back_url": SITE_URL,
        "metadata": {"campaign": CAMPAIGN},
    })["url"]
    return url.replace("lang=en", "lang=ar") if "lang=" in url else url + ("&" if "?" in url else "?") + "lang=ar"


def is_campaign_invoice(inv: dict) -> bool:
    metadata = inv.get("metadata") or {}
    return metadata.get("campaign") == CAMPAIGN or inv.get("description") == DESCRIPTION


def collected_total() -> float:
    with _total_lock:
        if _total_cache["value"] is not None and time.time() - _total_cache["at"] < TOTAL_CACHE_SECONDS:
            return _total_cache["value"]

        halalas = 0
        page = 1
        while page:
            data = moyasar(f"/invoices?page={page}")
            for inv in data.get("invoices", []):
                if inv.get("status") == "paid" and inv.get("currency") == "SAR" and is_campaign_invoice(inv):
                    halalas += inv.get("amount", 0)
            page = (data.get("meta") or {}).get("next_page")

        _total_cache.update(value=halalas / 100, at=time.time())
        return _total_cache["value"]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/donate":
            self.handle_donate()
        elif path == "/total":
            self.handle_total()
        else:
            self.send_response(302)
            self.send_header("Location", SITE_URL)
            self.end_headers()

    def handle_donate(self):
        try:
            url = create_invoice()
        except Exception as exc:
            code = ""
            if isinstance(exc, urllib.error.HTTPError):
                detail = exc.read()[:300].decode(errors="replace")
                code = f" (Moyasar HTTP {exc.code}: {detail})"
                self.log_error("Moyasar invoice failed: HTTP %s %s", exc.code, detail)
            else:
                self.log_error("Moyasar invoice failed: %s", exc)
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"تعذر إنشاء رابط الدفع، حاول مرة أخرى.{code}".encode())
            return
        self.send_response(303)
        self.send_header("Location", url)
        self.end_headers()

    def handle_total(self):
        try:
            payload = {"collected": collected_total()}
            status = 200
        except Exception as exc:
            self.log_error("Moyasar total failed: %s", exc)
            payload = {"error": "unavailable"}
            status = 502
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
