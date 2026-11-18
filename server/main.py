"""يُنشئ فاتورة ميسر بـ 10 ريال لكل متبرع ويحوّله لصفحة الدفع المستضافة (فيها Apple Pay)."""

import base64
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SITE_URL = os.environ.get("SITE_URL", "https://fawzaan911.github.io/ps5-gta6/")
SECRET_KEY = os.environ["MOYASAR_SECRET_KEY"]
AUTH = "Basic " + base64.b64encode(f"{SECRET_KEY}:".encode()).decode()


def create_invoice() -> str:
    body = json.dumps({
        "amount": 1000,
        "currency": "SAR",
        "description": "تبرع لشراء PS5 و GTA 6",
        "success_url": SITE_URL + "thanks.html?status=paid",
        "back_url": SITE_URL,
    }).encode()
    req = urllib.request.Request(
        "https://api.moyasar.com/v1/invoices",
        data=body,
        headers={"Authorization": AUTH, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.load(res)["url"]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] != "/donate":
            self.send_response(302)
            self.send_header("Location", SITE_URL)
            self.end_headers()
            return
        try:
            url = create_invoice()
        except Exception as exc:
            self.log_error("Moyasar invoice failed: %s", exc)
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("تعذر إنشاء رابط الدفع، حاول مرة أخرى.".encode())
            return
        self.send_response(303)
        self.send_header("Location", url)
        self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
