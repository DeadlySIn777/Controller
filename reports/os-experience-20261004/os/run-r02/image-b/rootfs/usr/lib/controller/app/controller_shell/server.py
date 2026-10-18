"""Appliance shell, preserving the existing setup transport and authority.

The original handler owns tokens, origin checks, cookies, all API operations,
and workbench rendering. This layer changes navigation and presentation only.
It does not initialize settings, contact AI, connect hardware or start motion.
"""
from pathlib import Path
import re
from urllib.parse import urlsplit

from controller_config.setup_web import make_server as make_setup_server

WEB = Path(__file__).with_name("web")
ASSETS = {"/shell.css": "text/css; charset=utf-8",
          "/shell.js": "text/javascript; charset=utf-8",
          "/workbench-shell.css": "text/css; charset=utf-8",
          "/workbench-shell.js": "text/javascript; charset=utf-8"}


def make_server(directory, port=8769, provider_config=None):
    server = make_setup_server(directory, port, provider_config=provider_config)
    base_handler = server.RequestHandlerClass
    shell_html = (WEB / "index.html").read_text(encoding="utf-8")
    assets = {route: (WEB / route[1:]).read_bytes() for route in ASSETS}

    class ShellHandler(base_handler):
        def respond(self, status, body, content_type="application/json; charset=utf-8", **kwargs):
            if status == 200 and content_type == "text/html; charset=utf-8":
                if getattr(self, "_workbench", False):
                    body = body.replace("</head>", '<link rel="stylesheet" href="/workbench-shell.css">'
                                        '<script defer src="/workbench-shell.js"></script></head>')
                elif urlsplit(self.path).path == "/":
                    match = re.search(r'<meta name="setup-token" content="([A-Za-z0-9_-]+)">', body)
                    if match is None:
                        raise ValueError("The shared service did not supply its session token")
                    body = shell_html.replace("__SETUP_TOKEN__", match.group(1))
            return super().respond(status, body, content_type, **kwargs)

        def do_GET(self):
            route = urlsplit(self.path).path
            if self.headers.get_all("Host", []) != [f"127.0.0.1:{self.server.server_port}"]:
                return super().do_GET()
            if route in ASSETS:
                return self.respond(200, assets[route], ASSETS[route])
            if route == "/workbench":
                original_path = self.path
                self._workbench = True
                try:
                    self.path = "/"
                    return super().do_GET()
                finally:
                    self.path = original_path
            return super().do_GET()

    server.RequestHandlerClass = ShellHandler
    return server
