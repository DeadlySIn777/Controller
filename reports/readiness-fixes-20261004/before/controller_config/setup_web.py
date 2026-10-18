"""Local-only UI adapter. No physical transports, arbitrary files, or paid calls."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
from pathlib import Path
import secrets
import threading
from urllib.parse import urlsplit

from .model import ConfigurationError
from .setup_service import SetupService
from .setup_budget import BudgetLedger

WEB = Path(__file__).with_name("web")
MAX_BODY = 256_000


class SetupApplication:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.service = SetupService(self.directory / "setup.json")
        self.ledger = BudgetLedger(self.directory / "budget.json")
        self.lock = threading.Lock()

    def context(self):
        return {"setup": self.service.status(), "profiles": self.service.profiles(),
                "capabilities": self.service.capabilities(),
                "budget": self.ledger.status() if (self.directory / "budget.json").exists() else None,
                "paid_ai_enabled": False, "simulation_only": True}

    def action(self, action, payload):
        if type(payload) is not dict:
            raise ConfigurationError("REQUEST", "Expected an object")
        fields = {"initialize": set(), "template": {"profile_id"},
                  "save": {"draft", "expected_revision"}, "preview": set(),
                  "commit": {"plan", "request_id"}, "restore": {"generation"},
                  "guidance": {"question"}}
        if action not in fields or set(payload) != fields[action]:
            raise ConfigurationError("REQUEST", "Unsupported operation or fields")
        with self.lock:
            if action == "initialize":
                status = self.service.status()
                if not status["initialized"]:
                    status = self.service.initialize(actor="setup-ui")
                if not (self.directory / "budget.json").exists():
                    self.ledger.create(status["epoch"], cap_microdollars=15_000_000)
                return status
            if action == "template":
                return self.service.draft_template(payload["profile_id"])
            if action == "save":
                return self.service.save_draft(payload["draft"], payload["expected_revision"], actor="setup-ui")
            if action == "preview":
                return self.service.preview()
            if action == "commit":
                return self.service.commit(payload["plan"], payload["request_id"], actor="setup-ui")
            if action == "restore":
                return self.service.restore_preview(payload["generation"])
            from .setup_assistant import local_guidance
            return local_guidance(self.service, payload["question"])


def make_server(directory, port=8766):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ConfigurationError("PORT", "Port must be 0–65535")
    app = SetupApplication(directory)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Request bodies/answers/tokens never enter access logs.

        def respond(self, status, body, content_type="application/json; charset=utf-8"):
            data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def authorized(self, mutate=False):
            host = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != host:
                self.respond(403, {"ok": False, "error": {"code": "HOST", "message": "Use the exact local address printed by the server"}})
                return False
            if mutate and self.headers.get("Origin") != "http://" + host:
                self.respond(403, {"ok": False, "error": {"code": "ORIGIN", "message": "Same-origin UI required"}})
                return False
            if not hmac.compare_digest(self.headers.get("X-Setup-Token", ""), token):
                self.respond(403, {"ok": False, "error": {"code": "TOKEN", "message": "Reload the local setup page"}})
                return False
            return True

        def do_GET(self):
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                self.respond(403, {"ok": False, "error": {"code": "HOST", "message": "Local address required"}})
                return
            path = urlsplit(self.path).path
            try:
                if path == "/":
                    self.respond(200, (WEB / "setup.html").read_text(encoding="utf-8").replace("__SETUP_TOKEN__", token), "text/html; charset=utf-8")
                elif path in ("/setup.js", "/setup.css"):
                    self.respond(200, (WEB / path[1:]).read_text(encoding="utf-8"), "text/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8")
                elif path in ("/api/context", "/api/export") and self.authorized():
                    self.respond(200, {"ok": True, "result": app.context() if path.endswith("context") else app.service.status()})
                elif not path.startswith("/api/"):
                    self.respond(404, {"ok": False, "error": {"code": "NOT_FOUND", "message": "Unknown page"}})
            except (ConfigurationError, OSError) as error:
                self.respond(409, {"ok": False, "error": error.as_dict() if isinstance(error, ConfigurationError) else {"code": "IO_ERROR", "message": "Unable to read setup state"}})

        def do_POST(self):
            if not self.authorized(mutate=True):
                return
            try:
                if self.headers.get("Content-Type") != "application/json" or self.headers.get("Transfer-Encoding"):
                    raise ConfigurationError("REQUEST", "JSON with a bounded Content-Length is required")
                try:
                    length = int(self.headers.get("Content-Length", "-1"))
                except ValueError:
                    length = -1
                if not 0 < length <= MAX_BODY:
                    raise ConfigurationError("REQUEST_SIZE", "Request too large or missing its length")
                def pairs(items):
                    result = {}
                    for k, v in items:
                        if k in result:
                            raise ConfigurationError("DUPLICATE_KEY", "Duplicate JSON field")
                        result[k] = v
                    return result
                self.connection.settimeout(5)
                payload = json.loads(self.rfile.read(length), object_pairs_hook=pairs,
                                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite number")))
                path = urlsplit(self.path).path
                if not path.startswith("/api/"):
                    raise ConfigurationError("REQUEST", "Unknown action")
                self.respond(200, {"ok": True, "result": app.action(path[5:], payload)})
            except (ConfigurationError, ValueError, UnicodeError, RecursionError, OSError) as error:
                self.respond(409, {"ok": False, "error": error.as_dict() if isinstance(error, ConfigurationError) else {"code": "REQUEST", "message": "Request could not be processed; reload state before retrying"}})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.application = app
    return server


def serve(directory, port=8766):
    server = make_server(directory, port)
    print(f"Disconnected setup workbench: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return {"stopped": True, "simulation_only": True}
