import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    channel: 'chrome',
    headless: true,
    launchOptions:{args:['--use-fake-device-for-media-stream']},
    viewport: { width: 1440, height: 1080 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: process.platform === 'win32'
        ? '.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log'
        : '.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log',
      cwd: '../backend',
      env: { COGAI_MODE: 'demo', COGAI_LLM_API_KEY:'', COGAI_ENVIRONMENT:'test', COGAI_SUPPORT_ACCEPTING:'true', COGAI_DATA_DIR: './test-results/browser-data' },
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: false,
      timeout: 30_000,
    },
    { command: 'npm run dev', url: 'http://127.0.0.1:5173', reuseExistingServer: false, timeout: 30_000 },
  ],
});
