import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { Activity, ArrowDownToLine, ArrowLeft, ArrowRight, BookOpen, Check, ChevronRight, CircleHelp, Heart, House, LayoutDashboard, Leaf, LoaderCircle, LockKeyhole, Menu, MessageCircle, Plus, ShieldCheck, Sparkles, Stethoscope, Sun, Trash2, X } from 'lucide-react';
import { api, download, errorText, type Candidate, type Config, type Consent, type Reframe, type Risk, type SavedRecord, type Screening, type Session } from './api';
import { Account, ExpertQueue, Login, ReminderNotice, SupportRequests } from './Account';
import { AdminDashboard } from './Admin';
import { SafetyPlan } from './SafetyPlan';
import { AgentChat } from './AgentChat';

type Page = 'home' | 'chat' | 'reframe' | 'screening' | 'journal' | 'support' | 'account' | 'expert' | 'admin';
const navigation = [
  { id: 'home', label: 'Góc của bạn', icon: House }, { id: 'chat', label: 'Trò chuyện', icon: MessageCircle },
  { id: 'reframe', label: 'Nhìn lại suy nghĩ', icon: Sparkles }, { id: 'screening', label: 'Sàng lọc', icon: Activity },
  { id: 'journal', label: 'Nhật ký của tôi', icon: BookOpen },
] as const;
const moodLabels = ['Rất khó khăn', 'Hơi chùng xuống', 'Bình thường', 'Khá dễ chịu', 'Thật tốt'];
const moodFaces = ['⌢', '⌢', '−', '⌣', '◡'];
const lensLabels: Record<string, string> = { CBT: 'Xem xét bằng chứng', ACT: 'Đón nhận suy nghĩ', CFT: 'Tử tế với bản thân' };
const formatDate = (seconds: number) => new Date(seconds * 1000).toLocaleString('vi-VN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Ho_Chi_Minh' });

function Busy({ text = 'Đang xử lý…' }: { text?: string }) { return <span className="busy"><LoaderCircle size={16} className="spin" />{text}</span>; }
function ErrorNote({ text }: { text: string }) { return text ? <div role="alert" className="error-note">{text}</div> : null; }

function Support({ config, compact = false }: { config: Config; compact?: boolean }) {
  const phone = /^[+\d ()-]{5,25}$/.test(config.support.phone) ? config.support.phone.replace(/[^+\d]/g, '') : '';
  return <section className={compact ? 'support-box' : 'card support-page'}>
    <div className="icon-tile coral"><Heart size={24} /></div>
    <h2>Bạn có thể tìm người ở bên</h2>
    <p>Nếu đang gặp nguy hiểm trước mắt, hãy gọi cấp cứu 115 hoặc nhờ một người tin tưởng ở gần đến ở cùng.</p>
    <a className="button danger support-call" href="tel:115">Gọi cấp cứu 115</a>
    <div className="support-options">
      <div><strong>Một người bạn tin tưởng</strong><p>Người thân, bạn bè hoặc người có thể ở cạnh và giúp bạn tìm hỗ trợ.</p></div>
      <div><strong>Người có chuyên môn</strong><p>Phòng tham vấn hoặc cơ sở y tế bạn có thể tiếp cận.</p></div>
      {config.support.name && phone ? <div><strong>{config.support.name}</strong><p>{config.support.hours || 'Hãy kiểm tra giờ hoạt động với đơn vị hỗ trợ.'}</p><a className="button secondary" href={`tel:${phone}`}>Gọi đơn vị hỗ trợ</a></div> : <div><strong>Đầu mối đối tác của CogAI</strong><p>Chưa cấu hình liên hệ đã xác minh. Bản này chưa kết nối dịch vụ tiếp nhận ca.</p></div>}
    </div>
    <p className="small muted">AnMi là trợ lý AI của CogAI, không tự gọi điện, gửi cảnh báo hay cử người đến. Không có người trực theo dõi phiên này.</p>
  </section>;
}

