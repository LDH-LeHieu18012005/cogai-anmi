"""Package the AnMi backend for a Kaggle dataset: code and the knowledge corpus only.

Never included: backend/.env, data/.key, devices.json, cogai.sqlite3 or any user data.
Usage (from the workspace root): python cogai/deploy/kaggle/make_bundle.py
"""
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / 'backend'
OUT = Path(__file__).resolve().parent / 'dist' / 'anmi-backend.zip'
INCLUDE = ['pyproject.toml', 'requirements.lock.txt', 'data/knowledge.sqlite3']


def main():
    OUT.parent.mkdir(exist_ok=True)
    code = [p for p in (BACKEND / 'app').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files = sorted(code) + [BACKEND / name for name in INCLUDE]
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(BACKEND).as_posix())
    names = zipfile.ZipFile(OUT).namelist()
    assert not any(n.endswith(('.env', '.key', 'devices.json', 'cogai.sqlite3')) for n in names)
    print(f'dist/{OUT.name}: {OUT.stat().st_size // 1024} KB, {len(names)} files')


if __name__ == '__main__':
    main()
