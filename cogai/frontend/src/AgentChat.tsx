import { useCallback, useEffect, useLayoutEffect, useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from 'react';
import { ArrowDown, ArrowUp, ChevronDown, Bot, Mic, Plus, RotateCcw, Square, Volume2, X } from 'lucide-react';
import { api, errorText, type Config, type Risk, type Turn } from './api';
import { Companion, type CompanionState } from './Companion';
import { SafetyCheckIn } from './SafetyCheckIn';
import { useVoice } from './useVoice';
import { useHandsFree } from './useHandsFree';
import './agent-chat.css';
import './handsfree.css';

type ChatTurn = Turn & { id: string; fresh?: boolean; failed?: boolean };
const starters = ['Hôm nay mình có nhiều điều muốn kể.', 'Mình muốn chậm lại một chút.', 'Mình đang lo về công việc.'];
const states: Record<CompanionState, { label: string; description: string }> = {
  idle: { label: 'Sẵn sàng trò chuyện', description: 'Bạn có thể bắt đầu từ bất cứ điều gì.' },
  listening: { label: 'Đang ghi âm', description: 'Micro chỉ bật trong lần ghi này. Tối đa 45 giây.' },
  thinking: { label: 'Đang suy nghĩ', description: 'AnMi sẽ trả lời sau khi nội dung được kiểm tra.' },
  speaking: { label: 'Đang nói', description: 'Bạn có thể dừng giọng đọc bất cứ lúc nào.' },
  support: { label: 'Ưu tiên hỗ trợ', description: 'Mình tạm dừng bài tập để tập trung vào sự an toàn của bạn.' },
  unavailable: { label: 'Tạm dừng một chút', description: 'Chưa thể hoàn tất xử lý. Bạn có thể thử lại sau.' },
};
// Reassure during the 3–8 s a checked reply takes; each phase is true of the pipeline at that point.
const waitPhases: [number, string][] = [[0, 'AnMi đang đọc điều bạn chia sẻ'], [2500, 'AnMi đang suy nghĩ cách trả lời'], [6000, 'Đang kiểm tra để phản hồi an toàn'], [12000, 'Sắp xong rồi, cảm ơn bạn đã chờ']];
const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
let counter = 0;
const nextId = () => `t${Date.now().toString(36)}${(counter++).toString(36)}`;
const withIds = (turns: Turn[]): ChatTurn[] => turns.map(t => ({ ...t, id: nextId() }));
const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

function Thinking({ label }: { label?: string }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => { const start = Date.now(); const timer = setInterval(() => setElapsed(Date.now() - start), 500); return () => clearInterval(timer); }, []);
  const phase = label ?? [...waitPhases].reverse().find(([at]) => elapsed >= at)![1];
  return <div className="agent-message assistant agent-thinking" role="status" aria-live="polite">
    <span className="agent-avatar" aria-hidden="true"><span className="agent-spinner" /><Bot size={14} /></span>
    <div className="agent-bubble"><span className="agent-dots" aria-hidden="true"><i /><i /><i /></span><span className="agent-thinking-text">{phase}…</span></div>
  </div>;
}

