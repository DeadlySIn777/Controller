"""Loopback HTTP tests using temporary simulation stores; no paid/hardware calls."""
import http.client
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from controller_config.setup_service import example_draft
from controller_config.service import canonical
from controller_config.setup_web import make_server, MAX_BODY


class SetupWebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.server = make_server(self.folder, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.host = f'127.0.0.1:{self.server.server_port}'
        status, _, body = self.request('/', authorize=False)
        self.assertEqual(status, 200)
        self.token = re.search(r'name="setup-token" content="([^"]+)"', body.decode()).group(1)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, payload=None, *, raw=None, headers=None, extra=(), authorize=True,
                method=None):
        method = method or ('POST' if payload is not None or raw is not None else 'GET')
        body = raw if raw is not None else json.dumps(payload).encode() if payload is not None else b''
        fields = {'Host': self.host}
        if authorize:
            fields['X-Setup-Token'] = self.token
        if method == 'POST':
            fields.update(Origin='http://' + self.host,
                          **{'Content-Type': 'application/json', 'Content-Length': str(len(body))})
        fields.update(headers or {})
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.putrequest(method, path, skip_host=True)
            for key, value in list(fields.items()) + list(extra):
                if value is not None:
                    connection.putheader(key, value)
            connection.endheaders(body)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def api(self, action, payload=None):
        status, _, body = self.request('/api/' + action, payload)
        value = json.loads(body)
        self.assertEqual(status, 200, value)
        self.assertTrue(value['ok'], value)
        return value['result']

    def test_loopback_static_security_headers_and_no_auto_state(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        status, headers, body = self.request('/', authorize=False)
        self.assertEqual(status, 200)
        self.assertIn('frame-ancestors \'none\'', headers['Content-Security-Policy'])
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['Referrer-Policy'], 'no-referrer')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertNotIn(b'__SETUP_TOKEN__', body)
        self.assertEqual(list(self.folder.iterdir()), [])
        for resource in ('/setup.js', '/setup.css'):
            self.assertEqual(self.request(resource, authorize=False)[0], 200)

    def test_unknown_api_and_traversal_always_receive_json_not_found(self):
        for route in ('/api/unknown', '/api/context/extra', '/../PROJECT_MEMORY.md',
                      '/%2e%2e/PROJECT_MEMORY.md', '/favicon.ico'):
            with self.subTest(route=route):
                status, _, body = self.request(route)
                self.assertEqual(status, 404)
                self.assertEqual(json.loads(body)['error']['code'], 'NOT_FOUND')

    def test_host_token_and_origin_checks_deny_without_writing(self):
        for field, value in (('Host', 'evil.example'), ('Host', 'localhost:' + str(self.server.server_port)),
                             ('X-Setup-Token', None), ('X-Setup-Token', 'wrong'),
                             ('X-Setup-Token', '\xff'), ('Origin', 'https://evil.example'),
                             ('Origin', None)):
            with self.subTest(field=field, value=value):
                status, _, body = self.request('/api/initialize', {}, headers={field: value})
                self.assertEqual(status, 403, body)
                self.assertFalse(json.loads(body)['ok'])
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_read_apis_also_require_token(self):
        for route in ('/api/context', '/api/export'):
            self.assertEqual(self.request(route, authorize=False)[0], 403)

    def test_duplicate_authority_headers_rejected(self):
        for key, value in (('Host', self.host), ('Origin', 'http://' + self.host),
                           ('X-Setup-Token', self.token)):
            with self.subTest(header=key):
                self.assertEqual(self.request('/api/initialize', {}, extra=[(key, value)])[0], 403)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_request_framing_content_type_and_limit_rejected(self):
        cases = [{'Content-Length': str(MAX_BODY + 1)}, {'Content-Length': '-2'},
                 {'Content-Length': '+2'}, {'Content-Length': 'bad'}, {'Content-Length': None},
                 {'Content-Length': '2,2'}, {'Content-Type': 'text/plain'},
                 {'Transfer-Encoding': 'chunked'}, {'Transfer-Encoding': ''}]
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.request('/api/initialize', {}, headers=headers)[0], 409)
        for duplicate in (('Content-Length', '2'), ('Content-Type', 'application/json')):
            self.assertEqual(self.request('/api/initialize', {}, extra=[duplicate])[0], 409)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_invalid_duplicate_and_nonfinite_json_and_wrong_fields_rejected(self):
        for raw in (b'not json', b'{"a":1,"a":2}', b'{"a":NaN}', b'[]', b'null',
                    b'{"execute":true}', b'{"\xff":1}', b'[' * 1200 + b']' * 1200):
            with self.subTest(raw=raw[:30]):
                status, _, body = self.request('/api/initialize', raw=raw)
                self.assertEqual(status, 409, body)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_simulation_setup_preview_commit_recovery_and_export(self):
        context = self.api('context')
        self.assertFalse(context['paid_ai_enabled'])
        self.assertTrue(context['simulation_only'])
        initial = self.api('initialize', {})
        template = self.api('template', {'profile_id': 'sim-machine-12motor'})
        self.assertEqual(len(template['motors']), 12)
        self.api('save', {'draft': template, 'expected_revision': initial['current_revision']})
        self.assertEqual(self.request('/api/preview', {})[0], 409)
        status = self.api('context')['setup']
        draft = example_draft('sim-machine-12motor')
        self.api('save', {'draft': draft, 'expected_revision': status['current_revision']})
        plan = self.api('preview', {})
        committed = self.api('commit', {'plan': plan, 'request_id': 'http-test-commit'})
        replay = self.api('commit', {'plan': plan, 'request_id': 'http-test-commit'})
        self.assertTrue(replay['replayed'])
        result = self.api('export')
        self.assertEqual(result['generation'], 1)
        self.assertFalse(result['motion_authorized'])
        self.assertTrue(result['outputs_inhibited'])
        self.assertFalse(result['homed'])
        self.assertEqual(result['machine_commands'], [])
        restore = self.api('restore', {'generation': 1})
        self.assertEqual(restore['operation'], 'restore')
        self.assertFalse(restore['motion_authorized'])
        self.assertEqual(self.request('/api/save', {'draft': draft, 'expected_revision': 0})[0], 409)
        self.assertFalse(committed['motion_authorized'])

    def test_guidance_is_nonactuating_and_unknown_actions_denied(self):
        self.api('initialize', {})
        for question in ('run job', 'do not start spindle', 'What does home mean?', '"jog X10"'):
            result = self.api('guidance', {'question': question})
            self.assertFalse(result['executed'])
            self.assertEqual(result['machine_commands'], [])
            self.assertEqual(result['paid_calls'], 0)
        self.assertEqual(self.request('/api/runJob', {})[0], 409)
        self.assertEqual(self.request('/api/paid_advice', {})[0], 409)

    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for the actual browser-number round trip')
    def test_exact_plan_string_survives_javascript_preview_commit_and_restore(self):
        def javascript_roundtrip(value):
            # Only stdin/stdout JSON; no app, transport, network or filesystem API.
            script = "let s='';process.stdin.setEncoding('utf8');process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s))));"
            return subprocess.run([shutil.which('node'), '-e', script],
                                  input=json.dumps(value).encode(), stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, check=True, timeout=5).stdout

        initial = self.api('initialize', {})
        draft = example_draft('sim-machine-12motor')
        draft['motors'][0]['max_velocity_units_per_second'] = 1e-6
        self.api('save', {'draft': draft, 'expected_revision': initial['current_revision']})
        status, _, body = self.request('/api/preview', {})
        self.assertEqual(status, 200)
        envelope = json.loads(body)
        self.assertEqual(envelope['commit_payload'], canonical(envelope['result']).decode())
        self.assertIn('640.0', envelope['commit_payload'])
        self.assertIn('1e-06', envelope['commit_payload'])
        normalized = json.loads(javascript_roundtrip(envelope))
        self.assertNotEqual(canonical(envelope['result']), canonical(normalized['result']))
        before = (self.folder / 'setup.json').read_bytes()
        status, _, rejected = self.request('/api/commit', raw=javascript_roundtrip({
            'plan': normalized['result'], 'request_id': 'numeric-roundtrip-negative-control'}))
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(rejected)['error']['code'], 'SETUP_PLAN_CHANGED')
        self.assertEqual((self.folder / 'setup.json').read_bytes(), before)
        self.assertEqual(normalized['commit_payload'], envelope['commit_payload'])
        request = javascript_roundtrip({'plan': normalized['commit_payload'], 'request_id': 'opaque-plan'})
        status, _, committed = self.request('/api/commit', raw=request)
        self.assertEqual(status, 200, committed)
        self.assertFalse(json.loads(committed)['result']['motion_authorized'])
        status, _, replayed = self.request('/api/commit', raw=request)
        self.assertEqual(status, 200, replayed)
        self.assertTrue(json.loads(replayed)['result']['replayed'])
        status, _, body = self.request('/api/restore', {'generation': 1})
        self.assertEqual(status, 200)
        restore = json.loads(javascript_roundtrip(json.loads(body)))
        self.assertEqual(restore['result']['operation'], 'restore')
        self.assertEqual(canonical(json.loads(restore['commit_payload'])), canonical(json.loads(body)['result']))
        status, _, restored = self.request('/api/commit', raw=javascript_roundtrip({
            'plan': restore['commit_payload'], 'request_id': 'opaque-restore'}))
        self.assertEqual(status, 200, restored)
        self.assertFalse(json.loads(restored)['result']['motion_authorized'])

    def test_serialized_plan_rejects_invalid_tampered_and_stale_content_without_writes(self):
        initial = self.api('initialize', {})
        draft = example_draft('sim-machine-12motor')
        self.api('save', {'draft': draft, 'expected_revision': initial['current_revision']})
        _, _, body = self.request('/api/preview', {})
        plan = json.loads(body)['commit_payload']
        before = (self.folder / 'setup.json').read_bytes()
        for malformed in ('not json', '{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}',
                          '{"a":1e999}', '[]', 'null', '[' * 1200 + ']' * 1200):
            with self.subTest(plan=malformed[:30]):
                status, _, _ = self.request('/api/commit', {'plan': malformed, 'request_id': 'invalid-string'})
                self.assertEqual(status, 409)
                self.assertEqual((self.folder / 'setup.json').read_bytes(), before)
        tampered = plan.replace('"review_required":true', '"review_required":false')
        self.assertNotEqual(tampered, plan)
        status, _, body = self.request('/api/commit', {'plan': tampered, 'request_id': 'tampered-string'})
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)['error']['code'], 'SETUP_PLAN_CHANGED')
        self.assertEqual((self.folder / 'setup.json').read_bytes(), before)
        current = self.api('export')
        draft['motors'][0]['max_velocity_units_per_second'] = 11
        self.api('save', {'draft': draft, 'expected_revision': current['current_revision']})
        newer = (self.folder / 'setup.json').read_bytes()
        status, _, body = self.request('/api/commit', {'plan': plan, 'request_id': 'stale-string'})
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)['error']['code'], 'SETUP_STALE')
        self.assertEqual((self.folder / 'setup.json').read_bytes(), newer)

    def test_corrupt_state_is_reported_without_overwriting(self):
        path = self.folder / 'setup.json'
        path.write_bytes(b'corrupt user source')
        for method, route, payload in (('GET', '/api/context', None), ('POST', '/api/initialize', {})):
            status, _, _ = self.request(route, payload, method=method)
            self.assertEqual(status, 409)
            self.assertEqual(path.read_bytes(), b'corrupt user source')

    def test_paid_advice_is_disabled_by_default(self):
        self.api('initialize', {})
        payload = {'facts': 'Test-only user facts', 'expected_revision': 0, 'allow_paid': True}
        status, _, body = self.request('/api/paid_advice', payload)
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)['error']['code'], 'AI_DISABLED')
        self.assertFalse(self.api('context')['paid_ai_enabled'])

    def test_corrupt_budget_preserved_while_offline_workflow_remains_available(self):
        initial = self.api('initialize', {})
        budget_path = self.folder / 'budget.json'
        previous_schema = json.loads(budget_path.read_bytes())
        previous_schema.pop('administrative_hold')
        corrupt = json.dumps(previous_schema).encode()
        budget_path.write_bytes(corrupt)
        adapter = Mock()
        adapter.capabilities.return_value = {'machine_authority': False}
        self.server.application.advisor = adapter
        context = self.api('context')
        self.assertIsNone(context['budget'])
        self.assertEqual(context['budget_error']['code'], 'BUDGET_CORRUPT')
        self.assertFalse(context['paid_ai_enabled'])
        self.api('initialize', {})
        self.api('save', {'draft': example_draft('sim-machine-12motor'),
                          'expected_revision': initial['current_revision']})
        plan = self.api('preview', {})
        self.api('commit', {'plan': plan, 'request_id': 'offline-with-unavailable-allowance'})
        export = self.api('export')
        self.assertEqual(export['generation'], 1)
        self.assertFalse(export['motion_authorized'])
        status, _, body = self.request('/api/paid_advice', {
            'facts': 'Test-only facts', 'expected_revision': export['current_revision'], 'allow_paid': True})
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)['error']['code'], 'BUDGET_CORRUPT')
        adapter.advise.assert_not_called()
        self.assertEqual(budget_path.read_bytes(), corrupt)

    def test_budget_io_failure_keeps_local_context_and_paid_requests_fail_closed(self):
        self.api('initialize', {})
        original = (self.folder / 'budget.json').read_bytes()
        adapter = Mock()
        adapter.capabilities.return_value = {'machine_authority': False}
        self.server.application.advisor = adapter
        with patch.object(self.server.application.ledger, 'status', side_effect=OSError('test-only read failure')):
            context = self.api('context')
            self.assertTrue(context['setup']['initialized'])
            self.assertIsNone(context['budget'])
            self.assertEqual(context['budget_error']['code'], 'BUDGET_IO')
            self.assertFalse(context['paid_ai_enabled'])
            self.assertTrue(self.api('export')['initialized'])
            self.assertEqual(self.request('/api/paid_advice', {
                'facts': 'Test-only facts', 'expected_revision': 0, 'allow_paid': True})[0], 409)
        adapter.advise.assert_not_called()
        self.assertEqual((self.folder / 'budget.json').read_bytes(), original)

    def test_configured_advice_requires_opt_in_and_never_saves_proposal(self):
        self.api('initialize', {})
        original = (self.folder / 'setup.json').read_bytes()
        adapter = Mock()
        adapter.capabilities.return_value = {'machine_authority': False, 'model_tools': []}
        adapter.advise.return_value = {'status': 'proposal', 'proposed_draft': {'test_only': True},
            'executed': False, 'machine_commands': [], 'simulation_only': True, 'paid_calls': 0}
        self.server.application.advisor = adapter
        self.assertTrue(self.api('context')['paid_ai_enabled'])
        payload = {'facts': 'Test-only user facts', 'expected_revision': 0, 'allow_paid': False}
        for flag in (False, None, 1, 'true'):
            with self.subTest(flag=flag):
                self.assertEqual(self.request('/api/paid_advice', {**payload, 'allow_paid': flag})[0], 409)
        self.assertEqual(self.request('/api/paid_advice', {**payload, 'allow_paid': True,
                                                        'execute': True})[0], 409)
        self.assertEqual(self.request('/api/paid_advice', {**payload, 'allow_paid': True},
                                      headers={'Origin': 'https://evil.example'})[0], 403)
        adapter.advise.assert_not_called()
        result = self.api('paid_advice', {**payload, 'allow_paid': True})
        adapter.advise.assert_called_once_with(payload['facts'], expected_revision=0, allow_paid=True)
        self.assertFalse(result['executed'])
        self.assertEqual(result['machine_commands'], [])
        self.assertEqual((self.folder / 'setup.json').read_bytes(), original)

    def test_provider_config_is_only_trusted_server_input(self):
        with patch('controller_config.setup_ai.AiSetupAdvisor') as factory:
            server = make_server(self.folder / 'other', port=0, provider_config={'test_only': 'config'})
            try:
                self.assertEqual(factory.call_args.args[-1], {'test_only': 'config'})
                factory.return_value.advise.assert_not_called()
            finally:
                server.server_close()
        self.assertEqual(self.request('/api/provider_config', {'approved': True})[0], 409)


if __name__ == '__main__':
    unittest.main()
