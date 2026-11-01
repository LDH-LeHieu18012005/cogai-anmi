"""Probe a public AnMi gateway without printing or saving device tokens."""
import argparse
import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('origin')
    parser.add_argument('--mac', action='append', default=[])
    args = parser.parse_args()
    origin = args.origin.rstrip('/')
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
        parser.error('Supply an HTTPS origin without credentials, path, or query.')
    for mac in [None, *args.mac]:
        path = '/xiaozhi/ota/' if mac else '/api/health'
        headers = {'User-Agent': 'AnMi-Connection-Diagnostic/1.0', 'ngrok-skip-browser-warning': '1'}
        if mac:
            headers.update({'Device-Id': mac, 'Content-Type': 'application/json'})
        result = {'path': path, 'mac': mac}
        request = urllib.request.Request(origin + path, data=b'{}' if mac else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result['status'] = response.status
                body = json.load(response)
            if mac:
                config = body.get('websocket', {})
                result.update(websocket_url=config.get('url'), websocket_version=config.get('version'), token_present=bool(config.get('token')))
        except urllib.error.HTTPError as error:
            result.update(status=error.code, ngrok_error_code=error.headers.get('ngrok-error-code'))
        except Exception as error:
            # Exception text may include redirected credentials; expose only the type.
            result['error_type'] = type(error).__name__
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
