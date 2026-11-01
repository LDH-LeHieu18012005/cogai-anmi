import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { AlertTriangle, CircleAlert, EyeOff, RefreshCw, Search, ShieldCheck } from 'lucide-react';
import { api, errorText } from './api';
import './admin.css';

type Daily = { day: string; active: number | null; chats: number; moods: number; screenings: number; exercises: number; mood_average: number | null };
type Bucket = { band: string; count: number | null };
type Overview = {
  suppressed: boolean; min_group: number; cohort: string | null; days: number;
  totals: { members: number; active_period: number | null; active_week: number | null; chats: number; moods: number; screenings: number; exercises: number; screening_completion: number | null };
  daily: Daily[]; mood_distribution: { score: number; count: number | null }[];
  phq9: { respondents: number | null; bands: Bucket[] }; gad7: { respondents: number | null; bands: Bucket[] };
  safety: { high: number; check_in: number; unavailable: number; phq9_item9_follow_up: number };
  referrals: { statuses: { status: string; count: number }[]; median_response_hours: number | null };
  consent: { purpose: string; share: number | null }[];
  ai: { calls: number; failures: number; average_latency_ms: number | null };
};
type Cohort = { name: string; members: number; reportable: boolean };
type Account = { alias: string; role: string; cohort: string; retention_days: number; created: number; records: number; referrals: number; last_active: number };
type Case = { id: string; status: string; created: number; updated: number; expert: string; cohort: string };
type AuditEvent = { action: string; created: number; actor: string };

const tabs = [['overview', 'Tổng quan'], ['accounts', 'Tài khoản'], ['support', 'Hỗ trợ & an toàn'], ['audit', 'Nhật ký hoạt động']] as const;
const statusLabels: Record<string, string> = { pending: 'Đang chờ', accepted: 'Đã tiếp nhận', in_progress: 'Đang xử lý', resolved: 'Đã đóng', declined: 'Không tiếp nhận', out_of_hours: 'Ngoài giờ', unavailable: 'Chưa có dịch vụ' };
const roleLabels: Record<string, string> = { user: 'Người dùng', expert: 'Chuyên gia', admin: 'Quản trị' };
const consentLabels: Record<string, string> = { persist: 'Lưu lịch sử', external_ai: 'AI ngoài hệ thống', voice_processing: 'Giọng nói', personalization: 'Cá nhân hóa', share_support: 'Chia sẻ với chuyên gia', screening_reminders: 'Nhắc sàng lọc' };
const moodLabels = ['Rất khó khăn', 'Hơi chùng xuống', 'Bình thường', 'Khá dễ chịu', 'Thật tốt'];
const actionLabels: Record<string, string> = {
  account_created: 'Tạo tài khoản', login: 'Đăng nhập', logout: 'Đăng xuất', support_requested: 'Gửi yêu cầu hỗ trợ', case_queue_viewed: 'Chuyên gia xem hàng đợi',
  case_accepted: 'Chuyên gia tiếp nhận ca', case_in_progress: 'Ca đang xử lý', case_resolved: 'Đóng ca', case_declined: 'Không tiếp nhận ca', case_out_of_hours: 'Báo ngoài giờ',
  case_unavailable: 'Báo chưa có dịch vụ', admin_report_viewed: 'Quản trị xem báo cáo', admin_report_suppressed: 'Báo cáo bị ẩn (nhóm nhỏ)', admin_accounts_viewed: 'Quản trị xem tài khoản',
  admin_account_changed: 'Quản trị đổi tài khoản', admin_role_expert: 'Được cấp vai trò chuyên gia', admin_role_user: 'Về vai trò người dùng', data_exported: 'Xuất dữ liệu',
  retention_changed: 'Đổi thời hạn lưu', voice_spoken: 'Nghe giọng đọc', handsfree_turn: 'Lượt nói rảnh tay', voice_transcribed: 'Chép giọng nói', ambiguous_safety_clarified: 'Tự làm rõ an toàn',
  operator_role_expert: 'Vận hành cấp chuyên gia', operator_role_admin: 'Vận hành cấp quản trị', operator_role_user: 'Vận hành thu quyền',
};
// One hue, light to dark: ordered severity bands are magnitude, not identity.
const ramp = ['#9cc4b2', '#6fa58c', '#4d8a72', '#336f5b', '#1f4f42'];
const dateTime = (s: number) => new Date(s * 1000).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Asia/Ho_Chi_Minh' });
const shortDay = (d: string) => `${d.slice(8, 10)}/${d.slice(5, 7)}`;
const percent = (v: number | null) => v === null ? '—' : `${Math.round(v * 100)}%`;
const hidden = (v: number | null, k: number) => v === null ? `< ${k}` : v.toLocaleString('vi-VN');

