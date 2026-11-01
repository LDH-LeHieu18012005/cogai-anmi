import json
import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.ai import ChatReply, OutputCheck, ModelRisk
from app.research import AppraisalState


def live_app(tmp_path,monkeypatch,complete):
    app=create_app(Settings(data_dir=tmp_path,mode='live',llm_api_key='synthetic'))
    monkeypatch.setattr(app.state.ai,'complete',complete)
    return app


def test_risk_appraisal_and_draft_run_in_parallel_but_output_is_still_checked(tmp_path,monkeypatch):
    order=[]
    async def complete(task,data,schema,**kwargs):
        order.append(schema)
        if schema is ModelRisk:
            assert data['latest_message']=='Hôm nay tôi mệt vì làm ca'
            return ModelRisk(level='low',reason='synthetic')
        if schema is AppraisalState:
            return AppraisalState()
        if schema is ChatReply:
            assert 'AnMi' in task and 'công nhân' in task and 'sinh viên' in task
            return ChatReply(reply='Mình đang nghe bạn. Hôm nay điều gì làm bạn mệt nhất?')
        assert schema is OutputCheck
        return OutputCheck(allow=True)
    with TestClient(live_app(tmp_path,monkeypatch,complete)) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        response=client.post('/api/chat',json={'message':'Hôm nay tôi mệt vì làm ca','channel':'voice'})
        assert response.status_code==200 and 'mệt nhất' in response.json()['reply']
        assert set(order)=={ModelRisk,AppraisalState,ChatReply,OutputCheck}
        assert order.index(OutputCheck)>order.index(ChatReply) and order.count(OutputCheck)==1


def test_high_risk_discards_parallel_draft_and_skips_output(tmp_path,monkeypatch):
    calls=[]
    async def complete(task,data,schema,**kwargs):
        calls.append(schema)
        if schema is ModelRisk:
            return ModelRisk(level='high',reason='synthetic')
        if schema is ChatReply:
            return ChatReply(reply='DRAFT_MUST_NOT_BE_SHOWN')
        return AppraisalState()
    with TestClient(live_app(tmp_path,monkeypatch,complete)) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        response=client.post('/api/chat',json={'message':'Tôi muốn kể một chuyện','channel':'voice'})
        assert response.json()['risk']['level']=='high'
        assert 'DRAFT_MUST_NOT_BE_SHOWN' not in response.text
        assert OutputCheck not in calls


def test_vietnamese_stt_and_tts_have_explicit_style_and_matching_wav_mime(tmp_path,monkeypatch):
    app=create_app(Settings(data_dir=tmp_path,mode='live',llm_api_key='synthetic',
        transcription_model='gpt-4o-transcribe',speech_model='gpt-4o-mini-tts',speech_voice='marin',speech_provider='openai',speech_format='wav'))
    async def post(self,url,**kwargs):
        if url.endswith('/transcriptions'):
            assert kwargs['data']['language']=='vi' and 'prompt' in kwargs['data']
            return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Tôi muốn trò chuyện'})
        assert kwargs['json']['voice']=='marin'
        assert 'tiếng Việt' in kwargs['json']['instructions']
        assert kwargs['json']['response_format']=='wav'
        return httpx.Response(200,request=httpx.Request('POST',url),content=b'RIFFsynthetic',headers={'Content-Type':'audio/wav'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    with TestClient(app) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        client.patch('/api/consent',json={'voice_processing':True})
        response=client.post('/api/voice/transcribe',content=b'\x1aE\xdf\xa3synthetic',headers={'Content-Type':'audio/webm'})
        assert response.status_code==200
        session=app.state.store.session(client.cookies.get('cogai_session'))
        app.state.store.put_document(session,'conversation','conversation',{'turns':[{'role':'assistant','content':'Mình đang nghe bạn.'}]})
        response=client.post('/api/voice/speak',json={})
        assert response.status_code==200 and response.headers['content-type'].startswith('audio/wav')


def test_invalid_risk_assessment_stops_reply(tmp_path,monkeypatch):
    from app.ai import ProviderFailure
    async def complete(task,data,schema,**kwargs):
        if schema is ChatReply:
            return ChatReply(reply='DRAFT_MUST_NOT_BE_SHOWN')
        raise ProviderFailure('Invalid assessment')
    with TestClient(live_app(tmp_path,monkeypatch,complete)) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        response=client.post('/api/chat',json={'message':'Hôm nay tôi hơi mệt','channel':'voice'})
        assert response.json()['risk']['level']=='unavailable'
        assert 'DRAFT_MUST_NOT_BE_SHOWN' not in response.text


def test_parallel_draft_still_withholds_unsafe_output(tmp_path,monkeypatch):
    async def complete(task,data,schema,**kwargs):
        if schema is ModelRisk:
            return ModelRisk(level='low',reason='synthetic')
        if schema is AppraisalState:
            return AppraisalState()
        if schema is ChatReply:
            return ChatReply(reply='SYNTHETIC_OUTPUT_MUST_BE_WITHHELD')
        return OutputCheck(allow=False)
    with TestClient(live_app(tmp_path,monkeypatch,complete)) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        response=client.post('/api/chat',json={'message':'Hôm nay tôi hơi mệt','channel':'voice'})
        assert response.json()['withheld'] is True and response.json()['risk']['requires_support'] is False
        assert 'SYNTHETIC_OUTPUT_MUST_BE_WITHHELD' not in response.text


def test_check_in_is_resolved_by_context_aware_model_not_stuck_forever(tmp_path,monkeypatch):
    seen=[]
    async def complete(task,data,schema,**kwargs):
        if schema is ModelRisk:
            seen.append(data)
            return ModelRisk(level='low',reason='synthetic')
        if schema is AppraisalState:
            return AppraisalState()
        if schema is ChatReply:
            return ChatReply(reply='Chào bạn, mình là AnMi. Hôm nay bạn muốn kể gì?')
        return OutputCheck(allow=True)
    with TestClient(live_app(tmp_path,monkeypatch,complete)) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True,'persist':True})
        assert client.post('/api/chat',json={'message':'Tôi không muốn tiếp tục nữa'}).json()['risk']['level']=='check_in'
        client.post('/api/chat/reset',json={})
        result=client.post('/api/chat',json={'message':'xin chào'}).json()
        assert result['risk']['level']=='low' and 'AnMi' in result['reply']
        assert seen[-1]['latest_message']=='xin chào'
        assert client.get('/api/chat').json()['risk']['level']=='low'
        # Rules see only the new message; the handled phrase does not re-trigger later turns.
        assert client.post('/api/chat',json={'message':'Mình muốn kể về việc học'}).json()['risk']['level']=='low'


