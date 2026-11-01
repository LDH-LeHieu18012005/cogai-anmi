from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PrepareTests(unittest.TestCase):
    def test_preparing_twice_preserves_canonical_board_and_user_fixes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copy2(ROOT / 'prepare_ricky.py', root / 'prepare_ricky.py')
            firmware = root / 'xiaozhi-esp32'
            for relative in ('main/boards/ricky-war-tank', 'main/boards/bread-compact-wifi'):
                shutil.copytree(ROOT / 'xiaozhi-esp32' / relative, firmware / relative)
            for name in ('main/CMakeLists.txt', 'main/Kconfig.projbuild'):
                shutil.copy2(ROOT / 'xiaozhi-esp32' / name, firmware / name)
            board = firmware / 'main/boards/ricky-war-tank/ricky_war_tank.cc'
            original = board.read_bytes() + b'\n// preserve operator changes\n'
            board.write_bytes(original)
            before = (firmware / 'main/Kconfig.projbuild').read_bytes()
            for _ in range(2):
                result = subprocess.run([sys.executable, str(root / 'prepare_ricky.py')], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            self.assertEqual(board.read_bytes(), original)
            self.assertEqual((firmware / 'main/Kconfig.projbuild').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
