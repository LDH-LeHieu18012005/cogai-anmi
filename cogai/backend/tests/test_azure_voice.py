import contextlib

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class Streamed:
    def __init__(self, status, chunks):
        self.status_code, self.chunks = status, chunks

    async def aiter_bytes(self):
        for chunk in self.chunks:
            yield chunk


def voice_app(tmp_path, **settings):
    app = create_app(Settings(data_dir=tmp_path, mode='live', llm_api_key='synthetic', **settings))
    client = TestClient(app)
    client.__enter__()
    client.post('/api/session', json={'accepted': True, 'adult': True, 'external_ai': True})
    client.patch('/api/consent', json={'voice_processing': True})
    session = app.state.store.session(client.cookies.get('cogai_session'))
    return app, client, session


def spoken(app, client, session, text):
    async def collect():
        return [chunk async for chunk in app.state.voice.speech_chunks(session, text)]
    return client.portal.call(collect)


def test_azure_speaks_hoaimy_with_escaped_ssml(tmp_path, monkeypatch):
    requests = []
    @contextlib.asynccontextmanager
    async def stream(self, method, url, **kwargs):
        requests.append((url, kwargs['headers'], kwargs['content'].decode()))
        yield Streamed(200, [b'ID3azure-', b'chunk'])
    monkeypatch.setattr(httpx.AsyncClient, 'stream', stream)
    app, client, session = voice_app(tmp_path, speech_provider='auto', azure_speech_key='synthetic-key')
    assert b''.join(spoken(app, client, session, 'Mình <đang> nghe bạn & bạn.')) == b'ID3azure-chunk'
    url, headers, ssml = requests[0]
    assert url == 'https://southeastasia.tts.speech.microsoft.com/cognitiveservices/v1'
    assert headers['Ocp-Apim-Subscription-Key'] == 'synthetic-key'
    # spoken_text drops Markdown symbols such as '>' first; what remains must be XML-escaped.
    assert "name='vi-VN-HoaiMyNeural'" in ssml and 'Mình &lt;đang nghe bạn &amp; bạn.' in ssml
    client.__exit__(None, None, None)


def test_azure_failure_falls_back_to_edge_hoaimy_never_another_voice(tmp_path, monkeypatch):
    import edge_tts
    voices = []
    class Communicate:
        def __init__(self, text, voice, **kwargs):
            voices.append(voice)
        async def stream(self):
            yield {'type': 'audio', 'data': b'ID3edge'}
    monkeypatch.setattr(edge_tts, 'Communicate', Communicate)
    @contextlib.asynccontextmanager
    async def stream(self, method, url, **kwargs):
        assert 'tts.speech.microsoft.com' in url, 'only Azure HoaiMy, never a provider voice'
        yield Streamed(401, [])
    monkeypatch.setattr(httpx.AsyncClient, 'stream', stream)
    app, client, session = voice_app(tmp_path, speech_provider='auto', azure_speech_key='expired',
                                     speech_model='gpt-4o-mini-tts', speech_voice='marin')
    assert spoken(app, client, session, 'Mình đang nghe bạn.') == [b'ID3edge']
    assert voices == ['vi-VN-HoaiMyNeural']
    client.__exit__(None, None, None)


def test_auto_without_azure_key_uses_edge(tmp_path, monkeypatch):
    import edge_tts
    class Communicate:
        def __init__(self, text, voice, **kwargs):
            pass
        async def stream(self):
            yield {'type': 'audio', 'data': b'ID3edge'}
    monkeypatch.setattr(edge_tts, 'Communicate', Communicate)
    async def no_azure(*args, **kwargs):
        raise AssertionError('Azure must not be called without a key')
    monkeypatch.setattr(httpx.AsyncClient, 'stream', no_azure)
    app, client, session = voice_app(tmp_path, speech_provider='auto')
    assert spoken(app, client, session, 'Chào bạn.') == [b'ID3edge']
    client.__exit__(None, None, None)
