"""Verify exported Ricky images and their partition layout without flashing."""
import hashlib
import json
import struct
import sys
from pathlib import Path

def require(condition, message):
    if not condition:
        raise ValueError(message)


output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / 'output-ricky-20261026'
# Never leave a stale PASS report next to a later corrupt or failed build.
(output / 'verification.json').unlink(missing_ok=True)
manifest = json.loads((output / 'manifest.json').read_text('utf-8'))
require(manifest['status'] == 'succeeded', 'Build did not succeed.')
require(manifest['board_type'] == 'ricky-war-tank', 'Unexpected board type.')
require(manifest['language'] == 'vi-VN' and manifest['wake_word'] == 'disabled', 'Unexpected language or wake-word configuration.')
names = [item['file'] for item in manifest['artifacts']]
require(len(names) == 2 and set(names) == {'xiaozhi.bin', 'merged-binary.bin'}, 'Manifest must list exactly the app and merged images.')
for item in manifest['artifacts']:
    require(0 < (output / item['file']).stat().st_size <= 16 * 1024 * 1024, 'Invalid image size.')
    data = (output / item['file']).read_bytes()
    require(len(data) == item['size'], f"Size mismatch: {item['file']}")
    require(hashlib.sha256(data).hexdigest() == item['sha256'], f"Hash mismatch: {item['file']}")

full = (output / 'merged-binary.bin').read_bytes()
app = (output / 'xiaozhi.bin').read_bytes()
require(len(full) >= 0x9000 and len(app) >= 256, 'Images are truncated.')
require(full[0] == 0xE9 and app[0] == 0xE9, 'Missing ESP image header.')
require(struct.unpack_from('<H', app, 12)[0] == 9, 'App is not for ESP32-S3.')
require(len(full) <= 16 * 1024 * 1024, 'Full image exceeds 16 MB flash.')
partitions = []
for entry_offset in range(0x8000, 0x9000, 32):
    entry = full[entry_offset:entry_offset + 32]
    if entry[:2] != b'\xaa\x50':
        break
    kind, subtype = entry[2:4]
    offset, size = struct.unpack_from('<II', entry, 4)
    name = entry[12:28].split(b'\0')[0].decode('ascii')
    require(size > 0 and offset >= 0x9000 and offset + size <= 16 * 1024 * 1024, f'Invalid partition bounds: {name}')
    partitions.append({'name': name, 'type': kind, 'subtype': subtype, 'offset': offset, 'size': size})
require(bool(partitions), 'Missing partition table.')
require(len({p['name'] for p in partitions}) == len(partitions), 'Duplicate partition names.')
ordered = sorted(partitions, key=lambda item: item['offset'])
for first, second in zip(ordered, ordered[1:]):
    require(first['offset'] + first['size'] <= second['offset'], 'Overlapping partitions.')
primary = next(p for p in partitions if p['type'] == 0 and p['name'] == 'ota_0')
require(len(app) <= primary['size'], 'App image exceeds OTA slot.')
require(full[primary['offset']:primary['offset'] + len(app)] == app, 'Merged image contains a different app.')
assets = next(p for p in partitions if p['name'] == 'assets')
require(len(full) >= assets['offset'] + 16 and full[assets['offset']:assets['offset'] + 16] != b'\xff' * 16, 'Missing assets.')
report = {'status': 'passed', 'flash_bytes': 16 * 1024 * 1024,
          'app_bytes': len(app), 'merged_bytes': len(full), 'partitions': partitions,
          'hardware_tested': False, 'flashed': False}
(output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', 'utf-8')
print(f"Firmware verified: app {len(app):,} bytes / slot {primary['size']:,}; merged {len(full):,} bytes.")
print('SHA-256, embedded app, partition bounds and assets verified. No device was flashed.')
