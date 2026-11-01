import { useEffect, useState, type FormEvent } from 'react';
import { api, errorText, type Config, type Session } from './api';

export function Login({onStarted}:{onStarted:(s:Session)=>void}) {
  const [alias,setAlias]=useState(''),[password,setPassword]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  async function login(e:FormEvent) {
    e.preventDefault();setBusy(true);setError('');
    try { onStarted(await api<Session>('/login',{alias,password}));setPassword(''); }
    catch(e){setError(errorText(e));}finally{setBusy(false);}
  }
  return <details><summary>Đã có tài khoản bí danh? Đăng nhập</summary><form className="consent-form" onSubmit={login}>
    <label>Bí danh đăng nhập<input value={alias} onChange={e=>setAlias(e.target.value)} autoComplete="username" required /></label>
    <label>Mật khẩu đăng nhập<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" required /></label>
    {error&&<p role="alert" className="error-note">{error}</p>}<button className="button secondary" disabled={busy}>Đăng nhập</button>
  </form></details>;
}

const purposes=[['persist','Lưu lịch sử và ngữ cảnh'],['external_ai','Xử lý qua dịch vụ AI ngoài'],['voice_processing','Gửi âm thanh và phản hồi tới dịch vụ giọng nói'],['personalization','Phân tích khuynh hướng nhiều phiên'],['share_support','Chia sẻ tóm tắt với chuyên gia tiếp nhận'],['screening_reminders','Nhắc sàng lọc trong ứng dụng']] as const;

