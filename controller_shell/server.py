"""Appliance shell, preserving the existing setup transport and authority.

The original handler owns tokens, origin checks, cookies, setup operations,
and workbench rendering. Appliance operations reuse those transport checks and
the same local preference/file service as the public appliance CLI.
It does not initialize settings, contact AI, connect hardware or start motion.
"""
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs

from controller_config.setup_web import make_server as make_setup_server, _request_json, MAX_BODY
from controller_config.model import ConfigurationError
from controller_config.service import canonical
from controller_appliance import ApplianceError, ApplianceService

WEB = Path(__file__).with_name("web")
ASSETS = {"/shell.css": "text/css; charset=utf-8",
          "/shell.js": "text/javascript; charset=utf-8",
          "/workbench-shell.css": "text/css; charset=utf-8",
          "/workbench-shell.js": "text/javascript; charset=utf-8",
          "/appliance.css": "text/css; charset=utf-8",
          "/appliance.js": "text/javascript; charset=utf-8",
          "/preferences.js": "text/javascript; charset=utf-8"}


def make_server(directory, port=8769, provider_config=None):
    server = make_setup_server(directory, port, provider_config=provider_config)
    base_handler = server.RequestHandlerClass
    shell_html = (WEB / "index.html").read_text(encoding="utf-8")
    appliance_html = (WEB / "appliance.html").read_text(encoding="utf-8")
    assets = {route: (WEB / route[1:]).read_bytes() for route in ASSETS}
    appliance = ApplianceService(server.application.directory)

    def action(name, payload):
        fields = {"preferences-preview": {"patch", "expected_revision"},
                  "reset-preview": {"scope"}, "undo-preview": set(),
                  "confirm": {"plan", "request_id", "confirmation"},
                  "service-mode": {"enabled", "confirmation"}}
        if type(payload) is not dict or name not in fields or set(payload) != fields[name]:
            raise ConfigurationError("REQUEST", "Unknown appliance action or fields")
        if name == "preferences-preview":
            return appliance.preview_preferences(payload["patch"], payload["expected_revision"])
        if name == "reset-preview":
            return appliance.preview_reset(payload["scope"])
        if name == "undo-preview":
            return appliance.preview_undo()
        if name == "service-mode":
            return appliance.service_mode(payload["enabled"], payload["confirmation"])
        plan = payload["plan"]
        if type(plan) is str:
            if len(plan.encode("utf-8")) > 16_000:
                raise ConfigurationError("REQUEST_SIZE", "Preference plan is too large")
            plan = _request_json(plan)
        return appliance.confirm(plan, payload["request_id"], payload["confirmation"])

    class ShellHandler(base_handler):
        def appliance_error(self, error):
            return self.respond(409, {"ok": False, "error": error.as_dict()
                if isinstance(error, (ConfigurationError, ApplianceError)) else
                {"code": "APPLIANCE_IO", "message": "Appliance state unavailable; preserve its files and refresh before retrying"}})

        def respond(self, status, body, content_type="application/json; charset=utf-8", **kwargs):
            if status == 200 and content_type == "text/html; charset=utf-8":
                if getattr(self, "_workbench", False):
                    body = body.replace("</head>", '<link rel="stylesheet" href="/workbench-shell.css">'
                                        '<script defer src="/workbench-shell.js"></script><script defer src="/preferences.js"></script></head>')
                elif getattr(self, "_appliance_view", None) or urlsplit(self.path).path == "/":
                    match = re.search(r'<meta name="setup-token" content="([A-Za-z0-9_-]+)">', body)
                    if match is None:
                        raise ValueError("The shared service did not supply its session token")
                    view = getattr(self, "_appliance_view", None)
                    body = (appliance_html.replace("__APPLIANCE_VIEW__", view) if view else shell_html).replace("__SETUP_TOKEN__", match.group(1))
                    if getattr(self, "_appliance_launch", False):
                        body = body.replace("</head>", '<meta name="appliance-launch" content="true"></head>').replace("<body>", '<body class="launching"><div class="launch-message" role="status"><b>MOTION X12</b><span>BY GARCIAMECH</span><p>Opening your local workspace…</p></div>')
            return super().respond(status, body, content_type, **kwargs)

        def do_GET(self):
            route = urlsplit(self.path).path
            if self.headers.get_all("Host", []) != [f"127.0.0.1:{self.server.server_port}"]:
                return super().do_GET()
            if route in ASSETS:
                return self.respond(200, assets[route], ASSETS[route])
            if route.startswith("/api/appliance/"):
                if not self.authorized(allow_download_cookie=route == "/api/appliance/download"):
                    return
                try:
                    query = parse_qs(urlsplit(self.path).query, keep_blank_values=True, strict_parsing=True)
                    with self.server.application.lock:
                        if route == "/api/appliance/download":
                            if set(query) != {"id", "sha256"} or any(len(values) != 1 for values in query.values()):
                                raise ConfigurationError("REQUEST", "Exact package identity and digest are required")
                            result = appliance.download(query["id"][0], query["sha256"][0])
                            return self.respond(200, result["data"], result["content_type"], attachment_name=result["metadata"]["filename"])
                        if query:
                            raise ConfigurationError("REQUEST", "Unexpected appliance query fields")
                        if route == "/api/appliance/status":
                            result = appliance.status()
                        elif route == "/api/appliance/files":
                            result = appliance.files()
                        else:
                            return self.respond(404, {"ok": False, "error": {"code": "NOT_FOUND", "message": "Unknown appliance operation"}})
                        return self.respond(200, {"ok": True, "result": result})
                except (ApplianceError, ConfigurationError, OSError, ValueError, UnicodeError, RecursionError) as error:
                    return self.appliance_error(error)
            if route in ("/files", "/settings", "/launch"):
                original_path = self.path
                self._appliance_view = route[1:] if route != "/launch" else None
                self._appliance_launch = route == "/launch"
                try:
                    self.path = "/"
                    return super().do_GET()
                finally:
                    self.path = original_path
            if route == "/workbench":
                original_path = self.path
                self._workbench = True
                try:
                    self.path = "/"
                    return super().do_GET()
                finally:
                    self.path = original_path
            return super().do_GET()

        def do_POST(self):
            path = urlsplit(self.path)
            if not path.path.startswith("/api/appliance/"):
                return super().do_POST()
            if not self.authorized(mutate=True):
                return
            try:
                if path.query or self.headers.get_all("Content-Type", []) != ["application/json"] or self.headers.get_all("Transfer-Encoding", []):
                    raise ConfigurationError("REQUEST", "Exact JSON content type and no query/transfer encoding required")
                lengths = self.headers.get_all("Content-Length", [])
                length = int(lengths[0]) if len(lengths) == 1 and lengths[0].isascii() and lengths[0].isdigit() and len(lengths[0]) <= 8 else -1
                if not 0 < length <= MAX_BODY:
                    raise ConfigurationError("REQUEST_SIZE", "Bounded request length required")
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ConfigurationError("REQUEST_SIZE", "Incomplete request body")
                name = path.path[len("/api/appliance/"):]
                with self.server.application.lock:
                    result = action(name, _request_json(body))
                envelope = {"ok": True, "result": result}
                if name.endswith("-preview"):
                    envelope["commit_payload"] = canonical(result).decode("utf-8")
                return self.respond(200, envelope)
            except (ApplianceError, ConfigurationError, OSError, ValueError, UnicodeError, RecursionError) as error:
                return self.appliance_error(error)

    server.RequestHandlerClass = ShellHandler
    return server