function ConsentPage({ config, onStarted }: { config: Config; onStarted: (session: Session) => void }) {
  const [adult, setAdult] = useState(false), [accepted, setAccepted] = useState(false), [persist, setPersist] = useState(false), [external, setExternal] = useState(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function begin(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const consent: Consent = { adult: true, accepted: true, persist, external_ai: config.mode === 'live' && external, version: '2026-10-22.v1' };
      onStarted(await api<Session>('/session', consent));
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <main className="welcome-layout"><div className="welcome-story">
    <a className="brand" href="#"><span className="brand-mark"><Leaf size={26} /></span>Cog<span>AI</span></a>
    <span className="eyebrow">MỘT KHOẢNG DÀNH CHO BẠN</span>
    <h1>Mọi cảm xúc<br />đều có chỗ<br /><em>để được lắng nghe.</em></h1>
    <p>Chậm lại một chút. Ghi nhận điều bạn đang trải qua và cùng nhìn mọi chuyện từ một góc khác.</p>
    <div className="welcome-art" aria-hidden="true"><div className="art-sun" /><div className="art-hill one" /><div className="art-hill two" /><Leaf className="art-leaf" size={90} strokeWidth={1} /></div>
  </div><div className="welcome-form"><div className="card">
    <span className="pill"><LockKeyhole size={14} /> Không cần tên thật</span>
    <h2>Trước khi bắt đầu</h2><p>Dành cho người từ 18 tuổi. AnMi là trợ lý AI của CogAI, hỗ trợ tự chăm sóc, không chẩn đoán hay thay thế chuyên gia.</p>
    <form onSubmit={begin} className="consent-form">
      <label className="check-row"><input type="checkbox" checked={adult} onChange={e => setAdult(e.target.checked)} required /><span>Tôi từ 18 tuổi trở lên.</span></label>
      <label className="check-row"><input type="checkbox" checked={accepted} onChange={e => setAccepted(e.target.checked)} required /><span>Tôi hiểu đang tương tác với AI và đồng ý xử lý nội dung để sử dụng các tính năng tôi chọn.</span></label>
      <label className="check-row"><input type="checkbox" checked={persist} onChange={e => setPersist(e.target.checked)} /><span>Lưu lịch sử có mã hóa trên máy chủ.</span></label>
      {config.mode === 'live' && <label className="check-row"><input type="checkbox" checked={external} onChange={e => setExternal(e.target.checked)} required /><span>Tôi đồng ý gửi nội dung tới dịch vụ AI để AnMi trả lời.</span></label>}
      <ErrorNote text={error} /><button className="button primary full" disabled={!adult || !accepted || (config.mode === 'live' && !external) || busy}>{busy ? <Busy /> : <>Bắt đầu khoảng riêng của bạn <ArrowRight size={17} /></>}</button>
    </form><Login onStarted={onStarted}/>
  </div><details className="before-support"><summary>Cần hỗ trợ ngay?</summary><Support config={config} compact /></details></div></main>;
}

export default function App() {
  const [config, setConfig] = useState<Config | null>(null), [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true), [error, setError] = useState(''), [generation, setGeneration] = useState(0);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      setConfig(await api<Config>('/config'));
      const response = await fetch('/api/session', { credentials: 'same-origin' });
      if (response.ok) setSession(await response.json());
      else if (response.status === 401) setSession(null);
      else throw new Error('Chưa thể kiểm tra phiên. Hãy thử kết nối lại.');
    } catch (e) { setError(errorText(e)); } finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    const expired = () => { setSession(null); setGeneration(g => g + 1); };
    window.addEventListener('cogai-expired', expired);
    return () => window.removeEventListener('cogai-expired', expired);
  }, []);
  if (loading) return <main className="loading-page"><Leaf size={40} /><Busy text="Đang mở không gian của bạn…" /></main>;
  if (error || !config) return <main className="loading-page"><ErrorNote text={error || 'Chưa thể tải cấu hình.'} /><button className="button primary" onClick={load}>Kết nối lại</button></main>;
  if (!session) return <ConsentPage config={config} onStarted={s => { setGeneration(g => g + 1); setSession(s); }} />;
  return <Workspace key={generation} config={config} session={session} onEnded={() => { setSession(null); setGeneration(g => g + 1); }} />;
}

