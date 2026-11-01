"""Write anmi_server.ipynb: runs the AnMi backend on Kaggle behind a fixed ngrok domain."""
import json
from pathlib import Path

CELLS = [
('markdown', """# AnMi server trên Kaggle

Chạy backend AnMi (CogAI) cho robot, sau tên miền ngrok cố định. Robot dùng OTA URL `https://<NGROK_DOMAIN>/xiaozhi/ota/`.

**Chuẩn bị (một lần):**
1. *Add Input* → dataset tải lên từ `anmi-backend.zip` (tạo bằng `cogai/deploy/kaggle/make_bundle.py`; Kaggle tự giải nén cũng được).
2. *Add-ons → Secrets*, bật cho notebook này: `OPENAI_API_KEY`, `NGROK_AUTHTOKEN`, `NGROK_DOMAIN`, `ANMI_DEVICE_TOKENS` (tùy chọn `AZURE_SPEECH_KEY`).
3. *Settings*: **Internet on**. Không cần GPU.
4. Chạy lâu dài: **Save Version → Save & Run All (Commit)**; phiên chạy tối đa 12 giờ rồi dừng.

Không ghi key vào notebook. Robot giữ hội thoại trong bộ nhớ phiên, không lưu xuống đĩa; mọi thứ mất khi phiên Kaggle kết thúc."""),
('code', """from kaggle_secrets import UserSecretsClient

secrets = UserSecretsClient()

def secret(name, required=True):
    try:
        value = secrets.get_secret(name)
    except Exception:
        value = ''
    if required and not value:
        raise SystemExit(f'Thiếu Kaggle Secret: {name} (Add-ons → Secrets)')
    return value

OPENAI_API_KEY = secret('OPENAI_API_KEY')
NGROK_AUTHTOKEN = secret('NGROK_AUTHTOKEN')
NGROK_DOMAIN = secret('NGROK_DOMAIN').removeprefix('https://').strip('/')
ANMI_DEVICE_TOKENS = secret('ANMI_DEVICE_TOKENS')
AZURE_SPEECH_KEY = secret('AZURE_SPEECH_KEY', required=False)
print('Đã đọc secrets. Tên miền:', NGROK_DOMAIN)"""),
('code', """import glob, os, shutil, subprocess, sys, zipfile

APP = '/kaggle/working/anmi'
shutil.rmtree(APP, ignore_errors=True)
bundles = glob.glob('/kaggle/input/**/anmi-backend.zip', recursive=True)
# Kaggle unpacks an uploaded .zip into the dataset, so look for the unpacked backend too.
unpacked = [os.path.dirname(p) for p in glob.glob('/kaggle/input/**/requirements.lock.txt', recursive=True)
            if os.path.exists(os.path.join(os.path.dirname(p), 'app', 'main.py'))]
if bundles:
    zipfile.ZipFile(bundles[0]).extractall(APP)
elif unpacked:
    shutil.copytree(unpacked[0], APP)
else:
    raise SystemExit('Không thấy mã nguồn AnMi: Add Input dataset anmi-backend.')
print('Mã nguồn từ:', bundles[0] if bundles else unpacked[0])
# The backend needs Python 3.12; uv installs it alongside Kaggle's own Python.
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'uv', 'pyngrok'], check=True)
subprocess.run([sys.executable, '-m', 'uv', 'venv', '-q', '--python', '3.12', f'{APP}/.venv'], check=True)
subprocess.run([sys.executable, '-m', 'uv', 'pip', 'install', '-q', '--python', f'{APP}/.venv/bin/python',
                '-r', f'{APP}/requirements.lock.txt'], check=True)
print('Đã cài backend AnMi.')"""),
('code', """import time, urllib.request

# Same live settings as `node cogai/scripts/dev.mjs --live --device`.
env = {**os.environ,
       'COGAI_MODE': 'live', 'COGAI_LLM_API_KEY': OPENAI_API_KEY,
       'COGAI_LLM_BASE_URL': 'https://api.openai.com/v1', 'COGAI_LLM_MODEL': 'gpt-4.1-mini',
       'COGAI_TRANSCRIPTION_MODEL': 'gpt-4o-transcribe',
       'COGAI_SPEECH_PROVIDER': 'auto', 'COGAI_EDGE_VOICE': 'vi-VN-HoaiMyNeural', 'COGAI_EDGE_RATE': '+0%',
       'COGAI_AZURE_SPEECH_KEY': AZURE_SPEECH_KEY, 'COGAI_AZURE_SPEECH_REGION': 'southeastasia',
       'COGAI_LLM_MAX_COMPLETION_TOKENS': '1800', 'COGAI_EXTERNAL_DAILY_CALL_LIMIT': '0',
       'COGAI_RESEARCH_DEEP_ENABLED': 'true', 'COGAI_EMBEDDING_MODEL': 'text-embedding-3-large',
       'COGAI_KNOWLEDGE_DEVELOPMENT': 'true', 'COGAI_VOICE_MAX_RECORDING_SECONDS': '45',
       'COGAI_DEVICE_GATEWAY': 'true', 'COGAI_DEVICE_TOKENS': ANMI_DEVICE_TOKENS,
       'COGAI_DATA_DIR': f'{APP}/data'}
log = open('/kaggle/working/anmi.log', 'w')
server = subprocess.Popen([f'{APP}/.venv/bin/python', '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                           '--port', '8000', '--no-access-log'], cwd=APP, env=env, stdout=log, stderr=subprocess.STDOUT)
for _ in range(60):
    try:
        print(urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).read().decode())
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit('Server không khởi động được, xem /kaggle/working/anmi.log')"""),
('code', Path(__file__).with_name('connect_gateway_cell.py').read_text(encoding='utf-8')),
('code', """# Keep the session alive and report health every 10 minutes (Kaggle stops it at 12 hours).
started = time.time()
while time.time() - started < 11.9 * 3600:
    if server.poll() is not None:
        raise SystemExit('Server đã dừng, xem /kaggle/working/anmi.log')
    turns = [line.strip() for line in open('/kaggle/working/anmi.log', encoding='utf-8', errors='ignore')
             if 'device turn' in line]
    print(time.strftime('%H:%M'), 'AnMi đang chạy |', len(turns), 'lượt nói |', turns[-1] if turns else '')
    time.sleep(600)"""),
]


def main():
    cells = []
    for kind, source in CELLS:
        cell = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True)}
        if kind == 'code':
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                                              'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}
    out = Path(__file__).with_name('anmi_server.ipynb')
    out.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding='utf-8')
    for kind, source in CELLS:  # every code cell must at least compile
        if kind == 'code':
            compile(source, 'cell', 'exec')
    print('wrote', out.name)


if __name__ == '__main__':
    main()
