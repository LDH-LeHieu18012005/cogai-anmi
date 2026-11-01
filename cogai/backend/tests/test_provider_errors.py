import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.mark.parametrize('endpoint', ['/api/chat','/api/voice/turn'])
def test_provider_auth_error_is_specific_without_exposing_response_or_retry(tmp_path,monkeypatch,endpoint):
    calls=[]
    async def post(self,url,**kwargs):
        calls.append(url)
        return httpx.Response(401,request=httpx.Request('POST',url),json={'error':{'message':'Do not expose synthetic-private-marker'}})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    app=create_app(Settings(data_dir=tmp_path,mode='live',llm_api_key='synthetic-private-marker',transcription_model='test',speech_model='test',speech_voice='test',speech_provider='openai'))
    with TestClient(app) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        client.patch('/api/consent',json={'voice_processing':True})
        response=(client.post(endpoint,json={'message':'Xin chào'}) if endpoint.endswith('chat') else
                  client.post(endpoint,content=b'\x1aE\xdf\xa3synthetic',headers={'Content-Type':'audio/webm'}))
        assert response.status_code==503
        assert '401' in response.json()['detail']
        assert 'synthetic-private-marker' not in response.text
        # Chat starts risk, appraisal and draft concurrently; none of them is retried.
        assert len(calls)==(3 if endpoint.endswith('chat') else 1)