function Workspace({ config, session: initialSession, onEnded }: { config: Config; session: Session; onEnded: () => void }) {
  const [session,setSession]=useState(initialSession);
  const [page, setPage] = useState<Page>('home'), [mobile, setMobile] = useState(false), [records, setRecords] = useState<SavedRecord[]>([]);
  const [error, setError] = useState(''), [deleting, setDeleting] = useState(false), [busy, setBusy] = useState(false);
  const refresh = useCallback(async () => {
    try { const data = await api<{ records: SavedRecord[] }>('/records'); setRecords(data.records); } catch (e) { setError(errorText(e)); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(()=>{const changed=()=>{void api<Session>('/session').then(setSession).catch(e=>setError(errorText(e)));};window.addEventListener('cogai-session-changed',changed);return()=>window.removeEventListener('cogai-session-changed',changed);},[]);
  function navigate(next: Page) { setPage(next); setMobile(false); setError(''); }
  async function exportData() { try { download('cogai-du-lieu-phien.json', await api('/export')); } catch (e) { setError(errorText(e)); } }
  async function endSession() {
    setBusy(true); setError('');
    try { await api('/session', undefined, 'DELETE'); onEnded(); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  const title = page==='account'?'Tài khoản & quyền dữ liệu':page==='expert'?'Tiếp nhận hỗ trợ':page==='admin'?'Quản trị':navigation.find(item => item.id === page)?.label ?? 'Tìm người hỗ trợ';
  return <div className="app-shell">
    {mobile && <button className="mobile-scrim" aria-label="Đóng menu" onClick={() => setMobile(false)} />}
    <aside className={`sidebar ${mobile ? 'open' : ''}`}>
      <button className="brand" onClick={() => navigate('home')}><span className="brand-mark"><Leaf size={24} /></span>Cog<span>AI</span></button>
      <div className="sidebar-caption">KHÔNG GIAN CỦA BẠN</div>
      <button className="nav-item" onClick={()=>navigate('account')}><LockKeyhole size={19}/>Tài khoản & quyền dữ liệu</button>
      {session.account?.role==='expert'&&<button className={`nav-item ${page==='expert'?'active':''}`} onClick={()=>navigate('expert')}><Stethoscope size={19}/>Tiếp nhận hỗ trợ</button>}
      {session.account?.role==='admin'&&<button className={`nav-item ${page==='admin'?'active':''}`} onClick={()=>navigate('admin')}><LayoutDashboard size={19}/>Quản trị</button>}
      <nav aria-label="Điều hướng chính">{navigation.map(item => <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => navigate(item.id)} aria-current={page === item.id ? 'page' : undefined}><item.icon size={19} />{item.label}{page === item.id && <span className="active-dot" />}</button>)}</nav>
      <div className="sidebar-bottom">
        <button className={`nav-item support-link ${page === 'support' ? 'active' : ''}`} onClick={() => navigate('support')}><Heart size={18} />Tìm người hỗ trợ</button>
      </div>
    </aside>
    <div className="workspace"><header className="topbar"><div><button className="icon-button menu-button" onClick={() => setMobile(true)} aria-label="Mở menu"><Menu size={21} /></button><span>{title}</span></div>{session.account && <div className="header-right"><span className="account-chip">{session.account.alias}</span></div>}</header>
      <main className="main-content"><ErrorNote text={error} />
        <ReminderNotice/>
        {page==='account'&&<Account session={session} onChanged={s=>{setSession(s);void refresh();}} onEnded={onEnded}/>}
        {page==='expert'&&<ExpertQueue/>}
        {page==='admin'&&<AdminDashboard/>}
        {page === 'home' && <Home records={records} persist={session.consent.persist} refresh={refresh} navigate={navigate} />}
        {page === 'chat' && <Chat config={config} refresh={refresh} />}
        {page === 'reframe' && <ReframeExercise config={config} persist={session.consent.persist} refresh={refresh} />}
        {page === 'screening' && <ScreeningPage config={config} refresh={refresh} />}
        {page === 'journal' && <Journal records={records} persist={session.consent.persist} onExport={exportData} onDelete={() => setDeleting(true)} />}
        {page === 'support' && <><PageHeading eyebrow="KẾT NỐI VỚI NGƯỜI THẬT" title="Bạn không cần tự xoay xở mọi thứ." description="Tìm một người có thể lắng nghe và hỗ trợ bạn ở ngoài cuộc trò chuyện này." /><Support config={config} /><SafetyPlan config={config} /><SupportRequests config={config}/></>}
      </main><footer className="workspace-footer"><button onClick={() => setDeleting(true)}>Quản lý & kết thúc phiên</button></footer>
    </div>
    {deleting && <div className="modal-backdrop"><section className="card modal" role="dialog" aria-modal="true" aria-labelledby="delete-title"><button className="icon-button modal-close" onClick={() => setDeleting(false)} aria-label="Đóng"><X size={20} /></button><h2 id="delete-title">Xóa dữ liệu & kết thúc phiên?</h2><p>Nội dung được lưu của phiên sẽ bị xóa khỏi dữ liệu hoạt động. Phiên hiện tại không thể khôi phục. Bạn có thể xuất dữ liệu trước khi xóa.</p><p className="small muted">Xóa logic không bảo đảm xóa dấu vết trên ổ đĩa hoặc bản sao lưu thủ công. Người vận hành phải quản lý thời hạn và việc khôi phục các bản sao lưu.</p><ErrorNote text={error} /><div className="button-row"><button className="button secondary" onClick={exportData}>Xuất dữ liệu</button><button className="button danger" disabled={busy} onClick={endSession}>{busy ? <Busy /> : 'Xóa & kết thúc'}</button></div></section></div>}
  </div>;
}

function PageHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="page-heading"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>;
}

function Home({ records, persist, refresh, navigate }: { records: SavedRecord[]; persist: boolean; refresh: () => Promise<void>; navigate: (page: Page) => void }) {
  const [mood, setMood] = useState<number | null>(null), [note, setNote] = useState(''), [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('');
  const [risk, setRisk] = useState<Risk | null>(null);
  const moods = records.filter(r => r.kind === 'mood').slice(0, 7).reverse();
  async function saveMood(event: FormEvent) {
    event.preventDefault(); if (!mood) return; setBusy(true); setError(''); setMessage('');
    try { const result = await api<{ saved: boolean; risk: Risk }>('/moods', { score: mood, note }); setRisk(result.risk); setMessage(result.saved ? 'Đã lưu vào nhật ký của bạn.' : 'Đã ghi nhận trong lần thao tác này. Bạn đang chọn không lưu lịch sử.'); setNote(''); await refresh(); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <><div className="greeting-line"><span><Sun size={16} />{new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'Asia/Ho_Chi_Minh' })}</span><span className="pill">Từng bước nhỏ cũng có ý nghĩa</span></div>
    <div className="home-grid"><div className="home-main"><section className="hero-panel"><div><span className="eyebrow">CHÀO BẠN,</span><h1>Hôm nay,<br />bạn thấy thế nào?</h1><p>Không cần phải luôn ổn.<br />Ở đây, bạn có thể bắt đầu từ điều nhỏ nhất.</p><button className="button primary" onClick={() => navigate('chat')}>Mình muốn chia sẻ <ArrowRight size={16} /></button></div><div className="hero-art" aria-hidden="true"><div className="orbit o1" /><div className="orbit o2" /><div className="hero-sun"><Leaf size={60} strokeWidth={1} /></div><span className="floating-leaf l1"><Leaf size={30} /></span><span className="floating-leaf l2"><Sparkles size={23} /></span></div></section>
      <section className="card mood-card"><div className="section-title"><div><h2>Một phút cho cảm xúc</h2><p>Chọn điều gần với bạn nhất lúc này.</p></div><span className="icon-tile"><Heart size={20} /></span></div><form onSubmit={saveMood}><div className="mood-options">{moodLabels.map((label, i) => <button type="button" key={label} aria-pressed={mood === i + 1} className={`mood-option mood-${i} ${mood === i + 1 ? 'selected' : ''}`} onClick={() => { setMood(i + 1); setMessage(''); }}><span className="mood-face"><span>··</span><b>{moodFaces[i]}</b></span><span>{label}</span></button>)}</div><label className="sr-only" htmlFor="mood-note">Ghi chú cảm xúc</label><input id="mood-note" maxLength={1000} value={note} onChange={e => setNote(e.target.value)} placeholder="Có điều gì bạn muốn ghi lại? (không bắt buộc)" /><div className="mood-action"><span className="small muted"><LockKeyhole size={12} />{persist ? 'Chỉ trong nhật ký phiên của bạn' : 'Không lưu lịch sử trên máy chủ'}</span><button className="button secondary" disabled={!mood || busy}>{busy ? <Busy /> : <>Ghi nhận <Check size={15} /></>}</button></div></form><ErrorNote text={error} />{message && <p className="success" role="status">{message}</p>}{risk?.requires_support && <button className="notice-button" onClick={() => navigate('support')}>Ghi chú của bạn có nội dung cần ưu tiên an toàn. Xem lựa chọn hỗ trợ <ArrowRight size={15} /></button>}</section>
      <div className="section-title tools-heading"><h2>Chọn một bước nhỏ cho mình</h2></div><div className="tool-grid"><button className="card tool-card" onClick={() => navigate('reframe')}><span className="icon-tile lilac"><Sparkles size={22} /></span><h3>Một góc nhìn khác</h3><p>Cùng xem lại suy nghĩ đang làm bạn bận lòng.</p><span>Thử bài tập <ArrowRight size={15} /></span></button><button className="card tool-card" onClick={() => navigate('screening')}><span className="icon-tile sand"><Activity size={22} /></span><h3>Hiểu mình hơn</h3><p>Nhìn lại hai tuần vừa qua qua các câu hỏi ngắn.</p><span>Mở sàng lọc <ArrowRight size={15} /></span></button></div>
    </div><aside className="home-aside"><section className="card rhythm-card"><span className="eyebrow">NHỊP CẢM XÚC CỦA BẠN</span><h2>Mỗi ngày một chút</h2>{moods.length ? <><div className="mood-chart" aria-label="Các lần ghi nhận tâm trạng gần đây">{moods.map(r => <div key={r.id}><span style={{ height: `${Number(r.payload.score) * 22}px` }} title={`${formatDate(r.created)}: ${r.payload.score}/5`} /><small>{new Date(r.created * 1000).toLocaleDateString('vi-VN', { day: 'numeric', month: 'numeric', timeZone: 'Asia/Ho_Chi_Minh' })}</small></div>)}</div><p className="small muted">Các lần ghi nhận gần đây, không phải đánh giá sức khỏe.</p></> : <div className="empty-rhythm"><div className="empty-bars"><i /><i /><i /><i /><i /><i /><i /></div><p>{persist ? 'Những lần ghi nhận sẽ tạo nên nhịp cảm xúc riêng của bạn.' : 'Bạn đang chọn không lưu lịch sử. Biểu đồ sẽ không thu thập dữ liệu.'}</p></div>}<button className="text-button" onClick={() => navigate('journal')}>Mở nhật ký của tôi <ChevronRight size={15} /></button></section>
      <section className="quote-card"><span className="quote-mark">“</span><p>Bạn không cần giải quyết tất cả mọi thứ trong một ngày.</p><span>Một lời nhắc nhẹ cho hôm nay</span><Leaf size={36} strokeWidth={1} /></section><div className="help-note"><CircleHelp size={20} /><div><strong>Cần một người thật lắng nghe?</strong><p>Tìm hiểu những lựa chọn hỗ trợ bạn có thể tiếp cận.</p><button className="text-button" onClick={() => navigate('support')}>Xem hỗ trợ <ArrowRight size={14} /></button></div></div>
    </aside></div></>;
}

function Chat({ config, refresh }: { config: Config; refresh: () => Promise<void> }) {
  return <AgentChat config={config} refresh={refresh} support={<><Support config={config} compact/><SafetyPlan config={config} compact/><SupportRequests config={config}/></>}/>;
}

function ReframeExercise({ config, persist, refresh }: { config: Config; persist: boolean; refresh: () => Promise<void> }) {
  const edited=useRef(false);
  const [situation, setSituation] = useState(''), [thought, setThought] = useState(''), [lenses, setLenses] = useState(['CBT']);
  const [result, setResult] = useState<Reframe | null>(null), [selected, setSelected] = useState(0), [feedback, setFeedback] = useState(''), [rating, setRating] = useState(0), [savedFeedback, setSavedFeedback] = useState(false);
  const [busy, setBusy] = useState(false), [saving, setSaving] = useState(false), [error, setError] = useState('');
  const candidate = result?.candidates?.[selected];
  useEffect(()=>{let active=true;api<{situation?:string;thought?:string}>('/chat').then(s=>{if(active&&!edited.current){setSituation(s.situation??'');setThought(s.thought??'');}}).catch(e=>{if(active)setError(errorText(e));});return()=>{active=false;};},[]);
  async function generate(improve = false) {
    setBusy(true); setError('');
    try {
      const data = await api<Reframe>('/reframe', { situation, thought, lenses, previous: improve && candidate ? candidate.reframe : '', feedback: improve ? feedback : '' });
      setResult(data); setSelected(0); setRating(0); setSavedFeedback(false); setFeedback(''); await refresh();
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  async function rate() {
    if (!result || !rating) return; setSaving(true); setError('');
    try { await api('/feedback', { record_id: result.record_id, helpfulness: rating, comment: '' }); setSavedFeedback(true); await refresh(); }
    catch (e) { setError(errorText(e)); } finally { setSaving(false); }
  }
  function example() { edited.current=true;setSituation('Hôm nay tổ trưởng nhắc tôi vì làm chậm. Máy ở chỗ tôi đã bị lỗi.'); setThought('Tôi làm gì cũng hỏng, chắc chắn tôi sẽ bị đuổi việc.'); }
  return <><PageHeading eyebrow="BÀI TẬP TỪ MIND-REFRAME & LUMINA" title="Thử nhìn câu chuyện từ một góc khác." description="Tách điều đã xảy ra khỏi điều mình đang nghĩ. Bạn là người quyết định góc nhìn nào phù hợp với mình." /><div className="exercise-layout"><section className="card exercise-input"><div className="section-title"><h2>1. Điều đang làm bạn bận lòng</h2><button className="text-button" disabled={busy} onClick={example}>Dùng ví dụ</button></div><form onSubmit={e => { e.preventDefault(); void generate(); }}><label htmlFor="situation">Chuyện gì đã xảy ra?</label><textarea id="situation" required maxLength={4000} rows={4} value={situation} onChange={e => {edited.current=true;setSituation(e.target.value);}} placeholder="Thử kể những điều bạn quan sát được…" disabled={busy} /><label htmlFor="thought">Lúc đó, bạn đã nghĩ gì?</label><textarea id="thought" required maxLength={4000} rows={3} value={thought} onChange={e => {edited.current=true;setThought(e.target.value);}} placeholder="Ví dụ: Mình làm gì cũng không tốt…" disabled={busy} /><label>Chọn cách bạn muốn thử</label><div className="lens-options">{Object.entries(lensLabels).map(([key, label]) => <label key={key} className={lenses.includes(key) ? 'selected' : ''}><input type="checkbox" checked={lenses.includes(key)} disabled={busy} onChange={() => setLenses(prev => prev.includes(key) ? prev.filter(x => x !== key) : [...prev, key])} />{label}<small>{key}</small></label>)}</div><button className="button primary full" disabled={busy || !situation.trim() || !thought.trim() || !lenses.length}>{busy ? <Busy text="Đang tạo và kiểm tra góc nhìn…" /> : <>Cùng nhìn lại <Sparkles size={17} /></>}</button></form><p className="small muted">Đây là bài tập tự phản tư. Các lựa chọn trên không phải chỉ định liệu pháp hay dịch vụ điều trị.</p></section><section className="exercise-output"><ErrorNote text={error} />{result?.blocked ? <><div className="notice">{result.message}</div><Support config={config} compact /></> : result?.analysis ? <>
      <div className="card"><span className="eyebrow">2. CÙNG TÁCH NHỎ CÂU CHUYỆN</span><h2>Điều đã biết & điều còn mở</h2><dl className="analysis-list"><dt>Sự kiện bạn chia sẻ</dt><dd>{result.analysis.facts}</dd><dt>Cách bạn đang diễn giải</dt><dd>{result.analysis.interpretation}</dd><dt>Bằng chứng đang có</dt><dd>{result.analysis.evidence_for}</dd><dt>Điều cần xem thêm</dt><dd>{result.analysis.evidence_against}</dd></dl><div className="gentle-question"><CircleHelp size={20} /><p>{result.analysis.question}</p></div></div>
      <div className="card"><span className="eyebrow">3. CHỌN MỘT GÓC NHÌN ĐỂ THỬ</span><div className="candidate-tabs">{result.candidates?.map((item, i) => <button key={item.lens} className={selected === i ? 'selected' : ''} onClick={() => setSelected(i)}>{lensLabels[item.lens]}</button>)}</div>{candidate && <><blockquote>{candidate.reframe}</blockquote><p>{candidate.rationale}</p><div className="next-step"><Leaf size={18} /><div><strong>Một bước nhỏ</strong><p>{candidate.next_step}</p></div></div><details><summary>{config.mode === 'demo' ? 'Về nội dung minh họa' : 'Nhận xét của bộ đánh giá AI'}</summary><p className="small">{candidate.review}</p></details><div className="button-row"><button className="button secondary" onClick={() => download('cogai-goc-nhin.json', { situation, thought, candidate, mode: config.mode })}><ArrowDownToLine size={15} />Tải kết quả</button></div><label htmlFor="reframe-feedback">Bạn muốn điều chỉnh gì?</label><textarea id="reframe-feedback" rows={2} maxLength={1000} value={feedback} onChange={e => setFeedback(e.target.value)} placeholder="Ví dụ: Mình muốn cách diễn đạt ngắn và gần gũi hơn…" /><button className="button secondary" disabled={busy || !feedback.trim()} onClick={() => generate(true)}>{busy ? <Busy /> : 'Thử điều chỉnh góc nhìn'}</button>
      <div className="feedback-area"><strong>Bài tập có hữu ích với bạn?</strong><div className="rating-buttons">{[1, 2, 3, 4, 5].map(n => <button key={n} className={rating === n ? 'selected' : ''} disabled={!persist || savedFeedback} aria-label={`Mức hữu ích ${n} trên 5`} onClick={() => setRating(n)}>{n}</button>)}</div><span className="small muted">1 = chưa hữu ích · 5 = rất hữu ích</span>{persist ? <button className="text-button" disabled={!rating || savedFeedback || saving} onClick={rate}>{savedFeedback ? 'Đã lưu phản hồi' : saving ? 'Đang lưu…' : 'Gửi phản hồi'}</button> : <p className="small muted">Phản hồi không được lưu vì bạn chọn không lưu lịch sử.</p>}</div></>}
      </div></> : <div className="card empty-exercise"><div className="icon-tile lilac"><Sparkles size={28} /></div><h2>Không cần ép mình nghĩ tích cực.</h2><p>Mình chỉ thử tìm một cách nhìn đầy đủ hơn, có chỗ cho cả khó khăn và những điều chưa biết.</p><div className="exercise-steps"><span>01 · Kể lại</span><span>02 · Xem bằng chứng</span><span>03 · Chọn bước nhỏ</span></div></div>}</section></div></>;
}

function ScreeningPage({ config, refresh }: { config: Config; refresh: () => Promise<void> }) {
  const [items, setItems] = useState<Record<string, string[]> | null>(null), [kind, setKind] = useState('PHQ-9'), [answers, setAnswers] = useState<(number | null)[]>(Array(9).fill(null)), [index, setIndex] = useState(0), [difficulty, setDifficulty] = useState(0);
  const [result, setResult] = useState<Screening | null>(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const load = useCallback(async () => { setError(''); try { const data = await api<{ items: Record<string, string[]> }>('/questionnaires'); setItems(data.items); } catch (e) { setError(errorText(e)); } }, []);
  useEffect(() => { void load(); }, [load]);
  const questions = items?.[kind] ?? [], complete = answers.every(answer => answer !== null);
  function chooseKind(next: string) { setKind(next); setAnswers(Array(next === 'PHQ-9' ? 9 : 7).fill(null)); setIndex(0); setResult(null); setError(''); setDifficulty(0); }
  async function submit() { setBusy(true); setError(''); try { setResult(await api<Screening>('/screenings', { kind, answers, difficulty })); await refresh(); } catch (e) { setError(errorText(e)); } finally { setBusy(false); } }
  return <><PageHeading eyebrow="NHÌN LẠI HAI TUẦN VỪA QUA" title="Dành một chút thời gian hiểu mình." description="Kết quả giúp bạn bắt đầu một cuộc trao đổi, không xác định bạn có hay không có một rối loạn." /><div className="notice">Bản Việt hóa thử nghiệm phục vụ phát triển. Cần chuyên gia rà soát câu chữ và quy trình trước khi thí điểm.</div><ErrorNote text={error} />{!items ? <button className="button secondary" onClick={load}>Tải câu hỏi</button> : <div className="screening-layout"><section className="card"><div className="candidate-tabs">{['PHQ-9', 'GAD-7'].map(k => <button key={k} disabled={busy} className={kind === k ? 'selected' : ''} onClick={() => chooseKind(k)}>{k} · {k === 'PHQ-9' ? 'Khí sắc' : 'Lo âu'}</button>)}</div>{result ? <><span className="eyebrow">KẾT QUẢ BẢNG HỎI {kind}</span><div className="screening-score">{result.score}<small>/{result.maximum}</small></div><span className="pill">Mức điểm: {result.band}</span><p>{result.message}</p><p>{result.next_step}</p>{result.requires_support && <div className="notice">Câu trả lời ở mục 9 cần được hỏi thêm về an toàn, bất kể tổng điểm. Điều này chưa tự xác định mức nguy cơ.</div>}<button className="button secondary" onClick={() => chooseKind(kind)}>Làm lại bảng hỏi</button></> : <><div className="question-meta"><span>Câu {index + 1} / {questions.length}</span><span>{answers.filter(a => a !== null).length} câu đã trả lời</span></div><progress value={answers.filter(a => a !== null).length} max={questions.length} /><p>Trong hai tuần qua, bạn thường bị làm phiền bởi vấn đề sau ở mức nào?</p><h2 className="question-text">{questions[index]}</h2><div className="answer-options">{['Không ngày nào', 'Vài ngày', 'Hơn một nửa số ngày', 'Gần như mỗi ngày'].map((label, n) => <button key={label} className={answers[index] === n ? 'selected' : ''} aria-pressed={answers[index] === n} onClick={() => setAnswers(previous => previous.map((a, i) => i === index ? n : a))}><span>{n}</span>{label}{answers[index] === n && <Check size={17} />}</button>)}</div>{kind === 'PHQ-9' && (answers[8] ?? 0) > 0 && <div className="notice">Bạn có thể xem phần hỗ trợ bên cạnh ngay bây giờ. Không cần chờ hoàn tất bảng hỏi.</div>}{index === questions.length - 1 && <label>Mức ảnh hưởng tới công việc, sinh hoạt hoặc quan hệ<select value={difficulty} onChange={e => setDifficulty(Number(e.target.value))}><option value={0}>Không khó khăn</option><option value={1}>Hơi khó khăn</option><option value={2}>Rất khó khăn</option><option value={3}>Cực kỳ khó khăn</option></select></label>}<div className="button-row spread"><button className="button secondary" disabled={index === 0 || busy} onClick={() => setIndex(i => i - 1)}><ArrowLeft size={16} />Trước</button>{index < questions.length - 1 ? <button className="button primary" disabled={answers[index] === null} onClick={() => setIndex(i => i + 1)}>Tiếp theo <ArrowRight size={16} /></button> : <button className="button primary" disabled={!complete || busy} onClick={submit}>{busy ? <Busy /> : 'Xem mức điểm'}</button>}</div></>}</section><aside>{(kind === 'PHQ-9' && (answers[8] ?? 0) > 0) || result?.requires_support ? <Support config={config} compact /> : <div className="card screening-aside"><div className="icon-tile sand"><Leaf size={25} /></div><h2>Không có câu trả lời đúng hay sai.</h2><p>Chọn điều gần với trải nghiệm của bạn nhất. Bạn có thể dừng bất cứ lúc nào.</p><p className="small muted">Câu trả lời được chấm bằng quy tắc xác định, không gửi tới mô hình AI. Bản nháp vi-draft-1.</p><a href="https://www.uab.edu/medicine/pcp-sci/images/SCIMS/PHQ-9_Instruction_Manual.pdf" target="_blank" rel="noreferrer" className="text-button">Nguồn hướng dẫn chấm điểm <ArrowRight size={14} /></a></div>}</aside></div>}</>;
}

function Journal({ records, persist, onExport, onDelete }: { records: SavedRecord[]; persist: boolean; onExport: () => void; onDelete: () => void }) {
  const [filter, setFilter] = useState('all');
  const visible = records.filter(r => r.kind !== 'feedback' && r.kind !== 'chat_reset' && (filter === 'all' || r.kind === filter));
  const labels: Record<string, string> = { mood: 'Ghi nhận cảm xúc', reframe: 'Nhìn lại suy nghĩ', screening: 'Bảng hỏi', chat: 'Cuộc trò chuyện' };
  function summary(record: SavedRecord) {
    const p = record.payload;
    if (record.kind === 'mood') return <><strong>{moodLabels[Number(p.score) - 1]} · {String(p.score)}/5</strong>{Boolean(p.note) && <p>{String(p.note)}</p>}</>;
    if (record.kind === 'screening') return <><strong>{String(p.kind)}: {String(p.score)}/{String(p.maximum)} · {String(p.band)}</strong><p>Kết quả bảng hỏi, không phải chẩn đoán.</p></>;
    if (record.kind === 'chat') return <><strong>{String(p.message)}</strong><p>{String(p.reply)}</p></>;
    const candidates = p.candidates as Candidate[] | undefined;
    return <><strong>{(p.input as { thought?: string } | undefined)?.thought ?? 'Bài tập nhìn lại'}</strong>{candidates?.map(c => <p key={c.lens}><b>{lensLabels[c.lens]}:</b> {c.reframe}</p>)}{Boolean(p.message) && <p>{String(p.message)}</p>}</>;
  }
  return <><PageHeading eyebrow="NHỮNG ĐIỀU BẠN ĐÃ GHI NHẬN" title="Một chút hiểu mình, qua từng lần viết." description="Lịch sử thuộc tài khoản hoặc phiên khách của bạn. Bạn chọn thời hạn lưu và mục đích chia sẻ trong Tài khoản & quyền dữ liệu." /><div className="journal-actions"><div className="candidate-tabs">{[['all', 'Tất cả'], ['mood', 'Cảm xúc'], ['reframe', 'Bài tập'], ['screening', 'Bảng hỏi'], ['chat', 'Trò chuyện']].map(([key, label]) => <button key={key} className={filter === key ? 'selected' : ''} onClick={() => setFilter(key)}>{label}</button>)}</div><button className="button secondary" onClick={onExport}><ArrowDownToLine size={16} />Xuất dữ liệu</button></div>{!persist && <div className="notice">Bạn đang tắt lưu lịch sử. Có thể đổi trong Tài khoản & quyền dữ liệu.</div>}{visible.length ? <div className="journal-list">{visible.map(record => <article key={record.id} className="card journal-entry"><div><span className="pill">{labels[record.kind] ?? record.kind}</span><time>{formatDate(record.created)}</time></div><div>{summary(record)}</div></article>)}</div> : <div className="card empty-state"><BookOpen size={36} strokeWidth={1} /><h2>Chưa có ghi nhận nào ở đây.</h2><p>{persist ? 'Khi bạn hoàn tất một thao tác, nội dung sẽ xuất hiện tại đây.' : 'Lịch sử đang tắt theo lựa chọn của bạn.'}</p></div>}<div className="data-settings"><LockKeyhole size={18} /><div><strong>Bạn giữ quyền quyết định với dữ liệu của mình.</strong><p>Xuất dữ liệu hoặc xóa dữ liệu hoạt động và kết thúc phiên.</p></div><button className="text-button danger-text" onClick={onDelete}><Trash2 size={15} />Xóa dữ liệu phiên</button></div></>;
}


