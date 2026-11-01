import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.migrations import MIGRATIONS
from test_system import start


@pytest.fixture
def core(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    with TestClient(app) as client:
        start(client, persist=True)
        yield app, client


def register(client, alias="nguoi-dung"):
    response = client.post('/api/account', json={'alias': alias, 'password': 'test-password-unique-123'})
    assert response.status_code == 201, response.text
    return response.json()


def test_account_logout_restart_login_preserves_owned_history(core, tmp_path):
    _, client = core
    saved = client.post('/api/moods', json={'score': 3, 'note': 'private-note'}).json()
    register(client)
    assert client.post('/api/logout').status_code == 200
    assert client.get('/api/records').status_code == 401
    app = create_app(Settings(data_dir=tmp_path))
    with TestClient(app) as other:
        assert other.post('/api/login', json={'alias': 'nguoi-dung', 'password': 'wrong-password-123'}).status_code == 401
        assert other.post('/api/login', json={'alias': 'nguoi-dung', 'password': 'test-password-unique-123'}).status_code == 200
        assert other.get('/api/records').json()['records'][0]['id'] == saved['record_id']
        assert other.get('/api/session').json()['account']['alias'] == 'nguoi-dung'
        assert other.delete('/api/account').status_code == 200
        assert other.post('/api/login', json={'alias': 'nguoi-dung', 'password': 'test-password-unique-123'}).status_code == 401


def test_revoke_deletes_derived_state_and_rejects_inflight_write(core):
    app, client = core
    client.post('/api/chat', json={'message': 'Tôi lo về kỳ thi'})
    old = app.state.store.session(client.cookies.get('cogai_session'))
    response = client.patch('/api/consent', json={'persist': False})
    assert response.status_code == 200
    assert client.get('/api/records').json()['records'] == []
    assert client.get('/api/chat').json()['turns'] == []
    with pytest.raises(Exception) as exc:
        app.state.store.save(old, 'mood', {'note': 'late'})
    assert exc.value.status_code == 409


def test_mood_screening_and_exercise_share_safety_branch(core):
    _, client = core
    client.post('/api/moods', json={'score': 1, 'note': 'Tôi muốn chết'})
    blocked = client.post('/api/reframe', json={'situation': 'Tôi đi học', 'thought': 'Tôi lo'}).json()
    assert blocked['blocked'] and blocked['risk']['level'] == 'high'
    client.post('/api/chat/reset')
    assert client.post('/api/chat', json={'message': 'Xin chào'}).json()['risk']['level'] == 'high'
    events = client.get('/api/safety').json()['events']
    assert any(e['channel'] == 'mood' and e['level'] == 'high' for e in events)


def test_account_isolation_and_expired_auth_does_not_delete_account(core):
    app, first = core
    first.post('/api/moods', json={'score': 4})
    register(first)
    with app.state.store.connection() as db:
        db.execute('UPDATE auth_sessions SET expires=?', (time.time()-1,))
    assert first.get('/api/records').status_code == 401
    assert first.post('/api/login', json={'alias': 'nguoi-dung', 'password': 'test-password-unique-123'}).status_code == 200
    assert len(first.get('/api/records').json()['records']) == 1
    with TestClient(app) as second:
        start(second, persist=True)
        register(second, 'nguoi-khac')
        assert second.get('/api/records').json()['records'] == []


def test_referral_requires_sharing_and_real_acceptance(core):
    app, client = core
    register(client)
    assert client.post('/api/referrals', json={'summary': 'Tôi muốn được hỗ trợ'}).status_code == 403
    assert client.patch('/api/consent', json={'share_support': True}).status_code == 200
    case = client.post('/api/referrals', json={'summary': 'Tôi muốn được hỗ trợ'}).json()
    assert case['status'] == 'unavailable'
    assert client.get('/api/expert/cases').status_code == 403
    assert client.patch('/api/expert/cases/'+case['id'], json={'status': 'accepted'}).status_code == 403
    exported = client.get('/api/export').json()
    assert exported['referrals'][0]['summary'] == 'Tôi muốn được hỗ trợ'


def test_personality_abstains_and_revocation_removes_jobs(core):
    _, client = core
    assert client.post('/api/personality/jobs').status_code == 403
    client.patch('/api/consent', json={'personalization': True})
    assert client.post('/api/personality/jobs').status_code == 202
    profile = client.get('/api/personality').json()
    assert profile['status'] in {'pending', 'insufficient_evidence', 'adapter_unavailable'}
    client.patch('/api/consent', json={'personalization': False})
    assert client.get('/api/personality').json()['status'] == 'disabled'


def test_reminders_are_opt_in_and_versioned_questionnaire(core):
    _, client = core
    assert client.put('/api/reminders', json={'days': 14}).status_code == 403
    client.patch('/api/consent', json={'screening_reminders': True})
    assert client.put('/api/reminders', json={'days': 14}).status_code == 200
    assert client.get('/api/reminders').json()['days'] == 14
    assert client.post('/api/screenings', json={'kind':'PHQ-9','answers':[0]*9,'version':'unknown'}).status_code == 422
    client.patch('/api/consent', json={'screening_reminders':False})
    assert client.get('/api/reminders').json()['enabled'] is False


def test_expert_acceptance_is_atomic_and_shared_summary_revokes(core):
    app, owner = core
    app.state.dialogue.config.support_accepting=True
    owner.patch('/api/consent',json={'share_support':True})
    case=owner.post('/api/referrals',json={'summary':'Chỉ chia sẻ tóm tắt này'}).json()
    assert case['status']=='pending'
    with TestClient(app) as professional:
        start(professional,persist=True)
        register(professional,'chuyen-gia')
        with app.state.store.connection() as db:
            db.execute("UPDATE accounts SET role='expert' WHERE alias='chuyen-gia'")
        assert professional.get('/api/records').json()['records']==[]
        assert professional.get('/api/expert/cases').json()['cases'][0]['summary']=='Chỉ chia sẻ tóm tắt này'
        assert professional.patch('/api/expert/cases/'+case['id'],json={'status':'resolved'}).status_code==409
        assert professional.patch('/api/expert/cases/'+case['id'],json={'status':'accepted'}).status_code==200
        assert owner.get('/api/referrals').json()['cases'][0]['status']=='accepted'
        owner.patch('/api/consent',json={'share_support':False})
        assert professional.get('/api/expert/cases').json()['cases']==[]
        assert professional.patch('/api/expert/cases/'+case['id'],json={'status':'resolved'}).status_code==404


def test_no_persist_reset_does_not_erase_safety(core):
    _, client=core
    client.patch('/api/consent',json={'persist':False})
    client.post('/api/moods',json={'score':1,'note':'Tôi muốn chết'})
    client.post('/api/chat/reset')
    assert client.get('/api/safety').json()['state']['level']=='high'
    assert client.post('/api/chat',json={'message':'Tôi đang ở nhà'}).json()['risk']['level']=='high'


def test_safety_clarification_can_resume_without_erasing_events(core):
    _, client=core
    client.post('/api/chat',json={'message':'Tôi không muốn tiếp tục nữa'})
    response=client.post('/api/safety/check-in',json={'no_current_danger':True,'message':'Tôi muốn dừng bài tập vì mệt, tôi đang ở cùng bạn'})
    assert response.status_code==200
    assert response.json()['status']=='self_reported_no_current_danger'
    result=client.post('/api/chat',json={'message':'Tôi muốn kể về công việc'}).json()
    assert result['risk']['level']=='low'
    assert any(e['level']=='check_in' for e in client.get('/api/safety').json()['events'])


def test_legacy_migration_keeps_ciphertext_and_is_idempotent(tmp_path):
    import json
    import sqlite3
    from cryptography.fernet import Fernet
    from app.storage import Store
    key=Fernet.generate_key()
    (tmp_path/'.key').write_bytes(key)
    encrypted=Fernet(key).encrypt(b'{"note":"legacy"}')
    with sqlite3.connect(tmp_path/'cogai.sqlite3') as db:
        db.executescript('CREATE TABLE sessions(id TEXT PRIMARY KEY,token_hash TEXT UNIQUE NOT NULL,consent TEXT NOT NULL,expires REAL NOT NULL); CREATE TABLE records(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,kind TEXT NOT NULL,payload BLOB NOT NULL,created REAL NOT NULL);')
        db.execute('INSERT INTO sessions VALUES (?,?,?,?)',('old',Store.token_hash('legacy-token'),json.dumps({'persist':True,'external_ai':False}),time.time()+1000))
        db.execute('INSERT INTO records VALUES (?,?,?,?,?)',('r','old','mood',encrypted,time.time()))
    for _ in range(2):
        store=Store(Settings(data_dir=tmp_path))
        assert store.records(store.session('legacy-token'))[0]['payload']['note']=='legacy'
        with store.connection() as db:
            assert db.execute('SELECT payload FROM records').fetchone()[0]==encrypted
            assert db.execute('PRAGMA user_version').fetchone()[0]==len(MIGRATIONS)


def test_new_risk_during_generation_withholds_normal_reply(core, monkeypatch):
    from app.models import MoodInput, Risk
    app,client=core
    session=app.state.store.session(client.cookies.get('cogai_session'))
    async def generating(*args,**kwargs):
        app.state.dialogue.safety_event(session,'mood',Risk(level='high',reason='test',source='rules',requires_support=True))
        return {'reply':'ordinary reply must be withheld','risk':Risk(level='low',reason='test',source='rules').model_dump(),'mode':'demo'}
    monkeypatch.setattr(app.state.ai,'chat',generating)
    result=client.post('/api/chat',json={'message':'Tôi lo kỳ thi'}).json()
    assert result['risk']['level']=='high'
    assert 'must be withheld' not in result['reply']


def test_restoring_history_does_not_consume_generation_quota(core):
    _,client=core
    for _ in range(12):
        assert client.get('/api/chat').status_code==200
    assert client.post('/api/chat',json={'message':'Xin chào'}).status_code==200


def test_unrelated_consent_change_cannot_erase_temporary_safety(core):
    _,client=core
    client.patch('/api/consent',json={'persist':False})
    client.post('/api/moods',json={'score':1,'note':'Tôi muốn chết'})
    client.patch('/api/consent',json={'share_support':True})
    assert client.get('/api/safety').json()['state']['level']=='high'
    client.patch('/api/consent',json={'persist':True})
    assert client.post('/api/chat',json={'message':'Tôi muốn làm bài tập'}).json()['risk']['level']=='high'


def test_revocation_between_provider_calls_prevents_next_external_request(tmp_path,monkeypatch):
    import httpx
    app=create_app(Settings(data_dir=tmp_path,mode='live',llm_api_key='synthetic-key'))
    calls=[]
    with TestClient(app) as client:
        start(client,persist=True,external_ai=True)
        session=app.state.store.session(client.cookies.get('cogai_session'))
        async def post(self,url,**kwargs):
            calls.append(url)
            # Consent is withdrawn while the first provider request is in flight.
            app.state.store.consent(session,{'external_ai':False})
            return httpx.Response(200,request=httpx.Request('POST',url),json={'choices':[{'message':{'content':'{"level":"low","reason":"synthetic"}'}}]})
        monkeypatch.setattr(httpx.AsyncClient,'post',post)
        result=client.post('/api/chat',json={'message':'Tôi lo kỳ thi'})
        assert result.status_code==409
        assert len(calls)==1
        assert client.get('/api/records').json()['records']==[]


def test_guest_snapshot_cannot_write_after_account_logout(core):
    app,client=core
    guest=app.state.store.session(client.cookies.get('cogai_session'))
    register(client)
    client.post('/api/logout')
    with pytest.raises(Exception) as exc:
        app.state.store.save(guest,'mood',{'note':'stale guest snapshot'})
    assert exc.value.status_code==401


def test_restored_chat_shows_mood_safety_before_next_message(core):
    _,client=core
    client.post('/api/moods',json={'score':1,'note':'Tôi muốn chết'})
    restored=client.get('/api/chat').json()
    assert restored['risk']['level']=='high'
    assert restored['step']=='support'


def test_parallel_safety_channels_cannot_downgrade_high_or_lose_events(core):
    from concurrent.futures import ThreadPoolExecutor
    from app.models import Risk
    app,client=core
    session=app.state.store.session(client.cookies.get('cogai_session'))
    def emit(index):
        risk=Risk(level='high' if index==3 else 'low',reason='synthetic',source='rules',requires_support=index==3)
        app.state.dialogue.safety_event(session,'mood',risk)
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(emit,range(12)))
    result=client.get('/api/safety').json()
    assert result['state']['level']=='high'
    assert len(result['events'])==12


def test_personality_jobs_run_after_consented_chat_and_abstain(core):
    _,client=core
    client.patch('/api/consent',json={'personalization':True})
    for index in range(3):
        if index:
            client.post('/api/chat/reset')
        assert client.post('/api/chat',json={'message':'Tôi muốn kể về công việc'}).status_code==200
    profile=client.get('/api/personality').json()
    assert profile['source_conversations']==3
    assert profile['status']=='adapter_unavailable'
    assert profile['traits']=={} and profile['evidence']==[]
