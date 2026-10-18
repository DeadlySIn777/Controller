"""Loopback setup UI. No physical transport; paid proposals require configured opt-in."""
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
    def __init__(self, directory, provider_config=None):
        self.directory = Path(directory).resolve()
        self.service = SetupService(self.directory / "setup.json")
        self.ledger = BudgetLedger(self.directory / "budget.json")
        self.lock = threading.Lock()
        self.advisor = None
        if provider_config is not None:
            from .setup_ai import AiSetupAdvisor
            self.advisor = AiSetupAdvisor(self.service, self.ledger,
                                          self.directory / "advisor-cache", provider_config)

    def context(self):
        with self.lock:
            budget, budget_error = None, None
            try:
                if (self.directory / "budget.json").exists():
                    budget = self.ledger.status()
            except (ConfigurationError, OSError) as error:
                budget_error = (error.as_dict() if isinstance(error, ConfigurationError) else
                                {"code": "BUDGET_IO", "message": "Unable to read allowance; retain its file and reconcile before paid use"})
            return {"setup": self.service.status(), "profiles": self.service.profiles(),
                    "capabilities": self.service.capabilities(),
                    "budget": budget, "budget_error": budget_error,
                    "paid_ai_enabled": self.advisor is not None and budget is not None and not budget["blocked"],
                    "paid_ai": self.advisor.capabilities() if self.advisor is not None else None,
                    "simulation_only": True}

    def export(self):
        with self.lock:
            return self.service.status()

    def action(self, action, payload):
        if type(payload) is not dict:
            raise ConfigurationError("REQUEST", "Expected an object")
        fields = {"initialize": set(), "template": {"profile_id"},
                  "save": {"draft", "expected_revision"}, "preview": set(),
                  "commit": {"plan", "request_id"}, "restore": {"generation"},
                  "guidance": {"question"},
                  "paid_advice": {"facts", "expected_revision", "allow_paid"}}
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
            if action == "paid_advice":
                if self.advisor is None:
                    raise ConfigurationError("AI_DISABLED", "Paid advice is not configured; local guidance remains available")
                if payload["allow_paid"] is not True:
                    raise ConfigurationError("AI_PAID_OPT_IN", "Explicit approval is required for this bounded paid request")
                budget = self.ledger.status()
                if budget["blocked"]:
                    raise ConfigurationError("BUDGET_BLOCKED", "Reconcile the held allowance before requesting paid advice")
                return self.advisor.advise(payload["facts"], expected_revision=payload["expected_revision"],
                                           allow_paid=True)
            from .setup_assistant import local_guidance
            return local_guidance(self.service, payload["question"])


def make_server(directory, port=8766, provider_config=None):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ConfigurationError("PORT", "Port must be 0–65535")
    app = SetupApplication(directory, provider_config=provider_config)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

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
            if self.headers.get_all("Host", []) != [host]:
                self.respond(403, {"ok": False, "error": {"code": "HOST", "message": "Use the exact local address printed by the server"}})
                return False
            if mutate and self.headers.get_all("Origin", []) != ["http://" + host]:
                self.respond(403, {"ok": False, "error": {"code": "ORIGIN", "message": "Same-origin UI required"}})
                return False
            tokens = self.headers.get_all("X-Setup-Token", [])
            if len(tokens) != 1 or not hmac.compare_digest(tokens[0].encode("utf-8"), token.encode("ascii")):
                self.respond(403, {"ok": False, "error": {"code": "TOKEN", "message": "Reload the local setup page"}})
                return False
            return True

        def do_GET(self):
            if self.headers.get_all("Host", []) != [f"127.0.0.1:{self.server.server_port}"]:
                self.respond(403, {"ok": False, "error": {"code": "HOST", "message": "Local address required"}})
                return
            try:
                path = urlsplit(self.path).path
                if path == "/":
                    self.respond(200, (WEB / "setup.html").read_text(encoding="utf-8").replace("__SETUP_TOKEN__", token), "text/html; charset=utf-8")
                elif path in ("/setup.js", "/setup.css"):
                    self.respond(200, (WEB / path[1:]).read_text(encoding="utf-8"), "text/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8")
                elif path in ("/api/context", "/api/export") and self.authorized():
                    self.respond(200, {"ok": True, "result": app.context() if path.endswith("context") else app.export()})
                elif path not in ("/api/context", "/api/export"):
                    self.respond(404, {"ok": False, "error": {"code": "NOT_FOUND", "message": "Unknown page"}})
            except (ConfigurationError, OSError, ValueError, UnicodeError, RecursionError) as error:
                self.respond(409, {"ok": False, "error": error.as_dict() if isinstance(error, ConfigurationError) else {"code": "IO_ERROR", "message": "Unable to read setup state"}})

        def do_POST(self):
            if not self.authorized(mutate=True):
                return
            try:
                if self.headers.get_all("Content-Type", []) != ["application/json"] or self.headers.get_all("Transfer-Encoding", []):
                    raise ConfigurationError("REQUEST", "JSON with a bounded Content-Length is required")
                lengths = self.headers.get_all("Content-Length", [])
                length = int(lengths[0]) if (len(lengths) == 1 and lengths[0].isascii() and
                                             lengths[0].isdigit() and len(lengths[0]) <= 6) else -1
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
                data = self.rfile.read(length)
                if len(data) != length:
                    raise ConfigurationError("REQUEST_SIZE", "Incomplete request body")
                payload = json.loads(data, object_pairs_hook=pairs,
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


def serve(directory, port=8766, provider_config=None):
    server = make_server(directory, port, provider_config=provider_config)
    print(f"Disconnected setup workbench: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return {"stopped": True, "simulation_only": True}
