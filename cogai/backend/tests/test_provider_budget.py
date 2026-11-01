import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.ai import AI, ChatReply
from app.config import Settings


def test_daily_limit_survives_reconstruction_and_counts_all_attempts(tmp_path):
    from app.provider_budget import ProviderBudget
    settings=Settings(_env_file=None,data_dir=tmp_path,external_daily_call_limit=2)
    ProviderBudget(settings).reserve()
    ProviderBudget(settings).reserve()
    with pytest.raises(HTTPException) as exc:
        ProviderBudget(settings).reserve()
    assert exc.value.status_code==429


def test_chat_budget_blocks_before_network_and_bounds_output(tmp_path,monkeypatch):
    calls=[]
    async def post(self,url,**kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(200,request=httpx.Request('POST',url),json={'choices':[{'message':{'content':'{"reply":"Xin chào."}'}}]})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    settings=Settings(_env_file=None,data_dir=tmp_path,llm_api_key='synthetic',external_daily_call_limit=1,llm_max_completion_tokens=512)
    asyncio.run(AI(settings).complete('reply',{},ChatReply))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(AI(settings).complete('reply',{},ChatReply))
    assert exc.value.status_code==429
    assert len(calls)==1 and calls[0]['max_completion_tokens']==512


def test_chat_and_voice_share_one_daily_allowance(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import create_app
    settings=Settings(_env_file=None,data_dir=tmp_path,mode='live',llm_api_key='synthetic',
        transcription_model='synthetic',external_daily_call_limit=1)
    async def post(self,url,**kwargs):
        return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Xin chào'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    app=create_app(settings)
    with TestClient(app) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        client.patch('/api/consent',json={'voice_processing':True})
        assert client.post('/api/voice/transcribe',content=b'\x1aE\xdf\xa3synthetic',headers={'Content-Type':'audio/webm'}).status_code==200
        with pytest.raises(HTTPException) as exc:
            asyncio.run(app.state.ai.complete('reply',{},ChatReply))
        assert exc.value.status_code==429


def test_parallel_reservations_cannot_overrun_cap(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from app.provider_budget import ProviderBudget
    settings=Settings(_env_file=None,data_dir=tmp_path,external_daily_call_limit=3)
    def attempt(_):
        try:
            ProviderBudget(settings).reserve()
            return True
        except HTTPException as exc:
            assert exc.status_code==429
            return False
    with ThreadPoolExecutor(max_workers=6) as pool:
        assert sum(pool.map(attempt,range(12)))==3


def test_live_probe_uses_only_three_small_requests_and_exposes_no_credentials(tmp_path,monkeypatch):
    from app import check_voice
    settings=Settings(_env_file=None,data_dir=tmp_path,llm_api_key='synthetic-private-marker',external_daily_call_limit=12)
    monkeypatch.setattr(check_voice,'Settings',lambda **kwargs:settings)
    calls=[]
    async def post(self,url,**kwargs):
        calls.append(url)
        if url.endswith('/chat/completions'):
            return httpx.Response(200,request=httpx.Request('POST',url),json={'choices':[{'message':{'content':'{"reply":"Xin chào."}'}}]})
        if url.endswith('/audio/speech'):
            return httpx.Response(200,request=httpx.Request('POST',url),content=b'ID3synthetic',headers={'Content-Type':'audio/mpeg'})
        return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Xin chào tôi muốn trò chuyện'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    result=asyncio.run(check_voice.check())
    assert len(calls)==3 and result=={'chat':True,'speech':True,'transcription':True,'requests_attempted':3}
    assert 'synthetic-private-marker' not in str(result)


def test_live_probe_stops_on_failure_without_retry(tmp_path,monkeypatch):
    from app import check_voice
    monkeypatch.setattr(check_voice,'Settings',lambda **kwargs:Settings(_env_file=None,data_dir=tmp_path,llm_api_key='synthetic'))
    calls=[]
    async def post(self,url,**kwargs):
        calls.append(url)
        return httpx.Response(401,request=httpx.Request('POST',url),json={'error':'synthetic'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    result=asyncio.run(check_voice.check())
    assert len(calls)==1 and result['chat'] is False and result['speech'] is False
    assert result['status_code']==401 and result['error']=='provider_rejected_request'
