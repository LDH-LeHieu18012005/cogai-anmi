"""Paste this cell after the backend startup cell in the Kaggle notebook."""
import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from pyngrok import conf, ngrok
from pyngrok.exception import PyngrokNgrokHTTPError

domain = NGROK_DOMAIN.strip().removeprefix('https://').rstrip('/')
if not domain or any(char in domain for char in '/?#@'):
    raise RuntimeError('NGROK_DOMAIN chỉ được chứa tên miền, không kèm đường dẫn OTA.')

macs = []
for entry in ANMI_DEVICE_TOKENS.strip().split(';'):
    mac, separator, token = entry.strip().partition('=')
    mac = mac.lower().replace('-', ':').strip()
    if not separator or not token.strip() or not re.fullmatch(r'[0-9a-f]{2}(:[0-9a-f]{2}){5}', mac):
        raise RuntimeError('ANMI_DEVICE_TOKENS phải có dạng MAC=token;MAC=token, trên một dòng.')
    if mac in macs:
        raise RuntimeError(f'MAC bị lặp trong Secret: {mac}')
    macs.append(mac)


def check_ota(origin, mac, location):
    request = urllib.request.Request(
        origin + '/xiaozhi/ota/', data=b'{}', method='POST',
        headers={'Device-Id': mac, 'Content-Type': 'application/json',
                 'User-Agent': 'AnMi-Notebook/1.0', 'ngrok-skip-browser-warning': '1'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            answer = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            detail = ('Backend thiếu route OTA: kiểm tra COGAI_DEVICE_GATEWAY=true và gói backend.'
                      if location == 'local' else
                      'Backend nội bộ đã đạt nhưng URL công khai trả 404: kiểm tra tunnel/domain ngrok.')
        elif error.code == 403:
            detail = f'Backend chưa chấp nhận MAC {mac}. Chạy lại cell Secrets và khởi động lại backend.'
        else:
            detail = 'Kiểm tra notebook backend và trạng thái tunnel ngrok.'
        raise RuntimeError(f'{location}: HTTP {error.code}. {detail}') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError(f'{location}: không kết nối được. Kiểm tra backend, mạng và tunnel.') from None
    except ValueError:
        raise RuntimeError(f'{location}: phản hồi không phải JSON của AnMi.') from None
    websocket = answer.get('websocket', {})
    if not websocket.get('url') or not websocket.get('token'):
        raise RuntimeError(f'{location}: phản hồi OTA thiếu cấu hình WebSocket.')
    if location == 'public':
        endpoint = urlsplit(websocket['url'])
        if endpoint.scheme != 'wss' or endpoint.netloc != domain or endpoint.path != '/xiaozhi/v1/':
            raise RuntimeError('OTA trả URL WebSocket sai host/giao thức. Kiểm tra proxy HTTPS của backend.')
    return websocket['url']  # Never print or save the token.


# Verify the actual local gateway before exposing or diagnosing a tunnel.
for mac in macs:
    check_ota('http://127.0.0.1:8000', mac, 'local')
    print('Backend nội bộ OK:', mac)

conf.get_default().auth_token = NGROK_AUTHTOKEN
public_origin = f'https://{domain}'
tunnel = next((item for item in ngrok.get_tunnels()
               if item.public_url.rstrip('/') == public_origin), None)
if tunnel is None:
    try:
        tunnel = ngrok.connect(8000, 'http', url=public_origin)
    except PyngrokNgrokHTTPError:
        tunnel = ngrok.connect(8000, 'http', domain=domain)

OTA_URL = public_origin + '/xiaozhi/ota/'
print('OTA URL cho cả hai robot:', OTA_URL)
for mac in macs:
    websocket_url = check_ota(public_origin, mac, 'public')
    print('OTA công khai HTTP 200:', mac, '| WebSocket:', websocket_url)
