"""Desk device bridge: xiaozhi WebSocket protocol into the same AnMi journey as web voice.

The device streams Opus microphone frames; the server finds the end of speech,
transcribes, runs dialogue.chat (risk check, CBT step, output check) and streams the
checked reply back as Opus in the AnMi voice. No audio is stored. See
https://github.com/78/xiaozhi-esp32/blob/main/docs/websocket.md for the protocol.
"""
import array
import asyncio
import contextlib
import io
import json
import logging
import math
import re
import time
import uuid
import wave
from collections import deque

import av
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .devices import Devices
from .dialogue import draft_ready, reply_ready
from .models import ChatInput
from .safety import rule_risk

IN_RATE, OUT_RATE, FRAME_MS = 16000, 24000, 60
OUT_SAMPLES = OUT_RATE*FRAME_MS//1000
LEAD_FRAMES = 5  # sent ahead of real time so the device buffer never runs dry
# The person at the device agreed when the operator registered it; nothing is kept after the session.
DEVICE_CONSENT = {'accepted':True,'adult':True,'persist':False,'external_ai':True,'voice_processing':True}
WEB_ONLY = 'Bạn có thể mở mục Hỗ trợ để xem các lựa chọn.'
TURNS_PER_MINUTE = 10
END_SILENCE_MS = 1500  # 1200 split "Xin chào AnMi. Hôm nay..." into two turns in testing
CLAUSE_CHARS = 40
MIN_SPEECH_LEVEL = 400    # RMS; quiet rooms
FLOOR_RISE = 1.01         # per 60 ms frame of continuous loudness (~x2 in 4 s)
SPEECH_OVER_NOISE = 2.5   # speech must stand this far above the room's background
START_BUFFER_FRAMES = 4  # ~0.25 s buffered before playback, so a slow voice stream does not stutter
GREETING = 'Chào bạn, mình là AnMi. Hôm nay bạn muốn chia sẻ điều gì?'
log = logging.getLogger('uvicorn.error')


def pcm_rms(pcm):
    samples=array.array('h',pcm)
    return math.sqrt(sum(s*s for s in samples)/len(samples)) if samples else 0.0


def wav_bytes(pcm):
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(IN_RATE)
        out.writeframes(pcm)
    return buffer.getvalue()


def sentences(text):
    parts=[p.strip() for p in re.split(r'(?<=[.!?…])\s+',text) if p.strip()]
    merged=[]
    for part in parts:  # very short sentences ride along with the next one
        if merged and len(merged[-1])<25:
            merged[-1]+=' '+part
        else:
            merged.append(part)
    # Edge starts a ~40 character clause in about half a second but a 60+ character sentence
    # in about three (measured): speak long sentences clause by clause, split at commas.
    pieces=[]
    for part in merged:
        while len(part)>CLAUSE_CHARS:
            cut=part.find(', ',12)
            if not 0<cut<len(part)-12:
                break
            pieces.append(part[:cut+1])
            part=part[cut+2:]
        pieces.append(part)
    return pieces


class Decoder:
    """Opus frames from the microphone -> 16 kHz mono s16 PCM."""
    def __init__(self):
        self.codec=av.CodecContext.create('opus','r')
        self.codec.sample_rate=IN_RATE
        self.codec.layout='mono'
        self.resampler=av.AudioResampler(format='s16',layout='mono',rate=IN_RATE)

    def pcm(self,packet):
        out=bytearray()
        try:
            for frame in self.codec.decode(av.Packet(packet)):
                for f in self.resampler.resample(frame):
                    out+=bytes(f.planes[0])[:f.samples*2]
        except av.FFmpegError:
            pass  # one corrupt frame is dropped, not the turn
        return bytes(out)


