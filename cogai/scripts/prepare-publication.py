"""Audit prospective Git files and optionally export a source ZIP. Never uploads.

Run from any directory with Python 3.12+:
  python cogai/scripts/prepare-publication.py
  python cogai/scripts/prepare-publication.py --export

Uses a temporary Git metadata directory to apply the actual .gitignore rules;
does not initialize or change the working repository or staging area.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD = 'cogai/firmware/xiaozhi-esp32/main/boards/ricky-war-tank/'
FORBIDDEN = re.compile(
    r'(^|/)(?:\.tools|\.local-backups|data|data-demo|backups|archive|test-results|'
    r'node_modules|\.venv|dist|build|managed_components|output-ricky-[^/]+)(/|$)|'
    r'(^|/)\.env(?:\..*)?$|\.(?:sqlite\w*|db|key|pem|bin|zip|pyc)$', re.I)
CREDENTIAL = re.compile(r'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|'
                        r'github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|'
                        r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
ENDPOINT = re.compile(r'https?://[^\s\"<>]+(?:ngrok-free\.(?:dev|app)|trycloudflare\.com)')


def git_files():
    with tempfile.TemporaryDirectory(prefix='cogai-git-audit-') as temp:
        subprocess.run(['git','init','--quiet',temp],check=True,capture_output=True)
        cmd=['git','-c','core.excludesFile='+os.devnull,'--git-dir',str(Path(temp)/'.git'),'--work-tree',str(ROOT),
             'ls-files','--others','--exclude-standard','-z']
        result=subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True)
        # Never silently accept a partial enumeration (e.g. permission denied).
        if result.stderr.strip():
            raise RuntimeError('Git could not enumerate all public candidates; review filesystem permissions.')
        names=set(result.stdout.decode('utf-8').split('\0'))-{''}
    # If a repository is added later, ignored files already tracked remain public.
    if (ROOT/'.git').exists():
        result=subprocess.run(['git','ls-files','-z'],cwd=ROOT,check=True,capture_output=True)
        names.update(result.stdout.decode('utf-8').split('\0'))
        names.discard('')
    return sorted(names)


def local_secrets():
    values=set()
    env=ROOT/'cogai/backend/.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            key,sep,value=line.partition('=')
            value=value.strip().strip('\"\'')
            if sep and re.search('KEY|TOKEN|SECRET|PASSWORD',key,re.I) and len(value)>=10:
                values.add(value)
                # Device tokens can be a semicolon-separated MAC=token map.
                if 'DEVICE_TOKENS' in key:
                    values.update(v.partition('=')[2] for v in value.split(';') if len(v.partition('=')[2])>=10)
    for path in [ROOT/'data/.key',ROOT/'cogai/backend/data/.key',ROOT/'cogai/backend/data-demo/.key']:
        if path.exists():
            value=path.read_text(encoding='utf-8').strip()
            if len(value)>=10:
                values.add(value)
    token_file=ROOT/'cogai/deploy/kaggle/dist/ANMI_DEVICE_TOKENS.txt'
    if token_file.exists():
        for token in re.findall(r'[0-9a-f:]{17}=([^;\s]+)',token_file.read_text(encoding='utf-8'),re.I):
            if len(token)>=10:
                values.add(token)
    return values


def prepare(export=False):
    secrets=local_secrets()
    findings=[]
    records=[]
    names=git_files()
    for name in names:
        p=ROOT/name
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT):
            findings.append({'path':name,'reason':'linked path'})
            continue
        if FORBIDDEN.search(name) and not p.name in {'.env.example','.env.production.example'}:
            findings.append({'path':name,'reason':'private/generated file is eligible for Git'})
            continue
        data=p.read_bytes()
        # Preserve ASCII credentials even inside otherwise non-UTF-8 files.
        content=data.decode('utf-8-sig',errors='replace')
        for n,line in enumerate(content.splitlines(),1):
            if CREDENTIAL.search(line) or any(s in line for s in secrets):
                findings.append({'path':name,'line':n,'reason':'possible credential'})
            if ENDPOINT.search(line):
                findings.append({'path':name,'line':n,'reason':'live tunnel endpoint'})
        if p.suffix=='.ipynb':
            notebook=json.loads(content)
            if any(c.get('outputs') or c.get('execution_count') is not None for c in notebook.get('cells',[]) if c.get('cell_type')=='code'):
                findings.append({'path':name,'reason':'notebook contains execution state/outputs'})
        records.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    if findings:
        print(json.dumps({'status':'blocked','findings':findings},ensure_ascii=True,indent=2))
        return 1
    report={'status':'passed','files':len(records),'bytes':sum(r['bytes'] for r in records),
            'scope':'Local source scan; excludes ignored files and does not audit remote Git history.'}
    if export:
        out=ROOT/'dist/github-source-2026-11-02.zip'
        out.parent.mkdir(exist_ok=True)
        temp=out.with_suffix('.zip.tmp')
        try:
            with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
                for rec in records:
                    data=(ROOT/rec['path']).read_bytes()
                    if hashlib.sha256(data).hexdigest()!=rec['sha256']:
                        raise RuntimeError('Source changed after audit; rerun export.')
                    z.writestr(rec['path'],data)
                # The operational config stays untouched locally. The public ZIP
                # gets a buildable template with no private deployment address.
                public=(ROOT/BOARD/'config.public.example.json').read_bytes()
                z.writestr(BOARD+'config.json',public)
                z.writestr('PUBLICATION_MANIFEST.json',json.dumps({'files':records,
                    'generated_config':BOARD+'config.json','hardware_accessed':False},indent=2))
            with zipfile.ZipFile(temp) as z:
                if z.testzip() is not None:
                    raise RuntimeError('ZIP verification failed')
            temp.replace(out)
        finally:
            temp.unlink(missing_ok=True)
        report['export']=out.relative_to(ROOT).as_posix()
        report['export_bytes']=out.stat().st_size
        report['export_sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
    print(json.dumps(report,indent=2))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',action='store_true')
    raise SystemExit(prepare(parser.parse_args().export))
