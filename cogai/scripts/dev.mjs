import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { networkInterfaces } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkPorts } from './dev-ports.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const windows = process.platform === 'win32';
const live = process.argv.includes('--live') || process.argv.includes('--economy');
const demoData = process.argv.includes('--demo-data');
// Desk devices on the local Wi-Fi: the API listens on all interfaces, not just loopback.
const device = process.argv.includes('--device');
if (process.argv.slice(2).some(arg => !['--live','--economy','--demo-data','--device'].includes(arg))) {
  console.error('Usage: node cogai/scripts/dev.mjs [--live] [--demo-data] [--device]');
  process.exit(1);
}
// Non-secret overrides only. Do not read, print or rewrite the user's .env.
const backendEnv = { ...process.env, ...(live ? {
  COGAI_MODE: 'live', COGAI_LLM_BASE_URL: 'https://api.openai.com/v1',
  COGAI_LLM_MODEL: 'gpt-4.1-mini', COGAI_TRANSCRIPTION_MODEL: 'gpt-4o-transcribe',
  // One AnMi voice everywhere: the MYHealth device voice (Edge HoaiMy, default rate). No provider-voice fallback.
  // auto: official Azure Speech (same HoaiMy voice) when COGAI_AZURE_SPEECH_KEY is in backend/.env, else Edge.
  COGAI_SPEECH_PROVIDER: 'auto', COGAI_EDGE_VOICE: 'vi-VN-HoaiMyNeural', COGAI_EDGE_RATE: '+0%',
  COGAI_SPEECH_MODEL: 'gpt-4o-mini-tts', COGAI_SPEECH_VOICE: 'marin', COGAI_SPEECH_FORMAT:'wav',
  COGAI_LLM_MAX_COMPLETION_TOKENS: '1800', COGAI_EXTERNAL_DAILY_CALL_LIMIT: '0',
  // CARE agents (DoT/distortion/social) and CogRAG with the draft starter corpus (development only).
  COGAI_RESEARCH_DEEP_ENABLED: 'true', COGAI_EMBEDDING_MODEL: 'text-embedding-3-large',
  COGAI_KNOWLEDGE_DEVELOPMENT: 'true', COGAI_VOICE_MAX_RECORDING_SECONDS: '45',
} : {}),
  // Synthetic accounts and history in their own directory; the real ./data store is untouched.
  ...(demoData ? { COGAI_DATA_DIR: join(root, 'backend', 'data-demo') } : {}),
  ...(device ? { COGAI_DEVICE_GATEWAY: 'true' } : {}) };
const python = join(root, 'backend', '.venv', windows ? 'Scripts/python.exe' : 'bin/python');
const vite = join(root, 'frontend', 'node_modules', 'vite', 'bin', 'vite.js');
if (!existsSync(python) || !existsSync(vite)) {
  console.error('Install backend/frontend dependencies first. See cogai/README.md.');
  process.exit(1);
}
// Fail before starting either service or seeding data when an old session is running.
try {
  await checkPorts([5173, 8000]);
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
if (demoData && !existsSync(join(root, 'backend', 'data-demo', 'cogai.sqlite3'))) {
  const seeded = spawnSync(python, ['-m', 'app.seed_demo'], { cwd: join(root, 'backend'), env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, stdio: 'inherit', windowsHide: true });
  if (seeded.status !== 0) process.exit(seeded.status ?? 1);
}
const children = [
  spawn(python, ['-m', 'uvicorn', 'app.main:app', '--host', device ? '0.0.0.0' : '127.0.0.1', '--port', '8000', '--no-access-log'], { cwd: join(root, 'backend'), env: backendEnv, stdio: 'inherit', windowsHide: true }),
  spawn(process.execPath, [vite, '--host', '127.0.0.1', '--port', '5173', '--strictPort'], { cwd: join(root, 'frontend'), stdio: 'inherit', windowsHide: true }),
];
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (!child.pid) continue;
    if (windows) spawnSync('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true, stdio: 'ignore' });
    else child.kill('SIGTERM');
  }
  process.exit(code);
}
children.forEach(child => {
  child.on('error', error => { console.error(error.message); stop(1); });
  child.on('exit', code => { if (!stopping) stop(code ?? 1); });
});
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
console.log('CogAI local: http://127.0.0.1:5173 · API: http://127.0.0.1:8000/docs');
console.log('Press Ctrl+C to stop both processes.');
if (demoData) console.log('Demo data: backend/data-demo · password cogai2026demo · admin / expert / user');
if (live) console.log('Live voice: daily provider call cap disabled. Input/output safety checks and consent remain enforced. No automatic API probe.');
if (device) {
  const lan = Object.entries(networkInterfaces()).flatMap(([name, entries]) =>
    (entries ?? []).filter(i => i.family === 'IPv4' && !i.internal).map(i => ({ name, address: i.address })));
  console.log('Device gateway: choose the Wi-Fi interface shared with the robot:');
  for (const { name, address } of lan) console.log(`  ${name}: http://${address}:8000/xiaozhi/ota/`);
  if (!lan.length) console.log('  http://<LAN IP>:8000/xiaozhi/ota/');
  console.log('Register from cogai/backend: python -m app.devices add <MAC> <name>');
}
