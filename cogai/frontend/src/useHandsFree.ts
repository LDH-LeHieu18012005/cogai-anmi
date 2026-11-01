import { useCallback, useEffect, useRef, useState } from 'react';
import { errorText, type Config, type Risk } from './api';
import { VoiceActivity } from './voiceActivity';

export type HandsFreePhase='off'|'listening'|'thinking'|'speaking'|'paused';
export type SpokenTurn={heard:boolean;transcript:string;reply:string;risk:Risk;audio_base64?:string;audio_type?:string;speech_stream?:boolean;pause_for_support?:boolean;audio_error?:string};

/** Progressive turn: the transcript line arrives first (shown at once), then the checked reply. */
async function readTurn(response:Response,heard:(transcript:string)=>void):Promise<SpokenTurn>{
  if(!response.headers.get('content-type')?.includes('ndjson')||!response.body)return await response.json() as SpokenTurn;
  const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';
  for(;;){
    const {value,done}=await reader.read();buffer+=decoder.decode(value??new Uint8Array(),{stream:!done});
    let newline;
    while((newline=buffer.indexOf('\n'))>=0){
      const line=buffer.slice(0,newline).trim();buffer=buffer.slice(newline+1);if(!line)continue;
      const event=JSON.parse(line) as {transcript?:string;result?:SpokenTurn;error?:{detail?:unknown}};
      if(event.transcript)heard(event.transcript);
      if(event.error)throw new Error(typeof event.error.detail==='string'?event.error.detail:'Chưa thể hoàn tất lượt nói. Hãy thử lại.');
      if(event.result)return event.result;
    }
    if(done)throw new Error('Chưa thể hoàn tất lượt nói. Hãy thử lại.');
  }
}

