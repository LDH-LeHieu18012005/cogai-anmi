import httpx
import pytest
import asyncio
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def voice(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,mode='live',llm_api_key='test-only',
        transcription_model='test-stt',speech_model='test-tts',speech_voice='test-voice',speech_provider='openai'))
    with TestClient(app) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'persist':True,'external_ai':True})
        yield app,client


def test_voice_requires_separate_consent_and_does_not_store_audio(voice,monkeypatch):
    app,client=voice
    audio=b'\x1aE\xdf\xa3'+b'synthetic-audio'*3000
    assert client.post('/api/voice/transcribe',content=audio,headers={'Content-Type':'audio/webm'}).status_code==403
    assert client.patch('/api/consent',json={'voice_processing':True}).status_code==200
    async def post(self,url,**kwargs):
        assert url.endswith('/audio/transcriptions')
        assert kwargs['files']['file'][1]==audio
        return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Tôi muốn chia sẻ về công việc'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    result=client.post('/api/voice/transcribe',content=audio,headers={'Content-Type':'audio/webm'})
    assert result.status_code==200 and result.json()['transcript']=='Tôi muốn chia sẻ về công việc'
    assert client.get('/api/records').json()['records']==[]


def test_transcription_emits_safety_event_before_user_sends_chat(voice,monkeypatch):
    _,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    async def post(self,url,**kwargs):
        return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Tôi muốn chết'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    result=client.post('/api/voice/transcribe',content=b'\x1aE\xdf\xa3test',headers={'Content-Type':'audio/webm'})
    assert result.json()['risk']['level']=='high'
    assert client.get('/api/safety').json()['state']['level']=='high'


