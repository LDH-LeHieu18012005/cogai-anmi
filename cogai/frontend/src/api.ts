export type Consent = { accepted: true; adult: true; persist: boolean; external_ai: boolean; personalization?:boolean; share_support?:boolean; screening_reminders?:boolean; voice_processing?:boolean; version: '2026-10-22.v1' };
export type Session = { consent: Consent; expires: number; account?: {alias:string;role:string;retention_days:number;cohort?:string|null}|null };
export type Config = { mode: 'demo' | 'live'; session_hours: number; support: { name: string; phone: string; hours: string }; referral_connected: boolean; voice?:{transcription:boolean;speech:boolean;max_audio_bytes:number;max_recording_seconds:number} };
export type Risk = { level: 'low' | 'check_in' | 'high' | 'unavailable'; requires_support: boolean; reason: string };
export type Turn = { role: 'user' | 'assistant'; content: string };
export type Candidate = { lens: string; reframe: string; rationale: string; next_step: string; review: string };
export type Reframe = { blocked: boolean; message?: string; risk: Risk; record_id: string; mode: string; analysis?: { facts: string; interpretation: string; evidence_for: string; evidence_against: string; possible_patterns: string[]; question: string }; candidates?: Candidate[] };
export type Screening = { kind: string; score: number; maximum: number; band: string; requires_support: boolean; message: string; next_step: string; record_id: string };
export type SavedRecord = { id: string; kind: string; created: number; payload: Record<string, unknown> };

export async function api<T>(path: string, body?: unknown, method?: string): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: method ?? (body === undefined ? 'GET' : 'POST'),
    credentials: 'same-origin',
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(115_000),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && path !== '/session') window.dispatchEvent(new Event('cogai-expired'));
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : 'Yêu cầu chưa hợp lệ hoặc dịch vụ chưa sẵn sàng. Hãy thử lại.');
  }
  return data as T;
}

export function download(name: string, data: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' }));
  const anchor = document.createElement('a');
  anchor.href = url; anchor.download = name; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const errorText = (error: unknown) => error instanceof Error ? error.message : 'Chưa thể hoàn tất. Bạn hãy thử lại.';