export function AdminDashboard() {
  const [tab, setTab] = useState<(typeof tabs)[number][0]>('overview');
  const [cohorts, setCohorts] = useState<Cohort[]>([]), [minGroup, setMinGroup] = useState(5);
  const [cohort, setCohort] = useState(''), [days, setDays] = useState(30), [stamp, setStamp] = useState(0);
  useEffect(() => { void api<{ min_group: number; cohorts: Cohort[] }>('/admin/cohorts').then(r => { setCohorts(r.cohorts); setMinGroup(r.min_group); }).catch(() => {}); }, [stamp]);
  return <div className="admin">
    <div className="page-heading"><span className="eyebrow">BẢNG ĐIỀU KHIỂN VẬN HÀNH</span><h1>Quản trị CogAI</h1>
      <p>Chỉ hiển thị số liệu tổng hợp và thông tin tài khoản. Nội dung trò chuyện, ghi chú và tóm tắt hỗ trợ không bao giờ hiện ở đây. Nhóm hoặc mức có dưới {minGroup} người được ẩn.</p></div>
    <div className="admin-tabs" role="tablist">{tabs.map(([id, label]) => <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>{label}</button>)}</div>
    {(tab === 'overview' || tab === 'support') && <div className="admin-filters">
      <label>Nhóm tổ chức<select value={cohort} onChange={e => setCohort(e.target.value)}><option value="">Tất cả người dùng</option>{cohorts.map(c => <option key={c.name} value={c.name}>{c.name} · {c.reportable ? `${c.members} người` : `dưới ${minGroup} người`}</option>)}</select></label>
      <div className="admin-range" role="group" aria-label="Khoảng thời gian">{[7, 30, 90].map(d => <button key={d} aria-pressed={days === d} onClick={() => setDays(d)}>{d} ngày</button>)}</div>
      <button className="button secondary admin-refresh" onClick={() => setStamp(s => s + 1)}><RefreshCw size={15} />Làm mới</button>
    </div>}
    {tab === 'overview' && <OverviewTab cohort={cohort} days={days} stamp={stamp} />}
    {tab === 'accounts' && <AccountsTab cohorts={cohorts} onChanged={() => setStamp(s => s + 1)} />}
    {tab === 'support' && <SupportTab cohort={cohort} days={days} stamp={stamp} />}
    {tab === 'audit' && <AuditTab />}
  </div>;
}

function useOverview(cohort: string, days: number, stamp: number) {
  const [data, setData] = useState<Overview | null>(null), [error, setError] = useState('');
  useEffect(() => {
    let live = true; setError('');
    const query = new URLSearchParams({ days: String(days), ...(cohort ? { cohort } : {}) });
    api<Overview>('/admin/overview?' + query).then(r => { if (live) setData(r); }).catch(e => { if (live) setError(errorText(e)); });
    return () => { live = false; };
  }, [cohort, days, stamp]);
  return { data, error };
}

function Suppressed({ k }: { k: number }) {
  return <div className="card admin-suppressed"><EyeOff size={22} /><div><strong>Nhóm này chưa đủ {k} người để báo cáo.</strong><p>Để không ai bị nhận diện, CogAI không hiển thị số liệu của nhóm nhỏ. Hãy chọn nhóm lớn hơn hoặc xem toàn bộ người dùng.</p></div></div>;
}

