"""Local operator CLI. Never expose provisioning, restore or corpus writes over HTTP."""
import argparse
import hashlib
import json
import shutil
import sqlite3
import asyncio
from pathlib import Path

from cryptography.fernet import Fernet
from .config import Settings
from .migrations import MIGRATIONS
from .storage import Store


def backup(store: Store, target: Path):
    if target.exists() or target.with_suffix(target.suffix+'.json').exists():
        raise FileExistsError('Use a new backup destination; existing backups are never overwritten.')
    target.parent.mkdir(parents=True,exist_ok=True)
    with store.connection() as source, sqlite3.connect(target) as destination:
        source.backup(destination)
        if destination.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise RuntimeError('Backup integrity check failed')
        schema=destination.execute('PRAGMA user_version').fetchone()[0]
    manifest={'schema':schema,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
              'key_fingerprint':store.key_fingerprint,'contains_sensitive_data':True}
    target.with_suffix(target.suffix+'.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Knowledge index contains reviewed public corpus, no user query vectors.
    knowledge=store.settings.data_dir/'knowledge.sqlite3'
    if knowledge.exists():
        corpus_target=target.with_suffix(target.suffix+'.knowledge')
        if corpus_target.exists():
            raise FileExistsError('Knowledge snapshot already exists')
        with sqlite3.connect(knowledge) as source,sqlite3.connect(corpus_target) as destination:
            source.backup(destination)
    return manifest


def restore(settings: Settings, source: Path, target_dir: Path):
    if target_dir.exists():
        raise FileExistsError('Restore only to a new directory; stop the app and switch directories after verification.')
    manifest=json.loads(source.with_suffix(source.suffix+'.json').read_text(encoding='utf-8'))
    if manifest['sha256']!=hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError('Backup hash mismatch')
    if manifest['schema']>len(MIGRATIONS):
        raise ValueError('Backup needs a matching or newer application release')
    key=settings.encryption_key.encode() if settings.encryption_key else (settings.data_dir/'.key').read_bytes()
    if hashlib.sha256(key).hexdigest()!=manifest['key_fingerprint']:
        raise ValueError('Encryption key does not match the snapshot. Restore the key from separate secret storage.')
    cipher=Fernet(key)
    with sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True) as db:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise ValueError('Corrupt snapshot')
        for row in db.execute('SELECT payload FROM records LIMIT 1'):
            cipher.decrypt(row[0])
    target_dir.mkdir(parents=True)
    shutil.copy2(source,target_dir/'cogai.sqlite3')
    corpus=source.with_suffix(source.suffix+'.knowledge')
    if corpus.exists():
        shutil.copy2(corpus,target_dir/'knowledge.sqlite3')
    if not settings.encryption_key:
        (target_dir/'.key').write_bytes(key)


def main():
    parser=argparse.ArgumentParser(description='CogAI local operator tools')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('cleanup')
    b=sub.add_parser('backup');b.add_argument('target',type=Path)
    r=sub.add_parser('restore');r.add_argument('source',type=Path);r.add_argument('target_dir',type=Path)
    g=sub.add_parser('grant-expert');g.add_argument('alias')
    revoke=sub.add_parser('revoke-expert');revoke.add_argument('alias')
    ga=sub.add_parser('grant-admin');ga.add_argument('alias')
    ra=sub.add_parser('revoke-admin');ra.add_argument('alias')
    ingest=sub.add_parser('ingest-knowledge');ingest.add_argument('source',type=Path)
    prepare=sub.add_parser('prepare-knowledge');prepare.add_argument('source',type=Path)
    args=parser.parse_args()
    settings=Settings()
    if args.command=='restore':
        restore(settings,args.source,args.target_dir)
        print('Restored to new directory. Verify before switching the running service.')
        return
    store=Store(settings)
    if args.command=='cleanup':
        store.cleanup();print('Cleanup completed')
    elif args.command=='backup':
        backup(store,args.target);print('Encrypted snapshot created; encryption key is not included.')
    elif args.command in {'grant-expert','revoke-expert','grant-admin','revoke-admin'}:
        role={'grant-expert':'expert','grant-admin':'admin'}.get(args.command,'user')
        with store.connection() as db:
            result=db.execute('UPDATE accounts SET role=? WHERE alias=?',(role,args.alias))
            if result.rowcount!=1:
                raise ValueError('Account does not exist')
            row=db.execute('SELECT owner_id FROM accounts WHERE alias=?',(args.alias,)).fetchone()
            db.execute("INSERT INTO audit(owner_id,action,created) VALUES (?,?,strftime('%s','now'))",(row['owner_id'],'operator_role_'+role))
        print('Role updated locally. This does not verify qualifications or activate a partner service.')
    elif args.command in {'ingest-knowledge','prepare-knowledge'}:
        from .retrieval import CognitivePipeline, KnowledgeIndex, ProviderEncoder, expand_bundle
        data=expand_bundle(json.loads(args.source.read_text(encoding='utf-8')))
        index=KnowledgeIndex(settings.data_dir/'knowledge.sqlite3')
        if args.command=='prepare-knowledge':
            from .ai import AI
            from .research import ResearchServices
            settings=settings.model_copy(update={'mode':'live'})
            asyncio.run(CognitivePipeline(index,ResearchServices(settings,AI(settings)),ProviderEncoder(settings)).prepare(data))
        else:
            index.ingest(data)
        print(f'Index updated with {len(data)} cards. Only reviewed cards are used in production; drafts only in development.')


if __name__=='__main__':
    main()
