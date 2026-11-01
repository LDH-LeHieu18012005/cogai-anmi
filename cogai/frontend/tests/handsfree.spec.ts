import { test,expect,type Page } from '@playwright/test';

function silence(seconds:number){
  const count=16000*seconds,wav=Buffer.alloc(44+count*2);wav.write('RIFF');wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(1,22);wav.writeUInt32LE(16000,24);wav.writeUInt32LE(32000,28);wav.writeUInt16LE(2,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(count*2,40);return wav.toString('base64');
}

async function prepare(page:Page,maxSeconds=45){
  await page.context().grantPermissions(['microphone']);
  await page.route('**/api/config',async route=>{const response=await route.fetch();await route.fulfill({json:{...await response.json(),voice:{transcription:true,speech:true,max_audio_bytes:2_000_000,max_recording_seconds:maxSeconds}}});});
  await page.addInitScript(()=>{
    const runtime=window as unknown as {hfSignal:number;hfSamples:number;hfStreams:MediaStream[]};runtime.hfSignal=0;runtime.hfSamples=0;runtime.hfStreams=[];
    AnalyserNode.prototype.getFloatTimeDomainData=function(array){array.fill(runtime.hfSignal);runtime.hfSamples++;};
    const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia=async constraints=>{const stream=await original(constraints);runtime.hfStreams.push(stream);return stream;};
  });
  await page.request.post('/api/session',{data:{accepted:true,adult:true,persist:true}});
  await page.goto('/');await page.getByRole('button',{name:'Trò chuyện',exact:true}).click();
  await page.getByRole('button',{name:'Bắt đầu nói chuyện',exact:true}).click();
  await page.getByLabel('Tôi đồng ý gửi âm thanh và phản hồi tới dịch vụ AI và giọng nói đã cấu hình.').check();
  await page.getByRole('button',{name:'Bật trò chuyện giọng nói',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button',{name:'Bắt đầu nói chuyện',exact:true}).click();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
}

async function say(page:Page){
  const initial=await page.evaluate(()=>{const w=window as unknown as {hfSignal:number;hfSamples:number};w.hfSignal=.12;return w.hfSamples;});
  await expect.poll(()=>page.evaluate(()=>(window as unknown as {hfSamples:number}).hfSamples)).toBeGreaterThan(initial+11);
  await page.evaluate(()=>{(window as unknown as {hfSignal:number}).hfSignal=0;});
}

test('speech gate ignores clicks and ends only after sustained speech and silence',async({page})=>{
  await page.goto('/');
  const output=await page.evaluate(async()=>{
    const modulePath='/src/voiceActivity.ts';const {VoiceActivity}=await import(modulePath);const g=new VoiceActivity();
    const results=[g.feed(0,0),g.feed(.1,10),g.feed(0,50),g.feed(0,2000),g.feed(.1,2100),g.feed(.1,2350),g.feed(0,2500),g.feed(0,3500),g.feed(0,3700)];
    return results;
  });
  // A 1.15 s pause is still mid-sentence; the turn ends after 1.3 s of silence.
  expect(output).toEqual([null,null,null,null,null,'start',null,null,'end']);
});

test('one start automatically handles two spoken turns and reopens listening',async({page})=>{
  let turns=0;
  await page.route('**/api/voice/turn',async route=>{turns++;await route.fulfill({json:{heard:true,transcript:`Lượt nói ${turns}`,reply:`Phản hồi ${turns}`,risk:{level:'low',requires_support:false},audio_base64:silence(2),audio_type:'audio/wav',pause_for_support:false}});});
  await prepare(page);
  expect(turns).toBe(0);
  await say(page);
  await expect(page.getByText('Phản hồi 1',{exact:true})).toBeVisible();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','speaking');
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
  await say(page);
  await expect(page.getByText('Phản hồi 2',{exact:true})).toBeVisible();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
  expect(turns).toBe(2);
  await page.getByRole('button',{name:'Kết thúc cuộc gọi',exact:true}).click();
  await expect.poll(()=>page.evaluate(()=>(window as unknown as {hfStreams:MediaStream[]}).hfStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended')))).toBe(true);
  await expect(page.getByRole('button',{name:'Bắt đầu nói chuyện',exact:true})).toBeVisible();
});

test('user speech interrupts playback and a support turn closes the microphone',async({page})=>{
  let turns=0;
  await page.route('**/api/voice/turn',async route=>{turns++;const support=turns===2;await route.fulfill({json:{heard:true,transcript:`Lời nói ${turns}`,reply:support?'Tạm dừng để ưu tiên hỗ trợ.':'AnMi đang nói dài.',risk:{level:support?'high':'low',requires_support:support},audio_base64:silence(support?1:10),audio_type:'audio/wav',pause_for_support:support}});});
  await prepare(page);await say(page);
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','speaking');
  await say(page); // Interrupt via actual analyser activity, without pressing a button.
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
  await expect(page.getByText('Tạm dừng để ưu tiên hỗ trợ.',{exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Bạn có thể tìm người ở bên'})).toBeVisible();
  await expect(page.getByText('Đã tạm dừng cuộc gọi để ưu tiên hỗ trợ.',{exact:true})).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>(window as unknown as {hfStreams:MediaStream[]}).hfStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended')))).toBe(true);
  expect(turns).toBe(2);
});

test('leaving the chat stops the handsfree microphone without uploading silence',async({page})=>{
  let requests=0;await page.route('**/api/voice/turn',route=>{requests++;return route.abort();});
  await prepare(page);
  await page.getByRole('button',{name:'Góc của bạn',exact:true}).click();
  await expect.poll(()=>page.evaluate(()=>(window as unknown as {hfStreams:MediaStream[]}).hfStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended')))).toBe(true);
  expect(requests).toBe(0);
});

test('speech added while the server thinks is kept and old audio is skipped',async({page})=>{
  let turns=0,release!:()=>void;
  const delayed=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/api/voice/turn',async route=>{
    const index=++turns;if(index===1)await delayed;
    await route.fulfill({json:{heard:true,transcript:`Ý nói ${index}`,reply:`Câu trả lời ${index}`,risk:{level:'low',requires_support:false},audio_base64:silence(index===1?15:1),audio_type:'audio/wav',pause_for_support:false}});
  });
  await prepare(page);await say(page);
  await expect.poll(()=>turns).toBe(1);
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','thinking');
  await say(page);
  await expect(page.getByText('Đã giữ phần bạn nói thêm; AnMi sẽ nghe tiếp trước khi trả lời.',{exact:true})).toBeVisible();
  release();
  await expect.poll(()=>turns,{timeout:8000}).toBe(2);
  await expect(page.getByText('Câu trả lời 2',{exact:true})).toBeVisible();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
  await page.getByRole('button',{name:'Kết thúc cuộc gọi',exact:true}).click();
});

test('ending a call discards added speech and cancels the pending turn',async({page})=>{
  let turns=0,cancellations=0,release!:()=>void;
  const delayed=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/api/voice/cancel',async route=>{cancellations++;await route.fulfill({json:{cancelled:true}});});
  await page.route('**/api/voice/turn',async route=>{
    turns++;await delayed;
    await route.fulfill({json:{heard:true,transcript:'Lời cũ',reply:'Phản hồi đã dừng',risk:{level:'low',requires_support:false},audio_base64:silence(1),audio_type:'audio/wav'}}).catch(()=>{});
  });
  await prepare(page);await say(page);
  await expect.poll(()=>turns).toBe(1);
  await say(page);
  await expect(page.getByText('Đã giữ phần bạn nói thêm; AnMi sẽ nghe tiếp trước khi trả lời.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Kết thúc cuộc gọi',exact:true}).click();
  await expect.poll(()=>cancellations).toBe(1);
  release();
  await expect(page.getByRole('button',{name:'Bắt đầu nói chuyện',exact:true})).toBeVisible();
  await expect(page.getByText('Phản hồi đã dừng',{exact:true})).toHaveCount(0);
  await expect.poll(()=>page.evaluate(()=>(window as unknown as {hfStreams:MediaStream[]}).hfStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended')))).toBe(true);
  expect(turns).toBe(1);
});

test('interrupting support speech still pauses the call',async({page})=>{
  await page.route('**/api/voice/turn',route=>route.fulfill({json:{heard:true,transcript:'Lời cần hỗ trợ',reply:'Ưu tiên hỗ trợ ngay.',risk:{level:'high',requires_support:true},audio_base64:silence(15),audio_type:'audio/wav',pause_for_support:true}}));
  await prepare(page);await say(page);
  await expect(page.getByRole('button',{name:'Ngắt lời AnMi',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Ngắt lời AnMi',exact:true}).click();
  await expect(page.getByText('Đã tạm dừng cuộc gọi để ưu tiên hỗ trợ.',{exact:true})).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>(window as unknown as {hfStreams:MediaStream[]}).hfStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended')))).toBe(true);
});

test('a full follow-up buffer clearly pauses capture then submits the saved speech',async({page})=>{
  let turns=0,release!:()=>void;
  const delayed=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/api/voice/turn',async route=>{
    const index=++turns;if(index===1)await delayed;
    await route.fulfill({json:{heard:true,transcript:`Ý ${index}`,reply:`Đáp ${index}`,risk:{level:'low',requires_support:false},audio_base64:silence(1),audio_type:'audio/wav'}});
  });
  await prepare(page,2);await say(page);
  await expect.poll(()=>turns).toBe(1);
  await say(page);
  await expect(page.getByText('Bộ đệm lời nói đã đầy; micro tạm ngừng ghi. Hãy chờ AnMi xử lý phần đã giữ rồi nói tiếp.',{exact:true})).toBeVisible();
  expect(turns).toBe(1);
  release();
  await expect.poll(()=>turns).toBe(2);
  await expect(page.getByText('Đáp 2',{exact:true})).toBeVisible();
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
  await page.getByRole('button',{name:'Kết thúc cuộc gọi',exact:true}).click();
});

test('authentication failure shows the cause and stops capture without retry',async({page})=>{
  let requests=0;
  await page.route('**/api/voice/turn',async route=>{
    requests++;
    await route.fulfill({status:503,json:{detail:'Dịch vụ AI từ chối xác thực (401). Hãy tự kiểm tra khóa trong backend/.env và khởi động lại CogAI.'}});
  });
  await prepare(page);await say(page);
  await expect(page.getByRole('alert').filter({hasText:'401'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Bắt đầu nói chuyện',exact:true})).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>(window as unknown as {hfStreams:MediaStream[]}).hfStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended')))).toBe(true);
  expect(requests).toBe(1);
});

test('progressive turn shows the spoken words once, then the reply; a late error keeps the words',async({page})=>{
  let turns=0;
  await page.route('**/api/voice/turn',async route=>{
    turns++;
    expect(route.request().headers()['x-cogai-progress']).toBe('ndjson');
    const lines=turns===1?[{transcript:'Tớ buồn.'},{result:{heard:true,transcript:'Tớ buồn.',reply:'Mình nghe bạn đây.',risk:{level:'low',requires_support:false},audio_base64:silence(1),audio_type:'audio/wav',pause_for_support:false}}]
      :[{transcript:'Tớ vẫn buồn.'},{error:{status:503,detail:'Dịch vụ tạm thời chưa sẵn sàng.'}}];
    await route.fulfill({contentType:'application/x-ndjson',body:lines.map(l=>JSON.stringify(l)).join('\n')+'\n'});
  });
  await prepare(page);
  await say(page);
  await expect(page.getByText('Mình nghe bạn đây.',{exact:true})).toBeVisible();
  await expect(page.getByText('Tớ buồn.',{exact:true})).toHaveCount(1);
  await expect(page.locator('.companion-figure')).toHaveAttribute('data-state','listening');
  await say(page);
  await expect(page.getByText('Tớ vẫn buồn.',{exact:true})).toBeVisible();
  await expect(page.getByRole('alert')).toContainText('Dịch vụ tạm thời chưa sẵn sàng.');
});
