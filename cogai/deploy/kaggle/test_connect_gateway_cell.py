import contextlib
import io
import json
from pathlib import Path
import runpy
import types
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError


CELL = Path(__file__).with_name('connect_gateway_cell.py')
DOMAIN = 'example.ngrok-free.dev'
MACS = ['aa:bb:cc:dd:ee:01', 'aa:bb:cc:dd:ee:02']


class GatewayCellTests(unittest.TestCase):
    def run_cell(self, failure=None, wrong_host=False):
        requests = []
        output = io.StringIO()
        connect = Mock()
        module = types.ModuleType('pyngrok')
        module.conf = types.SimpleNamespace(get_default=lambda: types.SimpleNamespace())
        module.ngrok = types.SimpleNamespace(
            get_tunnels=lambda: [types.SimpleNamespace(public_url='https://' + DOMAIN)],
            connect=connect)
        exception = types.ModuleType('pyngrok.exception')
        exception.PyngrokNgrokHTTPError = type('PyngrokNgrokHTTPError', (Exception,), {})

        def open_request(request, timeout):
            requests.append(request)
            public = request.full_url.startswith('https:')
            if failure and failure[0] == public:
                raise HTTPError(request.full_url, failure[1], 'error', {}, None)
            host = 'wrong.example' if public and wrong_host else DOMAIN
            body = {'websocket': {'url': f'wss://{host}/xiaozhi/v1/', 'token': 'response-secret'}}
            return io.BytesIO(json.dumps(body).encode())

        try:
            with patch.dict('sys.modules', {'pyngrok': module, 'pyngrok.exception': exception}), \
                    patch('urllib.request.urlopen', side_effect=open_request), \
                    contextlib.redirect_stdout(output):
                runpy.run_path(str(CELL), init_globals={
                    'NGROK_DOMAIN': DOMAIN, 'NGROK_AUTHTOKEN': 'agent-secret',
                    'ANMI_DEVICE_TOKENS': ';'.join(mac + '=input-secret-' + str(i) for i, mac in enumerate(MACS))})
        except RuntimeError as error:
            return str(error), requests, connect, output.getvalue()
        return None, requests, connect, output.getvalue()

    def test_checks_both_devices_locally_and_publicly_without_recreating_tunnel(self):
        error, requests, connect, output = self.run_cell()
        self.assertIsNone(error)
        self.assertEqual([r.get_header('Device-id') for r in requests], MACS * 2)
        connect.assert_not_called()
        self.assertNotIn('secret', output)
        self.assertEqual(output.count('OTA công khai HTTP 200:'), 2)

    def test_local_404_stops_before_public_requests(self):
        error, requests, connect, _ = self.run_cell(failure=(False, 404))
        self.assertIn('COGAI_DEVICE_GATEWAY', error)
        self.assertEqual(len(requests), 1)
        connect.assert_not_called()

    def test_public_404_reports_tunnel_problem(self):
        error, requests, _, _ = self.run_cell(failure=(True, 404))
        self.assertIn('tunnel/domain', error)
        self.assertEqual(len(requests), 3)

    def test_stale_device_secret_and_wrong_websocket_host_are_distinguished(self):
        error, _, _, _ = self.run_cell(failure=(False, 403))
        self.assertIn('cell Secrets', error)
        error, _, _, _ = self.run_cell(wrong_host=True)
        self.assertIn('sai host/giao thức', error)


if __name__ == '__main__':
    unittest.main()