export function Account({session,onChanged,onEnded}:{session:Session;onChanged:(s:Session)=>void;onEnded:()=>void}) {
  const [choices,setChoices]=useState({...session.consent}),[alias,setAlias]=useState(''),[password,setPassword]=useState('');
  const [error,setError]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false),[deleting,setDeleting]=useState(false);
  const [days,setDays]=useState(session.account?.retention_days??30),[reminderDays,setReminderDays]=useState(14),[profile,setProfile]=useState('');
  useEffect(()=>{setChoices({...session.consent});},[session]);
  async function perform(action:()=>Promise<void>){setBusy(true);setError('');setMessage('');try{await action();}catch(e){setError(errorText(e));}finally{setBusy(false);}}
  return <section className="card account-settings"><h1>Tài khoản & quyền dữ liệu</h1>
    {session.account?<><p>Bí danh: {session.account.alias}</p><p>Đăng xuất giữ dữ liệu đã đồng ý lưu. Mật khẩu chỉ được băm tại máy chủ; hiện chưa có khôi phục mật khẩu.</p></>:<form className="consent-form" onSubmit={e=>{e.preventDefault();void perform(async()=>{onChanged(await api<Session>('/account',{alias,password}));setPassword('');});}}>
      <h2>Giữ không gian của bạn giữa các lần đăng nhập</h2><label>Bí danh mới<input value={alias} onChange={e=>setAlias(e.target.value)} pattern="[a-z0-9][a-z0-9_-]{2,39}" minLength={3} maxLength={40} autoComplete="username" required /></label>
      <p className="small muted">3–40 chữ thường không dấu, chữ số, gạch ngang hoặc gạch dưới. Không cần dùng tên thật.</p>
      <label>Mật khẩu mới<input type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={12} maxLength={128} autoComplete="new-password" required /></label>
      <button className="button primary" disabled={busy}>Tạo tài khoản bí danh</button></form>}
    <h2>Đồng ý theo từng mục đích</h2><p>Tắt lưu sẽ xóa lịch sử và trạng thái dẫn xuất. Tắt chia sẻ sẽ rút tóm tắt khỏi hàng đợi chuyên gia. Không thể thu hồi những gì người tiếp nhận đã đọc hoặc bản sao lưu ngoài hệ thống.</p>
    <div className="consent-form">{purposes.map(([key,label])=><label className="check-row" key={key}><input type="checkbox" checked={choices[key]??false} disabled={busy || (key==='personalization'&&!choices.persist)} onChange={e=>setChoices(c=>({...c,[key]:e.target.checked,...(key==='persist'&&!e.target.checked?{personalization:false}:{})}))} /><span>{label}</span></label>)}</div>
    <button className="button primary" disabled={busy} onClick={()=>void perform(async()=>{const body=Object.fromEntries(purposes.map(([k])=>[k,choices[k]??false]));onChanged(await api<Session>('/consent',body,'PATCH'));setMessage('Đã cập nhật quyền dữ liệu.');})}>Lưu lựa chọn đồng ý</button>
    {session.account&&<><h2>Thời hạn lưu nội dung</h2><label>Số ngày lưu<input type="number" min={1} max={365} value={days} onChange={e=>setDays(Number(e.target.value))} /></label><button className="button secondary" disabled={busy} onClick={()=>void perform(async()=>{await api('/retention',{days},'PUT');onChanged(await api<Session>('/session'));setMessage('Đã cập nhật thời hạn lưu.');})}>Lưu thời hạn</button></>}
    {choices.screening_reminders&&<><h2>Nhắc sàng lọc</h2><p>Chỉ hiện trong ứng dụng khi bạn quay lại; không gửi email, SMS hoặc thông báo ra ngoài.</p><label>Nhắc sau số ngày<input type="number" min={7} max={90} value={reminderDays} onChange={e=>setReminderDays(Number(e.target.value))} /></label><button className="button secondary" disabled={busy} onClick={()=>void perform(async()=>{await api('/reminders',{days:reminderDays},'PUT');setMessage('Đã đặt nhắc trong ứng dụng.');})}>Đặt nhắc sàng lọc</button></>}
    {choices.personalization&&<><h2>Cá nhân hóa nghiên cứu</h2><p>Cấu hình hiện tại chỉ kiểm tra điều kiện bằng chứng và chưa kết luận OCEAN. Chưa có adapter nghiên cứu được kiểm chứng.</p><button className="button secondary" disabled={busy} onClick={()=>void perform(async()=>{await api('/personality/jobs',{});const result=await api<{status:string}>('/personality');setProfile(result.status);})}>Kiểm tra bằng chứng nhiều phiên</button><p>{profile}</p><button className="text-button" disabled={busy} onClick={()=>void perform(async()=>{const s=await api<Session>('/consent',{personalization:false},'PATCH');onChanged(s);setProfile('');setMessage('Đã tắt và xóa dữ liệu cá nhân hóa.');})}>Tắt và xóa cá nhân hóa</button></>}
    {error&&<p role="alert" className="error-note">{error}</p>}{message&&<p role="status">{message}</p>}
    <div className="button-row"><button className="button secondary" disabled={busy} onClick={()=>void perform(async()=>{await api('/logout',{});onEnded();})}>Đăng xuất</button>{session.account&&<button className="text-button" disabled={busy} onClick={()=>void perform(async()=>{await api('/logout-all',{});onEnded();})}>Đăng xuất mọi thiết bị</button>}</div>
    <hr/><label className="check-row"><input type="checkbox" checked={deleting} onChange={e=>setDeleting(e.target.checked)} /><span>Tôi muốn xóa tài khoản và toàn bộ dữ liệu hoạt động</span></label><button className="button danger" disabled={!deleting||busy} onClick={()=>void perform(async()=>{await api('/account',undefined,'DELETE');onEnded();})}>Xóa tài khoản</button>
  </section>;
}

type Case={id:string;status:string;summary:string;created:number};
const statusLabels:Record<string,string>={pending:'Đang chờ người tiếp nhận',accepted:'Đã có người xác nhận tiếp nhận',in_progress:'Đang xử lý',resolved:'Đã đóng yêu cầu',declined:'Không tiếp nhận được',unavailable:'Chưa có dịch vụ tiếp nhận',out_of_hours:'Ngoài giờ tiếp nhận'};

