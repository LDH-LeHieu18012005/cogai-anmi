import sqlite3
import time

import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.storage import Store


def test_backup_restore_is_consistent_and_preserves_encryption(tmp_path):
    from app.operations import backup, restore
    settings=Settings(data_dir=tmp_path/'source')
    store=Store(settings)
    token,session=store.create_session({'persist':True,'external_ai':False})
    store.save(session,'mood',{'note':'synthetic backup text'})
    path=tmp_path/'backup.sqlite3'
    backup(store,path)
    assert path.exists()
    with pytest.raises(FileExistsError):
        backup(store,path)
    restored=tmp_path/'restored'
    restore(settings,path,restored)
    new=Store(Settings(data_dir=restored))
    assert new.records(new.session(token))[0]['payload']['note']=='synthetic backup text'
    with pytest.raises(FileExistsError):
        restore(settings,path,restored)


def test_cleanup_removes_old_sources_and_derived_state(tmp_path):
    store=Store(Settings(data_dir=tmp_path))
    token,session=store.create_session({'persist':True,'external_ai':False})
    store.register(session,'retention-test','test-only-password-123')
    session=store.session(token)
    store.save(session,'chat',{'message':'old','reply':'old'})
    store.put_document(session,'conversation','conversation',{'turns':[{'content':'old'}]})
    with store.connection() as db:
        db.execute('UPDATE records SET created=?',(time.time()-31*86400,))
    store.cleanup()
    assert store.records(session)==[]
    assert store.document(session,'conversation') is None


def test_production_fails_without_external_key_or_secure_cookie(tmp_path):
    from app.main import create_app
    from cryptography.fernet import Fernet
    with pytest.raises(RuntimeError):
        create_app(Settings(data_dir=tmp_path,environment='production'))
    app=create_app(Settings(data_dir=tmp_path,environment='production',encryption_key=Fernet.generate_key().decode()))
    with pytest.raises(RuntimeError):
        with TestClient(app):
            pass