function OverviewTab({ cohort, days, stamp }: { cohort: string; days: number; stamp: number }) {
  const { data, error } = useOverview(cohort, days, stamp);
  if (error) return <p role="alert" className="error-note">{error}</p>;
  if (!data) return <p className="muted">Đang tải số liệu…</p>;
  if (data.suppressed) return <Suppressed k={data.min_group} />;
  const t = data.totals, k = data.min_group;
  const pending = data.referrals.statuses.find(s => s.status === 'pending')?.count ?? 0;
  return <>
    <div className="admin-tiles">
      <Tile label="Người dùng trong nhóm" value={t.members.toLocaleString('vi-VN')} />
      <Tile label="Hoạt động 7 ngày qua" value={hidden(t.active_week, k)} hint={t.active_week !== null ? `${Math.round(t.active_week / t.members * 100)}% người dùng` : undefined} />
      <Tile label="Đã làm sàng lọc trong kỳ" value={percent(t.screening_completion)} hint="Mục tiêu thí điểm ≥ 70%" />
      <Tile label="Lượt trò chuyện" value={t.chats.toLocaleString('vi-VN')} hint={`${days} ngày`} />
      <Tile label="Ghi nhận tâm trạng" value={t.moods.toLocaleString('vi-VN')} hint={`${days} ngày`} />
      <Tile label="Yêu cầu hỗ trợ đang chờ" value={String(pending)} tone={pending ? 'warning' : undefined} />
    </div>
    <div className="admin-grid">
      <ChartCard title="Người dùng hoạt động mỗi ngày" note={`Ngày có dưới ${k} người hoạt động được để trống.`} wide
        table={<DataTable head={['Ngày', 'Người hoạt động', 'Trò chuyện', 'Tâm trạng', 'Sàng lọc']} rows={data.daily.map(d => [d.day, hidden(d.active, k), d.chats, d.moods, d.screenings])} />}>
        <Columns points={data.daily.map(d => ({ label: shortDay(d.day), value: d.active, tip: `${shortDay(d.day)}: ${d.active === null ? `dưới ${k}` : d.active} người · ${d.chats} lượt trò chuyện` }))} />
      </ChartCard>
      <ChartCard title="Tâm trạng trung bình mỗi ngày" note="Thang 1 (rất khó khăn) – 5 (thật tốt). Trung bình theo người, chỉ tính ngày đủ người ghi nhận." wide
        table={<DataTable head={['Ngày', 'Trung bình']} rows={data.daily.map(d => [d.day, d.mood_average ?? '—'])} />}>
        <MoodLine points={data.daily.map(d => ({ label: shortDay(d.day), value: d.mood_average }))} />
      </ChartCard>
      <ChartCard title={`Kết quả PHQ-9 gần nhất · ${hidden(data.phq9.respondents, k)} người`} note="Mức điểm sàng lọc, không phải chẩn đoán."
        table={<DataTable head={['Mức', 'Số người']} rows={data.phq9.bands.map(b => [b.band, hidden(b.count, k)])} />}>
        <Bars rows={data.phq9.bands.map((b, i) => ({ label: b.band, value: b.count, color: ramp[i] }))} k={k} />
      </ChartCard>
      <ChartCard title={`Kết quả GAD-7 gần nhất · ${hidden(data.gad7.respondents, k)} người`} note="Mức điểm sàng lọc, không phải chẩn đoán."
        table={<DataTable head={['Mức', 'Số người']} rows={data.gad7.bands.map(b => [b.band, hidden(b.count, k)])} />}>
        <Bars rows={data.gad7.bands.map((b, i) => ({ label: b.band, value: b.count, color: ramp[i + 1] }))} k={k} />
      </ChartCard>
      <ChartCard title="Phân bố ghi nhận tâm trạng" note="Số lượt ghi nhận trong kỳ."
        table={<DataTable head={['Mức', 'Số lượt']} rows={data.mood_distribution.map(m => [moodLabels[m.score - 1], hidden(m.count, k)])} />}>
        <Bars rows={data.mood_distribution.map(m => ({ label: moodLabels[m.score - 1], value: m.count }))} k={k} />
      </ChartCard>
      <ChartCard title="Tỷ lệ đồng ý theo mục đích" note="Người dùng chọn riêng từng mục đích dữ liệu."
        table={<DataTable head={['Mục đích', 'Tỷ lệ']} rows={data.consent.map(c => [consentLabels[c.purpose] ?? c.purpose, percent(c.share)])} />}>
        <Bars rows={data.consent.map(c => ({ label: consentLabels[c.purpose] ?? c.purpose, value: c.share === null ? null : Math.round(c.share * 100) }))} k={k} max={100} unit="%" />
      </ChartCard>
    </div>
    <p className="small muted">Dịch vụ AI từ khi máy chủ khởi động: {data.ai.calls} lời gọi, {data.ai.failures} lỗi{data.ai.average_latency_ms !== null ? `, trung bình ${(data.ai.average_latency_ms / 1000).toFixed(1)} giây/lời gọi` : ''}.</p>
  </>;
}

