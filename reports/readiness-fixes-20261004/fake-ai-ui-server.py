"""Browser integration fixture: real local service, fake provider, no paid API.

Only creates the dedicated sibling ui-ai-fixture directory, refusing existing
state. No API key/environment access or external network. Not model-quality evidence.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

REPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORT.parents[1]))
from controller_config.setup_ai import AiSetupAdvisor
from controller_config.setup_web import make_server

CONFIG = {"schema_version": 1, "approved": True, "provider": "openai",
          "model": "fixture-snapshot", "model_version": "UI-FAKE-ONLY-v1",
          "pricing": {"currency": "USD", "version": "FAKE-TEST-PRICE-v1",
                      "microdollars_per_million_tokens": {"input_tokens": 1_000_000, "cached_input_tokens": 500_000, "output_tokens": 2_000_000},
                      "microdollars_per_tool_call": {"input_token_count": 0}},
          "pricing_source": "https://developers.openai.com/api/docs/pricing",
          "valid_until": "2099-01-01T00:00:00+00:00", "max_input_tokens": 10_000, "max_output_tokens": 1000}


def main():
    fixture = REPORT / "ui-ai-fixture"
    if fixture.exists() or fixture.is_symlink() or fixture.resolve().parent != REPORT:
        raise SystemExit("Refusing existing or redirected ui-ai-fixture directory; preserve its evidence.")
    server = make_server(fixture, port=8768)
    try:
        fixture.mkdir(exist_ok=False)
        app = server.application
        status = app.action("initialize", {})
        app.service.save_draft(app.service.draft_template("sim-mill-3axis"), status["current_revision"], actor="fake-ui-fixture")
        request_log = fixture / "fake-provider-requests.jsonl"
        def fake_transport(endpoint, payload):
            assert endpoint in ("responses/input_tokens", "responses")
            with request_log.open("a", encoding="utf-8") as log:
                log.write(json.dumps({"provider": "FAKE-ONLY", "endpoint": endpoint, "time_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
            if endpoint == "responses/input_tokens":
                return {"object": "response.input_tokens", "input_tokens": 200}
            proposal = {"proposals": [{"path": "$.motors[0].motor_steps_per_revolution", "value": 200,
                                      "source_quote": "200 full steps per revolution"}], "questions": ["What microstep setting is selected?"]}
            return {"id": "resp_FAKE_UI_ONLY", "model": "fixture-snapshot", "status": "completed",
                    "usage": {"input_tokens": 200, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 30},
                    "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": json.dumps(proposal)}]}]}
        app.advisor = AiSetupAdvisor(app.service, app.ledger, fixture / "advisor-cache", CONFIG, transport=fake_transport)
        print("FAKE PROVIDER ONLY — zero paid API calls, no credentials, no live model-quality claim", flush=True)
        print("http://127.0.0.1:8768", flush=True)
        print(f"Fake request-count evidence: {request_log}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