class OpusStream:
    """MP3 chunks in, 60 ms Opus packets (24 kHz mono) out as soon as enough audio is decoded."""
    def __init__(self):
        self.decoder=av.CodecContext.create('mp3','r')
        self.resampler=av.AudioResampler(format='s16',layout='mono',rate=OUT_RATE)
        self.encoder=av.CodecContext.create('libopus','w')
        self.encoder.sample_rate,self.encoder.layout,self.encoder.format,self.encoder.bit_rate=OUT_RATE,'mono','s16',32000
        self.encoder.options={'frame_duration':str(FRAME_MS),'application':'voip'}
        self.encoder.open()
        self.pcm,self.pts=bytearray(),0

    def _resampled(self,frame):
        for f in self.resampler.resample(frame):
            self.pcm+=bytes(f.planes[0])[:f.samples*2]

    def _encode(self):
        step,packets=OUT_SAMPLES*2,[]
        while len(self.pcm)>=step:
            frame=av.AudioFrame(format='s16',layout='mono',samples=OUT_SAMPLES)
            frame.planes[0].update(bytes(self.pcm[:step]))
            frame.sample_rate,frame.pts=OUT_RATE,self.pts
            del self.pcm[:step]
            self.pts+=OUT_SAMPLES
            packets+=[bytes(p) for p in self.encoder.encode(frame)]
        return packets

    def _decode(self,packets):
        for packet in packets:
            try:
                frames=self.decoder.decode(packet)
            except av.InvalidDataError:
                continue  # an encoder tag frame or a damaged frame is skipped, not the sentence
            for frame in frames:
                self._resampled(frame)

    def feed(self,mp3):
        self._decode(self.decoder.parse(mp3))
        return self._encode()

    def finish(self):
        self._decode(self.decoder.parse(b''))
        for frame in self.decoder.decode(None):
            self._resampled(frame)
        self._resampled(None)
        if self.pcm:
            self.pcm+=b'\0'*(OUT_SAMPLES*2-len(self.pcm))
        return self._encode()+[bytes(p) for p in self.encoder.encode(None)]


def opus_frames(mp3):
    """MP3 speech -> 60 ms Opus packets at 24 kHz mono."""
    stream=OpusStream()
    return stream.feed(mp3)+stream.finish()


class Endpointer:
    """Energy end-of-speech detection for the device's auto listening mode.

    Speech is measured against the room's own background level, so a café or a
    fan does not count as the person still talking.
    """
    def __init__(self,max_seconds):
        self.max_frames=max_seconds*1000//FRAME_MS
        # Background level, kept across turns: the room stays the same between them.
        # Starts as a quiet room so someone who talks straight away is still heard.
        self.floor=MIN_SPEECH_LEVEL/SPEECH_OVER_NOISE
        self.reset()

    def reset(self):
        self.pcm,self.frames,self.voiced,self.silence,self.speaking=bytearray(),0,0,0,False

    def add(self,pcm):
        """Append one frame; True once the user has spoken and then paused."""
        self.pcm+=pcm
        self.frames+=1
        level=pcm_rms(pcm)
        loud=level>max(MIN_SPEECH_LEVEL,self.floor*SPEECH_OVER_NOISE)
        if loud:
            # Steady noise louder than a quiet room (a café, a fan) is "loud" at first; the
            # floor creeps up until it is recognised as background. Real speech has quiet
            # gaps between words that pull it straight back down.
            self.floor*=FLOOR_RISE
        else:
            self.floor=self.floor*0.9+level*0.1
        if not self.speaking:
            self.voiced=self.voiced+1 if loud else 0
            self.speaking=self.voiced>=3
            if not self.speaking and len(self.pcm)>IN_RATE*2:
                del self.pcm[:len(self.pcm)-IN_RATE]  # keep only 0.5 s before speech starts
            # Limit actual buffered speech, rather than time spent waiting in silence.
            self.frames=len(self.pcm)//(IN_RATE*2*FRAME_MS//1000)
            return self.speaking and self.frames>=self.max_frames
        self.silence=0 if loud else self.silence+1
        # People pause between sentences, more so when talking about something hard.
        return self.silence*FRAME_MS>=END_SILENCE_MS or self.frames>=self.max_frames