function Tile({ label, value, hint, tone }: { label: string; value: string; hint?: string; tone?: 'warning' | 'critical' }) {
  return <div className={`admin-tile ${tone ?? ''}`}>{tone && (tone === 'critical' ? <AlertTriangle size={16} /> : <CircleAlert size={16} />)}<span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</div>;
}

function ChartCard({ title, note, children, table, wide }: { title: string; note: string; children: ReactNode; table: ReactNode; wide?: boolean }) {
  return <section className={`card admin-chart ${wide ? 'wide' : ''}`}><h2>{title}</h2><p className="small muted">{note}</p>{children}
    <details><summary>Xem bảng số liệu</summary>{table}</details></section>;
}

function DataTable({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return <div className="admin-table-wrap"><table className="admin-table"><thead><tr>{head.map(h => <th key={h}>{h}</th>)}</tr></thead>
    <tbody>{rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody></table></div>;
}

function niceMax(values: number[]) {
  const top = Math.max(1, ...values), step = 10 ** Math.floor(Math.log10(top));
  return Math.ceil(top / step) * step;
}

function Columns({ points }: { points: { label: string; value: number | null; tip: string }[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const max = niceMax(points.map(p => p.value ?? 0));
  const every = Math.ceil(points.length / 8);
  return <div className="admin-columns" onMouseLeave={() => setHover(null)}>
    <div className="admin-gridlines">{[1, .5, 0].map(f => <span key={f} style={{ bottom: `${f * 100}%` }}>{Math.round(max * f)}</span>)}</div>
    <div className="admin-column-row">{points.map((p, i) => <button key={i} className="admin-column" aria-label={p.tip} onMouseEnter={() => setHover(i)} onFocus={() => setHover(i)} onBlur={() => setHover(null)}>
      <i style={{ height: p.value ? `${(p.value / max) * 100}%` : 0 }} className={hover === i ? 'hover' : ''} />
      {i % every === 0 && <em>{p.label}</em>}
    </button>)}</div>
    {hover !== null && <div className="admin-tooltip" style={{ left: `${((hover + .5) / points.length) * 100}%` }}>{points[hover].tip}</div>}
  </div>;
}

function MoodLine({ points }: { points: { label: string; value: number | null }[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const x = (i: number) => (i + .5) / points.length * 100, y = (v: number) => 100 - ((v - 1) / 4) * 100;
  // Break the line where a day was suppressed instead of bridging it.
  const segments: string[] = [];
  let current = '';
  points.forEach((p, i) => { if (p.value === null) { if (current) segments.push(current); current = ''; } else current += `${current ? 'L' : 'M'}${x(i)},${y(p.value)}`; });
  if (current) segments.push(current);
  const every = Math.ceil(points.length / 8);
  return <div className="admin-line" onMouseLeave={() => setHover(null)}>
    <div className="admin-gridlines">{[5, 3, 1].map(v => <span key={v} style={{ bottom: `${((v - 1) / 4) * 100}%` }}>{v}</span>)}</div>
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{segments.map((d, i) => <path key={i} d={d} vectorEffect="non-scaling-stroke" />)}</svg>
    {points.map((p, i) => <button key={i} className="admin-line-hit" style={{ left: `${(i / points.length) * 100}%`, width: `${100 / points.length}%` }}
      aria-label={`${p.label}: ${p.value ?? 'không đủ người'}`} onMouseEnter={() => setHover(i)} onFocus={() => setHover(i)} onBlur={() => setHover(null)}>
      {i % every === 0 && <em>{p.label}</em>}</button>)}
    {hover !== null && <>
      <span className="admin-crosshair" style={{ left: `${x(hover)}%` }} />
      {points[hover].value !== null && <span className="admin-dot" style={{ left: `${x(hover)}%`, bottom: `${100 - y(points[hover].value!)}%` }} />}
      <div className="admin-tooltip" style={{ left: `${x(hover)}%` }}>{points[hover].label}: {points[hover].value === null ? 'không đủ người ghi nhận' : `${points[hover].value} / 5`}</div>
    </>}
  </div>;
}

function Bars({ rows, k, max, unit = '' }: { rows: { label: string; value: number | null; color?: string }[]; k: number; max?: number; unit?: string }) {
  const top = max ?? niceMax(rows.map(r => r.value ?? 0));
  return <div className="admin-bars">{rows.map(r => <div className="admin-bar" key={r.label} title={`${r.label}: ${r.value === null ? `dưới ${k}` : r.value + unit}`}>
    <span>{r.label}</span>
    <div className="admin-bar-track">{r.value === null ? <em>ẩn · dưới {k}</em> : r.value > 0 && <i style={{ width: `${(r.value / top) * 100}%`, background: r.color }} />}</div>
    <strong>{r.value === null ? '—' : r.value.toLocaleString('vi-VN') + unit}</strong>
  </div>)}</div>;
}

function AccountsTab({ cohorts, onChanged }: { cohorts: Cohort[]; onChanged: () => void }) {
  const [data, setData] = useState<{ guests_active: number; accounts: Account[] } | null>(null);
  const [query, setQuery] = useState(''), [role, setRole] = useState(''), [error, setError] = useState(''), [message, setMessage] = useState('');
  async function load() { try { setData(await api('/admin/accounts')); } catch (e) { setError(errorText(e)); } }
  useEffect(() => { void load(); }, []);
  async function change(alias: string, body: { role?: string; cohort?: string }) {
    setError(''); setMessage('');
    try { await api('/admin/accounts/' + encodeURIComponent(alias), body, 'PATCH'); setMessage(`Đã cập nhật ${alias}.`); await load(); onChanged(); }
    catch (e) { setError(errorText(e)); }
  }
  const visible = useMemo(() => (data?.accounts ?? []).filter(a => (!role || a.role === role) && (a.alias.includes(query.trim().toLowerCase()) || a.cohort.toLowerCase().includes(query.trim().toLowerCase()))), [data, query, role]);
  if (!data) return error ? <p role="alert" className="error-note">{error}</p> : <p className="muted">Đang tải tài khoản…</p>;
  const counts = data.accounts.reduce<Record<string, number>>((all, a) => ({ ...all, [a.role]: (all[a.role] ?? 0) + 1 }), {});
  return <>
    <div className="admin-tiles">
      <Tile label="Tài khoản bí danh" value={String(data.accounts.length)} />
      <Tile label="Chuyên gia" value={String(counts.expert ?? 0)} />
      <Tile label="Quản trị" value={String(counts.admin ?? 0)} />
      <Tile label="Phiên khách đang mở" value={String(data.guests_active)} hint="Không có tài khoản, hết hạn sau 24 giờ" />
    </div>
    <section className="card">
      <div className="admin-filters inline"><label className="admin-search"><Search size={15} /><input placeholder="Tìm bí danh hoặc nhóm" value={query} onChange={e => setQuery(e.target.value)} /></label>
        <label>Vai trò<select value={role} onChange={e => setRole(e.target.value)}><option value="">Tất cả</option>{Object.entries(roleLabels).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label></div>
      {error && <p role="alert" className="error-note">{error}</p>}{message && <p role="status" className="small">{message}</p>}
      <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Bí danh</th><th>Vai trò</th><th>Nhóm tổ chức</th><th>Bản ghi</th><th>Yêu cầu hỗ trợ</th><th>Hoạt động gần nhất</th><th>Tạo lúc</th></tr></thead>
        <tbody>{visible.map(a => <tr key={a.alias}><td><strong>{a.alias}</strong></td>
          <td>{a.role === 'admin' ? roleLabels.admin : <select aria-label={`Vai trò của ${a.alias}`} value={a.role} onChange={e => void change(a.alias, { role: e.target.value })}><option value="user">Người dùng</option><option value="expert">Chuyên gia</option></select>}</td>
          <td>{a.role === 'admin' ? '—' : <select aria-label={`Nhóm của ${a.alias}`} value={a.cohort} onChange={e => void change(a.alias, { cohort: e.target.value })}><option value="">Không thuộc nhóm</option>{cohorts.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}{a.cohort && !cohorts.some(c => c.name === a.cohort) && <option value={a.cohort}>{a.cohort}</option>}</select>}</td>
          <td>{a.records}</td><td>{a.referrals}</td><td>{dateTime(a.last_active)}</td><td>{dateTime(a.created)}</td></tr>)}</tbody></table></div>
      <p className="small muted">Hiển thị {visible.length}/{data.accounts.length} tài khoản. Quyền quản trị chỉ cấp bằng công cụ vận hành: <code>python -m app.operations grant-admin &lt;bí-danh&gt;</code>.</p>
    </section>
  </>;
}

function SupportTab({ cohort, days, stamp }: { cohort: string; days: number; stamp: number }) {
  const { data, error } = useOverview(cohort, days, stamp);
  const [cases, setCases] = useState<Case[]>([]);
  useEffect(() => { void api<{ cases: Case[] }>('/admin/referrals').then(r => setCases(r.cases)).catch(() => {}); }, [stamp]);
  if (error) return <p role="alert" className="error-note">{error}</p>;
  if (!data) return <p className="muted">Đang tải…</p>;
  if (data.suppressed) return <Suppressed k={data.min_group} />;
  const s = data.safety, shown = cohort ? cases.filter(c => c.cohort === cohort) : cases;
  return <>
    <div className="admin-tiles">
      <Tile label="Tín hiệu nguy cơ cao" value={String(s.high)} hint={`${days} ngày · đã hiện kênh khẩn cấp`} tone={s.high ? 'critical' : undefined} />
      <Tile label="Cần hỏi lại về an toàn" value={String(s.check_in)} hint={`${days} ngày`} tone={s.check_in ? 'warning' : undefined} />
      <Tile label="PHQ-9 câu 9 cần theo dõi" value={String(s.phq9_item9_follow_up)} tone={s.phq9_item9_follow_up ? 'warning' : undefined} />
      <Tile label="Thời gian phản hồi trung vị" value={data.referrals.median_response_hours === null ? '—' : `${data.referrals.median_response_hours} giờ`} hint="Từ lúc gửi đến khi chuyên gia trả lời" />
    </div>
    <div className="admin-grid">
      <ChartCard title="Yêu cầu hỗ trợ theo trạng thái" note={`Gửi trong ${days} ngày.`}
        table={<DataTable head={['Trạng thái', 'Số yêu cầu']} rows={data.referrals.statuses.map(r => [statusLabels[r.status] ?? r.status, r.count])} />}>
        <Bars rows={data.referrals.statuses.map(r => ({ label: statusLabels[r.status] ?? r.status, value: r.count }))} k={data.min_group} />
      </ChartCard>
      <section className="card admin-chart"><h2><ShieldCheck size={18} /> Quy tắc xử lý</h2><ul className="admin-rules">
        <li>Tín hiệu nguy cơ cao luôn hiện kênh khẩn cấp ngay cho người dùng; AI không tự xử lý ca.</li>
        <li>Quản trị chỉ thấy trạng thái và thời gian. Tóm tắt chỉ chuyên gia được cấp quyền mới đọc được, và chỉ khi người dùng đồng ý chia sẻ.</li>
        <li>Phân công ca do chuyên gia tự xác nhận ở trang Tiếp nhận hỗ trợ.</li></ul></section>
    </div>
    <section className="card"><h2>Danh sách yêu cầu</h2><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Mã</th><th>Nhóm</th><th>Trạng thái</th><th>Chuyên gia</th><th>Gửi lúc</th><th>Cập nhật</th></tr></thead>
      <tbody>{shown.map(c => <tr key={c.id}><td><code>{c.id}</code></td><td>{c.cohort || '—'}</td><td><span className={`admin-status status-${c.status}`}>{statusLabels[c.status] ?? c.status}</span></td><td>{c.expert || 'Chưa có'}</td><td>{dateTime(c.created)}</td><td>{dateTime(c.updated)}</td></tr>)}</tbody></table></div>
      {shown.length === 0 && <p className="muted">Chưa có yêu cầu.</p>}</section>
  </>;
}

function AuditTab() {
  const [events, setEvents] = useState<AuditEvent[]>([]), [error, setError] = useState('');
  useEffect(() => { void api<{ events: AuditEvent[] }>('/admin/audit?limit=200').then(r => setEvents(r.events)).catch(e => setError(errorText(e))); }, []);
  return <section className="card"><h2>Nhật ký hoạt động</h2><p className="small muted">200 sự kiện gần nhất. Nhật ký chỉ ghi hành động và thời điểm, không ghi nội dung; tự xóa sau 90 ngày.</p>
    {error && <p role="alert" className="error-note">{error}</p>}
    <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Thời điểm</th><th>Tài khoản</th><th>Hành động</th></tr></thead>
      <tbody>{events.map((e, i) => <tr key={i}><td>{dateTime(e.created)}</td><td>{e.actor}</td><td>{actionLabels[e.action] ?? e.action}</td></tr>)}</tbody></table></div></section>;
}
