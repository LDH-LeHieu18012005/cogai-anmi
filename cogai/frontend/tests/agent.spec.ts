import { test, expect } from '@playwright/test';

async function begin(page:import('@playwright/test').Page){
  await page.request.post('/api/session',{data:{accepted:true,adult:true,persist:true}});
  await page.goto('/');
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Chào bạn, mình là AnMi.'})).toBeVisible();
}

test('CogAI companion keeps server chat and handles safety',async({page})=>{
  await begin(page);
  await expect(page.getByRole('img',{name:/AnMi, tác nhân CogAI/})).toBeVisible();
  await expect(page).toHaveTitle('AnMi · Trợ lý AI của CogAI');
  await expect(page.locator('body')).not.toContainText('Mầm');
  await page.screenshot({path:'test-results/cogai-agent-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'Mình đang lo về công việc.',exact:true}).click();
  await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();
  await expect(page.getByText(/Trong chuyện vừa kể/)).toBeVisible();
  await page.reload();
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await expect(page.getByText('Mình đang lo về công việc.',{exact:true})).toBeVisible();
  await page.getByLabel('Tin nhắn của bạn').fill('Tôi muốn chết');
  await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','support');
  await expect(page.getByRole('heading',{name:'Bạn có thể tìm người ở bên'})).toBeVisible();
  await page.screenshot({path:'test-results/cogai-agent-support.png',fullPage:true});
});

test('mobile companion is responsive and missing voice config is explicit',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.request.post('/api/session',{data:{accepted:true,adult:true,persist:false}});
  await page.goto('/');
  await page.getByRole('button',{name:'Mở menu'}).click();
  await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await expect(page.getByRole('img',{name:/AnMi, tác nhân CogAI/})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'test-results/cogai-agent-mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Cài đặt giọng nói',exact:true}).click();
  await expect(page.getByText(/Chưa cấu hình dịch vụ giọng nói trên máy chủ/)).toBeVisible();
  await expect(page.getByRole('button',{name:'Bật trò chuyện giọng nói',exact:true})).toBeDisabled();
});

test('voice records only after consent, reviews transcript, plays and cancels speech',async({page,context})=>{
  await context.grantPermissions(['microphone']);
  await page.route('**/api/config',async route=>{const response=await route.fetch();const data=await response.json();await route.fulfill({json:{...data,voice:{transcription:true,speech:true,max_audio_bytes:2_000_000,max_recording_seconds:45}}});});
  await page.addInitScript(()=>{
    const original=MediaRecorder.prototype.start;
    MediaRecorder.prototype.start=function(...args){this.addEventListener('dataavailable',()=>{document.documentElement.dataset.audioChunk='ready';});return original.apply(this,args);};
  });
  let uploads=0;
  await page.route('**/api/voice/transcribe',async route=>{uploads++;expect(route.request().postDataBuffer()?.length).toBeGreaterThan(0);await route.fulfill({json:{transcript:'Đây là bản chép lời giả lập.',risk:{level:'low',requires_support:false,reason:'test'},audio_stored:false}});});
  // Three seconds of synthetic silence; exercises playback without provider calls.
  const samples=48_000, wav=Buffer.alloc(44+samples*2);
  wav.write('RIFF');wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(1,22);wav.writeUInt32LE(16000,24);wav.writeUInt32LE(32000,28);wav.writeUInt16LE(2,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(samples*2,40);
  await page.route('**/api/voice/stream*',route=>route.fulfill({contentType:'audio/wav',body:wav}));
  await begin(page);
  expect(uploads).toBe(0);
  await page.getByRole('button',{name:'Ghi âm tin nhắn',exact:true}).click();
  await page.getByLabel('Tôi đồng ý gửi âm thanh và phản hồi tới dịch vụ AI và giọng nói đã cấu hình.').check();
  await page.getByRole('button',{name:'Bật trò chuyện giọng nói',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button',{name:'Ghi âm tin nhắn',exact:true}).click();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
  await page.waitForFunction(()=>document.documentElement.dataset.audioChunk==='ready');
  await page.getByRole('button',{name:'Dừng ghi âm',exact:true}).click();
  await expect(page.getByLabel('Tin nhắn của bạn')).toHaveValue('Đây là bản chép lời giả lập.');
  expect(uploads).toBe(1);
  await expect(page.getByRole('log')).not.toContainText('Đây là bản chép lời giả lập.');
  await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();
  await expect(page.getByText(/Trong chuyện vừa kể/)).toBeVisible();
  await page.getByRole('button',{name:'Nghe phản hồi',exact:true}).click();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','speaking');
  await page.getByRole('button',{name:'Dừng âm thanh',exact:true}).click();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','idle');
  await page.getByRole('button',{name:'Cài đặt giọng nói',exact:true}).click();
  await page.getByRole('button',{name:'Tắt giọng nói và thu hồi đồng ý',exact:true}).click();
  await expect(page.getByRole('button',{name:'Bật trò chuyện giọng nói',exact:true})).toBeVisible();
});
