"""Export source-only GitHub Actions kit. Never includes device backups or keys."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT_FILES = {'CMakeLists.txt', 'LICENSE', '.clang-format', '.gitignore',
              'sdkconfig.defaults', 'README.md'}
SOURCE_DIRS = {'main', 'scripts', 'partitions', 'docs', 'docker'}
EXCLUDED = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache',
            'test-results', 'backups', 'build', 'managed_components', 'components', 'releases'}


def source_files(source):
    source = source.resolve()
    for path in sorted(source.rglob('*')):
        relative = path.relative_to(source)
        parts = relative.parts
        if any(part in EXCLUDED or part.startswith('.env') for part in parts):
            continue
        allowed = (len(parts) == 1 and (path.name in ROOT_FILES or path.name.startswith('sdkconfig.defaults.')))
        allowed |= parts[0] in SOURCE_DIRS
        allowed |= len(parts) > 2 and parts[:2] == ('.github', 'ci')
        if not allowed:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError(f'Refusing linked source path: {relative}')
        if not path.is_file() or path.suffix in {'.pyc', '.log'} or path.name == 'lang_config.h':
            continue
        yield path, 'firmware/' + relative.as_posix()


def build_package(source, output):
    source, output = Path(source), Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    files = list(source_files(source))
    files.extend([(HERE / 'verify_firmware.py', 'verify_firmware.py'),
                  (HERE / 'verify_offline_voice.py', 'verify_offline_voice.py'),
                  (HERE / 'remote-build/README.md', 'README.md'),
                  (HERE / 'remote-build/.github/workflows/build-anmi.yml', '.github/workflows/build-anmi.yml')])
    records = {}
    temporary = output.with_suffix('.zip.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path, name in files:
                data = path.read_bytes()
                # Checkouts on Windows may contain CRLF; shell entrypoints need LF.
                if path.suffix in {'.py', '.sh', '.cc', '.cpp', '.h', '.yml', '.yaml', '.md', '.txt', '.json', '.csv'} or path.name.startswith('sdkconfig.defaults'):
                    data = data.replace(b'\r\n', b'\n')
                archive.writestr(name, data)
                records[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            archive.writestr('SOURCE_MANIFEST.json', json.dumps({
                'upstream_revision': 'c435f99a88066029ec2dbd2d758c8cc9d051565b',
                'board': 'ricky-war-tank', 'files': records,
                'contains_device_backup': False,
            }, ensure_ascii=False, indent=2))
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return {'path': str(output), 'files': len(records), 'bytes': output.stat().st_size,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'dist/anmi-ricky-source.zip')
    args = parser.parse_args()
    print(json.dumps(build_package(HERE / 'xiaozhi-esp32', args.output), indent=2))
