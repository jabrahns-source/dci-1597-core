"""
Vercel Serverless entry for DCI-1597 Core
Routes:
  GET  /api/health
  POST /api/attest
  POST /api/verify
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

# Make core importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.dci_1597 import (
    build_deterministic_receipt,
    verify_receipt,
    prove_core_identities,
    MODULUS,
)


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body, sort_keys=True).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/api", "/api/health", "/health"):
            try:
                prove_core_identities()
                self._send(200, {
                    "status": "ok",
                    "engine": "dci-1597-v1.0.0",
                    "characteristic": MODULUS,
                    "determinism": "pure-function-no-entropy",
                    "phi_identity": "verified",
                })
            except AssertionError as e:
                self._send(500, {"status": "error", "detail": str(e)})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send(400, {"error": "invalid JSON"})
            return

        if self.path in ("/api/attest", "/attest"):
            try:
                receipt = build_deterministic_receipt(data)
                self._send(200, receipt)
            except Exception as e:
                self._send(400, {"error": str(e)})

        elif self.path in ("/api/verify", "/verify"):
            try:
                valid = verify_receipt(data)
                self._send(200, {"valid": valid})
            except Exception as e:
                self._send(400, {"error": str(e), "valid": False})

        else:
            self._send(404, {"error": "not found"})