/** Holds one mic stream; segments locally, sends only speech and re-arms itself. */
export function useHandsFree(config:Config,enabled:boolean,onTurn:(turn:SpokenTurn)=>void,onHeard?:(transcript:string)=>void){
  const [phase,setPhase]=useState<HandsFreePhase>('off'),[error,setError]=useState(''),[level,setLevel]=useState(0),[following,setFollowing]=useState(false);
  const [bufferFull,setBufferFull]=useState(false);
  const supportPlayback=useRef(false);
  const callback=useRef(onTurn);callback.current=onTurn;
  const heardCallback=useRef(onHeard);heardCallback.current=onHeard;
  const active=useRef(false),generation=useRef(0),phaseRef=useRef<HandsFreePhase>('off');
  const stream=useRef<MediaStream|null>(null),context=useRef<AudioContext|null>(null),analyser=useRef<AnalyserNode|null>(null);
  const recorder=useRef<MediaRecorder|null>(null),chunks=useRef<Blob[]>([]),bytes=useRef(0),started=useRef(0),heard=useRef(false),mime=useRef('');
  const interval=useRef<ReturnType<typeof setInterval>|null>(null),request=useRef<AbortController|null>(null);
  const turnId=useRef('');
  const processing=useRef(false),pending=useRef<Blob|null>(null),speechEnded=useRef(false);
  const audio=useRef<HTMLAudioElement|null>(null),url=useRef(''),lastActivity=useRef(0);
  const gate=useRef(new VoiceActivity()),interruptGate=useRef(new VoiceActivity(.04,280,1100));
  const armRef=useRef<()=>void>(()=>{}),finishRef=useRef<()=>void>(()=>{});
  function change(next:HandsFreePhase){phaseRef.current=next;setPhase(next);}
  const stopPlayback=useCallback(()=>{if(audio.current){audio.current.onended=null;audio.current.onerror=null;audio.current.pause();audio.current.removeAttribute('src');audio.current.load();audio.current=null;}if(url.current)URL.revokeObjectURL(url.current);url.current='';},[]);
  const stop=useCallback(()=>{
    if(turnId.current){void fetch('/api/voice/cancel',{method:'POST',credentials:'same-origin',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({turn_id:turnId.current})}).catch(()=>{});turnId.current='';}
    active.current=false;generation.current++;request.current?.abort();request.current=null;
    if(interval.current)clearInterval(interval.current);interval.current=null;
    const capture=recorder.current;recorder.current=null;
    if(capture){capture.onstop=null;capture.ondataavailable=null;if(capture.state==='recording')capture.stop();}
    chunks.current=[];bytes.current=0;heard.current=false;
    processing.current=false;pending.current=null;speechEnded.current=false;setFollowing(false);setBufferFull(false);supportPlayback.current=false;
    stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;analyser.current=null;
    if(context.current){void context.current.close().catch(()=>{});context.current=null;}
    stopPlayback();phaseRef.current='off';setPhase('off');setLevel(0);
  },[stopPlayback]);
  useEffect(()=>{if(!enabled)stop();},[enabled,stop]);
  useEffect(()=>{
    const hide=()=>{if(document.hidden)stop();};const revoke=()=>stop();
    document.addEventListener('visibilitychange',hide);window.addEventListener('cogai-session-changed',revoke);
    return()=>{document.removeEventListener('visibilitychange',hide);window.removeEventListener('cogai-session-changed',revoke);stop();};
  },[stop]);

  function discardRecording(){
    const capture=recorder.current;recorder.current=null;
    if(capture){capture.onstop=null;capture.ondataavailable=null;if(capture.state==='recording')capture.stop();}
    chunks.current=[];bytes.current=0;heard.current=false;speechEnded.current=false;gate.current.reset();interruptGate.current.reset();
  }
  function fail(message:string){stop();setError(message);}
  function arm(){
    if(!active.current||!stream.current)return;
    discardRecording();
    const current=generation.current;
    const capture=new MediaRecorder(stream.current,{mimeType:mime.current,audioBitsPerSecond:64000});
    recorder.current=capture;started.current=performance.now();const parts:Blob[]=[];
    capture.ondataavailable=e=>{
      if(!active.current||current!==generation.current||recorder.current!==capture)return;
      if(e.data.size){parts.push(e.data);bytes.current+=e.data.size;if(bytes.current>(config.voice?.max_audio_bytes??2_000_000))fail('Âm thanh quá dài. Hãy bắt đầu lại cuộc trò chuyện.');}
    };
    capture.onerror=()=>{if(current===generation.current)fail('Micro bị gián đoạn. Hãy kiểm tra thiết bị rồi bắt đầu lại.');};
    capture.onstop=()=>{
      if(!active.current||current!==generation.current||recorder.current!==capture)return;
      recorder.current=null;
      if(!heard.current){armRef.current();return;}
      const blob=new Blob(parts,{type:mime.current});
      if(processing.current){pending.current=blob;setFollowing(true);setBufferFull(true);}
      else void processTurn(blob,current);
    };
    capture.start(250);
  }
  armRef.current=arm;
  function listen(){
    if(!active.current)return;
    lastActivity.current=performance.now();change('listening');armRef.current();
  }
  function finish(){
    if(!active.current||phaseRef.current!=='listening'||!heard.current)return;
    change('thinking');
    if(recorder.current?.state==='recording')recorder.current.stop();
  }
  finishRef.current=finish;
  async function processTurn(blob:Blob,current:number){
    processing.current=true;pending.current=null;setFollowing(false);setBufferFull(false);change('thinking');armRef.current();
    const controller=new AbortController();request.current=controller;
    // Text and voice arrive together: the reply is shown when its sound starts (or at once if there is none).
    let reply:SpokenTurn|null=null,shown=false;const show=()=>{if(reply&&!shown){shown=true;callback.current(reply);}};
    const id=crypto.randomUUID();turnId.current=id;
    const timeout=setTimeout(()=>controller.abort(),115_000);
    setError('');
    try{
      const response=await fetch('/api/voice/turn',{method:'POST',credentials:'same-origin',body:blob,
        headers:{'Content-Type':mime.current,'X-CogAI-Voice-Turn':id,'X-CogAI-Speech':'stream','X-CogAI-Progress':'ndjson'},signal:controller.signal});
      if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:'Chưa thể hoàn tất lượt nói. Hãy thử lại.');}
      const result=await readTurn(response,transcript=>{if(active.current&&current===generation.current)heardCallback.current?.(transcript);});
      if(!active.current||current!==generation.current)return;
      processing.current=false;
      if(result.heard)reply=result;
      if(!active.current||current!==generation.current)return;
      const needsSupport=result.heard&&(result.pause_for_support||result.risk.requires_support);
      // Never throw away an utterance captured while waiting. Keep chronological
      // server history, skip the now-outdated audio, then submit the added speech.
      if(!needsSupport&&(pending.current||heard.current)){
        const queued=pending.current;pending.current=null;setFollowing(false);
        if(queued){void processTurn(queued,current);return;}
        change('listening');
        if(speechEnded.current)finishRef.current();
        return;
      }
      if(!result.heard){listen();return;}
      if(!result.audio_base64&&!result.speech_stream){fail(result.audio_error??'Chưa có giọng đọc hợp lệ. Nội dung chữ đã được giữ trong hội thoại.');return;}
      let source='/api/voice/stream?turn='+id; // Streams the server-checked reply; playback starts on the first chunk.
      if(result.audio_base64){
        const raw=atob(result.audio_base64),buffer=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)buffer[i]=raw.charCodeAt(i);
        source=url.current=URL.createObjectURL(new Blob([buffer],{type:result.audio_type??'audio/mpeg'}));
      }
      const player=new Audio(source);audio.current=player;
      // A voice hiccup keeps the call going: the checked text reply is already on screen.
      const skipVoice=()=>{stopPlayback();setError('Không phát được giọng đọc lượt này; phản hồi chữ vẫn ở trên.');if(needsSupport){stop();change('paused');}else listen();};
      supportPlayback.current=Boolean(needsSupport);
      player.onended=()=>{
        if(!active.current||current!==generation.current)return;
        stopPlayback();
        if(needsSupport){stop();change('paused');}else listen();
      };
      player.onerror=()=>{if(active.current&&current===generation.current)skipVoice();};
      try{await player.play();}catch(e){if(active.current&&current===generation.current&&audio.current===player)skipVoice();return;}
      show();
      if(!active.current||current!==generation.current){player.pause();return;}
      change('speaking');
      if(needsSupport){discardRecording();stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;}
      else armRef.current(); // Keep an echo-cancelled local recording for interrupting.
    }catch(e){if(active.current&&current===generation.current)fail(errorText(e));}
    finally{show();clearTimeout(timeout);if(request.current===controller)request.current=null;if(turnId.current===id)turnId.current='';}
  }

  async function start(){
    stop();setError('');
    if(!enabled||!config.voice?.transcription||!config.voice?.speech){setError('Cần bật quyền và cấu hình đủ nhận giọng nói, giọng đọc.');return;}
    if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==='undefined'||typeof AudioContext==='undefined'){setError('Trình duyệt chưa hỗ trợ cuộc trò chuyện này. Hãy dùng Chrome/Edge qua HTTPS hoặc localhost.');return;}
    const current=generation.current;active.current=true;change('listening');
    try{
      const media=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
      if(!active.current||current!==generation.current){media.getTracks().forEach(t=>t.stop());return;}
      stream.current=media;
      mime.current=['audio/webm;codecs=opus','audio/webm','audio/mp4','audio/ogg;codecs=opus'].find(t=>MediaRecorder.isTypeSupported(t))??'';
      if(!mime.current)throw new Error('Không có định dạng ghi âm phù hợp.');
      const engine=new AudioContext();context.current=engine;await engine.resume();
      if(!active.current||current!==generation.current){void engine.close().catch(()=>{});return;}
      const meter=engine.createAnalyser();meter.fftSize=1024;analyser.current=meter;
      engine.createMediaStreamSource(media).connect(meter);
      const samples=new Float32Array(meter.fftSize);
      lastActivity.current=performance.now();armRef.current();
      interval.current=setInterval(()=>{
        if(!active.current||!analyser.current)return;
        meter.getFloatTimeDomainData(samples);let sum=0;for(const sample of samples)sum+=sample*sample;
        const rms=Math.sqrt(sum/samples.length),now=performance.now();setLevel(Math.min(1,rms*10));
        if(phaseRef.current==='thinking'){
          if(!recorder.current)return;
          const event=gate.current.feed(rms,now);
          if(event==='start'){heard.current=true;speechEnded.current=false;setFollowing(true);}
          if(event==='end')speechEnded.current=true;
          if(!heard.current&&!gate.current.detecting&&now-started.current>=2000){armRef.current();return;}
          if(now-started.current>=Math.min(config.voice?.max_recording_seconds??45,45)*1000){
            if(heard.current){if(recorder.current.state==='recording')recorder.current.stop();}
            else armRef.current();
          }
        }else if(phaseRef.current==='speaking'){
          if(interruptGate.current.feed(rms,now)==='start'){
            stopPlayback();heard.current=true;gate.current.reset();gate.current.feed(rms,now-250);gate.current.feed(rms,now);
            lastActivity.current=now;change('listening');
          }
          else if(!interruptGate.current.detecting&&now-started.current>=2000&&recorder.current)armRef.current();
        }else if(phaseRef.current==='listening'){
          const event=gate.current.feed(rms,now);
          if(event==='start'){heard.current=true;lastActivity.current=now;}
          if(rms>.012&&heard.current)lastActivity.current=now;
          if(event==='end'){finishRef.current();return;}
          if(!heard.current&&!gate.current.detecting&&now-started.current>=2000){armRef.current();return;}
          const maxMs=Math.min(config.voice?.max_recording_seconds??45,45)*1000;
          if(now-started.current>=maxMs){if(heard.current)finishRef.current();else armRef.current();}
          if(now-lastActivity.current>90_000)fail('Đã tạm dừng micro sau một lúc không có tiếng nói. Bạn có thể bắt đầu lại.');
        }
      },40);
    }catch(e){if(active.current&&current===generation.current)fail(e instanceof DOMException&&e.name==='NotAllowedError'?'Bạn chưa cấp quyền micro. Hãy kiểm tra quyền trong trình duyệt.':errorText(e));}
  }
  function interrupt(){if(phaseRef.current==='speaking'&&active.current){if(supportPlayback.current){stop();change('paused');}else{stopPlayback();listen();}}}
  return {phase,error,level,following,bufferFull,start,stop,interrupt,active:phase!=='off'&&phase!=='paused'};
}
