"""Privacy regressions: use synthetic secrets and disposable worktrees only."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC=importlib.util.spec_from_file_location('publication',Path(__file__).with_name('prepare-publication.py'))
publication=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def setup_tree(self,root):
        def write(name,data):
            path=root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(data,encoding='utf-8')
        write('.gitignore',(publication.ROOT/'.gitignore').read_text(encoding='utf-8'))
        write('cogai/backend/.env','COGAI_LLM_API_KEY=synthetic-private-value-1234567890')
        write('cogai/backend/.env.production','PRIVATE=production-secret')
        write('cogai/backend/data/.key','synthetic-encryption-key-1234567890')
        write('cogai/firmware/output-ricky-rsa-20261031/xiaozhi.bin','private firmware')
        write('cogai/deploy/kaggle/dist/ANMI_DEVICE_TOKENS.txt','aa:bb:cc:dd:ee:ff=synthetic-device-token')
        write(publication.BOARD+'config.json','{"private":"endpoint"}')
        write(publication.BOARD+'config.public.example.json','{"public":"example.invalid"}')
        write('cogai/backend/app/example.py','print("public code")')
        return write

    def test_export_excludes_secrets_and_preserves_operational_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.setup_tree(root)
            with patch.object(publication,'ROOT',root),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(publication.prepare(export=True),0)
            with zipfile.ZipFile(root/'dist/github-source-2026-11-02.zip') as z:
                self.assertIsNone(z.testzip())
                for name in z.namelist():
                    self.assertNotIn(b'synthetic-',z.read(name))
                self.assertEqual(json.loads(z.read(publication.BOARD+'config.json')),{'public':'example.invalid'})
            self.assertEqual(json.loads((root/publication.BOARD/'config.json').read_text()),{'private':'endpoint'})

    def test_leaked_known_secret_blocks_without_printing_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            write=self.setup_tree(root)
            write('cogai/backend/app/leak.py','key="synthetic-private-value-1234567890"')
            output=io.StringIO()
            with patch.object(publication,'ROOT',root),contextlib.redirect_stdout(output):
                self.assertEqual(publication.prepare(export=True),1)
            self.assertIn('leak.py',output.getvalue())
            self.assertNotIn('synthetic-private-value',output.getvalue())
            self.assertFalse((root/'dist').exists())

    def test_ignored_secret_already_tracked_still_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.setup_tree(root)
            subprocess.run(['git','init','--quiet',str(root)],check=True,capture_output=True)
            subprocess.run(['git','-C',str(root),'add','--force','cogai/backend/.env.production'],check=True,capture_output=True)
            output=io.StringIO()
            with patch.object(publication,'ROOT',root),contextlib.redirect_stdout(output):
                self.assertEqual(publication.prepare(),1)
            self.assertIn('private/generated file',output.getvalue())


if __name__=='__main__':
    unittest.main()
