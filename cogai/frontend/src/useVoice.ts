import { useCallback, useEffect, useRef, useState } from 'react';
import { api, errorText, type Config, type Risk, type Session } from './api';

export type VoicePhase='idle'|'recording'|'transcribing'|'loadingSpeech'|'speaking';

export function useVoice(config:Config,onTranscript:(text:string,risk:Risk)=>void){
  const [phase,setPhase]=useState<VoicePhase>('idle'),[enabled,setEnabled]=useState(false),[error,setError]=useState('');
  const recorder=useRef<MediaRecorder|null>(null),stream=useRef<MediaStream|null>(null),timer=useRef<ReturnType<typeof setTimeout>|null>(null);
  const request=useRef<AbortController|null>(null),player=useRef<HTMLAudioElement|null>(null),objectUrl=useRef(''),epoch=useRef(0);
  const callback=useRef(onTranscript);callback.current=onTranscript;
  const stop=useCallback(()=>{
    epoch.current++;request.current?.abort();request.current=null;
    if(timer.current)clearTimeout(timer.current);timer.current=null;
    if(recorder.current?.state==='recording')recorder.current.stop();recorder.current=null;
    stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;
    if(player.current){player.current.pause();player.current.removeAttribute('src');player.current.load();player.current=null;}
    if(objectUrl.current)URL.revokeObjectURL(objectUrl.current);objectUrl.current='';
    setPhase('idle');
  },[]);
  useEffect(()=>{
    let active=true;
    const refresh=()=>{stop();void api<Session>('/session').then(s=>{if(active)setEnabled(Boolean(s.consent.voice_processing&&s.consent.external_ai));}).catch(()=>{if(active)setEnabled(false);});};
    refresh();window.addEventListener('cogai-session-changed',refresh);
    const hide=()=>{if(document.hidden)stop();};document.addEventListener('visibilitychange',hide);
    return()=>{active=false;window.removeEventListener('cogai-session-changed',refresh);document.removeEventListener('visibilitychange',hide);stop();};
  },[stop]);
  async function enable(){setError('');try{await api('/consent',{voice_processing:true,external_ai:true},'PATCH');setEnabled(true);window.dispatchEvent(new Event('cogai-session-changed'));}catch(e){setError(errorText(e));}}
  async function disable(){stop();setEnabled(false);try{await api('/consent',{voice_processing:false},'PATCH');window.dispatchEvent(new Event('cogai-session-changed'));}catch(e){setError(errorText(e));}}
  async function fetchVoice(path:string,options:RequestInit,generation:number){
    const controller=new AbortController();request.current=controller;
    const timeout=setTimeout(()=>controller.abort(),50_000);
    try{
      const response=await fetch('/api/voice/'+path,{...options,credentials:'same-origin',signal:controller.signal});
      if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(typeof data.detail==='string'?data.detail:'Dịch vụ giọng nói chưa sẵn sàng.');}
      if(generation!==epoch.current)throw new DOMException('Cancelled','AbortError');
      return response;
    }finally{clearTimeout(timeout);if(request.current===controller)request.current=null;}
  }
  async function record(){
    stop();setError('');const generation=epoch.current;
    if(!enabled||!config.voice?.transcription){setError('Cần bật quyền và cấu hình dịch vụ nhận giọng nói trước.');return;}
    if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==='undefined'){setError('Trình duyệt chưa hỗ trợ ghi âm. Hãy dùng HTTPS hoặc localhost và thử Chrome/Edge.');return;}
    try{
      const media=await navigator.mediaDevices.getUserMedia({audio:true});
      if(generation!==epoch.current){media.getTracks().forEach(t=>t.stop());return;}
      stream.current=media;
      const mime=['audio/webm;codecs=opus','audio/webm','audio/mp4','audio/ogg;codecs=opus'].find(t=>MediaRecorder.isTypeSupported(t));
      if(!mime)throw new Error('Trình duyệt không có định dạng ghi âm phù hợp.');
      const capture=new MediaRecorder(media,{mimeType:mime,audioBitsPerSecond:64000});recorder.current=capture;
      const chunks:Blob[]=[];let size=0;
      capture.ondataavailable=e=>{if(e.data.size){size+=e.data.size;if(size>(config.voice?.max_audio_bytes??2_000_000)){stop();setError('Bản ghi quá dài. Hãy ghi lại ngắn hơn.');return;}chunks.push(e.data);}};
      capture.onerror=()=>{stop();setError('Ghi âm bị gián đoạn. Bạn có thể thử lại hoặc nhập chữ.');};
      capture.onstop=()=>{
        media.getTracks().forEach(t=>t.stop());stream.current=null;if(timer.current)clearTimeout(timer.current);timer.current=null;
        if(generation!==epoch.current)return;
        setPhase('transcribing');
        void (async()=>{try{
          const blob=new Blob(chunks,{type:mime});
          const response=await fetchVoice('transcribe',{method:'POST',body:blob,headers:{'Content-Type':mime}},generation);
          const data=await response.json() as {transcript:string;risk:Risk};
          if(generation===epoch.current)callback.current(data.transcript,data.risk);
        }catch(e){if(generation===epoch.current)setError(errorText(e));}finally{if(generation===epoch.current)setPhase('idle');}})();
      };
      capture.start(250);setPhase('recording');timer.current=setTimeout(()=>{if(capture.state==='recording')capture.stop();},(config.voice.max_recording_seconds??45)*1000);
    }catch(e){if(generation===epoch.current){stop();setError(e instanceof DOMException&&e.name==='NotAllowedError'?'Bạn chưa cho phép micro. Hãy cấp quyền trong trình duyệt hoặc nhập chữ.':errorText(e));}}
  }
  function finishRecording(){if(recorder.current?.state==='recording')recorder.current.stop();}
  /** Streams the latest checked reply; resolves true once sound is actually playing. */
  async function speak():Promise<boolean>{
    stop();setError('');const generation=epoch.current;
    if(!enabled||!config.voice?.speech){setError('Cần bật quyền và cấu hình giọng đọc trước.');return false;}
    setPhase('loadingSpeech');
    const failed=()=>{if(generation===epoch.current){stop();setError('Chưa phát được giọng đọc lúc này. Phản hồi chữ vẫn ở trên.');}};
    // Streaming source: playback starts with the first chunk, often already prepared by the server.
    const audio=new Audio('/api/voice/stream?t='+Date.now());player.current=audio;
    audio.onended=()=>{if(generation===epoch.current)stop();};audio.onerror=failed;
    try{await audio.play();}catch{failed();return false;}
    if(generation!==epoch.current)return false;
    setPhase('speaking');return true;
  }
  return {phase,enabled,error,enable,disable,record,finishRecording,speak,stop};
}