def test_affirmative_answer_to_check_in_escalates(tmp_path,monkeypatch):
    async def complete(task,data,schema,**kwargs):
        if schema is ModelRisk:
            assert any('làm hại bản thân' in t['content'] for t in data['recent_turns'])
            return ModelRisk(level='high',reason='synthetic')
        if schema is ChatReply:
            return ChatReply(reply='DRAFT_MUST_NOT_BE_SHOWN')
        return AppraisalState()
    with TestClient(live_app(tmp_path,monkeypatch,complete)) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        client.post('/api/chat',json={'message':'Tôi không muốn tiếp tục nữa'})
        result=client.post('/api/chat',json={'message':'Có'}).json()
        assert result['risk']['level']=='high' and 'DRAFT_MUST_NOT_BE_SHOWN' not in result['reply']


def test_stt_hallucinations_and_prompt_echo_are_dropped():
    from app.voice import clean_transcript
    from app.prompts import STT_CONTEXT
    assert clean_transcript('Hãy subscribe cho kênh Ghiền Mì Gõ để không bỏ lỡ những video hấp dẫn.')==''
    assert clean_transcript(STT_CONTEXT)==''
    assert clean_transcript('Hôm nay mình mệt quá. Cảm ơn các bạn đã theo dõi.')=='Hôm nay mình mệt quá.'
    assert clean_transcript('Cảm ơn AnMi nhé')=='Cảm ơn AnMi nhé'


def test_rules_separate_named_activity_from_ambiguous_or_urgent_phrases():
    from app.safety import rule_risk
    assert rule_risk('Mình không muốn tiếp tục học ngành này').level=='low'
    assert rule_risk('Mình không muốn tiếp tục nữa.').level=='check_in'
    assert rule_risk('Mình không muốn tiếp tục sống').level=='high'


def test_single_edge_voice_retries_edge_and_never_switches_to_provider_voice(tmp_path,monkeypatch):
    import edge_tts
    attempts=[]
    class Communicate:
        def __init__(self,text,voice,**kwargs):
            attempts.append((text,voice,kwargs.get('rate')))
        async def stream(self):
            if len(attempts)<=failures:
                raise RuntimeError('synthetic edge outage')
            yield {'type':'audio','data':b'ID3edge-'}
            yield {'type':'WordBoundary'}
            yield {'type':'audio','data':b'chunk'}
    monkeypatch.setattr(edge_tts,'Communicate',Communicate)
    async def no_provider_voice(*args,**kwargs):
        raise AssertionError('A second voice must never be used')
    monkeypatch.setattr(httpx.AsyncClient,'post',no_provider_voice)
    monkeypatch.setattr(httpx.AsyncClient,'stream',no_provider_voice)
    # Even with OpenAI speech settings present, AnMi keeps the single HoaiMy voice.
    app=create_app(Settings(data_dir=tmp_path,mode='live',llm_api_key='synthetic',transcription_model='gpt-4o-transcribe',
        speech_model='gpt-4o-mini-tts',speech_voice='marin'))
    with TestClient(app) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        client.patch('/api/consent',json={'voice_processing':True})
        assert client.get('/api/config').json()['voice']['speech'] is True
        session=app.state.store.session(client.cookies.get('cogai_session'))
        app.state.store.put_document(session,'conversation','conversation',{'turns':[{'role':'assistant','content':'**Mình** đang nghe bạn.'}]})
        failures=0
        response=client.get('/api/voice/stream')
        assert response.status_code==200 and response.headers['content-type']=='audio/mpeg'
        assert response.content==b'ID3edge-chunk' and attempts==[('Mình đang nghe bạn.','vi-VN-HoaiMyNeural','+0%')]
        attempts.clear();failures=1
        assert client.get('/api/voice/stream').content==b'ID3edge-chunk'
        assert [a[1] for a in attempts]==['vi-VN-HoaiMyNeural']*2
        attempts.clear();failures=4
        response=client.get('/api/voice/stream')
        assert response.status_code==503 and len(attempts)==4
        # The non-streaming read-aloud button uses the same voice.
        attempts.clear();failures=0
        response=client.post('/api/voice/speak',json={})
        assert response.status_code==200 and response.content==b'ID3edge-chunk'



