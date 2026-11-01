import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('package_remote', ROOT / 'package_remote.py')
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class RemotePackageTests(unittest.TestCase):
    def source(self, root):
        for name, data in {
            'CMakeLists.txt': 'project(test)', 'sdkconfig.defaults': 'CONFIG_TEST=y',
            'main/code.cc': '// source', 'main/assets/voice.ogg': 'voice',
            'scripts/build.py': '# builder', 'partitions/16m.csv': '# partitions',
            'LICENSE': 'license', 'main/.env': 'SECRET',
            'main/assets/lang_config.h': 'generated',
            'main/__pycache__/code.pyc': 'generated',
            'main/test-results/private.txt': 'private',
            'build/private.bin': 'private', 'backups/device.bin': 'private',
            'sdkconfig': 'wifi settings', '.git/config': 'credentials',
            '.github/workflows/build.yml': 'original workflow',
            '.github/ci/representatives.json': '{}',
        }.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, 'utf-8')

    def test_package_excludes_private_generated_and_unrelated_workflows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'source'
            root.mkdir()
            self.source(root)
            output = Path(folder) / 'package.zip'
            package.build_package(root, output)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn('firmware/main/code.cc', names)
                self.assertIn('firmware/sdkconfig.defaults', names)
                self.assertIn('.github/workflows/build-anmi.yml', names)
                self.assertNotIn('firmware/.github/workflows/build.yml', names)
                for private in ('SECRET', 'private', 'wifi settings', 'credentials', 'generated'):
                    self.assertFalse(any(archive.read(n).decode('utf-8',errors='ignore') == private for n in names))
                manifest = json.loads(archive.read('SOURCE_MANIFEST.json'))
                self.assertEqual(manifest['files']['firmware/main/code.cc']['bytes'], 9)

    def test_symlink_outside_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'source'
            root.mkdir()
            self.source(root)
            target = Path(folder) / 'secret.txt'
            target.write_text('do not upload')
            link = root / 'main/leak.txt'
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest('Symlink creation is unavailable for this Windows account')
            with self.assertRaises(ValueError):
                package.build_package(root, Path(folder) / 'package.zip')


if __name__ == '__main__':
    unittest.main()
