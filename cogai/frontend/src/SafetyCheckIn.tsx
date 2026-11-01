import { useState } from 'react';
import { api, errorText, type Risk } from './api';

export function SafetyCheckIn({onResolved}:{onResolved:()=>void}){
  const [message,setMessage]=useState(''),[confirmed,setConfirmed]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
  return <section className="card"><h2>Làm rõ điều bạn muốn dừng</h2><p>Nếu câu trước nói về việc dừng một hoạt động, bạn có thể giải thích thêm. Nếu đang không an toàn hoặc chưa chắc, hãy ưu tiên tìm người ở gần để hỗ trợ.</p>
    <form onSubmit={e=>{e.preventDefault();setBusy(true);setError('');void api<{status:string;risk:Risk}>('/safety/check-in',{no_current_danger:true,message}).then(r=>{if(r.status==='self_reported_no_current_danger')onResolved();else setError('Hệ thống vẫn ưu tiên hỗ trợ. Bạn có thể xem các lựa chọn bên dưới.');}).catch(e=>setError(errorText(e))).finally(()=>setBusy(false));}}>
      <label>Bạn muốn làm rõ điều gì?<textarea rows={3} maxLength={4000} required value={message} onChange={e=>setMessage(e.target.value)}/></label>
      <label className="check-row"><input type="checkbox" required checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/><span>Tôi đang không gặp nguy hiểm trước mắt và muốn làm rõ ý của câu trước.</span></label>
      <button className="button secondary" disabled={busy||!confirmed||!message.trim()}>Gửi lời làm rõ</button>{error&&<p role="alert" className="error-note">{error}</p>}
    </form>
  </section>;
}
