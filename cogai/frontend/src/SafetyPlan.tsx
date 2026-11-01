import { useEffect, useState, type FormEvent } from 'react';
import { ArrowDownToLine, Phone, ShieldCheck } from 'lucide-react';
import { api, errorText, type Config } from './api';

type Plan = Record<(typeof sections)[number][0], string[]>;
// Stanley & Brown (2012) safety plan, plus reasons to keep going.
const sections = [
  ['warning_signs', '1. Dấu hiệu báo trước', 'Suy nghĩ, cảm giác hay tình huống cho thấy mình sắp thấy quá sức.', 'Ví dụ: mất ngủ nhiều đêm, nghĩ "không ai cần mình"'],
  ['coping', '2. Việc mình tự làm để dịu lại', 'Những việc nhỏ làm được một mình.', 'Ví dụ: thở chậm 4–6, tắm nước ấm, đi bộ quanh khu trọ'],
  ['distractions', '3. Người và nơi giúp mình bớt một mình', 'Chỗ đông người hoặc người để trò chuyện chuyện khác.', 'Ví dụ: quán nước đầu ngõ, gọi cho bạn cùng quê'],
  ['people', '4. Người mình có thể nhờ giúp', 'Người tin tưởng, biết mình đang khó khăn.', 'Ví dụ: chị gái, bạn thân cùng phòng'],
  ['professionals', '5. Chuyên gia và dịch vụ', 'Nơi có người chuyên môn hoặc khẩn cấp.', 'Ví dụ: phòng y tế, phòng tư vấn của trường'],
  ['safe_environment', '6. Giữ nơi ở an toàn hơn', 'Việc giúp mình an toàn trong lúc khó khăn nhất.', 'Ví dụ: nhờ người giữ hộ đồ có thể gây hại, ở cùng người khác'],
  ['reasons', 'Lý do để mình tiếp tục', 'Người, điều hay ước mong quan trọng với mình.', 'Ví dụ: mẹ, em gái, ngày tốt nghiệp'],
] as const;
const empty = Object.fromEntries(sections.map(([key]) => [key, []])) as unknown as Plan;
const lines = (text: string) => text.split('\n').map(s => s.trim()).filter(Boolean).slice(0, 6).map(s => s.slice(0, 200));

export function SafetyPlan({ config, compact = false }: { config: Config; compact?: boolean }) {
  const [plan, setPlan] = useState<Record<string, string>>({}), [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(''), [error, setError] = useState('');
  useEffect(() => {
    void api<Partial<Plan> & { empty?: boolean }>('/safety-plan').then(saved => {
      const professionals = saved.professionals?.length ? saved.professionals : ['Cấp cứu 115 khi có nguy hiểm trước mắt', ...(config.support.name ? [`${config.support.name} ${config.support.phone}`.trim()] : [])];
      setPlan(Object.fromEntries(sections.map(([key]) => [key, (key === 'professionals' ? professionals : saved[key] ?? []).join('\n')])));
    }).catch(e => setError(errorText(e)));
  }, [config.support.name, config.support.phone]);
  async function save(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      const body = { ...empty, ...Object.fromEntries(sections.map(([key]) => [key, lines(plan[key] ?? '')])) };
      const saved = await api<{ saved: boolean }>('/safety-plan', body, 'PUT');
      setMessage(saved.saved ? 'Đã lưu kế hoạch an toàn của bạn (được mã hóa).' : 'Đã lưu cho phiên này. Bạn đang không lưu lịch sử nên hãy tải kế hoạch về máy.');
    } catch (err) { setError(errorText(err)); } finally { setBusy(false); }
  }
  function download() {
    const text = sections.map(([key, title]) => `${title}\n${lines(plan[key] ?? '').map(l => `- ${l}`).join('\n') || '-'}`).join('\n\n');
    const url = URL.createObjectURL(new Blob(['KẾ HOẠCH AN TOÀN CỦA TÔI\n\n' + text + '\n\nKhi có nguy hiểm trước mắt: gọi 115.\n'], { type: 'text/plain;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url; a.download = 'ke-hoach-an-toan.txt'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const form = <form className="safety-plan" onSubmit={save}>
    {sections.map(([key, title, hint, example]) => <label key={key}><strong>{title}</strong><span className="small muted">{hint}</span>
      <textarea rows={2} value={plan[key] ?? ''} placeholder={example} onChange={e => setPlan(p => ({ ...p, [key]: e.target.value }))} /></label>)}
    <p className="small muted">Mỗi dòng là một ý, tối đa 6 dòng mỗi mục. Viết bằng lời của bạn; AnMi không tự liên hệ những người bạn ghi.</p>
    {error && <p role="alert" className="error-note">{error}</p>}{message && <p role="status" className="small">{message}</p>}
    <div className="button-row"><button className="button primary" disabled={busy}>Lưu kế hoạch</button><button type="button" className="button secondary" onClick={download}><ArrowDownToLine size={15} />Tải về máy</button></div>
  </form>;
  return <section className={compact ? 'safety-plan-box' : 'card'}>
    <div className="safety-plan-head"><ShieldCheck size={20} /><div><h2>Kế hoạch an toàn của bạn</h2><p className="small muted">Chuẩn bị sẵn khi bình tĩnh để dùng lúc khó khăn nhất.</p></div>
      <a className="button danger safety-call" href="tel:115"><Phone size={15} />Gọi cấp cứu 115</a></div>
    {compact ? <details><summary>Mở kế hoạch an toàn</summary>{form}</details> : form}
  </section>;
}