def test_reply_speech_is_prefetched_once_and_replayed_to_the_browser(tmp_path,monkeypatch):
    import edge_tts
    calls=[]
    class Communicate:
        def __init__(self,text,voice,**kwargs):
            calls.append(text)
        async def stream(self):
            yield {'type':'audio','data':b'ID3pre-'}
            yield {'type':'audio','data':b'fetched'}
    monkeypatch.setattr(edge_tts,'Communicate',Communicate)
    replies=iter(['Mình đang nghe bạn.','Bạn muốn kể thêm không?'])
    async def complete(task,data,schema,**kwargs):
        if schema is ModelRisk:
            return ModelRisk(level='low',reason='synthetic')
        if schema is ChatReply:
            return ChatReply(reply=next(replies))
        if schema is OutputCheck:
            return OutputCheck(allow=True)
        return AppraisalState()
    app=live_app(tmp_path,monkeypatch,complete)
    with TestClient(app) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        client.patch('/api/consent',json={'voice_processing':True})
        assert client.post('/api/chat',json={'message':'Hôm nay mình mệt','speak':True}).status_code==200
        assert client.get('/api/voice/stream').content==b'ID3pre-fetched'
        assert client.get('/api/voice/stream').content==b'ID3pre-fetched'
        assert calls==['Mình đang nghe bạn.']  # synthesised once, in the background, then replayed
        client.post('/api/chat',json={'message':'Ừ','speak':True})
        assert client.get('/api/voice/stream').content==b'ID3pre-fetched'
        assert calls==['Mình đang nghe bạn.','Bạn muốn kể thêm không?']


def test_transient_provider_errors_are_retried_once(tmp_path,monkeypatch):
    from app.ai import ProviderFailure
    failures={'risk':1,'draft':1,'check':1}
    async def complete(task,data,schema,**kwargs):
        name={ModelRisk:'risk',ChatReply:'draft',OutputCheck:'check'}.get(schema)
        if name and failures[name]:
            failures[name]-=1
            raise ProviderFailure('Provider response unavailable or invalid')
        if schema is ModelRisk:
            return ModelRisk(level='low',reason='synthetic')
        if schema is ChatReply:
            return ChatReply(reply='Đánh cầu lông giúp bạn bớt nghĩ ngợi. Bạn thường chơi vào lúc nào?')
        if schema is OutputCheck:
            return OutputCheck(allow=True)
        return AppraisalState()
    with TestClient(live_app(tmp_path,monkeypatch,complete)) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        result=client.post('/api/chat',json={'message':'Tôi cảm thấy bớt nghĩ ngợi nhiều.'}).json()
        assert result['risk']['level']=='low' and 'cầu lông' in result['reply']


def test_progressive_turn_sends_transcript_before_reply(tmp_path,monkeypatch):
    async def complete(task,data,schema,**kwargs):
        if schema is ModelRisk:
            return ModelRisk(level='low',reason='synthetic')
        if schema is ChatReply:
            return ChatReply(reply='Mình nghe bạn đây.')
        if schema is OutputCheck:
            return OutputCheck(allow=True)
        return AppraisalState()
    async def post(self,url,**kwargs):
        return httpx.Response(200,request=httpx.Request('POST',url),json={'text':'Tớ buồn.'})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    app=create_app(Settings(data_dir=tmp_path,mode='live',llm_api_key='synthetic',transcription_model='gpt-4o-transcribe'))
    monkeypatch.setattr(app.state.ai,'complete',complete)
    with TestClient(app) as client:
        client.post('/api/session',json={'accepted':True,'adult':True,'external_ai':True})
        client.patch('/api/consent',json={'voice_processing':True})
        response=client.post('/api/voice/turn',content=b'\x1aE\xdf\xa3synthetic',
            headers={'Content-Type':'audio/webm','X-CogAI-Progress':'ndjson','X-CogAI-Speech':'stream'})
        assert response.headers['content-type'].startswith('application/x-ndjson')
        events=[json.loads(line) for line in response.text.splitlines()]
        assert events[0]=={'transcript':'Tớ buồn.'}
        assert events[-1]['result']['reply']=='Mình nghe bạn đây.' and events[-1]['result']['transcript']=='Tớ buồn.'
