"""Temporary-state localhost integration check; no external network or API keys."""
from copy import deepcopy
from datetime import datetime, timezone
from http.client import HTTPConnection
import importlib.util
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from controller_config.setup_ai import AiSetupAdvisor
from controller_config.setup_web import make_server


def main():
    spec = importlib.util.spec_from_file_location("fixture", ROOT / "tests/test_setup_ai.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    with TemporaryDirectory() as directory:
        server = make_server(directory, port=0)
        app = server.application
        app.service.initialize()
        app.ledger.create("http-failure-fixture", cap_microdollars=24_000)
        draft = app.service.draft_template("sim-mill-3axis")
        app.service.save_draft(draft, expected_revision=0)
        transport = fixture.FakeTransport(TimeoutError("fixture timeout"))
        app.advisor = AiSetupAdvisor(app.service, app.ledger, Path(directory) / "cache",
                                    deepcopy(fixture.CONFIG), transport=transport)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            connection.request("GET", "/")
            page = connection.getresponse().read().decode()
            token = re.search(r'name="setup-token" content="([^"]+)"', page)[1]
            headers = {"Content-Type": "application/json", "X-Setup-Token": token,
                       "Origin": f"http://127.0.0.1:{server.server_port}"}
            results = []
            for suffix, expected, calls in (("A", "AI_PROVIDER_UNCERTAIN", 2),
                                           ("A", "AI_PENDING", 2),
                                           ("B", "AI_PROVIDER_UNCERTAIN", 4),
                                           ("C", "BUDGET_EXHAUSTED", 4)):
                body = {"facts": fixture.FACTS + " " + suffix,
                        "expected_revision": 1, "allow_paid": True}
                connection.request("POST", "/api/paid_advice", json.dumps(body), headers)
                response = connection.getresponse()
                data = json.loads(response.read())
                assert response.status == 409 and data["error"]["code"] == expected, data
                assert len(transport.calls) == calls
                budget = app.ledger.status()
                assert budget["spent_microdollars"] + budget["outstanding_microdollars"] <= budget["cap_microdollars"]
                results.append({"facts_case": suffix, "HTTP_status": response.status,
                                "error_code": expected, "fake_provider_requests": calls,
                                "held_microdollars": budget["outstanding_microdollars"]})
            assert budget["outstanding_microdollars"] == 24_000
            assert budget["request_count"] == 2
            connection.request("GET", "/api/context", headers={"X-Setup-Token": token})
            recovered = json.loads(connection.getresponse().read())["result"]
            assert recovered["budget"]["outstanding_microdollars"] == 24_000
            assert recovered["setup"]["draft"] == draft
            return {"recorded_utc": datetime.now(timezone.utc).isoformat(), "passed": True,
                    "scope": "localhost HTTP plus actual setup service, budget, advisor; fake provider",
                    "external_network_calls": 0, "API_key_reads": 0,
                    "cap_microdollars": 24_000, "checks": results}
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
