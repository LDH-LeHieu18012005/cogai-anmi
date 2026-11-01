"""Explicitly consented, ephemeral speech transport through the CogAI boundary."""
import httpx
import base64
import asyncio
import contextlib
import json
import re
import secrets
import time
from xml.sax.saxutils import escape as xml_escape
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from .models import ChatInput, InputModel
from .safety import normalize, redact, rule_risk, support_reply
from .models import Risk
from .provider_budget import ProviderBudget
from .provider_errors import service_error
from .http_client import provider_client
from .prompts import STT_CONTEXT, TTS_STYLE
from .dialogue import draft_ready

# Speech models trained on subtitled video emit these on silence or noise.
HALLUCINATIONS=[r'subscribe',r'dang ky kenh',r'ghien mi go',r'bam chuong',r'vietsub',r'subtitles? by',
                r'like va share',r'theo doi kenh',r'cam on (cac ban|moi nguoi) da (xem|theo doi|lang nghe)',
                r'hen gap lai (cac ban )?(trong|o) (nhung|cac) video']


def clean_transcript(text):
    sentences=re.split(r'(?<=[.!?…])\s+',text.strip())
    kept=[s for s in sentences if not any(re.search(p,normalize(s)) for p in HALLUCINATIONS)]
    result=' '.join(kept).strip()
    # The STT prompt is example context; drop it if the model echoes it back.
    if normalize(STT_CONTEXT).strip(' .!?') in normalize(result):
        return ''
    return result


def spoken_text(text):
    """Plain text for the voice: no Markdown symbols, abbreviations spelled out."""
    text=re.sub(r'^\s*[-•*]\s+','',text,flags=re.M)
    text=re.sub(r'[*_#`>~]','',text)
    text=re.sub(r'\b(PHQ|GAD)-(\d+)\b',lambda m:' '.join(m.group(1))+' '+m.group(2),text)
    return re.sub(r'\s+',' ',text).strip()


EDGE_ATTEMPTS=4  # Free Edge endpoint fails about a third of requests on a bad day.


def speech_ready(config):
    if config.speech_provider!='openai':
        return bool(config.edge_voice)
    return bool(config.speech_model and config.speech_voice)


def azure_ssml(text,voice,rate):
    return (f"<speak version='1.0' xml:lang='vi-VN'><voice name='{xml_escape(voice)}'>"
            f"<prosody rate='{rate}'>{xml_escape(text)}</prosody></voice></speak>")


class SpeakInput(InputModel):
    pass  # Caller cannot supply arbitrary text for speech generation.


class Prefetch:
    """Speech for one checked reply, synthesised in the background as soon as the
    reply exists, so the browser's request finds audio already arriving."""
    def __init__(self, text):
        self.text, self.chunks, self.done, self.failed = text, [], False, None
        self.created = time.monotonic()
        self.changed = asyncio.Condition()
        self.task = None

    async def add(self, chunk=None, *, finished=False, failure=None):
        async with self.changed:
            if chunk:
                self.chunks.append(chunk)
            self.done = self.done or finished
            self.failed = failure or self.failed
            self.changed.notify_all()

    async def replay(self):
        index = 0
        while True:
            async with self.changed:
                await self.changed.wait_for(lambda: len(self.chunks) > index or self.done)
                ready, finished = self.chunks[index:], self.done
            for chunk in ready:
                yield chunk
            index += len(ready)
            if finished and index >= len(self.chunks):
                return


class CancelInput(InputModel):
    turn_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')


