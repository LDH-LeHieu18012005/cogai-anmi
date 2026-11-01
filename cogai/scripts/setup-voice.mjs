import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const python = join(root, 'backend', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
if (!existsSync(python)) {
  console.error('Install backend dependencies first. See cogai/README.md.');
  process.exit(1);
}
const command = process.argv[2] ?? 'setup';
if (!['setup', 'status', 'prepare'].includes(command) || process.argv.length > 3) {
  console.error('Usage: node cogai/scripts/setup-voice.mjs [setup|status|prepare]. Do not pass API keys.');
  process.exit(1);
}
const result = spawnSync(python, ['-m', 'app.configure_voice', command], {
  cwd: join(root, 'backend'), stdio: 'inherit', windowsHide: true,
});
if (result.error) console.error('Could not start local voice setup. Check backend dependencies.');
process.exit(result.status ?? 1);