export function AgentChat({ config, refresh, support }: { config: Config; refresh: () => Promise<void>; support: ReactNode }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]), [input, setInput] = useState(''), [risk, setRisk] = useState<Risk | null>(null);
  const [busy, setBusy] = useState(false), [restoring, setRestoring] = useState(true), [error, setError] = useState('');
  const [action, setAction] = useState('');
  const motion = !reducedMotion();
  const [voiceDialog, setVoiceDialog] = useState(false), [voiceConsent, setVoiceConsent] = useState(false), [autoRead, setAutoRead] = useState(false), [transcribed, setTranscribed] = useState(false);
  const [unseen, setUnseen] = useState(false);
  const list = useRef<HTMLDivElement>(null), field = useRef<HTMLTextAreaElement>(null), mounted = useRef(true), pinned = useRef(true);
  const voice = useVoice(config, (text, newRisk) => { setInput(previous => previous ? previous + '\n' + text : text); setTranscribed(true); setRisk(newRisk); });
  // Hands-free: the user's words appear as soon as they are recognised; the reply follows with its voice.
  const heardId = useRef<string | null>(null);
  const handsfree = useHandsFree(config, voice.enabled, result => {
    pinned.current = true;
    const shownId = heardId.current; heardId.current = null;
    setTurns(previous => [...(shownId && previous.some(t => t.id === shownId && t.content === result.transcript) ? previous : [...previous, { role: 'user' as const, content: result.transcript, id: nextId() }]),
      { role: 'assistant', content: result.reply, id: nextId(), fresh: motion }]);
    setRisk(result.risk); setInput(''); setTranscribed(false); void refresh();
  }, transcript => {
    pinned.current = true; const id = nextId(); heardId.current = id;
    setTurns(previous => [...previous, { role: 'user', content: transcript, id }]);
  });
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    let active = true;
    void api<{ turns: Turn[]; risk: Risk | null }>('/chat').then(r => { if (active) { setTurns(withIds(r.turns)); setRisk(r.risk); } })
      .catch(e => { if (active) setError(errorText(e)); }).finally(() => { if (active) setRestoring(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => { if (risk?.requires_support) voice.stop(); }, [risk?.level, risk?.requires_support, voice.stop]);

  // Scroll only the message list (never the page), and only while the reader is at the bottom.
  const follow = useCallback((smooth = false) => {
    const el = list.current; if (!el) return;
    if (pinned.current) { el.scrollTo({ top: el.scrollHeight, behavior: smooth && motion ? 'smooth' : 'auto' }); setUnseen(false); }
    else setUnseen(true);
  }, [motion]);
  useLayoutEffect(() => { follow(true); }, [turns.length, busy, restoring, follow]);
  function onScroll() { const el = list.current; if (!el) return; pinned.current = el.scrollHeight - el.scrollTop - el.clientHeight < 72; if (pinned.current) setUnseen(false); }
  function toLatest() { pinned.current = true; follow(true); }

  // The composer grows with the text, up to a comfortable limit.
  useLayoutEffect(() => { const el = field.current; if (!el) return; el.style.height = 'auto'; el.style.height = `${Math.min(el.scrollHeight, 176)}px`; }, [input]);

  const audioBusy = voice.phase === 'recording' || voice.phase === 'transcribing' || handsfree.active;
  const waiting = busy || voice.phase === 'transcribing' || handsfree.phase === 'thinking';
  const state: CompanionState = risk?.level === 'high' || risk?.level === 'check_in' ? 'support' : risk?.level === 'unavailable' ? 'unavailable' : voice.phase === 'recording' || handsfree.phase === 'listening' ? 'listening' : voice.phase === 'speaking' || handsfree.phase === 'speaking' ? 'speaking' : waiting || restoring || voice.phase === 'loadingSpeech' ? 'thinking' : error || handsfree.error ? 'unavailable' : 'idle';
  const info = states[state];

  async function deliver(message: string, retryOf?: string) {
    voice.stop(); setBusy(true); setError(''); pinned.current = true;
    const id = retryOf ?? nextId();
    setTurns(previous => retryOf ? previous.map(t => t.id === id ? { ...t, failed: false } : t) : [...previous, { role: 'user', content: message, id }]);
    try {
      const speakAlong = Boolean(autoRead && voice.enabled && config.voice?.speech);
      // No action = AnMi paces the CBT steps itself; speak = the server starts the voice right away.
      const result = await api<{ reply: string; risk: Risk }>('/chat', { message, ...(action ? { action } : {}), ...(speakAlong ? { speak: true } : {}) });
      if (!mounted.current) return;
      // Reading aloud: keep the waiting indicator until the sound starts, then show the text with it.
      if (speakAlong && !result.risk.requires_support) await Promise.race([voice.speak(), wait(6000)]);
      if (!mounted.current) return;
      setTurns(previous => [...previous, { role: 'assistant', content: result.reply, id: nextId(), fresh: true }]);
      setRisk(result.risk); setTranscribed(false);
      void refresh();
    } catch (e) {
      if (!mounted.current) return;
      setTurns(previous => previous.map(t => t.id === id ? { ...t, failed: true } : t)); setError(errorText(e));
    } finally { if (mounted.current) setBusy(false); }
  }
  function send(e?: FormEvent) {
    e?.preventDefault(); const message = input.trim();
    if (!message || busy || restoring || audioBusy) return;
    setInput(''); void deliver(message);
  }
  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Never send mid-composition: Vietnamese Telex/VNI input methods compose with Enter.
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) { e.preventDefault(); send(); }
  }
  async function reset() {
    handsfree.stop(); voice.stop(); setBusy(true); setError('');
    try { await api('/chat/reset', {}); const r = await api<{ turns: Turn[]; risk: Risk | null }>('/chat'); if (mounted.current) { setTurns(withIds(r.turns)); setRisk(r.risk); setInput(''); setTranscribed(false); } }
    catch (e) { if (mounted.current) setError(errorText(e)); } finally { if (mounted.current) setBusy(false); }
  }
  const anyVoice = Boolean(config.voice?.transcription || config.voice?.speech);
  const status = waiting ? 'Đang trả lời…' : restoring ? 'Đang mở lại…' : 'Trợ lý AI của CogAI';

  return <div className={`agent-experience ${motion ? '' : 'reduce-motion'}`}>
    <div className="agent-layout">
      <aside className={`agent-stage theme-sage ${state === 'support' ? 'agent-stage-support' : ''}`} aria-label="Không gian tác nhân CogAI">
        <div className="agent-scenery"><div className="agent-sun" /><div className="agent-hill hill-back" /><div className="agent-hill hill-front" /></div>
        <Companion state={state} theme="sage" motion={motion} />
        <div className={`agent-presence state-${state}`} role="status"><span className="agent-presence-dot" />{handsfree.phase === 'listening' ? 'Đang nghe bạn nói' : info.label}</div>
        <div className="agent-intro"><h2>{state === 'support' ? 'Mình ưu tiên hỗ trợ bạn lúc này.' : 'Chào bạn, mình là AnMi.'}</h2><p>{state === 'support' ? info.description : 'Một lời sẻ chia, một khoảng bình an. Cứ nói theo nhịp của bạn.'}</p></div>
        <section className={`handsfree-panel ${handsfree.active ? 'is-active' : ''}`} aria-label="Trò chuyện giọng nói liên tục">
          <div className="handsfree-description"><span className="handsfree-symbol"><Mic size={19} /></span><div><strong>Nói chuyện cùng AnMi</strong><p>{handsfree.phase === 'listening' ? 'Micro đang bật. Bạn cứ nói; ngừng khoảng một giây để AnMi trả lời.' : handsfree.phase === 'thinking' ? 'AnMi đang nghe lại và chuẩn bị phản hồi…' : handsfree.phase === 'speaking' ? 'AnMi đang nói. Bạn có thể nói chen vào để ngắt lời.' : handsfree.phase === 'paused' ? 'Đã tạm dừng cuộc gọi để ưu tiên hỗ trợ.' : 'Bật một lần, nói chuyện liên tục.'}</p></div></div>
          {handsfree.active ? <div className="handsfree-controls"><div className="handsfree-meter" aria-label="Mức âm thanh micro">{[.25, .55, .9, .65, .4].map((n, i) => <i key={i} style={{ transform: `scaleY(${.2 + handsfree.level * n * 1.6})` }} />)}</div>{handsfree.phase === 'speaking' && <button className="button secondary" onClick={handsfree.interrupt}>Ngắt lời AnMi</button>}<button className="button danger" onClick={handsfree.stop}><Square size={15} />Kết thúc cuộc gọi</button></div>
            : <button className="button primary" disabled={busy || restoring || voice.phase !== 'idle' || Boolean(risk?.requires_support) || (voice.enabled && (!config.voice?.transcription || !config.voice?.speech))} onClick={() => { voice.stop(); if (!voice.enabled) setVoiceDialog(true); else void handsfree.start(); }}><Mic size={16} />Bắt đầu nói chuyện</button>}
          {handsfree.error && <p role="alert" className="error-note">{handsfree.error}</p>}
          {handsfree.following && <p className="handsfree-privacy" role="status">{handsfree.bufferFull ? 'Bộ đệm lời nói đã đầy; micro tạm ngừng ghi. Hãy chờ AnMi xử lý phần đã giữ rồi nói tiếp.' : 'Đã giữ phần bạn nói thêm; AnMi sẽ nghe tiếp trước khi trả lời.'}</p>}
        </section>
      </aside>
      <section className="agent-conversation" aria-label="Trò chuyện với AnMi">
        <header className="agent-chat-header">
          <div><span className={`agent-mini-avatar ${waiting ? 'is-busy' : ''}`}><Bot size={19} /></span><div><strong>AnMi</strong><span className="agent-status"><i className={waiting ? 'busy' : ''} />{status}</span></div></div>
          <button className="agent-new-chat" aria-label="Cuộc trò chuyện mới" title="Cuộc trò chuyện mới" onClick={() => void reset()} disabled={busy || restoring || audioBusy}><Plus size={15} /><span>Cuộc trò chuyện mới</span></button>
        </header>
        <div className="agent-messages" ref={list} onScroll={onScroll} role="log" aria-label="Nội dung trò chuyện" aria-live="polite" aria-busy={waiting || restoring}>
          {restoring && <div className="agent-skeleton" aria-label="Đang mở lại cuộc trò chuyện…"><i /><i className="user" /><i /></div>}
          {!restoring && turns.length === 0 && <div className="agent-welcome"><span className="agent-welcome-icon"><Bot size={28} /></span><p>Hôm nay, điều gì đang ở trong tâm trí bạn?</p><span>Một câu ngắn thôi cũng được.</span>
            <div className="agent-starters">{starters.map(text => <button key={text} disabled={busy || audioBusy} onClick={() => { setInput(text); setTranscribed(false); field.current?.focus(); }}>{text}</button>)}</div></div>}
          {turns.map((turn, index) => {
            const grouped = index > 0 && turns[index - 1].role === turn.role;
            return <div className={`agent-message ${turn.role} ${turn.fresh || (turn.role === 'user' && index === turns.length - 1) ? 'enter' : ''} ${grouped ? 'grouped' : ''}`} key={turn.id}>
              {turn.role === 'assistant' && <span className="agent-avatar" aria-hidden="true"><Bot size={14} /></span>}
              <div className="agent-bubble">{turn.content}</div>
              {turn.failed && <button className="agent-retry" onClick={() => void deliver(turn.content, turn.id)} disabled={busy}><RotateCcw size={13} />Chưa gửi được · Gửi lại</button>}
            </div>;
          })}
          {waiting && <Thinking label={voice.phase === 'transcribing' ? 'Đang chuyển bản ghi thành chữ' : handsfree.phase === 'thinking' ? 'AnMi đang nghe lại và chuẩn bị phản hồi' : undefined} />}
        </div>
        {unseen && <button className="agent-jump" onClick={toLatest}><ArrowDown size={14} />Tin nhắn mới</button>}
        <div className="agent-composer-area">
          <div className="agent-composer-meta">
            <details className="agent-dialogue-options"><summary><ChevronDown size={14} />Cách hỗ trợ</summary><label className="sr-only" htmlFor="agent-action">Cách trò chuyện</label><select id="agent-action" value={action} onChange={e => setAction(e.target.value)} disabled={busy || audioBusy}><option value="">Để AnMi tự điều chỉnh nhịp (khuyến nghị)</option><option value="listen">Chỉ lắng nghe</option><option value="clarify">Làm rõ tình huống</option><option value="identify">Nhận diện suy nghĩ</option><option value="evidence">Xem xét bằng chứng</option><option value="perspective">Thử góc nhìn khi sẵn sàng</option><option value="action">Chọn hành động nhỏ</option></select></details>
          </div>
          {(error || voice.error) && <p role="alert" className="error-note">{error || voice.error}</p>}
          {transcribed && <p className="agent-transcript-note">Đã chuyển thành chữ. Bạn có thể sửa nội dung trước khi gửi.</p>}
          <form className="agent-composer" onSubmit={send}>
            <label className="sr-only" htmlFor="chat-message">Tin nhắn của bạn</label>
            <textarea id="chat-message" ref={field} rows={1} maxLength={4000} value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKeyDown} placeholder="Viết điều bạn muốn chia sẻ…" disabled={audioBusy} />
            <div className="agent-composer-actions">
              <span className="agent-input-hint">{voice.phase === 'recording' ? 'Micro đang bật' : input.length > 3500 ? `${input.length}/4000` : ''}</span>
              <button type="button" className={`agent-mic ${voice.phase === 'recording' ? 'recording' : ''}`} aria-label={voice.phase === 'recording' ? 'Dừng ghi âm' : 'Ghi âm tin nhắn'} disabled={busy || restoring || handsfree.active || voice.phase === 'transcribing' || (voice.enabled && !config.voice?.transcription)} onClick={() => { if (voice.phase === 'recording') voice.finishRecording(); else if (!voice.enabled) setVoiceDialog(true); else void voice.record(); }}>{voice.phase === 'recording' ? <Square size={17} /> : <Mic size={18} />}</button>
              <button type="submit" className="agent-send" aria-label="Gửi tin nhắn" disabled={!input.trim() || busy || restoring || audioBusy}>{busy ? <span className="agent-send-spinner" aria-hidden="true" /> : <ArrowUp size={20} />}</button>
            </div>
          </form>
          <div className="agent-voice-toolbar"><button onClick={() => { if (!voice.enabled) setVoiceDialog(true); else void voice.speak(); }} disabled={busy || audioBusy || turns.length === 0 || (voice.enabled && !config.voice?.speech)}><Volume2 size={15} />Nghe phản hồi</button>{voice.phase !== 'idle' && <button onClick={voice.stop}><Square size={13} />Dừng âm thanh</button>}<button onClick={() => setVoiceDialog(true)}>Cài đặt giọng nói</button></div>
          <p className="agent-disclosure">AnMi là AI, có thể mắc sai sót và không thay thế chuyên gia.</p>
        </div>
      </section>
    </div>
    {risk?.level === 'check_in' && <SafetyCheckIn onResolved={() => { voice.stop(); setTurns([]); setRisk(null); }} />}{risk?.requires_support && support}
    {voiceDialog && <div className="modal-backdrop"><section className="card modal" role="dialog" aria-modal="true" aria-labelledby="voice-title"><button className="icon-button modal-close" aria-label="Đóng cài đặt giọng nói" onClick={() => setVoiceDialog(false)}><X size={20} /></button><h2 id="voice-title">Trò chuyện bằng giọng nói</h2><p>Micro chỉ bật khi bạn ghi âm hoặc bắt đầu cuộc gọi. Trong chế độ liên tục, lời nói được tự gửi khi bạn ngừng nói và AnMi tự đọc phản hồi; bạn không cần duyệt chữ từng lượt.</p><p>Âm thanh gốc được gửi tới dịch vụ nhận giọng nói đã cấu hình; chưa thể che tên trước bước này. CogAI không lưu bản ghi âm. Giọng đọc dùng phản hồi đã kiểm tra từ server. Nhà cung cấp có thể có chính sách lưu dữ liệu riêng.</p>
      {!anyVoice && <p className="notice">Chưa cấu hình dịch vụ giọng nói trên máy chủ. Bạn vẫn có thể nhắn tin với AnMi. Xem hướng dẫn cấu hình trong tài liệu vận hành.</p>}
      {anyVoice && <p className="small">Nhận giọng nói: {config.voice?.transcription ? 'đã cấu hình' : 'chưa được bật'}. Giọng đọc: {config.voice?.speech ? 'đã cấu hình' : 'chưa được bật'}. Trạng thái cấu hình chưa xác nhận dịch vụ hoạt động.</p>}
      {voice.enabled ? <><p className="small">Đã bật đồng ý xử lý giọng nói.</p><label className="check-row"><input type="checkbox" checked={autoRead} disabled={!config.voice?.speech} onChange={e => setAutoRead(e.target.checked)} /><span>Tự đọc phản hồi mới khi ở trang trò chuyện.</span></label><button className="button secondary" onClick={() => { void voice.disable(); setAutoRead(false); }}>Tắt giọng nói và thu hồi đồng ý</button></> : <><label className="check-row"><input type="checkbox" checked={voiceConsent} onChange={e => setVoiceConsent(e.target.checked)} /><span>Tôi đồng ý gửi âm thanh và phản hồi tới dịch vụ AI và giọng nói đã cấu hình.</span></label><button className="button primary" disabled={!voiceConsent || !anyVoice} onClick={() => { void voice.enable().then(() => setVoiceDialog(false)); }}>Bật trò chuyện giọng nói</button></>}
      <p className="small muted">Giọng nói sẽ dừng khi chuyển trang hoặc ẩn tab. Không có chế độ nghe nền.</p></section></div>}
  </div>;
}