export function SupportRequests({config}:{config:Config}) {
  const [cases,setCases]=useState<Case[]>([]),[summary,setSummary]=useState(''),[share,setShare]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  async function load(){const result=await api<{cases:Case[]}>('/referrals');setCases(result.cases);}
  useEffect(()=>{void load().catch(e=>setError(errorText(e)));},[]);
  async function request(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{
    await api('/consent',{share_support:true},'PATCH');window.dispatchEvent(new Event('cogai-session-changed'));
    await api('/referrals',{summary});setSummary('');await load();
  }catch(e){setError(errorText(e));}finally{setBusy(false);}}
  return <section className="card"><h2>Yêu cầu người thật hỗ trợ</h2><p>{config.referral_connected?'Chỉ chia sẻ tóm tắt bạn duyệt bên dưới. Yêu cầu chưa được tiếp nhận cho đến khi chuyên gia xác nhận.':'Chưa có dịch vụ tiếp nhận được cấu hình. Bạn có thể lưu yêu cầu ở trạng thái chưa tiếp nhận; sẽ không có người được thông báo tự động.'}</p>
    <form onSubmit={request} className="consent-form"><label>Tóm tắt bạn muốn chia sẻ<textarea value={summary} onChange={e=>setSummary(e.target.value)} maxLength={3000} required rows={4}/></label><label className="check-row"><input type="checkbox" checked={share} onChange={e=>setShare(e.target.checked)} required/><span>Tôi đồng ý chia sẻ tóm tắt này với người tiếp nhận được cấp quyền.</span></label><button className="button primary" disabled={busy||!share||!summary.trim()}>Tạo yêu cầu hỗ trợ</button></form>
    {error&&<p role="alert" className="error-note">{error}</p>}{cases.map(c=><article key={c.id}><strong>{statusLabels[c.status]??c.status}</strong><p>{c.summary}</p><button className="text-button" onClick={()=>{void api('/referrals/'+c.id,undefined,'DELETE').then(load).catch(e=>setError(errorText(e)));}}>Rút yêu cầu</button></article>)}
  </section>;
}

export function ExpertQueue(){
  const [cases,setCases]=useState<Case[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  async function load(){try{setCases((await api<{cases:Case[]}>('/expert/cases')).cases);}catch(e){setError(errorText(e));}}
  useEffect(()=>{void load();},[]);
  async function update(c:Case,status:string){setBusy(true);setError('');try{await api('/expert/cases/'+c.id,{status},'PATCH');await load();}catch(e){setError(errorText(e));}finally{setBusy(false);}}
  return <section className="card"><h1>Tiếp nhận hỗ trợ</h1><p>Chỉ hiện tóm tắt người dùng cho phép chia sẻ. Thao tác tiếp nhận là xác nhận của bạn; hệ thống không tự xác nhận có người trực.</p><button className="button secondary" onClick={load}>Làm mới hàng đợi</button>{error&&<p role="alert" className="error-note">{error}</p>}{cases.length===0&&<p>Không có yêu cầu trong quyền truy cập của bạn.</p>}{cases.map(c=><article className="card" key={c.id}><strong>{statusLabels[c.status]??c.status}</strong><p>{c.summary}</p><div className="button-row">{(c.status==='pending'?['accepted','declined','out_of_hours','unavailable']:c.status==='accepted'?['in_progress','resolved','declined']:c.status==='in_progress'?['resolved','declined']:[]).map(s=><button key={s} className="button secondary" disabled={busy} onClick={()=>void update(c,s)}>{s==='accepted'?'Xác nhận tiếp nhận':statusLabels[s]}</button>)}</div></article>)}</section>;
}

export function ReminderNotice(){
  const [due,setDue]=useState(false);
  useEffect(()=>{api<{enabled:boolean;next_due?:number}>('/reminders').then(r=>setDue(r.enabled&&Boolean(r.next_due&&r.next_due*1000<=Date.now()))).catch(()=>{});},[]);
  return due?<p className="notice" role="status">Đến lịch nhắc bạn đã chọn. Bạn có thể mở mục Sàng lọc hoặc bỏ qua lần này.</p>:null;
}