def xiaozhi_router(store,config,dialogue,limited_ai,voice):
    router=APIRouter()
    devices=Devices(store,config)
    greeting_frames=[]  # the greeting never changes: synthesised once, replayed instantly afterwards

    @router.post('/xiaozhi/ota/')
    def ota(request: Request):
        """Version check the firmware runs at boot; hands a registered device its WebSocket."""
        mac=request.headers.get('device-id','')
        token=devices.token(mac)
        if not token:
            return JSONResponse({'detail':'Thiết bị chưa được đăng ký với AnMi.'},status_code=403)
        base=str(request.base_url)
        if request.headers.get('x-forwarded-proto')=='https':
            base=base.replace('http://','https://',1)  # behind a TLS tunnel such as ngrok
        base=base.replace('http://','ws://',1).replace('https://','wss://',1)
        return {'server_time':{'timestamp':int(time.time()*1000),'timezone_offset':config.device_timezone_minutes},
                'websocket':{'url':base+'xiaozhi/v1/','token':token,'version':1}}

    @router.websocket('/xiaozhi/v1/')
    async def socket(ws: WebSocket):
        device=devices.by_token(ws.headers.get('authorization','').removeprefix('Bearer ').strip())
        if not device or ws.headers.get('device-id','').lower()!=device['mac']:
            await ws.close(code=1008)
            return
        await ws.accept()
        session_id=str(uuid.uuid4())
        decoder,endpoint=Decoder(),Endpointer(config.voice_max_recording_seconds)
        state={'listening':False,'mode':'auto','task':None}
        # One connection is one conversation; a shared robot must not resume
        # another person's history just because it has the same device MAC.
        session_token=None

        def device_session(renew=False):
            nonlocal session_token
            if session_token and not renew:
                return store.session(session_token)
            session_token,session=store.create_session(DEVICE_CONSENT)
            return session
        recent=deque()
        send_lock=asyncio.Lock()

        async def send(message):
            async with send_lock:
                await ws.send_text(json.dumps({'session_id':session_id,**message},ensure_ascii=False))

        def produce(session,part):
            """Start the AnMi voice for one sentence now; Opus frames arrive on the queue as decoded."""
            queue=asyncio.Queue()
            async def run():
                try:
                    stream=OpusStream()
                    async for chunk in voice.speech_chunks(session,part):
                        for frame in stream.feed(chunk):
                            queue.put_nowait(frame)
                    for frame in stream.finish():
                        queue.put_nowait(frame)
                    queue.put_nowait(None)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    queue.put_nowait(exc)
            queue.task=asyncio.create_task(run())
            queue.part=part
            return queue

        async def play(queue,keep=None):
            buffered,done=[],False
            while not done and len(buffered)<START_BUFFER_FRAMES:
                frame=await queue.get()
                if isinstance(frame,Exception):
                    raise frame
                done=frame is None
                if not done:
                    buffered.append(frame)
            # The subtitle appears with the voice, not while it is still being synthesised.
            await send({'type':'tts','state':'sentence_start','text':queue.part})
            started,number=time.monotonic(),0
            while buffered or not done:
                if buffered:
                    frame=buffered.pop(0)
                else:
                    frame=await queue.get()
                    if isinstance(frame,Exception):
                        raise frame
                    if frame is None:
                        break
                if keep is not None:
                    keep.append(frame)
                delay=started+(number-LEAD_FRAMES)*FRAME_MS/1000-time.monotonic()
                if delay>0:
                    await asyncio.sleep(delay)
                async with send_lock:
                    await ws.send_bytes(frame)
                if number==0:
                    state['first_audio']=state.get('first_audio') or time.monotonic()
                number+=1

        async def speak(session,text,early=None):
            parts=sentences(text)
            queues=[]
            if early and parts and early.part==parts[0]:
                queues.append(early)  # started from the draft; that draft is now the checked reply
            elif early:
                early.task.cancel()
            try:
                if parts and not queues:
                    queues.append(produce(session,parts[0]))
                await send({'type':'tts','state':'start'})
                for index in range(len(parts)):
                    if index+1<len(parts):
                        queues.append(produce(session,parts[index+1]))  # next sentence while this one plays
                    await play(queues[index])
            finally:
                for queue in queues:
                    queue.task.cancel()

        async def greet():
            """Say hello as soon as the robot connects, so the person knows AnMi is ready."""
            await send({'type':'llm','emotion':'happy','text':'😊'})
            await send({'type':'tts','state':'start'})
            queue=asyncio.Queue()
            queue.part=GREETING
            if greeting_frames:
                for frame in greeting_frames:
                    queue.put_nowait(frame)
                queue.put_nowait(None)
                await play(queue)
                return
            queue=produce(device_session(),GREETING)
            kept=[]
            try:
                await play(queue,keep=kept)
                greeting_frames[:]=kept  # cache only a complete greeting
            finally:
                queue.task.cancel()

        async def run_turn(pcm):
            now=time.monotonic()
            while recent and recent[0]<=now-60:
                recent.popleft()
            if len(recent)>=TURNS_PER_MINUTE:
                await send({'type':'alert','status':'AnMi','message':'Mình cần nghỉ một chút, bạn nói lại sau ít phút nhé.','emotion':'sleepy'})
                return
            recent.append(now)
            early=spoken=None
            times={'start':now}
            state['first_audio']=None

            async def answer(session,reply,support,early):
                await send({'type':'llm','emotion':'caring' if support else 'relaxed','text':'🙂'})
                try:
                    await speak(session,reply,early=early)
                except HTTPException as exc:
                    await send({'type':'alert','status':'AnMi','message':str(exc.detail),'emotion':'sad'})

            try:
                for attempt in (0,1):
                    session=device_session(renew=attempt==1)
                    def on_draft(draft):
                        # Voice the opening of the draft while the separate output check runs. It is
                        # played only if the checked reply begins with exactly the same sentence.
                        nonlocal early
                        if early:
                            early.task.cancel()
                        parts=sentences(draft.replace(WEB_ONLY,'').strip())
                        early=produce(session,parts[0]) if parts else None
                    def on_reply(reply):
                        # The reply passed the output check: speak now rather than after the CARE
                        # appraisal for the next turn. Verified against chat()'s final reply below.
                        nonlocal spoken
                        reply=reply.replace(WEB_ONLY,'').strip()
                        spoken=(reply,asyncio.create_task(answer(session,reply,False,early)))
                    async def execute():
                        text=await voice.recognize(session,wav_bytes(pcm),'audio/wav','wav')
                        times['stt']=time.monotonic()
                        if not text:
                            return None
                        await send({'type':'stt','text':text})
                        await send({'type':'llm','emotion':'thinking','text':'🤔'})
                        dialogue.safety_event(session,'device_transcript',rule_risk(text))
                        tokens=draft_ready.set(on_draft),reply_ready.set(on_reply)
                        try:
                            return await dialogue.chat(session,ChatInput(message=text,channel='voice'))
                        finally:
                            draft_ready.reset(tokens[0])
                            reply_ready.reset(tokens[1])
                    try:
                        result=await limited_ai(session,execute())
                        break
                    except HTTPException as exc:
                        if spoken:
                            spoken[1].cancel()
                        if exc.status_code==401 and attempt==0:
                            continue  # guest session expired between turns: start a fresh one
                        await send({'type':'alert','status':'AnMi','message':str(exc.detail),'emotion':'sad'})
                        return
                times['chat']=time.monotonic()
                if result is None:
                    endpoint.reset()  # nothing intelligible: keep listening, the device is still streaming
                    state['listening']=True
                    return
                support=result['risk']['requires_support']
                # The device has no "Hỗ trợ" tab; the rest of the checked support message is spoken as is.
                reply=result['reply'].replace(WEB_ONLY,'').strip()
                if support and config.support_phone:
                    reply+=f' Bạn cũng có thể gọi {config.support_name or "đường dây hỗ trợ"} theo số {config.support_phone}.'
                store.audit(session,'device_turn')
                if spoken and spoken[0]==reply and not support:
                    await spoken[1]
                else:
                    if spoken:
                        # A newer safety signal replaced the reply that had started: stop it.
                        spoken[1].cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await spoken[1]
                    # The draft audio belongs to the stopped reply, if any; never replay it here.
                    await answer(session,reply,support,None if support or spoken else early)
            finally:
                for task in (spoken[1] if spoken else None,early.task if early else None):
                    if task:
                        task.cancel()
            if state.get('first_audio'):
                # Timings only, never content: where the wait between speaking and hearing AnMi goes.
                log.info('device turn: stt %.2fs, dialogue %.2fs, first audio %.2fs after speech ended',
                         times['stt']-times['start'],times['chat']-times['stt'],state['first_audio']-times['start'])

        async def turn(job):
            try:
                await job
            except Exception as exc:
                log.warning('device turn failed: %s', type(exc).__name__)  # type only: no conversation content
                await send({'type':'alert','status':'AnMi','message':'Kết nối giọng nói tạm thời gặp lỗi. Bạn thử lại nhé.','emotion':'sad'})
            finally:
                # Firmware returns to listening when it receives tts.stop, including
                # STT failures, empty transcripts and rate limits before TTS starts.
                # If no tts.start was sent, it may already be listening and will
                # continue audio without sending another listen.start message.
                endpoint.reset()
                state['listening']=True
                with contextlib.suppress(Exception):
                    await send({'type':'tts','state':'stop'})

        def start_turn(pcm):
            state['listening']=False
            endpoint.reset()
            task=asyncio.create_task(turn(run_turn(pcm)))
            state['task']=task

        async def stop_task():
            task=state['task']
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(BaseException):
                    await task

        try:
            hello=await asyncio.wait_for(ws.receive_text(),timeout=10)
            hello=json.loads(hello)
            if not isinstance(hello,dict) or hello.get('type')!='hello':
                await ws.close(code=1002)
                return
            params=hello.get('audio_params',{})
            if not isinstance(params,dict) or any(params.get(k,v)!=v for k,v in
                    {'format':'opus','sample_rate':IN_RATE,'channels':1,'frame_duration':FRAME_MS}.items()):
                await ws.close(code=1003)
                return
            await send({'type':'hello','transport':'websocket',
                        'audio_params':{'format':'opus','sample_rate':OUT_RATE,'channels':1,'frame_duration':FRAME_MS}})
            while True:
                message=await ws.receive()
                if message['type']=='websocket.disconnect':
                    break
                if message.get('bytes') is not None:
                    if state['listening']:
                        pcm=decoder.pcm(message['bytes'])
                        if pcm:
                            ended=endpoint.add(pcm)
                            if (ended and state['mode']!='manual') or len(endpoint.pcm)>=IN_RATE*2*config.voice_max_recording_seconds:
                                start_turn(bytes(endpoint.pcm))
                    continue
                try:
                    data=json.loads(message.get('text') or '')
                except ValueError:
                    continue
                if not isinstance(data,dict):
                    continue
                kind=data.get('type')
                if kind=='listen' and data.get('state')=='start':
                    await stop_task()
                    state['mode']=data.get('mode') or 'auto'
                    endpoint.reset()
                    if not state.get('greeted'):
                        # First listen of the conversation: greet, then listen after tts.stop.
                        state['greeted'],state['listening']=True,False
                        state['task']=asyncio.create_task(turn(greet()))
                    else:
                        state['listening']=True
                elif kind=='listen' and data.get('state')=='stop':
                    if state['listening'] and endpoint.speaking:
                        start_turn(bytes(endpoint.pcm))
                    state['listening']=False
                elif kind=='abort':
                    await stop_task()
                    state['listening']=False
                    endpoint.reset()
        except (ValueError,asyncio.TimeoutError):
            with contextlib.suppress(RuntimeError):
                await ws.close(code=1002)
        except (WebSocketDisconnect,RuntimeError):
            pass
        finally:
            await stop_task()
            if session_token:
                with contextlib.suppress(HTTPException):
                    store.delete(store.session(session_token))

    return router
