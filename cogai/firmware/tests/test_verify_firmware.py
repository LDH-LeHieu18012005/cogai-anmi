import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

VERIFY = Path(__file__).resolve().parents[1] / 'verify_firmware.py'


class VerifyFirmwareTests(unittest.TestCase):
    def fixture(self, root):
        full = bytearray(b'\xff' * 0x12000)
        app = bytearray(b'\0' * 256)
        app[0] = full[0] = 0xE9
        struct.pack_into('<H', app, 12, 9)  # ESP32-S3 image chip ID
        for index, (kind, subtype, offset, size, name) in enumerate([
            (0, 0x10, 0x10000, 0x1000, b'ota_0'),
            (1, 0x82, 0x11000, 0x1000, b'assets'),
        ]):
            entry = struct.pack('<HBBII16sI', 0x50AA, kind, subtype, offset, size, name, 0)
            full[0x8000 + index * 32:0x8020 + index * 32] = entry
        full[0x10000:0x10100] = app
        full[0x11000:0x11010] = b'asset-contents!!.'
        (root / 'xiaozhi.bin').write_bytes(app)
        (root / 'merged-binary.bin').write_bytes(full)
        self.manifest(root)

    def manifest(self, root):
        (root / 'manifest.json').write_text(json.dumps({
            'status': 'succeeded', 'board_type': 'ricky-war-tank',
            'language': 'vi-VN', 'wake_word': 'disabled',
            'artifacts': [{'file': name, 'size': (root / name).stat().st_size,
                           'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest()}
                          for name in ('xiaozhi.bin', 'merged-binary.bin')],
        }), 'utf-8')

    def run_check(self, root, optimized=False):
        return subprocess.run([sys.executable, *(['-O'] if optimized else []), str(VERIFY), str(root)],
                              capture_output=True, text=True)

    def test_valid_images_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            result = self.run_check(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((root / 'verification.json').read_text())['status'], 'passed')

    def test_bad_hash_is_rejected_even_in_optimized_python(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            with (root / 'xiaozhi.bin').open('ab') as output:
                output.write(b'corrupt')
            self.assertNotEqual(self.run_check(root, optimized=True).returncode, 0)

    def test_merged_app_must_match_even_when_hashes_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            path = root / 'merged-binary.bin'
            data = bytearray(path.read_bytes())
            data[0x10080] ^= 1
            path.write_bytes(data)
            self.manifest(root)
            self.assertNotEqual(self.run_check(root).returncode, 0)

    def test_overlapping_partitions_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            path = root / 'merged-binary.bin'
            data = bytearray(path.read_bytes())
            struct.pack_into('<I', data, 0x8024, 0x10800)
            path.write_bytes(data)
            self.manifest(root)
            self.assertNotEqual(self.run_check(root).returncode, 0)

    def test_path_outside_artifact_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            data = json.loads((root / 'manifest.json').read_text())
            data['artifacts'] = []
            (root / 'manifest.json').write_text(json.dumps(data))
            self.assertNotEqual(self.run_check(root).returncode, 0)


if __name__ == '__main__':
    unittest.main()