def voice_router(store,config,current,dialogue,limited_ai):
    router=APIRouter(prefix='/api/voice')
    budget=ProviderBudget(config)
    running={}
    cancelled={}
    prefetched={}
    background=set()  # keeps progressive turns alive if the browser disconnects

    @router.post('/cancel')
    async def cancel(data: CancelInput,session=Depends(current)):
        key=(session['id'],data.turn_id)
        now=time.monotonic()
        for stale in [k for k,t in cancelled.items() if now-t>300]:
            cancelled.pop(stale,None)
        if len(cancelled)>=1000:
            cancelled.pop(next(iter(cancelled)))
        cancelled[key]=now
        task=running.get(key)
        if task:
            task.cancel()
        return {'cancelled':task is not None}

    def authorized(session):
        with store.connection() as db:
            store.validate(db,session)
        if not session['consent']['voice_processing'] or not session['consent']['external_ai']:
            raise HTTPException(403,'Cần đồng ý riêng cho âm thanh và dịch vụ AI ngoài.')
        if config.mode!='live' or not config.llm_api_key:
            raise HTTPException(503,'Giọng nói qua dịch vụ chưa được cấu hình. Bạn vẫn có thể nhắn tin.')

    async def provider(path,session,**kwargs):
        authorized(session)
        try:
            async with provider_client(dialogue.ai.http_client) as client:
                budget.reserve()
                result=await client.post(config.llm_base_url.rstrip('/')+path,
                    headers={'Authorization':'Bearer '+config.llm_api_key},**kwargs)
                result.raise_for_status()
            authorized(session)  # Do not return stale speech/transcripts after revocation.
            return result
        except httpx.HTTPStatusError as exc:
            raise service_error(exc.response.status_code) from None
        except httpx.HTTPError:
            raise HTTPException(503,'Dịch vụ giọng nói tạm thời chưa sẵn sàng. Hãy thử lại hoặc nhập chữ.')

    async def read_audio(request):
        mime=request.headers.get('content-type','').split(';')[0].strip().lower()
        formats={'audio/webm':('webm',b'\x1aE\xdf\xa3'),'audio/ogg':('ogg',b'OggS'),
                 'audio/wav':('wav',b'RIFF'),'audio/mp4':('m4a',None)}
        audio=await request.body()
        if mime not in formats or len(audio)<8:
            raise HTTPException(415,'Định dạng ghi âm chưa được hỗ trợ.')
        extension,signature=formats[mime]
        if (signature and not audio.startswith(signature)) or (mime=='audio/mp4' and audio[4:8]!=b'ftyp'):
            raise HTTPException(415,'Nội dung không khớp định dạng âm thanh.')
        return audio,mime,extension

    async def recognize(session,audio,mime,extension):
        response=await provider('/audio/transcriptions',session,
            data={'model':config.transcription_model,'language':'vi','prompt':STT_CONTEXT,'temperature':'0'},
            files={'file':('recording.'+extension,audio,mime)})
        try:
            text=response.json()['text']
            if not isinstance(text,str) or len(text)>4000:
                raise ValueError()
        except (KeyError,TypeError,ValueError):
            raise HTTPException(503,'Chưa nhận được bản chép lời hợp lệ. Hãy thử ghi ngắn hơn.')
        return clean_transcript(text)

    def openai_speech(text,response_format):
        payload={'model':config.speech_model,'voice':config.speech_voice,'input':text,'response_format':response_format}
        if config.speech_model.startswith('gpt-4o-mini-tts'):
            payload['instructions']=TTS_STYLE
        return payload

    async def edge_audio(text):
        import edge_tts
        started=False
        try:
            async for chunk in edge_tts.Communicate(text,config.edge_voice,rate=config.edge_rate,connect_timeout=5).stream():
                if chunk['type']=='audio' and chunk['data']:
                    started=True
                    yield chunk['data']
        except Exception:
            if not started:
                raise
            # Partial audio already played; stop instead of restarting mid-sentence.

    async def openai_audio(session,text):
        authorized(session)
        try:
            async with provider_client(dialogue.ai.http_client) as client:
                budget.reserve()
                async with client.stream('POST',config.llm_base_url.rstrip('/')+'/audio/speech',
                        headers={'Authorization':'Bearer '+config.llm_api_key},json=openai_speech(text,'mp3')) as response:
                    if response.status_code>=400:
                        raise service_error(response.status_code)
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.HTTPError:
            raise HTTPException(503,'Dịch vụ giọng nói tạm thời chưa sẵn sàng. Hãy thử lại hoặc nhập chữ.')

    async def first_audio(session,text):
        """First Edge request that produces audio; returns (stream, first chunk).

        AnMi has one voice everywhere (the MYHealth device voice), so a slow Edge
        connection is never covered by a different provider voice. Edge usually
        answers in about half a second but a cold connection can hang for several:
        after 1 s without audio, or on an error, another Edge request starts in
        parallel, up to four, and the first to speak is used.
        """
        authorized(session)
        streams={}
        def start(stream):
            streams[asyncio.ensure_future(anext(stream))]=stream
        start(edge_audio(text))
        attempts=1
        failure=None
        try:
            while streams:
                done,_=await asyncio.wait(streams,timeout=1.0 if attempts<EDGE_ATTEMPTS else None,return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    stream=streams.pop(task)
                    if not task.cancelled() and task.exception() is None:
                        return stream,task.result()
                    failure=task.exception() if not task.cancelled() else failure
                    await stream.aclose()
                if attempts<EDGE_ATTEMPTS and (not done or not streams):
                    attempts+=1
                    authorized(session)
                    start(edge_audio(text))
        finally:
            for task,stream in streams.items():
                task.cancel()
                with contextlib.suppress(BaseException):
                    await task
                await stream.aclose()
        if isinstance(failure,HTTPException):
            raise failure
        raise HTTPException(503,'Dịch vụ giọng đọc tiếng Việt tạm thời chưa sẵn sàng. Phản hồi chữ vẫn được giữ.')

    async def azure_audio(session,text):
        """HoaiMy through the official Azure Speech REST API, streamed as MP3."""
        authorized(session)
        url=f'https://{config.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1'
        headers={'Ocp-Apim-Subscription-Key':config.azure_speech_key,'Content-Type':'application/ssml+xml',
                 'X-Microsoft-OutputFormat':'audio-24khz-48kbitrate-mono-mp3','User-Agent':'cogai-anmi'}
        async with provider_client(dialogue.ai.http_client) as client:
            async with client.stream('POST',url,headers=headers,timeout=10,
                    content=azure_ssml(text,config.edge_voice,config.edge_rate).encode()) as response:
                if response.status_code>=400:
                    raise service_error(response.status_code)
                async for chunk in response.aiter_bytes():
                    yield chunk

    def azure_enabled():
        return config.speech_provider in {'azure','auto'} and bool(config.azure_speech_key)

    async def speech_chunks(session,text):
        text=spoken_text(redact(text))
        stream=None
        if azure_enabled():
            stream=azure_audio(session,text)
            try:
                first=await anext(stream)
            except (HTTPException,httpx.HTTPError,StopAsyncIteration):
                # Same HoaiMy voice from Edge: an Azure outage or quota never changes AnMi's voice.
                await stream.aclose()
                stream=None
        if stream is None and config.speech_provider!='openai':
            stream,first=await first_audio(session,text)
        if config.speech_provider=='openai':
            stream=openai_audio(session,text)
        else:
            yield first
        async for chunk in stream:
            yield chunk

    async def synthesize(session,text):
        """Whole clip and its MIME type, for clients that do not stream."""
        if config.speech_provider!='openai':
            audio=b''.join([chunk async for chunk in speech_chunks(session,text)])
            if not audio:
                raise HTTPException(503,'Dịch vụ chưa trả về âm thanh hợp lệ.')
            return audio,'audio/mpeg'
        response=await provider('/audio/speech',session,json=openai_speech(spoken_text(redact(text)),config.speech_format))
        if not response.headers.get('content-type','').startswith(('audio/','application/octet-stream')) or not response.content or len(response.content)>10_000_000:
            raise HTTPException(503,'Dịch vụ chưa trả về âm thanh hợp lệ.')
        if config.speech_format=='wav' and not response.content.startswith(b'RIFF'):
            raise HTTPException(503,'Dịch vụ chưa trả đúng định dạng giọng đọc WAV.')
        return response.content,'audio/wav' if config.speech_format=='wav' else 'audio/mpeg'

    def checked_reply(session):
        state=dialogue.state(session)
        turns=state.get('turns',[])
        if not turns or turns[-1]['role']!='assistant':
            raise HTTPException(409,'Chưa có phản hồi đã kiểm tra để đọc.')
        risk=store.document(session,'safety',{})
        text=support_reply(Risk.model_validate(risk)) if risk.get('level') in {'high','check_in'} else turns[-1]['content']
        return text,risk

    @router.post('/turn')
    async def continuous_turn(request: Request,session=Depends(current)):
        authorized(session)
        if not config.transcription_model or not speech_ready(config):
            raise HTTPException(503,'Cần cấu hình đủ nhận giọng nói và giọng đọc để trò chuyện liên tục.')
        audio,mime,extension=await read_audio(request)
        # Streaming clients fetch the checked reply's audio from /stream and can start
        # playing within the first chunk instead of waiting for the whole clip.
        stream=request.headers.get('x-cogai-speech')=='stream'
        # NDJSON progress: the transcript is sent as soon as speech is recognised, so the
        # user's words appear while AnMi is still thinking; the checked reply follows.
        progressive=request.headers.get('x-cogai-progress')=='ndjson'
        events=asyncio.Queue() if progressive else None
        turn_id=request.headers.get('x-cogai-voice-turn') or secrets.token_hex(16)
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',turn_id):
            raise HTTPException(422,'Mã lượt nói không hợp lệ.')
        async def execute():
            started=time.monotonic()
            text=await recognize(session,audio,mime,extension)
            recognized=time.monotonic()
            if not text:
                return {'heard':False,'audio_stored':False}
            if events:
                events.put_nowait({'transcript':text})
            dialogue.safety_event(session,'voice_transcript',rule_risk(text))
            token=draft_ready.set(lambda draft:prefetch(session,draft) if stream else None)
            try:
                result=await dialogue.chat(session,ChatInput(message=text,channel='voice'))
            finally:
                draft_ready.reset(token)
            replied=time.monotonic()
            # Only server-generated, checked replies reach synthesis. No direct
            # audio-to-audio provider bypass around the existing safety journey.
            latest=store.document(session,'safety',{})
            if latest.get('level') in {'high','check_in'} and latest.get('level')!=result['risk']['level']:
                raise HTTPException(409,'Có tín hiệu mới cần ưu tiên hỗ trợ. Hãy tải lại cuộc trò chuyện.')
            if stream:
                prefetch(session)
                store.audit(session,'handsfree_turn')
                latency={name:round((end-begin)*1000,2) for name,begin,end in (
                    ('transcription',started,recognized),('dialogue',recognized,replied),('total',started,replied))}
                return {'heard':True,'transcript':text,**result,'speech_stream':True,'audio_stored':False,
                        'pause_for_support':result['risk']['requires_support'],'latency_ms':latency}
            try:
                speech,audio_type=await synthesize(session,result['reply'])
            except HTTPException as exc:
                if exc.status_code!=503:
                    raise
                return {'heard':True,'transcript':text,**result,'audio_stored':False,
                        'audio_error':str(exc.detail)+' Phản hồi chữ vẫn được giữ.'}
            latest=store.document(session,'safety',{})
            if latest.get('level') in {'high','check_in'} and latest.get('level')!=result['risk']['level']:
                raise HTTPException(409,'Đã dừng âm thanh cũ vì có tín hiệu cần hỗ trợ.')
            store.audit(session,'handsfree_turn')
            finished=time.monotonic()
            latency={name:round((end-begin)*1000,2) for name,begin,end in (
                ('transcription',started,recognized),('dialogue',recognized,replied),
                ('speech',replied,finished),('total',started,finished))}
            return {'heard':True,'transcript':text,**result,'audio_base64':base64.b64encode(speech).decode(),
                    'audio_type':audio_type,'audio_stored':False,'pause_for_support':result['risk']['requires_support'],
                    'latency_ms':latency}
        key=(session['id'],turn_id)
        async def tracked():
            if key in cancelled:
                raise HTTPException(409,'Lượt nói đã được dừng.')
            task=asyncio.current_task();running[key]=task
            try:
                return await execute()
            finally:
                if running.get(key) is task:
                    running.pop(key,None)
                cancelled.pop(key,None)
        if not progressive:
            try:
                return await limited_ai(session,tracked())
            except asyncio.CancelledError:
                raise HTTPException(409,'Lượt nói đã được dừng.')

        async def run():
            try:
                events.put_nowait({'result':await limited_ai(session,tracked())})
            except HTTPException as exc:
                events.put_nowait({'error':{'status':exc.status_code,'detail':exc.detail}})
            except asyncio.CancelledError:
                events.put_nowait({'error':{'status':409,'detail':'Lượt nói đã được dừng.'}})
            except Exception:
                events.put_nowait({'error':{'status':503,'detail':'Dịch vụ tạm thời chưa sẵn sàng.'}})
        worker=asyncio.create_task(run())
        background.add(worker);worker.add_done_callback(background.discard)

        async def body():
            while True:
                event=await events.get()
                yield json.dumps(event,ensure_ascii=False)+'\n'
                if 'result' in event or 'error' in event:
                    return
        return StreamingResponse(body(),media_type='application/x-ndjson',headers={'Cache-Control':'no-store'})

    @router.post('/transcribe')
    async def transcribe(request: Request,session=Depends(current)):
        authorized(session)
        if not config.transcription_model:
            raise HTTPException(503,'Chưa cấu hình mô hình chuyển giọng nói thành chữ.')
        audio,mime,extension=await read_audio(request)
        async def execute():
            text=await recognize(session,audio,mime,extension)
            if not text:
                raise HTTPException(503,'Chưa nhận được bản chép lời hợp lệ. Hãy thử ghi ngắn hơn.')
            # Do not keep bytes or transcript records. The user reviews text before sending chat.
            risk=rule_risk(text)
            dialogue.safety_event(session,'voice_transcript',risk)
            store.audit(session,'voice_transcribed')
            return {'transcript':text.strip(),'risk':risk.model_dump(),'audio_stored':False}
        return await limited_ai(session,execute())

    @router.post('/speak')
    async def speak(data: SpeakInput,session=Depends(current)):
        authorized(session)
        if not speech_ready(config):
            raise HTTPException(503,'Chưa cấu hình mô hình và giọng đọc.')
        async def execute():
            text,risk=checked_reply(session)
            speech,audio_type=await synthesize(session,text)
            latest=store.document(session,'safety',{})
            if latest.get('level') in {'high','check_in'} and latest.get('level')!=risk.get('level'):
                raise HTTPException(409,'Có tín hiệu mới cần ưu tiên hỗ trợ; đã dừng giọng đọc cũ.')
            store.audit(session,'voice_spoken')
            return Response(speech,media_type=audio_type,headers={'Cache-Control':'no-store'})
        return await limited_ai(session,execute())

    def prefetch(session,text=None):
        """Start synthesising speech now: the latest checked reply, or a draft being checked.

        Audio stays on the server; /stream serves it only when `text` equals the reply
        that was saved after the output check, so a withheld draft is never heard.
        """
        if not speech_ready(config):
            return
        try:
            authorized(session)
            if text is None:
                text,_=checked_reply(session)
        except HTTPException:
            return
        text=text if isinstance(text,str) else ''
        if not text:
            return
        now=time.monotonic()
        for key in [k for k,v in prefetched.items() if now-v.created>120]:
            prefetched.pop(key).task.cancel()
        previous=prefetched.get(session['id'])
        if previous and previous.text==text:
            return
        if previous:
            previous.task.cancel()
        entry=Prefetch(text)

        async def run():
            try:
                async for chunk in speech_chunks(session,text):
                    await entry.add(chunk)
                await entry.add(finished=True)
            except asyncio.CancelledError:
                await entry.add(finished=True,failure='cancelled')
                raise
            except Exception as exc:  # Provider/consent errors surface when the browser asks.
                await entry.add(finished=True,failure=exc)
        entry.task=asyncio.create_task(run())
        prefetched[session['id']]=entry
    router.prefetch=prefetch
    # The desk device bridge reuses the same consented STT and AnMi voice.
    router.recognize=recognize
    router.speech_chunks=speech_chunks

    @router.get('/stream')
    async def stream(session=Depends(current)):
        """MP3 of the latest checked reply, streamed for an <audio> element.

        Not under the per-session AI lock: the browser aborts this request when the
        user talks over AnMi, and the next turn must not wait for it to close.
        """
        authorized(session)
        if not speech_ready(config):
            raise HTTPException(503,'Chưa cấu hình mô hình và giọng đọc.')
        text,_=checked_reply(session)
        entry=prefetched.get(session['id'])
        if entry and entry.text==text:
            # Audio started while the reply travelled to the browser; replay what is
            # buffered and follow the rest. A failed prefetch falls back to a fresh call.
            chunks=entry.replay()
            if entry.done and not entry.chunks:
                prefetched.pop(session['id'],None)
                chunks=speech_chunks(session,text)
        else:
            chunks=speech_chunks(session,text)
        try:
            # Fail with a real status code before headers are sent.
            first=await anext(chunks)
        except StopAsyncIteration:
            if not (entry and entry.text==text):
                raise HTTPException(503,'Dịch vụ chưa trả về âm thanh hợp lệ.')
            prefetched.pop(session['id'],None)  # background attempt produced nothing: try once more now
            chunks=speech_chunks(session,text)
            try:
                first=await anext(chunks)
            except StopAsyncIteration:
                raise HTTPException(503,'Dịch vụ chưa trả về âm thanh hợp lệ.')
        store.audit(session,'voice_spoken')
        async def body():
            yield first
            async for chunk in chunks:
                yield chunk
        return StreamingResponse(body(),media_type='audio/mpeg',headers={'Cache-Control':'no-store'})

    return router