def test_speech_only_reads_server_reply_and_redacts_it(voice,monkeypatch):
    app,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    session=app.state.store.session(client.cookies.get('cogai_session'))
    app.state.store.put_document(session,'conversation','conversation',{'turns':[{'role':'assistant','content':'Email user@example.org'}]})
    async def post(self,url,**kwargs):
        assert url.endswith('/audio/speech')
        assert 'user@example.org' not in kwargs['json']['input']
        return httpx.Response(200,request=httpx.Request('POST',url),content=b'ID3synthetic',headers={'Content-Type':'audio/mpeg'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    assert client.post('/api/voice/speak',json={'text':'arbitrary injection'}).status_code==422
    result=client.post('/api/voice/speak',json={})
    assert result.status_code==200 and result.headers['content-type'].startswith('audio/mpeg')


def test_revoking_voice_inflight_withholds_transcript(voice,monkeypatch):
    app,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    session=app.state.store.session(client.cookies.get('cogai_session'))
    async def post(self,url,**kwargs):
        app.state.store.consent(session,{'voice_processing':False})
        return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'must be withheld'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    result=client.post('/api/voice/transcribe',content=b'\x1aE\xdf\xa3test',headers={'Content-Type':'audio/webm'})
    assert result.status_code==409 and 'must be withheld' not in result.text


def test_voice_rejects_invalid_audio_and_provider_failure(voice,monkeypatch):
    _,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    assert client.post('/api/voice/transcribe',content=b'not audio',headers={'Content-Type':'audio/webm'}).status_code==415
    assert client.post('/api/voice/transcribe',content=b'x'*2_000_001,headers={'Content-Type':'audio/webm'}).status_code==413
    async def post(self,url,**kwargs):
        raise httpx.ConnectError('synthetic offline')
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    assert client.post('/api/voice/transcribe',content=b'\x1aE\xdf\xa3test',headers={'Content-Type':'audio/webm'}).status_code==503


def test_users_behind_one_proxy_have_separate_ai_quotas(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,mode='demo'))
    with TestClient(app) as first, TestClient(app) as second:
        for client in (first,second):
            client.post('/api/session',json={'accepted':True,'adult':True})
        for _ in range(10):
            assert first.post('/api/chat',json={'message':'Xin chào'}).status_code==200
        assert first.post('/api/chat',json={'message':'Xin chào'}).status_code==429
        assert second.post('/api/chat',json={'message':'Xin chào'}).status_code==200


def test_handsfree_turn_transcribes_chats_and_speaks_without_manual_send(voice,monkeypatch):
    app,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    paths=[]
    async def post(self,url,**kwargs):
        paths.append(url.rsplit('/',1)[-1])
        if url.endswith('/transcriptions'):
            return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Tôi muốn kể về ngày hôm nay'})
        if url.endswith('/speech'):
            assert kwargs['json']['input']=='Mình đang lắng nghe bạn.'
            return httpx.Response(200,request=httpx.Request('POST',url),content=b'ID3test',headers={'Content-Type':'audio/mpeg'})
        raise AssertionError(url)
    async def chat(session,data):
        assert data.message=='Tôi muốn kể về ngày hôm nay'
        assert data.channel=='voice'
        return {'reply':'Mình đang lắng nghe bạn.','risk':{'level':'low','source':'rules','reason':'test','requires_support':False},'conversation_id':'test-conversation','mode':'live'}
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    monkeypatch.setattr(app.state.dialogue,'chat',chat)
    response=client.post('/api/voice/turn',content=b'\x1aE\xdf\xa3test',headers={'Content-Type':'audio/webm'})
    assert response.status_code==200,response.text
    result=response.json()
    assert result['transcript']=='Tôi muốn kể về ngày hôm nay'
    assert result['reply']=='Mình đang lắng nghe bạn.' and result['audio_base64']
    assert set(result['latency_ms'])=={'transcription','dialogue','speech','total'}
    assert all(isinstance(v,(int,float)) and v>=0 for v in result['latency_ms'].values())
    assert paths==['transcriptions','speech']


def test_silent_handsfree_turn_does_not_generate_or_speak(voice,monkeypatch):
    _,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    async def post(self,url,**kwargs):
        assert url.endswith('/transcriptions')
        return httpx.Response(200,request=httpx.Request('POST',url),json={'text':''})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    result=client.post('/api/voice/turn',content=b'\x1aE\xdf\xa3test',headers={'Content-Type':'audio/webm'})
    assert result.status_code==200 and result.json()['heard'] is False


def test_cancelling_spoken_turn_stops_provider_and_owner_cannot_cancel_others(voice,monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    app,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    entered=threading.Event();cancelled=threading.Event()
    async def post(self,url,**kwargs):
        entered.set()
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.set();raise
        raise AssertionError('Provider must be cancelled')
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(client.post,'/api/voice/turn',content=b'\x1aE\xdf\xa3test',headers={'Content-Type':'audio/webm','X-CogAI-Voice-Turn':'turn-test-1'})
        assert entered.wait(5)
        other_token,_=app.state.store.create_session({'persist':False,'external_ai':True})
        assert client.post('/api/voice/cancel',json={'turn_id':'turn-test-1'},headers={'Cookie':'cogai_session='+other_token}).json()['cancelled'] is False
        # A stale cancel for another turn must not stop the active request.
        assert client.post('/api/voice/cancel',json={'turn_id':'different-turn'}).json()['cancelled'] is False
        assert client.post('/api/voice/cancel',json={'turn_id':'turn-test-1'}).json()['cancelled'] is True
        assert future.result(timeout=5).status_code==409
    assert cancelled.is_set()
    assert client.get('/api/records').json()['records']==[]


def test_handsfree_tts_failure_keeps_checked_reply_without_repeating_chat(voice,monkeypatch):
    app,client=voice
    client.patch('/api/consent',json={'voice_processing':True})
    chats=[]
    async def post(self,url,**kwargs):
        if url.endswith('/transcriptions'):
            return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Tôi muốn kể'})
        raise httpx.ConnectError('synthetic TTS outage')
    async def chat(session,data):
        chats.append(data.message)
        return {'reply':'Phản hồi đã kiểm tra.','risk':{'level':'low','requires_support':False},'mode':'live'}
    monkeypatch.setattr(httpx.AsyncClient,'post',post);monkeypatch.setattr(app.state.dialogue,'chat',chat)
    result=client.post('/api/voice/turn',content=b'\x1aE\xdf\xa3test',headers={'Content-Type':'audio/webm'})
    assert result.status_code==200
    assert result.json()['reply']=='Phản hồi đã kiểm tra.' and result.json()['audio_error']
    assert not result.json().get('audio_base64') and len(chats)==1
